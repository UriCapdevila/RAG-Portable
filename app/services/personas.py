from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
import yaml

from app.core.config import AppSettings
from app.core.db import sqlite_conn


class PersonaParameters(BaseModel):
    temperature: float = 0.1
    top_p: float = 0.9
    similarity_top_k: int = 4
    rerank_top_k: int = 4
    use_query_rewrite: bool = True
    use_hybrid_retrieval: bool = True
    grounding_threshold: float = 0.15
    tool_mode: str = "off"
    allowed_tools: list[str] = Field(default_factory=list)

    @field_validator("tool_mode", mode="before")
    @classmethod
    def normalize_tool_mode(cls, value):
        if isinstance(value, bool):
            return "auto" if value else "off"
        return str(value)


class Persona(BaseModel):
    slug: str
    name: str
    language: str = "es-AR"
    tone: str = "profesional y conciso"
    domain: str = "general"
    constraints: list[str] = Field(default_factory=list)
    parameters: PersonaParameters = Field(default_factory=PersonaParameters)
    few_shot: list[dict[str, str]] = Field(default_factory=list)
    fallback_message: str = "No tengo suficiente información en los documentos proporcionados para responder a esto."


class PersonaService:
    ACTIVE_KEY = "active_persona"

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def list_personas(self) -> list[Persona]:
        personas: list[Persona] = []
        for path in sorted(self._settings.personas_dir.glob("*.yaml")):
            personas.append(self._read_persona(path))
        return personas

    def get_active(self) -> Persona:
        slug = self._read_setting(self.ACTIVE_KEY) or "default"
        for persona in self.list_personas():
            if persona.slug == slug:
                return persona
        personas = self.list_personas()
        return personas[0] if personas else self._default_persona()

    def set_active(self, slug: str) -> Persona:
        persona = next((item for item in self.list_personas() if item.slug == slug), None)
        if persona is None:
            raise ValueError(f"Persona '{slug}' no encontrada.")
        self._write_setting(self.ACTIVE_KEY, slug)
        return persona

    def upsert(self, payload: dict) -> Persona:
        persona = Persona.model_validate(payload)
        path = self._settings.personas_dir / f"{persona.slug}.yaml"
        path.write_text(yaml.safe_dump(persona.model_dump(mode="json"), sort_keys=False), encoding="utf-8")
        return persona

    def _read_persona(self, path: Path) -> Persona:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return Persona.model_validate(data)

    def _default_persona(self) -> Persona:
        return Persona(slug="default", name="Default")

    def _read_setting(self, key: str) -> str | None:
        with sqlite_conn(self._settings) as conn:
            row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def _write_setting(self, key: str, value: str) -> None:
        with sqlite_conn(self._settings) as conn:
            conn.execute(
                """
                INSERT INTO app_settings(key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, value),
            )
