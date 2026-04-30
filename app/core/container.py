from __future__ import annotations

from functools import lru_cache

from app.adapters.embeddings.ollama import OllamaEmbeddingAdapter
from app.adapters.llm.ollama import OllamaLLMAdapter
from app.adapters.reranker.cross_encoder import CrossEncoderRerankerAdapter
from app.adapters.reranker.passthrough import PassthroughRerankerAdapter
from app.adapters.vector_store.lancedb import LanceDBKeywordIndexAdapter, LanceDBVectorStoreAdapter
from app.core.config import AppSettings, settings
from app.services.chat import ChatService
from app.services.ingestion import IngestionService
from app.services.personas import PersonaService
from app.services.tools.builtin import GetDocumentTool, ListSourcesTool
from app.services.tools.registry import ToolRegistry
from app.services.tracing import TraceService
from app.services.workspace import WorkspaceService


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return settings


@lru_cache(maxsize=1)
def get_llm() -> OllamaLLMAdapter:
    cfg = get_settings()
    return OllamaLLMAdapter(base_url=cfg.ollama_base_url, model=cfg.chat_model)


@lru_cache(maxsize=1)
def get_embeddings() -> OllamaEmbeddingAdapter:
    cfg = get_settings()
    return OllamaEmbeddingAdapter(model_name=cfg.embedding_model, base_url=cfg.ollama_base_url)


@lru_cache(maxsize=1)
def get_vector_store() -> LanceDBVectorStoreAdapter:
    return LanceDBVectorStoreAdapter(get_settings())


@lru_cache(maxsize=1)
def get_keyword_index() -> LanceDBKeywordIndexAdapter:
    return LanceDBKeywordIndexAdapter()


@lru_cache(maxsize=1)
def get_reranker():
    cfg = get_settings()
    if cfg.reranker_enabled:
        return CrossEncoderRerankerAdapter(cfg.reranker_model)
    return PassthroughRerankerAdapter()


@lru_cache(maxsize=1)
def get_persona_service() -> PersonaService:
    return PersonaService(get_settings())


@lru_cache(maxsize=1)
def get_trace_service() -> TraceService:
    return TraceService(get_settings())


@lru_cache(maxsize=1)
def get_workspace_service() -> WorkspaceService:
    return WorkspaceService(get_settings(), get_vector_store())


@lru_cache(maxsize=1)
def get_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    workspace = get_workspace_service()
    registry.register(ListSourcesTool(workspace))
    registry.register(GetDocumentTool(get_settings().project_root))
    return registry


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    cfg = get_settings()
    return ChatService(
        settings=cfg,
        llm=get_llm(),
        embed=get_embeddings(),
        vector_store=get_vector_store(),
        keyword_index=get_keyword_index(),
        reranker=get_reranker(),
        personas=get_persona_service(),
        tools=get_tool_registry(),
        traces=get_trace_service(),
    )


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    return IngestionService(get_settings(), get_vector_store())
