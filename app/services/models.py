from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ChunkPayload:
    chunk_id: str
    text: str
    metadata: dict[str, Any]


@dataclass(slots=True)
class IngestionReport:
    files_processed: int
    chunks_created: int
    vector_table: str
    vector_db_path: str
    embedding_model: str
    source_files: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RetrievedChunk:
    text: str
    score: float | None
    metadata: dict[str, Any]


@dataclass(slots=True)
class ChatResult:
    answer: str
    model: str
    sources: list[dict[str, Any]]
    retrieved_chunks: list[RetrievedChunk]
    grounded: bool = True
    retrieval_strategy: str = "vector"


@dataclass(slots=True)
class SourceRecord:
    source_path: str
    file_name: str
    file_type: str
    file_size: int | None
    last_modified: str | None
    chunk_count: int
    is_indexed: bool
    is_available: bool


@dataclass(slots=True)
class UploadReport:
    uploaded_files: list[str] = field(default_factory=list)
    rejected_files: list[str] = field(default_factory=list)
