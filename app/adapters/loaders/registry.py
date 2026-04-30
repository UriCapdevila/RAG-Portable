from __future__ import annotations

from pathlib import Path

from llama_index.core import SimpleDirectoryReader


class LoaderRegistry:
    def load_text(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md", ".csv", ".html", ".epub", ".docx", ".pdf"}:
            try:
                docs = SimpleDirectoryReader(input_files=[str(path)], filename_as_id=True).load_data()
                return "\n".join(getattr(doc, "text", "") for doc in docs)
            except Exception:
                return path.read_text(encoding="utf-8", errors="ignore")
        return path.read_text(encoding="utf-8", errors="ignore")
