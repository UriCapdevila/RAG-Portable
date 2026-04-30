from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.core.config import AppSettings


def init_sqlite(settings: AppSettings) -> None:
    with sqlite3.connect(settings.sqlite_db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ingest_manifest (
                source_path TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                size INTEGER NOT NULL,
                mtime REAL NOT NULL,
                last_indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                chunk_count INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS traces (
                request_id TEXT PRIMARY KEY,
                persona_slug TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trace_stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                ok INTEGER NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@contextmanager
def sqlite_conn(settings: AppSettings) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.sqlite_db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
