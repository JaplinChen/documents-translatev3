import asyncio
import json

from backend.api.pptx_translate import pptx_translate
from backend.config import settings

def test_pptx_translate_returns_llm_mode_warning(monkeypatch):
    monkeypatch.setattr(settings, "translate_llm_mode", "mock")
    blocks = [
        {
            "slide_index": 0,
            "shape_id": 1,
            "block_type": "textbox",
            "source_text": "Test text",
            "translated_text": "",
            "mode": "direct",
        }
    ]

    result = asyncio.run(
        pptx_translate(
            blocks=json.dumps(blocks),
            source_language=None,
            secondary_language=None,
            target_language="zh-TW",
            mode="bilingual",
            use_tm=False,
            provider=None,
            model=None,
            api_key=None,
            base_url=None,
            ollama_fast_mode=False,
            tone=None,
            vision_context=True,
            smart_layout=True,
        )
    )

    assert result["llm_mode"] == "mock"
    assert result["warning"]
