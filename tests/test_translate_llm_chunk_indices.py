from backend.config import settings
from backend.services.translate_llm import translate_blocks

def test_translate_blocks_chunk_indices(monkeypatch) -> None:
    monkeypatch.setattr(settings, "translate_llm_mode", "mock")
    monkeypatch.setattr(settings, "llm_single_request", False)
    monkeypatch.setattr(settings, "llm_chunk_size", 1)

    blocks = [
        {
            "slide_index": 0,
            "shape_id": 1,
            "block_type": "textbox",
            "source_text": "Hello",
            "translated_text": "",
            "mode": "direct",
        },
        {
            "slide_index": 0,
            "shape_id": 2,
            "block_type": "textbox",
            "source_text": "World",
            "translated_text": "",
            "mode": "direct",
        },
    ]
    result = translate_blocks(blocks, target_language="zh-TW", provider=None)

    assert len(result["blocks"]) == 2
