from __future__ import annotations

import io
import threading
import urllib.request
import wave
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from app.core.errors import TTSError
from app.ports.tts import SynthesisResult

if TYPE_CHECKING:
    import numpy as np

logger = structlog.get_logger(__name__)

_RELEASE_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download"
_VOICES_FILENAME = "voices-v1.0.bin"
_MODEL_FILENAMES = {
    "fp32": "kokoro-v1.0.onnx",
    "fp16": "kokoro-v1.0.fp16.onnx",
    "int8": "kokoro-v1.0.int8.onnx",
}


def _download_with_progress(url: str, target: Path, label: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_suffix(target.suffix + ".part")

    logger.info("tts.model.download.start", label=label, url=url, target=str(target))

    last_logged_percent = -1

    def _hook(blocks: int, block_size: int, total_size: int) -> None:
        nonlocal last_logged_percent
        if total_size <= 0:
            return
        downloaded = blocks * block_size
        percent = min(100, int(downloaded * 100 / total_size))
        if percent >= last_logged_percent + 10:
            logger.info(
                "tts.model.download.progress",
                label=label,
                percent=percent,
                downloaded_mb=round(downloaded / (1024 * 1024), 1),
                total_mb=round(total_size / (1024 * 1024), 1),
            )
            last_logged_percent = percent

    try:
        urllib.request.urlretrieve(url, tmp_path, reporthook=_hook)  # noqa: S310
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise TTSError(f"No se pudo descargar el modelo TTS '{label}': {exc}") from exc

    tmp_path.replace(target)
    logger.info("tts.model.download.done", label=label, target=str(target))


def _float_to_wav_bytes(samples: "np.ndarray", sample_rate: int) -> bytes:
    import numpy as np

    audio = np.clip(samples, -1.0, 1.0)
    pcm = (audio * 32767.0).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())
    return buffer.getvalue()


class KokoroTTSAdapter:
    def __init__(
        self,
        models_dir: Path,
        *,
        default_voice: str,
        default_lang: str,
        default_speed: float,
        quantization: str,
        release_tag: str,
    ) -> None:
        if quantization not in _MODEL_FILENAMES:
            raise TTSError(
                f"Cuantizacion TTS desconocida: '{quantization}'. "
                f"Opciones validas: {', '.join(_MODEL_FILENAMES)}"
            )

        self._models_dir = models_dir
        self._default_voice = default_voice
        self._default_lang = default_lang
        self._default_speed = default_speed
        self._model_filename = _MODEL_FILENAMES[quantization]
        self._release_tag = release_tag
        self._lock = threading.Lock()
        self._kokoro: Any | None = None

    @property
    def enabled(self) -> bool:
        return True

    @property
    def _model_path(self) -> Path:
        return self._models_dir / self._model_filename

    @property
    def _voices_path(self) -> Path:
        return self._models_dir / _VOICES_FILENAME

    def _ensure_model_files(self) -> None:
        if not self._model_path.exists():
            url = f"{_RELEASE_BASE}/{self._release_tag}/{self._model_filename}"
            _download_with_progress(url, self._model_path, label=self._model_filename)
        if not self._voices_path.exists():
            url = f"{_RELEASE_BASE}/{self._release_tag}/{_VOICES_FILENAME}"
            _download_with_progress(url, self._voices_path, label=_VOICES_FILENAME)

    def _ensure_engine(self) -> Any:
        if self._kokoro is not None:
            return self._kokoro

        with self._lock:
            if self._kokoro is not None:
                return self._kokoro

            try:
                from kokoro_onnx import Kokoro
            except Exception as exc:
                raise TTSError(
                    "El paquete 'kokoro-onnx' no esta instalado. "
                    "Ejecuta `pip install -r requirements.txt`."
                ) from exc

            self._ensure_model_files()
            logger.info(
                "tts.engine.loading",
                model=str(self._model_path),
                voices=str(self._voices_path),
            )
            self._kokoro = Kokoro(str(self._model_path), str(self._voices_path))
            logger.info("tts.engine.ready")
            return self._kokoro

    def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        lang: str | None = None,
        speed: float | None = None,
    ) -> SynthesisResult:
        cleaned = text.strip()
        if not cleaned:
            raise TTSError("El texto a sintetizar esta vacio.")

        engine = self._ensure_engine()
        chosen_voice = voice or self._default_voice
        chosen_lang = lang or self._default_lang
        chosen_speed = speed if speed is not None else self._default_speed

        try:
            samples, sample_rate = engine.create(
                cleaned,
                voice=chosen_voice,
                speed=chosen_speed,
                lang=chosen_lang,
            )
        except Exception as exc:
            raise TTSError(f"La sintesis de voz fallo: {exc}") from exc

        wav_bytes = _float_to_wav_bytes(samples, int(sample_rate))
        return SynthesisResult(
            audio=wav_bytes,
            mime_type="audio/wav",
            sample_rate=int(sample_rate),
            voice=chosen_voice,
            lang=chosen_lang,
        )
