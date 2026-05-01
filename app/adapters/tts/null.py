from __future__ import annotations

from app.core.errors import TTSDisabledError
from app.ports.tts import SynthesisResult


class NullTTSAdapter:
    @property
    def enabled(self) -> bool:
        return False

    def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        lang: str | None = None,
        speed: float | None = None,
    ) -> SynthesisResult:
        raise TTSDisabledError(
            "El servicio de TTS esta deshabilitado. Activa TTS_ENABLED=true en .env."
        )
