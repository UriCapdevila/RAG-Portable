from __future__ import annotations

from pathlib import Path

from app.ports.tool import ToolResult
from app.services.workspace import WorkspaceService


class ListSourcesTool:
    name = "list_sources"
    description = "Lista fuentes disponibles en el workspace."
    input_schema = {"type": "object", "properties": {}}

    def __init__(self, workspace: WorkspaceService) -> None:
        self._workspace = workspace

    def execute(self, args: dict, context: dict) -> ToolResult:
        _ = args
        _ = context
        sources = self._workspace.list_sources()
        content = "\n".join(item.source_path for item in sources) or "Sin fuentes."
        return ToolResult(content=content, metadata={"count": len(sources)})


class GetDocumentTool:
    name = "get_document"
    description = "Devuelve contenido textual de un documento por source_path."
    input_schema = {
        "type": "object",
        "properties": {"source_path": {"type": "string"}},
        "required": ["source_path"],
    }

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    def execute(self, args: dict, context: dict) -> ToolResult:
        _ = context
        source_path = str(args.get("source_path", ""))
        path = self._project_root / source_path
        if not path.exists():
            return ToolResult(content="Documento no encontrado.", metadata={})
        return ToolResult(content=path.read_text(encoding="utf-8", errors="ignore")[:5000], metadata={})
