from __future__ import annotations

from datetime import datetime
from pathlib import Path

import lancedb

from app.core.config import AppSettings
from app.services.models import SourceRecord, UploadReport


class WorkspaceService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def list_sources(self) -> list[SourceRecord]:
        indexed_chunks = self._load_indexed_chunk_counts()
        source_paths = {
            self._normalize_relpath(path)
            for path in self._discover_source_files()
        }
        source_paths.update(indexed_chunks.keys())

        sources: list[SourceRecord] = []
        for source_path in sorted(source_paths):
            file_path = self._settings.project_root / Path(source_path)
            stat = file_path.stat() if file_path.exists() else None
            sources.append(
                SourceRecord(
                    source_path=source_path,
                    file_name=Path(source_path).name,
                    file_type=Path(source_path).suffix.lower() or "unknown",
                    file_size=stat.st_size if stat else None,
                    last_modified=self._format_mtime(stat.st_mtime_ns) if stat else None,
                    chunk_count=indexed_chunks.get(source_path, 0),
                    is_indexed=source_path in indexed_chunks,
                    is_available=file_path.exists(),
                )
            )

        sources.sort(key=lambda item: (not item.is_indexed, item.file_name.lower()))
        return sources

    def save_uploaded_files(self, files: list[tuple[str, bytes]]) -> UploadReport:
        report = UploadReport()

        for original_name, content in files:
            safe_name = Path(original_name or "source").name
            suffix = Path(safe_name).suffix.lower()
            if suffix not in self._settings.supported_extensions:
                report.rejected_files.append(safe_name)
                continue

            target_path = self._settings.raw_data_dir / safe_name
            target_path.write_bytes(content)
            report.uploaded_files.append(self._normalize_relpath(target_path))

        return report

    def delete_source(self, source_path: str) -> dict[str, bool]:
        """Delete a source file from disk and remove its chunks from the vector store."""
        file_deleted = False
        chunks_deleted = False

        # 1. Remove the physical file
        file_path = self._settings.project_root / Path(source_path)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            file_deleted = True

        # 2. Remove chunks from LanceDB
        try:
            db = lancedb.connect(str(self._settings.vector_db_dir))
            if self._settings.vector_table_name in db.table_names():
                table = db.open_table(self._settings.vector_table_name)
                # LanceDB supports SQL-like filter for deletion
                normalized = source_path.replace("'", "''")
                table.delete(f"metadata.source_path = '{normalized}'")
                chunks_deleted = True
        except Exception:
            pass

        return {"file_deleted": file_deleted, "chunks_deleted": chunks_deleted}

    def _discover_source_files(self) -> list[Path]:
        return sorted(
            path
            for path in self._settings.raw_data_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in self._settings.supported_extensions
        )

    def _load_indexed_chunk_counts(self) -> dict[str, int]:
        try:
            db = lancedb.connect(str(self._settings.vector_db_dir))
            if self._settings.vector_table_name not in db.table_names():
                return {}

            table = db.open_table(self._settings.vector_table_name)
            rows = table.to_arrow().to_pylist()
        except Exception:
            return {}

        counts: dict[str, int] = {}
        for row in rows:
            metadata = row.get("metadata")
            metadata_source = metadata.get("source_path") if isinstance(metadata, dict) else None
            raw_source = metadata_source or row.get("source_path") or row.get("file_name") or "unknown"
            source_path = self._normalize_relpath(Path(str(raw_source)))
            counts[source_path] = counts.get(source_path, 0) + 1

        return counts

    def _normalize_relpath(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self._settings.project_root.resolve()).as_posix()
        except Exception:
            return str(path).replace("\\", "/")

    def _format_mtime(self, timestamp_ns: int) -> str:
        return datetime.fromtimestamp(timestamp_ns / 1_000_000_000).isoformat(
            timespec="seconds"
        )
