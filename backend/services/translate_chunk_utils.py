from __future__ import annotations

import random
from urllib.error import HTTPError

from backend.services.language_detect import detect_language


def detect_top_language(texts: list[str]) -> str | None:
    counts: dict[str, int] = {}
    for text in texts:
        detected = detect_language((text or "").strip())
        if detected:
            counts[detected] = counts.get(detected, 0) + 1
    if not counts:
        return None
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[0][0]


def is_vision_error(error_msg: str) -> bool:
    lower = error_msg.lower()
    return "image" in lower or "vision" in lower


def calculate_backoff(
    exc: Exception,
    attempt: int,
    backoff: float,
    max_backoff: float,
) -> float:
    retry_after = None
    if isinstance(exc, HTTPError) and exc.code in {429, 503}:
        retry_after = exc.headers.get("Retry-After")
    if retry_after:
        try:
            return max(float(retry_after), 0)
        except ValueError:
            pass
    return min(backoff * attempt, max_backoff) + random.uniform(0, 0.5)
