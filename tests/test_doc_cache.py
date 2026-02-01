import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.services.document_cache import doc_cache


def test_cache():
    print("=== 開始測試 DocumentCache ===")

    test_data = b"Hello Document Cache 2026"
    test_hash = doc_cache.get_hash(test_data)
    blocks = [{"text": "Hello World", "id": 1}]
    metadata = {"width": 100, "height": 200}

    print(f"1. 測試雜湊計算: {test_hash}")

    print("2. 測試寫入快取...")
    doc_cache.set(test_hash, blocks, metadata, "test_ext")

    print("3. 測試讀取快取...")
    cached = doc_cache.get(test_hash)

    if cached and cached["blocks"] == blocks and cached["metadata"] == metadata:
        print("✅ 快取讀寫驗證成功！")
    else:
        print("❌ 快取讀寫驗證失敗。")
        print(f"預取: {blocks}, {metadata}")
        print(f"實際: {cached}")


if __name__ == "__main__":
    test_cache()
