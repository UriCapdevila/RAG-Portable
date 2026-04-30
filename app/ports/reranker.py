from __future__ import annotations

from typing import Protocol

from app.services.models import RetrievedChunk


class RerankerPort(Protocol):
    def rerank(self, query: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]: ...
