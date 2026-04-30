from __future__ import annotations

from app.core.prompts import QUERY_REWRITE_PROMPT
from app.ports.llm import LLMProviderPort


class QueryProcessor:
    def __init__(self, llm: LLMProviderPort) -> None:
        self._llm = llm

    def rewrite(self, original_query: str) -> str:
        prompt = QUERY_REWRITE_PROMPT.format(question=original_query)
        rewritten = self._llm.generate("Eres un optimizador de búsquedas semánticas.", prompt)
        return rewritten.strip(' "\'\n')

    def hyde(self, original_query: str) -> str:
        return self._llm.generate(
            "Escribe un párrafo hipotético que responda la pregunta para mejorar retrieval.",
            original_query,
        ).strip()
