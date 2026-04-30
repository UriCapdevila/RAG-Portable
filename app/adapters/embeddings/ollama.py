from __future__ import annotations

from llama_index.embeddings.ollama import OllamaEmbedding


class OllamaEmbeddingAdapter:
    def __init__(self, model_name: str, base_url: str) -> None:
        self._embedder = OllamaEmbedding(model_name=model_name, base_url=base_url)

    def embed_query(self, text: str) -> list[float]:
        return list(self._embedder.get_query_embedding(text))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(self._embedder.get_text_embedding(text)) for text in texts]
