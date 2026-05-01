from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.config import AppSettings
from app.core.db import init_sqlite
from app.services.chat import ChatService
from app.services.conversation_history import ConversationHistoryService
from app.services.models import RetrievedChunk
from app.services.personas import Persona, PersonaParameters
from app.services.tools.registry import ToolRegistry
from app.services.tracing import TraceService


class FakeLLM:
    model = "fake-llm"

    def __init__(self) -> None:
        self.last_disambiguation_prompt = ""

    def health_check(self) -> bool:
        return True

    def generate(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.1) -> str:
        _ = temperature
        if "reformula consultas ambiguas" in system_prompt:
            self.last_disambiguation_prompt = user_prompt
            return "¿Cuál es el costo del plan premium?"
        return "El costo es 20 USD [precios.md]."


class FakeEmbeddings:
    def embed_query(self, text: str) -> list[float]:
        _ = text
        return [0.0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        _ = texts
        return [[0.0]]


class FakeVectorStore:
    def __init__(self, score: float = 0.9) -> None:
        self.last_query = ""
        self._score = score

    def is_ready(self) -> bool:
        return True

    def count(self) -> int:
        return 1

    def query(self, query_text: str, top_k: int) -> list[dict]:
        _ = top_k
        self.last_query = query_text
        return [
            {
                "text": "El plan premium cuesta 20 USD por mes.",
                "score": self._score,
                "metadata": {
                    "source_path": "data/raw/precios.md",
                    "file_name": "precios.md",
                    "file_type": "md",
                    "chunk_index": 0,
                },
            }
        ]

    def upsert(self, chunks: list[dict]) -> None:
        _ = chunks

    def delete_by_source(self, source_path: str) -> bool:
        _ = source_path
        return True


class FakeKeywordIndex:
    def query(self, query_text: str, top_k: int) -> list[dict]:
        _ = query_text
        _ = top_k
        return []


class FakeReranker:
    def rerank(self, query: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        _ = query
        return chunks[:top_k]


class FakePersonaService:
    def __init__(self, fallback_message: str = "Fallback por falta de evidencia.") -> None:
        self._persona = Persona(
            slug="default",
            name="Default",
            fallback_message=fallback_message,
            parameters=PersonaParameters(
                use_query_rewrite=False,
                use_hybrid_retrieval=False,
                similarity_top_k=1,
                rerank_top_k=1,
                grounding_threshold=0.15,
                tool_mode="off",
            ),
        )

    def get_active(self) -> Persona:
        return self._persona


def _build_settings(tmp_path: Path) -> AppSettings:
    settings = AppSettings(project_root=tmp_path)
    settings.ensure_directories()
    init_sqlite(settings)
    return settings


def test_chat_disambiguates_with_history(tmp_path: Path):
    settings = _build_settings(tmp_path)
    llm = FakeLLM()
    vector_store = FakeVectorStore(score=0.9)
    history = ConversationHistoryService(settings)
    persona_service = FakePersonaService()
    traces = TraceService(settings)

    chat = ChatService(
        settings=settings,
        llm=llm,
        embed=FakeEmbeddings(),
        vector_store=vector_store,
        keyword_index=FakeKeywordIndex(),
        reranker=FakeReranker(),
        personas=persona_service,
        tools=ToolRegistry(),
        traces=traces,
        history=history,
    )

    conversation_id = history.create("default")
    history.append_message(conversation_id, "user", "Quiero saber del plan premium.")
    history.append_message(conversation_id, "assistant", "Claro, ¿te interesa precio o características?")

    result = asyncio.run(chat.answer("¿Y cuánto cuesta eso?", conversation_id))

    assert result.conversation_id == conversation_id
    assert "plan premium" in vector_store.last_query.lower()
    assert "Historial reciente de la conversación" in llm.last_disambiguation_prompt
    assert result.answer.startswith("El costo")


def test_chat_history_does_not_override_grounding_fallback(tmp_path: Path):
    settings = _build_settings(tmp_path)
    llm = FakeLLM()
    vector_store = FakeVectorStore(score=0.01)
    history = ConversationHistoryService(settings)
    persona_service = FakePersonaService(fallback_message="Sin evidencia suficiente.")
    traces = TraceService(settings)

    chat = ChatService(
        settings=settings,
        llm=llm,
        embed=FakeEmbeddings(),
        vector_store=vector_store,
        keyword_index=FakeKeywordIndex(),
        reranker=FakeReranker(),
        personas=persona_service,
        tools=ToolRegistry(),
        traces=traces,
        history=history,
    )

    conversation_id = history.create("default")
    history.append_message(conversation_id, "user", "Dijiste que premium era caro.")
    history.append_message(conversation_id, "assistant", "Sí, depende del plan.")

    result = asyncio.run(chat.answer("¿Cuánto cuesta eso?", conversation_id))

    assert result.answer == "Sin evidencia suficiente."
    assert result.grounded is True
