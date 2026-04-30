from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from app.adapters.loaders.registry import LoaderRegistry
from app.core.config import AppSettings
from app.core.db import sqlite_conn
from app.ports.vector_store import VectorStorePort
from app.services.chunking import RecursiveChunker
from app.services.models import ChunkPayload, IngestionReport


class IngestionService:
    def __init__(self, settings: AppSettings, vector_store: VectorStorePort) -> None:
        self._settings = settings
        self._vector_store = vector_store
        self._chunker = RecursiveChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self._loaders = LoaderRegistry()

    def ingest(self, rebuild_index: bool = False) -> IngestionReport:
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

        chunks: list[ChunkPayload] = []
        changed_files: list[Path] = []
        for path in source_files:
            if rebuild_index or self._file_changed(path):
                changed_files.append(path)
                chunks.extend(self._build_chunks([self._to_document(path)]))
                self._vector_store.delete_by_source(path.relative_to(self._settings.project_root).as_posix())
        self._update_manifest(changed_files, chunks)

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

    def _to_document(self, path: Path) -> Any:
        text = self._loaders.load_text(path)
        relpath = path.relative_to(self._settings.project_root).as_posix()
        return type("Doc", (), {"text": text, "metadata": {"file_path": relpath, "file_name": path.name}})()

    def _build_chunks(self, documents: list[Any]) -> list[ChunkPayload]:
        chunks: list[ChunkPayload] = []

        for document_index, document in enumerate(documents):
            text = getattr(document, "text", "") or ""
            if not text.strip():
                continue

            metadata = dict(getattr(document, "metadata", {}) or {})
            source_path = self._normalize_source_path(metadata)
            
            # Pilar 3: Enriquecimiento con Metadatos (Metadata Normalization)
            word_count = len(text.split())
            base_metadata = {
                "source_path": source_path,
                "file_name": Path(source_path).name,
                "file_type": Path(source_path).suffix.lower(),
                "document_id": metadata.get("file_name") or source_path,
                "word_count": word_count,
                # Hooks para metadatos avanzados (ej. LlamaIndex SummaryExtractor)
                "author": metadata.get("author", "Desconocido"),
                "creation_date": metadata.get("creation_date", "Desconocida"),
            }
            base_metadata.update({key: value for key, value in metadata.items() if value is not None})

            seen_hashes: set[str] = set()
            for chunk_index, chunk_text in enumerate(self._chunker.split_text(text)):
                chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                if chunk_hash in seen_hashes:
                    continue
                seen_hashes.add(chunk_hash)
                chunk_id = f"{document_index}-{chunk_index}"
                chunk_metadata = {
                    **base_metadata,
                    "chunk_index": chunk_index,
                    "chunk_size": len(chunk_text),
                    "chunk_hash": chunk_hash,
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
        payload = [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ]
        self._vector_store.upsert(payload)

    def _file_changed(self, path: Path) -> bool:
        stats = path.stat()
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        rel = path.relative_to(self._settings.project_root).as_posix()
        with sqlite_conn(self._settings) as conn:
            row = conn.execute(
                "SELECT sha256, mtime FROM ingest_manifest WHERE source_path = ?",
                (rel,),
            ).fetchone()
        if not row:
            return True
        old_sha, old_mtime = row
        return old_sha != sha or float(old_mtime) != float(stats.st_mtime)

    def _update_manifest(self, source_files: list[Path], chunks: list[ChunkPayload]) -> None:
        chunks_per_source: dict[str, int] = {}
        for chunk in chunks:
            source = str(chunk.metadata.get("source_path", "unknown"))
            chunks_per_source[source] = chunks_per_source.get(source, 0) + 1
        with sqlite_conn(self._settings) as conn:
            for path in source_files:
                stats = path.stat()
                rel = path.relative_to(self._settings.project_root).as_posix()
                sha = hashlib.sha256(path.read_bytes()).hexdigest()
                conn.execute(
                    """
                    INSERT INTO ingest_manifest(source_path, sha256, size, mtime, chunk_count, last_indexed_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(source_path) DO UPDATE SET
                      sha256=excluded.sha256, size=excluded.size, mtime=excluded.mtime,
                      chunk_count=excluded.chunk_count, last_indexed_at=CURRENT_TIMESTAMP
                    """,
                    (rel, sha, stats.st_size, stats.st_mtime, chunks_per_source.get(rel, 0)),
                )
