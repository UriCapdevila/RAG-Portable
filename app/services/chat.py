from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

import structlog

from app.core.config import AppSettings
from app.core.prompts import build_system_prompt, build_user_prompt
from app.ports.embeddings import EmbeddingProviderPort
from app.ports.keyword_index import KeywordIndexPort
from app.ports.llm import LLMProviderPort
from app.ports.reranker import RerankerPort
from app.ports.vector_store import VectorStorePort
from app.services.fusion import reciprocal_rank_fusion
from app.services.grounding_validator import is_grounded
from app.services.intent_detector import is_small_talk
from app.services.models import ChatResult, RetrievedChunk
from app.services.personas import PersonaService
from app.services.query_processor import QueryProcessor
from app.services.tool_dispatcher import ToolDispatcher
from app.services.tools.registry import ToolRegistry
from app.services.tracing import TraceService

logger = structlog.get_logger("chat")


class ChatService:
    def __init__(
        self,
        settings: AppSettings,
        llm: LLMProviderPort,
        embed: EmbeddingProviderPort,
        vector_store: VectorStorePort,
        keyword_index: KeywordIndexPort,
        reranker: RerankerPort,
        personas: PersonaService,
        tools: ToolRegistry,
        traces: TraceService,
    ) -> None:
        self._settings = settings
        self._llm = llm
        self._embed = embed
        self._vector_store = vector_store
        self._keyword_index = keyword_index
        self._reranker = reranker
        self._personas = personas
        self._query = QueryProcessor(llm)
        self._dispatcher = ToolDispatcher(llm, tools, max_steps=settings.max_react_steps)
        self._traces = traces

    async def answer(self, question: str) -> ChatResult:
        request_id = str(uuid.uuid4())
        persona = self._personas.get_active()
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question cannot be empty.")

        total_start = time.perf_counter()
        log = logger.bind(request_id=request_id, persona=persona.slug, question=cleaned_question)
        log.info("chat.request.received")

        if is_small_talk(cleaned_question):
            log.info("chat.smalltalk.detected")
            return await self._answer_small_talk(request_id, persona, cleaned_question, log, total_start)

        if not self.vector_store_ready():
            raise RuntimeError("The vector store is empty. Run ingestion first.")

        with self._traces.stage(request_id, persona.slug, "query_rewrite"):
            optimized_query = cleaned_question
            if persona.parameters.use_query_rewrite:
                stage_start = time.perf_counter()
                optimized_query = await asyncio.to_thread(self._query.rewrite, cleaned_question)
                log.info(
                    "chat.query_rewrite.done",
                    duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
                    optimized_query=optimized_query,
                )

        top_k = max(1, persona.parameters.similarity_top_k)
        retrieve_start = time.perf_counter()
        if persona.parameters.use_hybrid_retrieval:
            with self._traces.stage(request_id, persona.slug, "vector_retrieve"):
                vector_task = asyncio.create_task(
                    asyncio.to_thread(self._vector_store.query, optimized_query, top_k * 2)
                )
            with self._traces.stage(request_id, persona.slug, "keyword_retrieve"):
                keyword_task = asyncio.create_task(
                    asyncio.to_thread(self._keyword_index.query, optimized_query, top_k * 2)
                )
            vector_rows, keyword_rows = await asyncio.gather(vector_task, keyword_task)
            vector_chunks = [RetrievedChunk(**row) for row in vector_rows]
            keyword_chunks = [RetrievedChunk(**row) for row in keyword_rows]
            with self._traces.stage(request_id, persona.slug, "fusion"):
                chunks = reciprocal_rank_fusion([vector_chunks, keyword_chunks])
            retrieval_strategy = "hybrid"
        else:
            with self._traces.stage(request_id, persona.slug, "vector_retrieve"):
                vector_rows = await asyncio.to_thread(self._vector_store.query, optimized_query, top_k * 2)
                vector_chunks = [RetrievedChunk(**row) for row in vector_rows]
            chunks = vector_chunks
            retrieval_strategy = "vector"

        log.info(
            "chat.retrieval.done",
            strategy=retrieval_strategy,
            vector_hits=len(vector_chunks),
            total_hits=len(chunks),
            duration_ms=round((time.perf_counter() - retrieve_start) * 1000, 2),
        )

        if not chunks:
            log.warning("chat.retrieval.empty")
            return ChatResult(
                answer=persona.fallback_message,
                model=self._llm.model,
                sources=[],
                retrieved_chunks=[],
                grounded=True,
                retrieval_strategy=retrieval_strategy,
            )

        with self._traces.stage(request_id, persona.slug, "rerank"):
            stage_start = time.perf_counter()
            ranked_chunks = await asyncio.to_thread(
                self._reranker.rerank,
                cleaned_question,
                chunks,
                max(1, persona.parameters.rerank_top_k),
            )
            top_score = ranked_chunks[0].score if ranked_chunks else None
            log.info(
                "chat.rerank.done",
                duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
                kept=len(ranked_chunks),
                top_score=top_score,
            )

        sources = self._collect_sources(ranked_chunks)

        if (ranked_chunks[0].score or 0.0) < persona.parameters.grounding_threshold:
            log.warning(
                "chat.grounding.below_threshold",
                top_score=ranked_chunks[0].score,
                threshold=persona.parameters.grounding_threshold,
            )
            return ChatResult(
                answer=persona.fallback_message,
                model=self._llm.model,
                sources=sources,
                retrieved_chunks=ranked_chunks,
                grounded=True,
                retrieval_strategy=retrieval_strategy,
            )

        context_blocks = [
            f"[Fuente {index}] {chunk.metadata.get('source_path', 'desconocido')}\n{chunk.text.strip()}"
            for index, chunk in enumerate(ranked_chunks, start=1)
        ]
        user_prompt = build_user_prompt(cleaned_question, context_blocks)
        system_prompt = build_system_prompt(persona, [])
        with self._traces.stage(request_id, persona.slug, "generate"):
            stage_start = time.perf_counter()
            if persona.parameters.tool_mode == "off":
                answer = await asyncio.to_thread(
                    self._llm.generate,
                    system_prompt,
                    user_prompt,
                    temperature=persona.parameters.temperature,
                )
            else:
                answer = await asyncio.to_thread(self._dispatcher.run, system_prompt, user_prompt, {})
            log.info(
                "chat.generate.done",
                duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
                model=self._llm.model,
            )

        grounded = is_grounded(answer, [source["file_name"] for source in sources])
        if not grounded:
            log.warning("chat.grounding.invalid_citation", answer_preview=answer[:160])

        log.info(
            "chat.request.completed",
            total_duration_ms=round((time.perf_counter() - total_start) * 1000, 2),
            strategy=retrieval_strategy,
            grounded=grounded,
        )

        return ChatResult(
            answer=answer,
            model=self._llm.model,
            sources=sources,
            retrieved_chunks=ranked_chunks,
            grounded=grounded,
            retrieval_strategy=retrieval_strategy,
        )

    async def _answer_small_talk(
        self,
        request_id: str,
        persona,
        question: str,
        log,
        total_start: float,
    ) -> ChatResult:
        system_prompt = (
            f"Eres {persona.name}. Tono: {persona.tone}. Idioma: {persona.language}.\n"
            "Responde de forma breve, natural y cordial. No cites fuentes ni inventes datos. "
            "Si el usuario pregunta cosas factuales, sugiere que pueden indagarlo en sus documentos."
        )
        with self._traces.stage(request_id, persona.slug, "generate_smalltalk"):
            stage_start = time.perf_counter()
            answer = await asyncio.to_thread(
                self._llm.generate,
                system_prompt,
                question,
                temperature=max(persona.parameters.temperature, 0.3),
            )
            log.info(
                "chat.smalltalk.done",
                duration_ms=round((time.perf_counter() - stage_start) * 1000, 2),
            )
        log.info(
            "chat.request.completed",
            total_duration_ms=round((time.perf_counter() - total_start) * 1000, 2),
            strategy="smalltalk",
            grounded=True,
        )
        return ChatResult(
            answer=answer,
            model=self._llm.model,
            sources=[],
            retrieved_chunks=[],
            grounded=True,
            retrieval_strategy="smalltalk",
        )

    def health_check(self) -> dict[str, Any]:
        return {
            "ollama_connected": self._llm.health_check(),
            "vector_store_ready": self.vector_store_ready(),
            "chat_model": self._settings.chat_model,
            "embedding_model": self._settings.embedding_model,
        }

    def vector_store_ready(self) -> bool:
        return self._vector_store.is_ready()

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
