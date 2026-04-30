from __future__ import annotations

import time
from contextlib import contextmanager

from app.core.config import AppSettings
from app.core.db import sqlite_conn


class TraceService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._records: list[dict] = []

    @contextmanager
    def stage(self, request_id: str, persona_slug: str, stage: str):
        start = time.perf_counter()
        ok = 1
        detail = ""
        try:
            yield
        except Exception as exc:  # noqa: BLE001
            ok = 0
            detail = str(exc)
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._write_stage(request_id, persona_slug, stage, duration_ms, ok, detail)

    def _write_stage(self, request_id: str, persona_slug: str, stage: str, duration_ms: float, ok: int, detail: str) -> None:
        with sqlite_conn(self._settings) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO traces(request_id, persona_slug) VALUES (?, ?)",
                (request_id, persona_slug),
            )
            conn.execute(
                """
                INSERT INTO trace_stages(request_id, stage, duration_ms, ok, detail)
                VALUES (?, ?, ?, ?, ?)
                """,
                (request_id, stage, duration_ms, ok, detail[:500]),
            )
            conn.execute(
                """
                DELETE FROM traces
                WHERE request_id NOT IN (
                    SELECT request_id FROM traces ORDER BY created_at DESC LIMIT ?
                )
                """,
                (self._settings.trace_retention,),
            )

    def latest(self, limit: int = 50) -> list[dict]:
        with sqlite_conn(self._settings) as conn:
            rows = conn.execute(
                """
                SELECT t.request_id, t.persona_slug, s.stage, s.duration_ms, s.ok, s.detail, s.created_at
                FROM traces t
                JOIN trace_stages s ON s.request_id = t.request_id
                ORDER BY s.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "request_id": row[0],
                "persona_slug": row[1],
                "stage": row[2],
                "duration_ms": row[3],
                "ok": bool(row[4]),
                "detail": row[5],
                "created_at": row[6],
            }
            for row in rows
        ]

    def metrics(self) -> dict:
        traces = self.latest(limit=1000)
        if not traces:
            return {"count": 0, "p50_ms": 0, "p95_ms": 0}
        durations = sorted(item["duration_ms"] for item in traces)
        p50 = durations[int(len(durations) * 0.5)]
        p95 = durations[max(0, int(len(durations) * 0.95) - 1)]
        return {"count": len(durations), "p50_ms": round(p50, 2), "p95_ms": round(p95, 2)}
