from __future__ import annotations

from typing import Any

import asyncio
import lancedb
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.lancedb import LanceDBVectorStore

from app.core.config import AppSettings
from app.core.errors import VectorStoreError
from app.services.models import RetrievedChunk


class LanceDBVectorStoreAdapter:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def is_ready(self) -> bool:
        try:
            db = lancedb.connect(str(self._settings.vector_db_dir))
            return self._settings.vector_table_name in db.table_names()
        except Exception:
            return False

    def count(self) -> int:
        if not self.is_ready():
            return 0
        db = lancedb.connect(str(self._settings.vector_db_dir))
        table = db.open_table(self._settings.vector_table_name)
        return len(table.to_arrow())

    def query(self, query_text: str, top_k: int) -> list[dict[str, Any]]:
        retriever = self._build_index().as_retriever(similarity_top_k=top_k)
        try:
            nodes = retriever.retrieve(query_text)
        except Exception as exc:
            raise VectorStoreError(str(exc)) from exc
        return [
            {
                "text": node.node.get_content(),
                "score": node.score,
                "metadata": dict(node.node.metadata or {}),
            }
            for node in nodes
        ]

    def upsert(self, chunks: list[dict[str, Any]]) -> None:
        embed_model = OllamaEmbedding(
            model_name=self._settings.embedding_model,
            base_url=self._settings.ollama_base_url,
        )
        vector_store = LanceDBVectorStore(
            uri=str(self._settings.vector_db_dir),
            table_name=self._settings.vector_table_name,
        )
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)
        nodes = [
            TextNode(id_=chunk["chunk_id"], text=chunk["text"], metadata=chunk["metadata"])
            for chunk in chunks
        ]
        index.insert_nodes(nodes)

    def delete_by_source(self, source_path: str) -> bool:
        if not self.is_ready():
            return False
        db = lancedb.connect(str(self._settings.vector_db_dir))
        table = db.open_table(self._settings.vector_table_name)
        escaped = source_path.replace("'", "''")
        table.delete(f"metadata.source_path = '{escaped}'")
        return True

    def source_chunk_counts(self) -> dict[str, int]:
        if not self.is_ready():
            return {}
        db = lancedb.connect(str(self._settings.vector_db_dir))
        table = db.open_table(self._settings.vector_table_name)
        rows = table.to_arrow().to_pylist()
        counts: dict[str, int] = {}
        for row in rows:
            metadata = row.get("metadata")
            source = metadata.get("source_path") if isinstance(metadata, dict) else "unknown"
            source = str(source or "unknown")
            counts[source] = counts.get(source, 0) + 1
        return counts

    def _build_index(self) -> VectorStoreIndex:
        vector_store = LanceDBVectorStore(
            uri=str(self._settings.vector_db_dir),
            table_name=self._settings.vector_table_name,
        )
        embed_model = OllamaEmbedding(
            model_name=self._settings.embedding_model,
            base_url=self._settings.ollama_base_url,
        )
        return VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)


class LanceDBKeywordIndexAdapter:
    def query(self, query_text: str, top_k: int) -> list[dict[str, Any]]:
        _ = query_text
        _ = top_k
        return []
