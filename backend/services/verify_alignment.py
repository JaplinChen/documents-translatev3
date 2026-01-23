from backend.services.bilingual_alignment import align_bilingual_blocks
import json

def test_alignment():
    blocks = [
        {"source_text": "Chào buổi sáng", "client_id": "1"},  # Vietnamese
        {"source_text": "早安", "client_id": "2"},           # Traditional Chinese
        {"source_text": "Bạn có khỏe không?", "client_id": "3"}, # Vietnamese
        {"source_text": "你好嗎？", "client_id": "4"},         # Traditional Chinese
        {"source_text": "This is English", "client_id": "5"},
    ]
    
    source_lang = "vi"
    target_lang = "zh-TW"
    
    print("--- Input Blocks ---")
    for b in blocks:
        print(f"[{b.get('source_text')}]")
        
    result = align_bilingual_blocks(blocks, source_lang, target_lang)
    
    print("\n--- Output Blocks ---")
    for b in result:
        print(f"ID: {b.get('client_id')}, Role: {b.get('alignment_role', 'none')}, Pair: {b.get('alignment_pair_id', 'none')}, Source: {b.get('alignment_source', 'none')}")

if __name__ == "__main__":
    test_alignment()
