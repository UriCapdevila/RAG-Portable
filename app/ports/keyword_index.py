from __future__ import annotations

from typing import Any, Protocol


class KeywordIndexPort(Protocol):
    def query(self, query_text: str, top_k: int) -> list[dict[str, Any]]: ...
