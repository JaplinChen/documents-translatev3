import os
import pytest
from docx import Document
from .extract import extract_blocks
from .apply import apply_translations, apply_bilingual

@pytest.fixture
def sample_docx():
    path = "test_sample.docx"
    doc = Document()
    doc.add_paragraph("Hello World")
    table = doc.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "Table Content"
    doc.save(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_docx_extraction(sample_docx):
    data = extract_blocks(sample_docx)
    blocks = data["blocks"]
    
    para_blocks = [b for b in blocks if b["block_type"] == "textbox"]
    assert len(para_blocks) >= 1
    assert para_blocks[0]["source_text"] == "Hello World"
    
    table_blocks = [b for b in blocks if b["block_type"] == "table_cell"]
    assert len(table_blocks) >= 1
    assert table_blocks[0]["source_text"] == "Table Content"
    assert isinstance(table_blocks[0]["shape_id"], int)

def test_docx_application(sample_docx):
    output_path = "test_output.docx"
    blocks = [
        {"slide_index": 0, "block_type": "textbox", "shape_id": 0, "source_text": "Hello World", "translated_text": "你好世界"},
        {"slide_index": 0, "shape_id": 0, "block_type": "table_cell", "source_text": "Table Content", "translated_text": "表格內容"}
    ]
    
    apply_translations(sample_docx, output_path, blocks, mode="direct")
    
    assert os.path.exists(output_path)
    output_doc = Document(output_path)
    assert output_doc.paragraphs[0].text == "你好世界"
    assert output_doc.tables[0].cell(0, 0).text == "表格內容"
    
    os.remove(output_path)

def test_docx_bilingual(sample_docx):
    output_path = "test_bilingual.docx"
    blocks = [
        {"slide_index": 0, "block_type": "textbox", "shape_id": 0, "source_text": "Hello World", "translated_text": "你好世界"},
    ]
    
    apply_bilingual(sample_docx, output_path, blocks)
    
    assert os.path.exists(output_path)
    output_doc = Document(output_path)
    assert "Hello World" in output_doc.paragraphs[0].text
    assert "你好世界" in output_doc.paragraphs[0].text
    
    os.remove(output_path)
