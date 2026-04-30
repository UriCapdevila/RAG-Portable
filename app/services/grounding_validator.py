from __future__ import annotations

import re


def is_grounded(answer: str, source_names: list[str]) -> bool:
    cited = re.findall(r"\[([^\]]+)\]", answer)
    if not cited:
        return True
    available = {item.lower() for item in source_names}
    return all(item.lower() in available for item in cited)
