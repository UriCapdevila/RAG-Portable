from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class ToolResult:
    content: str
    metadata: dict[str, Any]


class ToolPort(Protocol):
    name: str
    description: str
    input_schema: dict[str, Any]

    def execute(self, args: dict[str, Any], context: dict[str, Any]) -> ToolResult: ...
