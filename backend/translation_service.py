from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TranslationRequest:
    document_language: str
    target_language: str
    blocks: list[dict]


class MockGPTClient:
    def translate_blocks(self, blocks: Iterable[dict], target_language: str) -> list[str]:
        return [block["source_text"] for block in blocks]


def build_translation_contract(
    blocks: Iterable[dict],
    translated_texts: Iterable[str],
    document_language: str = "auto",
    target_language: str = "zh-TW",
) -> dict:
    contract_blocks = []
    for block, translated_text in zip(blocks, translated_texts):
        block_type = "paragraph"
        block_id = block.get("id", "")
        if block_id.startswith("t"):
            block_type = "table"
        contract_blocks.append(
            {
                "id": block_id,
                "type": block_type,
                "source_text": block.get("source_text", ""),
                "translated_text": translated_text,
                "bilingual_layout": "append",
                "corrections": [],
            }
        )

    return {
        "document_language": document_language,
        "target_language": target_language,
        "blocks": contract_blocks,
    }


def translate_document(
    blocks: Iterable[dict],
    document_language: str = "auto",
    target_language: str = "zh-TW",
    gpt_client: MockGPTClient | None = None,
) -> dict:
    client = gpt_client or MockGPTClient()
    translated_texts = client.translate_blocks(blocks, target_language)
    return build_translation_contract(
        blocks=blocks,
        translated_texts=translated_texts,
        document_language=document_language,
        target_language=target_language,
    )
