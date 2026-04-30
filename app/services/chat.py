from __future__ import annotations

import asyncio
from typing import Any

import lancedb
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.lancedb import LanceDBVectorStore

from app.core.config import AppSettings
from app.core.prompts import RAG_SYSTEM_PROMPT, QUERY_REWRITE_PROMPT
from app.services.models import ChatResult, RetrievedChunk
from app.services.ollama_client import OllamaChatClient


class ChatService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._ollama = OllamaChatClient(
            base_url=settings.ollama_base_url,
            model=settings.chat_model,
        )

    async def answer(self, question: str) -> ChatResult:
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        if not self.vector_store_ready():
            raise RuntimeError("The vector store is empty. Run ingestion first.")

        # Pilar 4: Normalización de la Consulta (Query Processing)
        optimized_query = await self._rewrite_query(cleaned_question)

        # Recuperamos el doble de chunks requeridos para tener margen en el Re-ranking
        retriever = self._build_index().as_retriever(
            similarity_top_k=self._settings.similarity_top_k * 2
        )
        retrieved_nodes = await asyncio.to_thread(retriever.retrieve, optimized_query)

        chunks = [
            RetrievedChunk(
                text=node.node.get_content(),
                score=node.score,
                metadata=dict(node.node.metadata or {}),
            )
            for node in retrieved_nodes
        ]

        if not chunks:
            return ChatResult(
                answer="No encontre contexto suficiente para responder con seguridad.",
                model=self._ollama.model,
                sources=[],
                retrieved_chunks=[],
            )

        # Pilar 5: Post-procesamiento y Re-ranking
        ranked_chunks = self._rerank_chunks(cleaned_question, chunks)[:self._settings.similarity_top_k]

        user_prompt = self._build_user_prompt(cleaned_question, ranked_chunks)
        answer = await asyncio.to_thread(
            self._ollama.generate,
            RAG_SYSTEM_PROMPT,
            user_prompt,
        )

        return ChatResult(
            answer=answer,
            model=self._ollama.model,
            sources=self._collect_sources(ranked_chunks),
            retrieved_chunks=ranked_chunks,
        )

    def health_check(self) -> dict[str, Any]:
        return {
            "ollama_connected": self._ollama.health_check(),
            "vector_store_ready": self.vector_store_ready(),
            "chat_model": self._settings.chat_model,
            "embedding_model": self._settings.embedding_model,
        }

    def vector_store_ready(self) -> bool:
        try:
            db = lancedb.connect(str(self._settings.vector_db_dir))
            return self._settings.vector_table_name in db.table_names()
        except Exception:
            return False

    def _build_index(self) -> VectorStoreIndex:
        vector_store = LanceDBVectorStore(
            uri=str(self._settings.vector_db_dir),
            table_name=self._settings.vector_table_name,
        )
        embed_model = OllamaEmbedding(
            model_name=self._settings.embedding_model,
            base_url=self._settings.ollama_base_url,
        )
        return VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model,
        )

    def _build_user_prompt(self, question: str, chunks: list[RetrievedChunk]) -> str:
        context_blocks = []
        for index, chunk in enumerate(chunks, start=1):
            source = chunk.metadata.get("source_path", "desconocido")
            context_blocks.append(
                f"[Fuente {index}] {source}\n{chunk.text.strip()}"
            )

        joined_context = "\n\n".join(context_blocks)
        return (
            "Contexto recuperado:\n"
            f"{joined_context}\n\n"
            "Pregunta del usuario:\n"
            f"{question}\n\n"
            "Instrucciones:\n"
            "- Responde solo con base en el contexto.\n"
            "- Si falta evidencia, indicalo.\n"
            "- Cita las fuentes relevantes al final."
        )

    def _collect_sources(self, chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        sources: list[dict[str, Any]] = []

        for chunk in chunks:
            source_path = str(chunk.metadata.get("source_path", "desconocido"))
            if source_path in seen:
                continue
            seen.add(source_path)
            sources.append(
                {
                    "source_path": source_path,
                    "file_name": chunk.metadata.get("file_name", source_path),
                    "file_type": chunk.metadata.get("file_type", ""),
                }
            )

        return sources

    async def _rewrite_query(self, original_query: str) -> str:
        """
        Utiliza el LLM para reformular la consulta, expandir sinónimos y mejorar la búsqueda vectorial.
        """
        try:
            prompt = QUERY_REWRITE_PROMPT.format(question=original_query)
            rewritten = await asyncio.to_thread(
                self._ollama.generate,
                "Eres un optimizador de búsquedas semánticas.",
                prompt
            )
            # Limpiamos posibles comillas que añada el LLM
            return rewritten.strip(' "\'\n')
        except Exception:
            return original_query

    def _rerank_chunks(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """
        Hook arquitectónico para implementar modelos de Re-ranking (Cross-Encoders).
        Por defecto, preserva y asegura el orden por score de similitud (Top-K).
        """
        return sorted(chunks, key=lambda x: x.score or 0.0, reverse=True)

