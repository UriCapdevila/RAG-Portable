from __future__ import annotations

import re

SMALL_TALK_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^\s*(hola|buenas|buen[oa]s? (d[ií]as|tardes|noches)|qu[eé] tal|qu[eé] hac[eé]s|c[oó]mo (est[aá]s|andas|va)|how are you|hi|hello|hey)\b",
        r"^\s*(gracias|muchas gracias|thanks|thank you|ok|listo|perfecto|genial|d[aá]le)\s*[!.?]*\s*$",
        r"^\s*(chau|adi[oó]s|hasta luego|nos vemos|bye|good ?bye)\s*[!.?]*\s*$",
        r"^\s*(qui[eé]n eres|quien sos|qu[eé] eres|qu[eé] sos|present[aá]te|qu[eé] pod[eé]s hacer|en qu[eé] me ayud[aá]s)\b",
    )
)


def is_small_talk(question: str) -> bool:
    text = question.strip()
    if not text:
        return False
    if len(text) > 80:
        return False
    return any(pattern.search(text) for pattern in SMALL_TALK_PATTERNS)
