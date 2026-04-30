from __future__ import annotations

from typing import Iterator, Protocol


class LLMProviderPort(Protocol):
    @property
    def model(self) -> str: ...

    def health_check(self) -> bool: ...

    def generate(self, system_prompt: str, user_prompt: str, *, temperature: float = 0.1) -> str: ...

    def stream(
        self, system_prompt: str, user_prompt: str, *, temperature: float = 0.1
    ) -> Iterator[str]: ...
