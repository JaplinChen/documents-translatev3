from __future__ import annotations

from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_COLOR_TYPE

# Language code to font mapping (to prevent fallback to Serif fonts)
FONT_MAPPING: dict[str, list[str]] = {
    "vi": ["Arial", "Segoe UI", "Calibri"],
    "th": ["Leelawadee UI", "Tahoma", "Arial"],
    "ar": ["Arial", "Segoe UI"],
    "he": ["Arial", "Segoe UI"],
    "ja": ["Meiryo", "Yu Gothic", "MS PGothic"],
    "ko": ["Malgun Gothic", "Gulim"],
    "en": ["Arial", "Calibri", "Segoe UI"],
}


def contains_cjk(text: str) -> bool:
    """Check if text contains CJK characters."""
    for char in text:
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
            return True
    return False


def estimate_scale(source_text: str, translated_text: str) -> float:
    """Estimates font scale based on text weight (CJK aware)."""

    def get_weight(t: str) -> int:
        weight = 0
        for char in t:
            code = ord(char)
            # CJK characters or Vietnamese diacritics / non-ASCII
            if (
                0x4E00 <= code <= 0x9FFF
                or 0x3400 <= code <= 0x4DBF
                or code > 0x00FF
            ):
                weight += 2
            else:
                weight += 1
        return max(weight, 1)

    s_weight = get_weight(source_text)
    t_weight = get_weight(translated_text)

    if t_weight <= s_weight:
        return 1.0

    # If target is heavier than source, shrink font
    ratio = s_weight / t_weight

    # 2026/01/22 Update: Decrease aggressiveness (use 0.5 power instead of 0.7)
    # This prevents text from becoming too small in complex slides.
    scale = ratio**0.5

    # Allow shrinking down to 0.6 to maintain readability
    return max(0.6, min(1.0, scale))


def clone_font_props(  # noqa: C901
    source_font: Any,
    target_font: Any,
    color_override: RGBColor | None = None,
    target_language: str | None = None,
    font_mapping: dict[str, list[str]] | None = None,
) -> None:
    """Clones all font properties from source_font to target_font.

    Args:
        source_font: Source font object (Run.font)
        target_font: Target font object (Run.font)
        color_override: Optional color to force applying.
        target_language: Optional target language code (e.g. 'vi') to
            apply font mapping.
        font_mapping: Optional dictionary mapping language codes to font lists.
    """
    try:
        if source_font.name:
            # Apply font mapping if target language requires specific fonts
            mapped_font = None
            if target_language:
                # Handle cases like 'vi-VN' -> 'vi'
                lang_code = target_language.split("-")[0].lower()

                # Priority 1: Custom Font Mapping passed from UI
                if (
                    font_mapping
                    and lang_code in font_mapping
                    and font_mapping[lang_code]
                ):
                    mapped_font = font_mapping[lang_code][0]

                # Priority 2: Built-in Font Mapping
                elif lang_code in FONT_MAPPING:
                    mapped_font = FONT_MAPPING[lang_code][0]

            if mapped_font:
                target_font.name = mapped_font
            else:
                target_font.name = source_font.name

        if source_font.size:
            target_font.size = source_font.size
        target_font.bold = source_font.bold
        target_font.italic = source_font.italic
        target_font.underline = source_font.underline

        if color_override is not None:
            target_font.color.rgb = color_override
        elif source_font.color and source_font.color.type != 0:
            # MSO_COLOR_TYPE.NONE = 0
            try:
                if source_font.color.type == MSO_COLOR_TYPE.RGB:
                    target_font.color.rgb = source_font.color.rgb
                elif source_font.color.type == MSO_COLOR_TYPE.SCHEME:
                    target_font.color.theme_color = (
                        source_font.color.theme_color
                    )
                    if source_font.color.brightness is not None:
                        target_font.color.brightness = (
                            source_font.color.brightness
                        )
                else:
                    target_font.color.rgb = source_font.color.rgb
            except (AttributeError, ValueError):
                pass
    except Exception:
        pass
