from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    ollama_base_url: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_BASE_URL")
    chat_model: str = Field(default="gemma3:latest", validation_alias="OLLAMA_CHAT_MODEL")
    embedding_model: str = Field(default="nomic-embed-text:latest", validation_alias="OLLAMA_EMBEDDING_MODEL")
    host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    port: int = Field(default=8000, validation_alias="APP_PORT")
    frontend_dev_url: str = Field(default="http://127.0.0.1:5173", validation_alias="FRONTEND_DEV_URL")
    chunk_size: int = Field(default=1200, validation_alias="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=180, validation_alias="RAG_CHUNK_OVERLAP")
    similarity_top_k: int = Field(default=4, validation_alias="RAG_TOP_K")
    vector_table_name: str = Field(default="document_chunks", validation_alias="RAG_VECTOR_TABLE")
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2", validation_alias="RAG_RERANKER_MODEL")
    reranker_enabled: bool = Field(default=False, validation_alias="RAG_RERANKER_ENABLED")
    grounding_threshold: float = Field(default=0.15, validation_alias="RAG_GROUNDING_THRESHOLD")
    max_react_steps: int = Field(default=3, validation_alias="RAG_MAX_REACT_STEPS")
    trace_retention: int = 2000
    supported_extensions: tuple[str, ...] = (".pdf", ".txt", ".md", ".csv", ".docx", ".html", ".epub")

    tts_enabled: bool = Field(default=True, validation_alias="TTS_ENABLED")
    tts_voice: str = Field(default="ef_dora", validation_alias="TTS_VOICE")
    tts_lang: str = Field(default="es", validation_alias="TTS_LANG")
    tts_speed: float = Field(default=1.0, validation_alias="TTS_SPEED")
    tts_model_quantization: str = Field(default="int8", validation_alias="TTS_MODEL_QUANTIZATION")
    tts_model_release: str = "model-files-v1.0"
    tts_max_text_length: int = Field(default=4000, validation_alias="TTS_MAX_TEXT_LENGTH")
    chat_history_enabled: bool = Field(default=True, validation_alias="CHAT_HISTORY_ENABLED")
    chat_history_turns_for_disambig: int = Field(default=4, validation_alias="CHAT_HISTORY_TURNS_FOR_DISAMBIG")

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def vector_db_dir(self) -> Path:
        return self.data_dir / "vector_db"

    @property
    def sql_db_dir(self) -> Path:
        return self.data_dir / "sql_db"

    @property
    def static_dir(self) -> Path:
        return self.project_root / "static"

    @property
    def frontend_dir(self) -> Path:
        return self.project_root / "frontend"

    @property
    def frontend_dist_dir(self) -> Path:
        return self.frontend_dir / "dist"

    @property
    def personas_dir(self) -> Path:
        return self.project_root / "app" / "personas"

    @property
    def sqlite_db_path(self) -> Path:
        return self.sql_db_dir / "app.db"

    @property
    def tts_models_dir(self) -> Path:
        return self.data_dir / "tts_models"

    def ensure_directories(self) -> None:
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_dir.mkdir(parents=True, exist_ok=True)
        self.sql_db_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_dir.mkdir(parents=True, exist_ok=True)
        self.personas_dir.mkdir(parents=True, exist_ok=True)
        self.tts_models_dir.mkdir(parents=True, exist_ok=True)


settings = AppSettings()
settings.ensure_directories()
