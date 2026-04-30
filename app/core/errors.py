from __future__ import annotations


class AppError(RuntimeError):
    code = "app_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class OllamaError(AppError):
    code = "ollama_error"


class VectorStoreError(AppError):
    code = "vector_store_error"


class IngestionError(AppError):
    code = "ingestion_error"


class RetrievalError(AppError):
    code = "retrieval_error"
