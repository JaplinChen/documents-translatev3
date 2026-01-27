import uuid
from unittest.mock import MagicMock, patch

import pytest

from backend.services.llm_clients import OpenAITranslator
from backend.services.llm_contract import build_contract
from backend.services.translate_llm import translate_blocks

def test_translate_blocks_raises_when_language_mismatch_persists(monkeypatch) -> None:
    """Test that ValueError is raised when translation language doesn't match target."""

    tagalog = "Katatuldugan ng PPT na kinutom na may awtorized kasambayanihan"

    def fake_translate(
        self,
        blocks,
        target_language,
        context=None,
        preferred_terms=None,
        placeholder_tokens=None,
        language_hint=None,
    ):
        blocks_list = list(blocks)
        return build_contract(
            blocks=blocks_list,
            target_language=target_language,
            translated_texts=[tagalog] * len(blocks_list),
        )

    monkeypatch.setattr(OpenAITranslator, "translate", fake_translate)

    # Use unique source text to avoid cache hits
    unique_source = f"Unique String For Language Mismatch Test {uuid.uuid4()}"

    blocks = [
        {
            "slide_index": 0,
            "shape_id": 1,
            "block_type": "textbox",
            "source_text": unique_source,
            "translated_text": "",
            "client_id": "block-1",
        }
    ]

    # Create mock settings
    mock_settings = MagicMock()
    mock_settings.translate_llm_mode = "real"
    mock_settings.llm_fallback_on_error = False
    mock_settings.source_language = "auto"
    mock_settings.openai_api_key = "dummy"
    mock_settings.openai_base_url = "http://example.invalid"
    mock_settings.openai_model = "gpt-4o-mini"
    mock_settings.llm_max_retries = 0
    mock_settings.llm_retry_backoff = 0.8
    mock_settings.llm_retry_max_backoff = 8.0
    mock_settings.llm_chunk_size = 40
    mock_settings.llm_single_request = True
    mock_settings.llm_chunk_delay = 0.0
    mock_settings.llm_context_strategy = "none"
    mock_settings.llm_glossary_path = None

    # Patch settings in all relevant modules
    with patch("backend.services.translate_llm.settings", mock_settings), patch(
        "backend.services.translate_selector.settings", mock_settings
    ):
        with pytest.raises(ValueError, match="不符合目標語言"):
            translate_blocks(blocks, target_language="vi", provider="openai", use_tm=False)
