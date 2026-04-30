from __future__ import annotations

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.db import init_sqlite
from app.core.errors import AppError
from app.core.logging import configure_logging, request_id_ctx, request_id_middleware

app = FastAPI(
    title="RAG Portable",
    version="0.1.0",
    description="Local-first RAG foundation with FastAPI, LlamaIndex, LanceDB and Ollama.",
)
configure_logging()
init_sqlite(settings)

app.include_router(router)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
app.middleware("http")(request_id_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_dev_url,
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_assets_dir = settings.frontend_dist_dir / "assets"
if frontend_assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=frontend_assets_dir), name="frontend-assets")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    _ = request
    return JSONResponse(
        status_code=500,
        content={
            "code": exc.code,
            "message": exc.message,
            "request_id": request_id_ctx.get(),
        },
    )


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_index(full_path: str) -> FileResponse:
    dist_index = settings.frontend_dist_dir / "index.html"
    if dist_index.exists():
        requested_path = settings.frontend_dist_dir / full_path
        if full_path and requested_path.exists() and requested_path.is_file():
            return FileResponse(requested_path)
        return FileResponse(dist_index)

    requested_path = settings.static_dir / full_path
    if full_path and requested_path.exists() and requested_path.is_file():
        return FileResponse(requested_path)
    return FileResponse(settings.static_dir / "index.html")
