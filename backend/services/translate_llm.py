"""LLM orchestration for translating PPTX block collections."""

from __future__ import annotations

from backend.config import settings
from backend.services.translate_llm_impl.core import translate_blocks, translate_blocks_async

__all__ = ["settings", "translate_blocks", "translate_blocks_async"]
