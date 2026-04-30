from __future__ import annotations

from dataclasses import dataclass

from app.ports.tool import ToolPort


@dataclass(slots=True)
class ToolDescriptor:
    name: str
    description: str
    input_schema: dict


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolPort] = {}

    def register(self, tool: ToolPort) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolPort:
        return self._tools[name]

    def list(self) -> list[ToolDescriptor]:
        return [ToolDescriptor(name=t.name, description=t.description, input_schema=t.input_schema) for t in self._tools.values()]

    def schema_for_llm(self) -> list[dict]:
        return [descriptor.__dict__ for descriptor in self.list()]
