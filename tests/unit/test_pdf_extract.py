from unittest.mock import MagicMock, patch

from backend.services.pdf.extract import extract_blocks, perform_ocr_on_page

@patch("backend.services.pdf.extract.convert_from_path")
@patch("backend.services.pdf.extract.pytesseract.image_to_data")
def test_perform_ocr_on_page_logic(mock_tesseract, mock_convert):
    # 1. Setup mocks
    mock_convert.return_value = [MagicMock()] # Mock PIL image
    mock_tesseract.return_value = {
        'text': ['', 'Hello', 'World'],
        'conf': [0, 90, 85],
        'left': [0, 10, 50],
        'top': [0, 10, 10],
        'width': [0, 30, 30],
        'height': [0, 15, 15],
        'block_num': [0, 1, 1],
        'line_num': [0, 1, 1]
    }

    # 2. Call
    blocks = perform_ocr_on_page("any.pdf", 0)

    # 3. Verify
    assert len(blocks) == 1 # Grouped into one line
    assert blocks[0]["source_text"] == "Hello World"
    assert blocks[0]["is_ocr"] is True
    assert blocks[0]["slide_index"] == 0

@patch("backend.services.pdf.extract.fitz.open")
def test_extract_blocks_fallback_trigger(mock_fitz_open):
    mock_page = MagicMock()
    mock_doc = [mock_page]
    mock_fitz_open.return_value = mock_doc

    # Mock text dict with image but no text
    mock_page.get_text.return_value = {
        "blocks": [{"type": 1, "bbox": (0,0,100,100)}]
    }

    with patch("backend.services.pdf.extract.perform_ocr_on_page") as mock_ocr:
        mock_ocr.return_value = [{"source_text": "OCR Text", "slide_index": 0}]

        result = extract_blocks("any.pdf")

        assert mock_ocr.called
        assert result["blocks"][0]["source_text"] == "OCR Text"
