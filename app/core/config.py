from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _read_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value else default


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


@dataclass(slots=True)
class AppSettings:
    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    vector_db_dir: Path
    sql_db_dir: Path
    static_dir: Path
    frontend_dir: Path
    frontend_dist_dir: Path
    ollama_base_url: str
    chat_model: str
    embedding_model: str
    host: str
    port: int
    frontend_dev_url: str
    chunk_size: int
    chunk_overlap: int
    similarity_top_k: int
    vector_table_name: str
    supported_extensions: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "AppSettings":
        project_root = Path(__file__).resolve().parents[2]
        _load_dotenv(project_root / ".env")
        data_dir = project_root / "data"

        return cls(
            project_root=project_root,
            data_dir=data_dir,
            raw_data_dir=data_dir / "raw",
            vector_db_dir=data_dir / "vector_db",
            sql_db_dir=data_dir / "sql_db",
            static_dir=project_root / "static",
            frontend_dir=project_root / "frontend",
            frontend_dist_dir=project_root / "frontend" / "dist",
            ollama_base_url=_read_env("OLLAMA_BASE_URL", "http://localhost:11434"),
            chat_model=_read_env("OLLAMA_CHAT_MODEL", "gemma3:latest"),
            embedding_model=_read_env("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest"),
            host=_read_env("APP_HOST", "127.0.0.1"),
            port=_read_int("APP_PORT", 8000),
            frontend_dev_url=_read_env("FRONTEND_DEV_URL", "http://127.0.0.1:5173"),
            chunk_size=_read_int("RAG_CHUNK_SIZE", 1200),
            chunk_overlap=_read_int("RAG_CHUNK_OVERLAP", 180),
            similarity_top_k=_read_int("RAG_TOP_K", 4),
            vector_table_name=_read_env("RAG_VECTOR_TABLE", "document_chunks"),
            supported_extensions=(".pdf", ".txt", ".md", ".csv"),
        )

    def ensure_directories(self) -> None:
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_dir.mkdir(parents=True, exist_ok=True)
        self.sql_db_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_dir.mkdir(parents=True, exist_ok=True)


settings = AppSettings.from_env()
settings.ensure_directories()
