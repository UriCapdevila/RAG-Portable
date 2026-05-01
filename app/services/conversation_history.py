from __future__ import annotations

import uuid

from app.core.config import AppSettings
from app.core.db import sqlite_conn
from app.services.models import ConversationContext, ConversationMessage


class ConversationHistoryService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def create(self, persona_slug: str) -> str:
        conversation_id = str(uuid.uuid4())
        with sqlite_conn(self._settings) as conn:
            conn.execute(
                """
                INSERT INTO conversations(id, persona_slug)
                VALUES (?, ?)
                """,
                (conversation_id, persona_slug),
            )
        return conversation_id

    def ensure(self, conversation_id: str | None, persona_slug: str) -> str:
        if conversation_id:
            with sqlite_conn(self._settings) as conn:
                row = conn.execute(
                    "SELECT id FROM conversations WHERE id = ?",
                    (conversation_id,),
                ).fetchone()
                if row is not None:
                    return conversation_id
        return self.create(persona_slug)

    def append_message(self, conversation_id: str, role: str, content: str) -> None:
        cleaned_content = content.strip()
        if not cleaned_content:
            return
        with sqlite_conn(self._settings) as conn:
            conn.execute(
                """
                INSERT INTO conversation_messages(conversation_id, role, content)
                VALUES (?, ?, ?)
                """,
                (conversation_id, role, cleaned_content),
            )
            conn.execute(
                """
                UPDATE conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (conversation_id,),
            )

    def latest_messages(self, conversation_id: str, turns: int) -> list[ConversationMessage]:
        limit = max(1, turns) * 2
        with sqlite_conn(self._settings) as conn:
            rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        rows.reverse()
        return [
            ConversationMessage(role=row[0], content=row[1], created_at=row[2])
            for row in rows
        ]

    def get_context(self, conversation_id: str, turns: int) -> ConversationContext:
        return ConversationContext(
            conversation_id=conversation_id,
            messages=self.latest_messages(conversation_id, turns),
        )
