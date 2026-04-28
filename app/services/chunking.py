from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RecursiveChunker:
    chunk_size: int
    chunk_overlap: int
    separators: tuple[str, ...] = ("\n# ", "\n## ", "\n### ", "\n\n", "\n", ". ", " ", "")

    def split_text(self, text: str) -> list[str]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []

        pieces = self._split_recursive(normalized, self.separators)
        return self._merge_with_overlap([piece.strip() for piece in pieces if piece.strip()])

    def _split_recursive(self, text: str, separators: tuple[str, ...]) -> list[str]:
        if len(text) <= self.chunk_size or not separators:
            return [text]

        separator = separators[0]
        if separator == "":
            return self._split_by_length(text)

        if separator not in text:
            return self._split_recursive(text, separators[1:])

        parts = text.split(separator)
        rebuilt_parts: list[str] = []

        for index, part in enumerate(parts):
            if not part.strip():
                continue
            prefix = separator if index > 0 and separator.strip() else ""
            rebuilt_parts.append(f"{prefix}{part}".strip())

        output: list[str] = []
        for part in rebuilt_parts:
            if len(part) <= self.chunk_size:
                output.append(part)
            else:
                output.extend(self._split_recursive(part, separators[1:]))
        return output

    def _split_by_length(self, text: str) -> list[str]:
        step = max(1, self.chunk_size - self.chunk_overlap)
        return [text[index : index + self.chunk_size] for index in range(0, len(text), step)]

    def _merge_with_overlap(self, pieces: list[str]) -> list[str]:
        merged: list[str] = []
        current = ""

        for piece in pieces:
            candidate = piece if not current else f"{current}\n{piece}"
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            if current:
                merged.append(current.strip())
            current = self._build_overlap(current, piece)

        if current.strip():
            merged.append(current.strip())

        return merged

    def _build_overlap(self, previous: str, next_piece: str) -> str:
        overlap = previous[-self.chunk_overlap :] if self.chunk_overlap else ""
        combined = f"{overlap}\n{next_piece}".strip()
        if len(combined) <= self.chunk_size:
            return combined
        return combined[: self.chunk_size].strip()

