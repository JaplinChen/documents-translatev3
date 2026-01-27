from backend.services.llm_prompt import build_prompt
from backend.services.translate_retry import matches_target_language

def test_build_prompt_includes_target_language_label_and_code() -> None:
    contract_example = {
        "document_language": "auto",
        "target_language": "zh-TW",
        "blocks": [
            {
                "slide_index": 1,
                "shape_id": 1,
                "block_type": "textbox",
                "source_text": "",
                "translated_text": "",
            }
        ],
    }
    prompt = build_prompt(
        blocks=[{"source_text": "PPT 自動影音生成方案"}],
        target_language="vi",
        contract_example=contract_example,
        context=None,
    )
    assert "目標語言：Vietnamese (vi)" in prompt
    assert "目標語言代碼：vi" in prompt
    assert "越南語" in prompt
    assert "ă" in prompt
    assert "PPT 自動影音生成方案" in prompt


def test_matches_target_language_rejects_tagalog_for_vi() -> None:
    tagalog = "Katatuldugan ng PPT na kinutom na may awtorized kasambayanihan"
    assert matches_target_language("Xin chào", "vi") is True
    assert matches_target_language(tagalog, "vi") is False
