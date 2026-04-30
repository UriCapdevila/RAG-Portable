from __future__ import annotations

from app.services.models import RetrievedChunk


class PassthroughRerankerAdapter:
    def rerank(self, query: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        _ = query
        ranked = sorted(chunks, key=lambda x: x.score or 0.0, reverse=True)
        return ranked[:top_k]
