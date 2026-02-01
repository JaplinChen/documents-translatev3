import os
import subprocess
import tempfile
import logging
import hashlib
from pathlib import Path
import fitz  # PyMuPDF

LOGGER = logging.getLogger(__name__)

THUMBNAIL_DIR = Path("data/thumbnails")
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)


def get_file_hash(path: str) -> str:
    """Get stable hash of file content."""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_pdf_thumbnails(pdf_path: str) -> list[str]:
    """Generate PNG thumbnails for each page of a PDF."""
    file_hash = get_file_hash(pdf_path)
    output_urls = []

    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        thumb_name = f"{file_hash}_{i}.png"
        thumb_path = THUMBNAIL_DIR / thumb_name

        if not thumb_path.exists():
            try:
                page = doc[i]
                # DPI 144 (Matrix 2.0) is much clearer than 96 DPI
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                pix.save(str(thumb_path))
            except Exception as e:
                LOGGER.error(f"Failed to render PDF page {i}: {e}")
                continue

        output_urls.append(f"/thumbnails/{thumb_name}")

    doc.close()
    return output_urls


def generate_pptx_thumbnails(pptx_path: str) -> list[str]:
    """Generate PNG thumbnails for PPTX by converting to PDF first."""
    file_hash = get_file_hash(pptx_path)

    # Fast cache check
    if (THUMBNAIL_DIR / f"{file_hash}_0.png").exists():
        urls, i = [], 0
        while (THUMBNAIL_DIR / f"{file_hash}_{i}.png").exists():
            urls.append(f"/thumbnails/{file_hash}_{i}.png")
            i += 1
        LOGGER.info(f"Using cached thumbnails for {file_hash} ({len(urls)} pages)")
        return urls

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            LOGGER.info(f"Converting PPTX to PDF for thumbnails: {pptx_path}")
            result = subprocess.run(
                ["soffice", "--headless", "--convert-to", "pdf", "--outdir", temp_dir, pptx_path],
                check=True,
                capture_output=True,
                text=True,
            )
            LOGGER.debug(f"Soffice output: {result.stdout}")

            pdf_name = Path(pptx_path).stem + ".pdf"
            tmp_pdf = os.path.join(temp_dir, pdf_name)

            if os.path.exists(tmp_pdf):
                doc = fitz.open(tmp_pdf)
                urls = []
                for i in range(len(doc)):
                    thumb_name = f"{file_hash}_{i}.png"
                    thumb_path = THUMBNAIL_DIR / thumb_name
                    # High quality 144 DPI
                    pix = doc[i].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                    pix.save(str(thumb_path))
                    urls.append(f"/thumbnails/{thumb_name}")
                doc.close()
                return urls
            else:
                LOGGER.error(f"Soffice conversion failed: {tmp_pdf} not found")
        except subprocess.CalledProcessError as e:
            LOGGER.error(f"Soffice command failed: {e.stderr}")
        except Exception as e:
            LOGGER.error(f"Failed to generate PPTX thumbnails: {e}")

    return []
