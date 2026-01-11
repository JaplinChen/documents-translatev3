import tempfile
import unittest

from pptx import Presentation

from backend.services.pptx_apply import apply_bilingual
from backend.services.pptx_extract import extract_blocks


class TestPptxApplyBilingual(unittest.TestCase):
    def test_apply_bilingual_updates_text(self) -> None:
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        textbox = slide.shapes.add_textbox(80, 80, 300, 100)
        textbox.text = "Alpha\nBeta"

        with tempfile.TemporaryDirectory() as temp_dir:
            pptx_in = f"{temp_dir}/sample.pptx"
            pptx_out = f"{temp_dir}/sample_bilingual.pptx"
            presentation.save(pptx_in)

            blocks = extract_blocks(pptx_in)
            for block in blocks:
                block["translated_text"] = f"TR:{block['source_text']}"

            apply_bilingual(pptx_in, pptx_out, blocks)

            updated = Presentation(pptx_out)
            updated_slide = updated.slides[0]
            updated_shape = None
            for shape in updated_slide.shapes:
                if shape.shape_id == textbox.shape_id:
                    updated_shape = shape
                    break

            self.assertIsNotNone(updated_shape)
            text = updated_shape.text
            self.assertIn("Alpha", text)
            self.assertIn("TR:Alpha\nBeta", text)


if __name__ == "__main__":
    unittest.main()
