"""
Token Usage Statistics API

Endpoints for retrieving token usage statistics.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.services.token_tracker import (
    estimate_tokens,
    get_all_time_stats,
    get_session_stats,
    record_usage,
)

router = APIRouter(prefix="/api/token-stats")


@router.get("")
async def get_token_stats() -> dict:
    """Get token usage statistics."""
    return {"session": get_session_stats(), "all_time": get_all_time_stats()}


@router.post("/record")
async def record_token_usage(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    operation: str = "translate",
) -> dict:
    """Manually record token usage (for testing or external tracking)."""
    usage = record_usage(
        provider,
        model,
        prompt_tokens,
        completion_tokens,
        operation,
    )
    return {
        "recorded": True,
        "usage": {
            "total_tokens": usage.total_tokens,
            "estimated_cost_usd": usage.estimated_cost_usd,
        },
    }


@router.post("/estimate")
async def estimate_token_count(text: str, provider: str = "openai") -> dict:
    """Estimate token count for given text."""
    count = estimate_tokens(text, provider)
    return {"estimated_tokens": count, "text_length": len(text)}
