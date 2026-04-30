from __future__ import annotations

from app.services.models import RetrievedChunk

try:
    from sentence_transformers import CrossEncoder
except Exception:  # noqa: BLE001
    CrossEncoder = None  # type: ignore


class CrossEncoderRerankerAdapter:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None

    def rerank(self, query: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        if not chunks or CrossEncoder is None:
            return chunks[:top_k]
        if self._model is None:
            self._model = CrossEncoder(self._model_name)
        pairs = [[query, chunk.text] for chunk in chunks]
        scores = self._model.predict(pairs)
        enriched = []
        for chunk, score in zip(chunks, scores, strict=False):
            enriched.append(RetrievedChunk(text=chunk.text, score=float(score), metadata=chunk.metadata))
        enriched.sort(key=lambda item: item.score or 0.0, reverse=True)
        return enriched[:top_k]
