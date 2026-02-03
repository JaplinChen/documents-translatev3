from __future__ import annotations

from typing import Iterable

EVENT_LOOKUP_HIT_TM = "lookup_hit_tm"
EVENT_LOOKUP_MISS = "lookup_miss"
EVENT_LOOKUP_HIT_GLOSSARY = "lookup_hit_glossary"
EVENT_OVERWRITE = "overwrite"
EVENT_PROMOTE = "promote"
EVENT_AUTO_PROMO_ERROR = "auto_promotion_error"
EVENT_WRONG_SUGGESTION = "wrong_suggestion"

LOOKUP_EVENT_TYPES: Iterable[str] = (EVENT_LOOKUP_HIT_TM, EVENT_LOOKUP_MISS)


def rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round((numerator / denominator) * 100, 2)
