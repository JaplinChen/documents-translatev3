import pytest

from backend.services.llm_clients import OpenAITranslator
from backend.services.llm_contract import build_contract
from backend.services.translate_llm import translate_blocks


def test_translate_blocks_raises_when_language_mismatch_persists(monkeypatch) -> None:
    monkeypatch.setenv("TRANSLATE_LLM_MODE", "real")
    monkeypatch.setenv("LLM_FALLBACK_ON_ERROR", "0")
    monkeypatch.setenv("LLM_MAX_RETRIES", "0")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://example.invalid")

    tagalog = "Katatuldugan ng PPT na kinutom na may awtorized kasambayanihan"

    def fake_translate(
        self,
        blocks,
        target_language,
        context=None,
        preferred_terms=None,
        placeholder_tokens=None,
    ):
        blocks_list = list(blocks)
        return build_contract(
            blocks=blocks_list,
            target_language=target_language,
            translated_texts=[tagalog] * len(blocks_list),
        )

    monkeypatch.setattr(OpenAITranslator, "translate", fake_translate)

    blocks = [
        {
            "slide_index": 0,
            "shape_id": 1,
            "block_type": "textbox",
            "source_text": "PPT 自動影音生成方案",
            "translated_text": "",
            "client_id": "block-1",
        }
    ]

    with pytest.raises(ValueError, match="不符合目標語言"):
        translate_blocks(blocks, target_language="vi", provider="openai")
