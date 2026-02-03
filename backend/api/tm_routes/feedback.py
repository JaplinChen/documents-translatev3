from __future__ import annotations

from fastapi import APIRouter

from backend.api.tm_routes.models import TermFeedbackPayload
from backend.services.learning_service import record_term_feedback

router = APIRouter()


@router.post("/feedback")
async def tm_record_feedback(payload: TermFeedbackPayload) -> dict:
    """
    Record user feedback for terminology learning.
    """
    try:
        record_term_feedback(
            payload.source, payload.target, payload.source_lang, payload.target_lang
        )
        return {"status": "recorded"}
    except Exception as exc:
        import logging

        logging.getLogger(__name__).error(f"Feedback recording failed: {exc}")
        return {"status": "error", "message": str(exc)}
