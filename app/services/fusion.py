from __future__ import annotations

from collections import defaultdict

from app.services.models import RetrievedChunk


def reciprocal_rank_fusion(rank_lists: list[list[RetrievedChunk]], k: int = 60) -> list[RetrievedChunk]:
    if not rank_lists:
        return []
    scores: dict[str, float] = defaultdict(float)
    chunks_by_key: dict[str, RetrievedChunk] = {}
    for rank_list in rank_lists:
        for rank, chunk in enumerate(rank_list, start=1):
            key = f"{chunk.metadata.get('source_path','unknown')}::{chunk.metadata.get('chunk_index',0)}::{hash(chunk.text)}"
            chunks_by_key[key] = chunk
            scores[key] += 1.0 / (k + rank)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [chunks_by_key[key] for key, _ in ordered]
