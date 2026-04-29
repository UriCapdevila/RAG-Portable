from __future__ import annotations

import asyncio
from dataclasses import asdict
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.chat import ChatService
from app.services.ingestion import IngestionService
from app.services.models import SourceRecord, UploadReport
from app.services.ollama_client import OllamaClientError
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/api", tags=["rag"])


class IngestionRequest(BaseModel):
    rebuild_index: bool = Field(
        default=True,
        description="If true, recreates the vector store from the current raw files.",
    )


class IngestionResponse(BaseModel):
    files_processed: int
    chunks_created: int
    vector_table: str
    vector_db_path: str
    embedding_model: str
    source_files: list[str]


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question.")


class HealthResponse(BaseModel):
    ollama_connected: bool
    vector_store_ready: bool
    chat_model: str
    embedding_model: str


class SourceResponse(BaseModel):
    source_path: str
    file_name: str
    file_type: str


class ChunkResponse(BaseModel):
    text: str
    score: float | None
    metadata: dict[str, Any]


class ChatResponse(BaseModel):
    answer: str
    model: str
    sources: list[SourceResponse]
    retrieved_chunks: list[ChunkResponse]


class SourceRecordResponse(BaseModel):
    source_path: str
    file_name: str
    file_type: str
    file_size: int | None
    last_modified: str | None
    chunk_count: int
    is_indexed: bool
    is_available: bool


class UploadResponse(BaseModel):
    uploaded_files: list[str]
    rejected_files: list[str]


class DashboardSummaryResponse(BaseModel):
    total_sources: int
    indexed_sources: int
    total_chunks: int
    raw_data_path: str
    vector_db_path: str


class StudioCardResponse(BaseModel):
    id: str
    title: str
    description: str
    value: str
    status: str
    action: str | None = None


class DashboardResponse(BaseModel):
    health: HealthResponse
    sources: list[SourceRecordResponse]
    summary: DashboardSummaryResponse
    studio_cards: list[StudioCardResponse]


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    return IngestionService(settings)


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService(settings)


@lru_cache(maxsize=1)
def get_workspace_service() -> WorkspaceService:
    return WorkspaceService(settings)


def _build_health_response() -> HealthResponse:
    return HealthResponse(**get_chat_service().health_check())


def _serialize_source(source: SourceRecord) -> SourceRecordResponse:
    return SourceRecordResponse(**asdict(source))


def _serialize_upload_report(report: UploadReport) -> UploadResponse:
    return UploadResponse(**asdict(report))


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return _build_health_response()


@router.get("/sources", response_model=list[SourceRecordResponse])
async def list_sources() -> list[SourceRecordResponse]:
    sources = await asyncio.to_thread(get_workspace_service().list_sources)
    return [_serialize_source(source) for source in sources]


@router.post("/sources/upload", response_model=UploadResponse)
async def upload_sources(files: list[UploadFile] = File(...)) -> UploadResponse:
    payload: list[tuple[str, bytes]] = []
    for file in files:
        payload.append((file.filename or "source", await file.read()))

    report = await asyncio.to_thread(get_workspace_service().save_uploaded_files, payload)
    return _serialize_upload_report(report)


class DeleteSourceRequest(BaseModel):
    source_path: str = Field(..., min_length=1, description="Relative source path to delete.")


class DeleteSourceResponse(BaseModel):
    source_path: str
    file_deleted: bool
    chunks_deleted: bool


@router.post("/sources/delete", response_model=DeleteSourceResponse)
async def delete_source(request: DeleteSourceRequest) -> DeleteSourceResponse:
    result = await asyncio.to_thread(
        get_workspace_service().delete_source,
        request.source_path,
    )
    if not result["file_deleted"] and not result["chunks_deleted"]:
        raise HTTPException(
            status_code=404,
            detail=f"La fuente '{request.source_path}' no existe o ya fue eliminada.",
        )
    return DeleteSourceResponse(
        source_path=request.source_path,
        file_deleted=result["file_deleted"],
        chunks_deleted=result["chunks_deleted"],
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard() -> DashboardResponse:
    health = _build_health_response()
    sources = await asyncio.to_thread(get_workspace_service().list_sources)

    summary = DashboardSummaryResponse(
        total_sources=len(sources),
        indexed_sources=sum(1 for source in sources if source.is_indexed),
        total_chunks=sum(source.chunk_count for source in sources),
        raw_data_path=str(settings.raw_data_dir),
        vector_db_path=str(settings.vector_db_dir),
    )

    studio_cards = [
        StudioCardResponse(
            id="reindex",
            title="Reindexar",
            description="Reconstruye el indice vectorial con las fuentes actuales.",
            value=f"{summary.total_sources} fuentes",
            status="action",
            action="reindex",
        ),
        StudioCardResponse(
            id="ollama",
            title="Ollama",
            description="Estado del runtime local de inferencia.",
            value="Conectado" if health.ollama_connected else "Sin conexion",
            status="ready" if health.ollama_connected else "warning",
        ),
        StudioCardResponse(
            id="chat-model",
            title="Modelo",
            description="Motor de sintesis activo para responder.",
            value=health.chat_model,
            status="neutral",
        ),
        StudioCardResponse(
            id="embedding-model",
            title="Embeddings",
            description="Modelo usado para indexacion y recuperacion.",
            value=health.embedding_model,
            status="neutral",
        ),
        StudioCardResponse(
            id="vector-store",
            title="LanceDB",
            description="Persistencia local del conocimiento recuperable.",
            value="Listo" if health.vector_store_ready else "Pendiente",
            status="ready" if health.vector_store_ready else "warning",
        ),
        StudioCardResponse(
            id="retrieval",
            title="Top K",
            description="Cantidad de fragmentos que se recuperan por pregunta.",
            value=str(settings.similarity_top_k),
            status="neutral",
        ),
    ]

    return DashboardResponse(
        health=health,
        sources=[_serialize_source(source) for source in sources],
        summary=summary,
        studio_cards=studio_cards,
    )


@router.post("/ingestion/run", response_model=IngestionResponse)
async def run_ingestion(request: IngestionRequest) -> IngestionResponse:
    try:
        report = await asyncio.to_thread(
            get_ingestion_service().ingest,
            request.rebuild_index,
        )
    except OllamaClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return IngestionResponse(**asdict(report))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = await get_chat_service().answer(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OllamaClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        answer=result.answer,
        model=result.model,
        sources=[SourceResponse(**source) for source in result.sources],
        retrieved_chunks=[
            ChunkResponse(
                text=chunk.text,
                score=chunk.score,
                metadata=chunk.metadata,
            )
            for chunk in result.retrieved_chunks
        ],
    )
