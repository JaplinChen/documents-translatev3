from backend.services.correction_mode import apply_correction_mode, prepare_blocks_for_correction

def test_prepare_blocks_for_correction_skips_target_language():
    blocks = [
        {"source_text": "Hello", "slide_index": 0, "shape_id": 1, "block_type": "textbox"},
        {"source_text": "你好", "slide_index": 0, "shape_id": 2, "block_type": "textbox"},
    ]
    prepared = prepare_blocks_for_correction(blocks, "zh-TW")
    assert prepared[0]["source_text"] == "Hello"
    assert prepared[1]["source_text"] == ""


def test_apply_correction_mode_matches_similar_target_text():
    blocks = [
        {"source_text": "Hello", "slide_index": 0, "shape_id": 1, "block_type": "textbox"},
        {"source_text": "你好", "slide_index": 0, "shape_id": 2, "block_type": "textbox"},
    ]
    translated_texts = ["你好啊", "你好"]
    result = apply_correction_mode(blocks, translated_texts, "zh-TW")
    assert result[0]["correction_temp"] is False
    assert result[0]["temp_translated_text"] == ""
    assert result[0]["translated_text"] == ""
    assert result[1]["translated_text"] == "你好啊"


def test_apply_correction_mode_keeps_temp_when_not_similar():
    blocks = [
        {"source_text": "Hello", "slide_index": 0, "shape_id": 1, "block_type": "textbox"},
        {"source_text": "再見", "slide_index": 0, "shape_id": 2, "block_type": "textbox"},
    ]
    translated_texts = ["你好", "再見"]
    result = apply_correction_mode(blocks, translated_texts, "zh-TW")
    assert result[0]["correction_temp"] is True
    assert result[0]["temp_translated_text"] == "你好"
    assert result[0]["translated_text"] == ""
    assert result[1]["translated_text"] == ""
