from __future__ import annotations

import json
import re

from app.ports.llm import LLMProviderPort
from app.services.tools.registry import ToolRegistry


class ToolDispatcher:
    def __init__(self, llm: LLMProviderPort, registry: ToolRegistry, max_steps: int = 3) -> None:
        self._llm = llm
        self._registry = registry
        self._max_steps = max_steps

    def run(self, system_prompt: str, user_prompt: str, context: dict) -> str:
        prompt = user_prompt
        for _ in range(self._max_steps):
            raw = self._llm.generate(system_prompt, prompt)
            parsed = self._parse_json(raw)
            if "answer" in parsed:
                return str(parsed["answer"])
            tool_call = parsed.get("tool_call")
            if isinstance(tool_call, dict) and tool_call.get("name") in [t.name for t in self._registry.list()]:
                tool = self._registry.get(tool_call["name"])
                result = tool.execute(tool_call.get("args", {}), context)
                prompt = f"{user_prompt}\n\nResultado de herramienta:\n{result.content}"
                continue
            return raw
        return "No fue posible completar la ejecución de herramientas en el límite de iteraciones."

    def _parse_json(self, content: str) -> dict:
        content = content.strip()
        try:
            return json.loads(content)
        except Exception:  # noqa: BLE001
            match = re.search(r"\{.*\}", content, flags=re.DOTALL)
            if not match:
                return {"answer": content}
            try:
                return json.loads(match.group(0))
            except Exception:  # noqa: BLE001
                return {"answer": content}
