from unittest.mock import MagicMock, patch

from backend.services.xlsx.apply import apply_bilingual

def test_xlsx_apply_bilingual_alignment_inheritance():
    # 1. Mock Workbook/Worksheet
    mock_wb = MagicMock()
    mock_ws = MagicMock()
    mock_cell = MagicMock()

    # 2. Setup mock relationships
    mock_wb.sheetnames = ["Sheet1"]
    mock_wb.__getitem__.return_value = mock_ws
    mock_ws.__getitem__.return_value = mock_cell

    # Existing alignment
    mock_alignment = MagicMock()
    mock_cell.alignment = mock_alignment

    # Blocks Input
    blocks = [
        {
            "sheet_name": "Sheet1",
            "cell_address": "A1",
            "source_text": "S",
            "translated_text": "T",
        }
    ]

    with patch("backend.services.xlsx.apply.openpyxl.load_workbook", return_value=mock_wb):
        with patch("backend.services.xlsx.apply.copy", return_value=mock_alignment) as mock_copy:
            apply_bilingual("fake.xlsx", "out.xlsx", blocks)

            # Verify copy was called to isolate style
            assert mock_copy.called
            # Verify wrapText was enabled
            assert mock_alignment.wrapText is True
