from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.lancedb import LanceDBVectorStore

from app.core.config import AppSettings
from app.services.chunking import RecursiveChunker
from app.services.models import ChunkPayload, IngestionReport


class IngestionService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._chunker = RecursiveChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    def ingest(self, rebuild_index: bool = True) -> IngestionReport:
        self._settings.ensure_directories()
        source_files = self._discover_source_files()
        if not source_files:
            return IngestionReport(
                files_processed=0,
                chunks_created=0,
                vector_table=self._settings.vector_table_name,
                vector_db_path=str(self._settings.vector_db_dir),
                embedding_model=self._settings.embedding_model,
            )

        if rebuild_index:
            self._reset_vector_store()

        documents = self._load_documents(source_files)
        chunks = self._build_chunks(documents)

        if chunks:
            self._index_chunks(chunks)

        return IngestionReport(
            files_processed=len(source_files),
            chunks_created=len(chunks),
            vector_table=self._settings.vector_table_name,
            vector_db_path=str(self._settings.vector_db_dir),
            embedding_model=self._settings.embedding_model,
            source_files=[
                path.relative_to(self._settings.project_root).as_posix()
                for path in source_files
            ],
        )

    def _discover_source_files(self) -> list[Path]:
        files = [
            path
            for path in self._settings.raw_data_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in self._settings.supported_extensions
        ]
        return sorted(files)

    def _load_documents(self, source_files: list[Path]) -> list[Any]:
        reader = SimpleDirectoryReader(
            input_files=[str(path) for path in source_files],
            filename_as_id=True,
        )
        return reader.load_data()

    def _build_chunks(self, documents: list[Any]) -> list[ChunkPayload]:
        chunks: list[ChunkPayload] = []

        for document_index, document in enumerate(documents):
            text = getattr(document, "text", "") or ""
            if not text.strip():
                continue

            metadata = dict(getattr(document, "metadata", {}) or {})
            source_path = self._normalize_source_path(metadata)
            base_metadata = {
                "source_path": source_path,
                "file_name": Path(source_path).name,
                "file_type": Path(source_path).suffix.lower(),
                "document_id": metadata.get("file_name") or source_path,
            }
            base_metadata.update({key: value for key, value in metadata.items() if value is not None})

            for chunk_index, chunk_text in enumerate(self._chunker.split_text(text)):
                chunk_id = f"{document_index}-{chunk_index}"
                chunk_metadata = {
                    **base_metadata,
                    "chunk_index": chunk_index,
                    "chunk_size": len(chunk_text),
                }
                chunks.append(ChunkPayload(chunk_id=chunk_id, text=chunk_text, metadata=chunk_metadata))

        return chunks

    def _normalize_source_path(self, metadata: dict[str, Any]) -> str:
        raw_value = metadata.get("file_path") or metadata.get("filename") or "unknown"
        source_path = Path(str(raw_value))
        try:
            relative_path = source_path.resolve().relative_to(self._settings.project_root.resolve())
            return relative_path.as_posix()
        except Exception:
            return str(source_path).replace("\\", "/")

    def _index_chunks(self, chunks: list[ChunkPayload]) -> None:
        embed_model = OllamaEmbedding(
            model_name=self._settings.embedding_model,
            base_url=self._settings.ollama_base_url,
        )
        vector_store = LanceDBVectorStore(
            uri=str(self._settings.vector_db_dir),
            table_name=self._settings.vector_table_name,
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(
            nodes=[],
            storage_context=storage_context,
            embed_model=embed_model,
            show_progress=True,
        )

        nodes = [
            TextNode(
                id_=chunk.chunk_id,
                text=chunk.text,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]
        index.insert_nodes(nodes)

    def _reset_vector_store(self) -> None:
        if self._settings.vector_db_dir.exists():
            shutil.rmtree(self._settings.vector_db_dir, ignore_errors=True)
        self._settings.vector_db_dir.mkdir(parents=True, exist_ok=True)
