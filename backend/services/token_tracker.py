"""
Token Usage Tracker Service

Tracks and estimates token usage for LLM API calls.
Supports multiple providers: OpenAI, Anthropic, Google, Ollama.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# Token estimation constants (approximate)
CHARS_PER_TOKEN = {
    "openai": 4,  # GPT models average ~4 chars per token
    "anthropic": 4,  # Claude similar to GPT
    "google": 4,  # Gemini similar
    "ollama": 4,  # Local models vary
    "default": 4,
}

# Cost per 1M tokens (USD) - approximate rates
COST_PER_MILLION_TOKENS = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "ollama": {"input": 0.00, "output": 0.00},  # Local = free
    "default": {"input": 1.00, "output": 3.00},
}

USAGE_FILE = Path(__file__).parent.parent / "data" / "token_usage.json"


@dataclass
class TokenUsage:
    """Single token usage record."""

    timestamp: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    operation: str = "translate"


def estimate_tokens(text: str, provider: str = "default") -> int:
    """Estimate token count from text length."""
    chars_per_token = CHARS_PER_TOKEN.get(provider, CHARS_PER_TOKEN["default"])
    return max(1, len(text) // chars_per_token)


def estimate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Estimate cost in USD based on model and token counts."""
    # Normalize model name for lookup
    model_key = model.lower()
    for key in COST_PER_MILLION_TOKENS:
        if key in model_key:
            rates = COST_PER_MILLION_TOKENS[key]
            break
    else:
        rates = COST_PER_MILLION_TOKENS["default"]

    input_cost = (prompt_tokens / 1_000_000) * rates["input"]
    output_cost = (completion_tokens / 1_000_000) * rates["output"]
    return round(input_cost + output_cost, 6)


def _load_usage_history() -> list[dict]:
    """Load usage history from JSON file."""
    if not USAGE_FILE.exists():
        return []
    try:
        with open(USAGE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_usage_history_bg(history: list[dict]) -> None:
    """Save usage history in a background thread to avoid blocking."""
    try:
        USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def record_usage(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    operation: str = "translate",
) -> TokenUsage:
    """Record a token usage event."""
    total_tokens = prompt_tokens + completion_tokens
    cost = estimate_cost(model, prompt_tokens, completion_tokens)

    usage = TokenUsage(
        timestamp=datetime.utcnow().isoformat() + "Z",
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=cost,
        operation=operation,
    )

    # Persist to file
    history = _load_usage_history()
    history.append(asdict(usage))

    # Keep only last 1000 records
    if len(history) > 1000:
        history = history[-1000:]

    # Use a thread to save to avoid 504 timeouts on heavy loads
    thread = threading.Thread(target=_save_usage_history_bg, args=(history,))
    thread.start()

    return usage


def get_session_stats() -> dict:
    """Get statistics for current session (last 24 hours)."""
    history = _load_usage_history()

    # Filter to last 24 hours
    cutoff = datetime.utcnow().timestamp() - 86400
    recent = []
    for record in history:
        try:
            ts = datetime.fromisoformat(
                record["timestamp"].replace("Z", "+00:00")
            )
            if ts.timestamp() > cutoff:
                recent.append(record)
        except Exception:
            continue

    if not recent:
        return {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "estimated_cost_usd": 0.0,
            "request_count": 0,
            "models_used": [],
        }

    total_tokens = sum(r.get("total_tokens", 0) for r in recent)
    prompt_tokens = sum(r.get("prompt_tokens", 0) for r in recent)
    completion_tokens = sum(r.get("completion_tokens", 0) for r in recent)
    total_cost = sum(r.get("estimated_cost_usd", 0) for r in recent)
    models = list({r.get("model", "unknown") for r in recent})

    return {
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost_usd": round(total_cost, 4),
        "request_count": len(recent),
        "models_used": models,
    }


def get_all_time_stats() -> dict:
    """Get all-time statistics."""
    history = _load_usage_history()

    if not history:
        return {
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "request_count": 0,
        }

    total_tokens = sum(r.get("total_tokens", 0) for r in history)
    total_cost = sum(r.get("estimated_cost_usd", 0) for r in history)

    return {
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(total_cost, 4),
        "request_count": len(history),
    }
