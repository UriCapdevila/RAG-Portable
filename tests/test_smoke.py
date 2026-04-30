from app.services.fusion import reciprocal_rank_fusion
from app.services.grounding_validator import is_grounded
from app.services.models import RetrievedChunk


def test_grounding_validator_ok():
    answer = "La política está en [manual.md]."
    assert is_grounded(answer, ["manual.md"]) is True


def test_grounding_validator_fail():
    answer = "La política está en [otro.md]."
    assert is_grounded(answer, ["manual.md"]) is False


def test_rrf_returns_items():
    chunks_a = [RetrievedChunk(text="a", score=0.1, metadata={"source_path": "a.md", "chunk_index": 0})]
    chunks_b = [RetrievedChunk(text="b", score=0.2, metadata={"source_path": "b.md", "chunk_index": 0})]
    merged = reciprocal_rank_fusion([chunks_a, chunks_b])
    assert len(merged) == 2
