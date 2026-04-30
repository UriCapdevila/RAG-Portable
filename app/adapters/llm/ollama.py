from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.errors import OllamaError


class OllamaLLMAdapter:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 120) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds

    @property
    def model(self) -> str:
        return self._model

    def health_check(self) -> bool:
        try:
            self._get("/api/tags")
            return True
        except OllamaError:
            return False

    def generate(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.1) -> str:
        payload = {
            "model": self._model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": temperature},
        }
        response = self._with_retry(lambda: self._post("/api/chat", payload))
        content = response.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise OllamaError("Ollama devolvió una respuesta vacía.")
        return content.strip()

    def stream(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.1) -> Iterator[str]:
        yield self.generate(system_prompt, user_prompt, temperature=temperature)

    def _with_retry(self, callback, retries: int = 3):
        delay = 0.25
        last_error: Exception | None = None
        for _ in range(retries):
            try:
                return callback()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(delay)
                delay *= 2
        assert last_error is not None
        raise last_error

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            url=f"{self._base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise OllamaError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise OllamaError(f"No se pudo conectar a Ollama en {self._base_url}.") from exc

    def _get(self, path: str) -> dict[str, Any]:
        request = Request(url=f"{self._base_url}{path}", method="GET")
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise OllamaError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise OllamaError(f"No se pudo conectar a Ollama en {self._base_url}.") from exc
