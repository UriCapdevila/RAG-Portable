from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SynthesisResult:
    audio: bytes
    mime_type: str
    sample_rate: int
    voice: str
    lang: str


class TTSPort(Protocol):
    @property
    def enabled(self) -> bool: ...

    def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        lang: str | None = None,
        speed: float | None = None,
    ) -> SynthesisResult: ...
