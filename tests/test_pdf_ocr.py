import os

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas

from backend.services.pdf.extract import extract_blocks

def _load_test_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "arial.ttf",
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def create_image_pdf(file_path, text="OCR TEST CONTENT"):
    # 1. Create an image with text
    img = Image.new('RGB', (900, 300), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    font = _load_test_font(56)
    d.text((40, 80), text, fill=(0, 0, 0), font=font)
    d.text((42, 80), text, fill=(0, 0, 0), font=font)
    img.save("temp_ocr.png")

    # 2. Put image in PDF
    c = canvas.Canvas(file_path, pagesize=img.size)
    c.drawImage("temp_ocr.png", 0, 0, width=img.size[0], height=img.size[1])
    c.save()
    os.remove("temp_ocr.png")

def test_pdf_ocr_extraction():
    file_path = "ocr_test.pdf"
    create_image_pdf(file_path, "HELLO OCR WORLD")

    try:
        # This should trigger OCR if normal text extraction yields nothing
        data = extract_blocks(file_path)
        blocks = data["blocks"]

        texts = [b["source_text"] for b in blocks]
        # Allow some OCR noise but check if keyword exists
        assert any("HELLO" in t.upper() for t in texts)
        assert any("OCR" in t.upper() for t in texts)

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def test_pdf_mixed_extraction():
    # Test if mixed (text + image) still works
    file_path = "mixed_test.pdf"
    c = canvas.Canvas(file_path)
    c.drawString(100, 700, "Normal Text")
    # Draw image below
    img = Image.new('RGB', (100, 50), color=(200, 200, 200))
    img.save("mini.png")
    c.drawImage("mini.png", 100, 600)
    c.save()
    os.remove("mini.png")

    try:
        data = extract_blocks(file_path)
        texts = [b["source_text"] for b in data["blocks"]]
        assert "Normal Text" in texts
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
