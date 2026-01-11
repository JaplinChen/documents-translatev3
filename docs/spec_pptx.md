# PPTX Translation – MVP Specification (Internal Tool)

## 1. Goal
Build an internal tool to translate PPTX files while preserving layout as much as possible.

Initial focus:
- Existing PPTX input
- Text extraction → translation → apply back to the same PPTX
- Internal usage only

## 2. In Scope (MVP)

### 2.1 Supported Text Types
- Text boxes (including placeholders)
- Table cell text
- Speaker notes (optional but recommended)

### 2.2 Translation Modes
- Direct translation:
  - Replace original text with translated text
- Bilingual:
  - Output format:
    source_text
    (blank line)
    translated_text

### 2.3 Correction Style (MVP)
- Color highlight only
  - Entire translated text may use a different font color
  - Fine-grained diff is out of scope for MVP

### 2.4 Language Handling
- Auto-detect source language
- User specifies target language (e.g. en, zh-TW, ja)

## 3. Explicitly Out of Scope (MVP)
- SmartArt
- Charts (including embedded Excel)
- WordArt / artistic text
- Text inside images (OCR)
- Animations and transitions
- Public access, billing, multi-tenant support

## 4. Data Model (Extraction Result)

Each extracted block MUST include:

- slide_index: integer (0-based)
- shape_id: integer (shape.shape_id from python-pptx)
- block_type: textbox | table_cell | notes
- source_text: string
- translated_text: string (empty before translation)
- mode: direct | bilingual

Text formatting rules:
- Preserve line breaks as '\n'
- Ignore empty or whitespace-only text blocks

## 5. Processing Flow

1. User uploads PPTX
2. System extracts text blocks
3. Blocks are sent to LLM for translation
4. LLM returns JSON following translation_contract_pptx.json
5. System applies translated text back to the PPTX
6. Output PPTX is generated

## 6. Quality Requirements
- Slides count must remain unchanged
- Shapes must not be repositioned or resized
- Text content must be replaced only inside the original shape
- No crashes on unsupported shapes (skip safely)

## 7. Known Limitations (Must Be Documented)
- Formatting (mixed fonts, runs) may be simplified
- Color highlighting may apply to entire text instead of per-sentence
- Some complex layouts may slightly reflow text
- When applying bilingual text, translated color may apply to the entire text block if per-paragraph coloring is not supported by the shape/runs.
- Correction styling applies at the shape or table level; per-cell borders and per-run background fills may not be available in python-pptx.

## 8. Definition of Done (for each work package)
- Code compiles and runs locally
- At least one automated test
- A runnable example command is documented
- Limitations are clearly stated in code comments or docs
