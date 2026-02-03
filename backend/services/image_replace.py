from __future__ import annotations

import os
import zipfile
from collections import defaultdict
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_paths = [
        os.getenv("IMAGE_FONT_PATH", "").strip(),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in font_paths:
        if not path:
            continue
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    if not text:
        return []
    words = text.split()
    if len(words) <= 1:
        # CJK or no spaces: wrap by characters
        line = ""
        lines = []
        for ch in text:
            test = f"{line}{ch}"
            if draw.textlength(test, font=font) <= max_width or not line:
                line = test
            else:
                lines.append(line)
                line = ch
        if line:
            lines.append(line)
        return lines

    lines = []
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) <= max_width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box_width: int,
    box_height: int,
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, list[str]]:
    size = max(10, min(72, int(box_height * 0.7)))
    while size >= 10:
        font = _load_font(size)
        lines = _wrap_text(draw, text, font, max_width=max(1, box_width - 6))
        if not lines:
            return font, lines
        total_height = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            total_height += bbox[3] - bbox[1]
        if total_height <= box_height:
            return font, lines
        size -= 2
    font = _load_font(10)
    return font, _wrap_text(draw, text, font, max_width=max(1, box_width - 4))


def _avg_color(image: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    left, top, right, bottom = box
    crop = image.crop((left, top, right, bottom))
    if crop.width <= 0 or crop.height <= 0:
        return (255, 255, 255)
    tiny = crop.resize((1, 1))
    color = tiny.getpixel((0, 0))
    if isinstance(color, tuple) and len(color) >= 3:
        return color[:3]
    return (255, 255, 255)


def _text_color_for_background(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    r, g, b = rgb
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return (0, 0, 0) if luminance > 0.6 else (255, 255, 255)


def _use_inpaint() -> bool:
    return os.getenv("IMAGE_INPAINT", "0").strip() == "1"


def _inpaint_radius() -> int:
    try:
        return int(os.getenv("IMAGE_INPAINT_RADIUS", "3"))
    except (TypeError, ValueError):
        return 3


def _render_blocks_on_image(image: Image.Image, blocks: list[dict]) -> Image.Image:
    if not blocks:
        return image
    work = image.convert("RGBA")

    if _use_inpaint():
        try:
            import cv2
            import numpy as np

            bgr = cv2.cvtColor(np.array(work), cv2.COLOR_RGBA2BGR)
            mask = np.zeros((bgr.shape[0], bgr.shape[1]), dtype="uint8")
            for block in blocks:
                left = int(block.get("image_left", block.get("x", 0)))
                top = int(block.get("image_top", block.get("y", 0)))
                right = int(block.get("image_right", left + block.get("width", 0)))
                bottom = int(block.get("image_bottom", top + block.get("height", 0)))
                if right <= left or bottom <= top:
                    continue
                cv2.rectangle(mask, (left, top), (right, bottom), 255, thickness=-1)
            if mask.any():
                radius = _inpaint_radius()
                bgr = cv2.inpaint(bgr, mask, radius, cv2.INPAINT_TELEA)
                work = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA))
        except Exception:
            pass

    draw = ImageDraw.Draw(work)

    for block in blocks:
        text = (block.get("translated_text") or "").strip()
        if not text:
            continue
        left = int(block.get("image_left", block.get("x", 0)))
        top = int(block.get("image_top", block.get("y", 0)))
        right = int(block.get("image_right", left + block.get("width", 0)))
        bottom = int(block.get("image_bottom", top + block.get("height", 0)))
        if right <= left or bottom <= top:
            continue

        box = (left, top, right, bottom)
        fill = _avg_color(work, box)
        if not _use_inpaint():
            draw.rectangle(box, fill=fill + (255,))

        font, lines = _fit_text(draw, text, right - left, bottom - top)
        if not lines:
            continue
        line_heights = [
            draw.textbbox((0, 0), line, font=font)[3]
            - draw.textbbox((0, 0), line, font=font)[1]
            for line in lines
        ]
        total_height = int(sum(line_heights) * 1.1)
        y = top + max(0, (bottom - top - total_height) // 2)
        text_color = _text_color_for_background(fill)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = left + max(0, (right - left - line_width) // 2)
            draw.text((x, y), line, fill=text_color + (255,), font=font)
            y += int((bbox[3] - bbox[1]) * 1.1)

    return work


def _save_image_bytes(image: Image.Image, original_name: str) -> bytes:
    fmt = (os.path.splitext(original_name)[1] or "").lower()
    if fmt in {".jpg", ".jpeg"}:
        out = image.convert("RGB")
        out_format = "JPEG"
    elif fmt == ".png":
        out = image
        out_format = "PNG"
    else:
        out = image
        out_format = (image.format or "PNG")
    buf = BytesIO()
    out.save(buf, format=out_format)
    return buf.getvalue()


def replace_images_in_package(
    input_path: str,
    output_path: str,
    blocks: list[dict],
) -> bool:
    image_blocks = [b for b in blocks if b.get("block_type") == "image_text"]
    if not image_blocks:
        return False

    grouped: dict[str, list[dict]] = defaultdict(list)
    for block in image_blocks:
        part = (block.get("image_part") or "").lstrip("/")
        if part:
            grouped[part].append(block)

    if not grouped:
        return False

    with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(
        output_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            name = item.filename
            if name in grouped:
                original = zin.read(name)
                try:
                    image = Image.open(BytesIO(original))
                except Exception:
                    zout.writestr(item, original)
                    continue
                updated = _render_blocks_on_image(image, grouped[name])
                new_bytes = _save_image_bytes(updated, name)
                zout.writestr(item, new_bytes)
            else:
                zout.writestr(item, zin.read(name))
    return True
