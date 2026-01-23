from __future__ import annotations
import re
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE

# Regex for XML sanitization and CJK Kinsoku
INVALID_XML_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
CJK_SPACE_PATTERN = re.compile(
    r'([\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f])\s+([\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f])'
)

# Regex for markdown symbols
MD_BOLD = re.compile(r"\*\*(.*?)\*\*")

def remove_markdown_symbols(text: str) -> str:
    if not text: return text
    # Replace **text** with text
    return MD_BOLD.sub(r"\1", text)

def sanitize_xml_text(text: str) -> str:
    if not text: return text
    text = remove_markdown_symbols(text)
    return INVALID_XML_CHARS.sub("", text)

def parse_hex_color(value: str | None, default: RGBColor) -> RGBColor:
    if not value: return default
    cleaned = value.strip().lstrip("#")
    if len(cleaned) != 6: return default
    try: return RGBColor.from_string(cleaned.upper())
    except ValueError: return default

def parse_dash_style(value: str | None) -> MSO_LINE_DASH_STYLE | None:
    if not value: return None
    mapping = {
        "dash": MSO_LINE_DASH_STYLE.DASH,
        "dot": MSO_LINE_DASH_STYLE.ROUND_DOT,
        "dashdot": MSO_LINE_DASH_STYLE.DASH_DOT,
        "solid": MSO_LINE_DASH_STYLE.SOLID,
    }
    return mapping.get(value.strip().lower())

def split_text_chunks(text: str, chunk_size: int) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines: return [text]
    chunks, current, current_len = [], [], 0
    for line in lines:
        if current_len + len(line) + 1 > chunk_size and current:
            chunks.append("\n".join(current)); current, current_len = [], 0
        current.append(line); current_len += len(line) + 1
    if current: chunks.append("\n".join(current))
    return chunks
