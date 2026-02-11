from backend.services.translation_memory import upsert_tm, get_tm_count
import re


def test_tm_filter():
    print("測試後端 TM 過濾器...")

    initial_count = get_tm_count()

    # 案例 1: 應該被攔截 (型號 -> 量詞)
    bad_entry_1 = {
        "source_lang": "en",
        "target_lang": "zh-TW",
        "source_text": "9 pro",
        "target_text": "九個",
    }
    upsert_tm(bad_entry_1)

    # 案例 2: 應該被連結 (CPU 過度翻譯)
    bad_entry_2 = {
        "source_lang": "en",
        "target_lang": "zh-TW",
        "source_text": "Intel Core Ultra 7",
        "target_text": "核心極致7號",
    }
    upsert_tm(bad_entry_2)

    # 案例 3: 應該被儲存 (正常翻譯)
    good_entry = {
        "source_lang": "en",
        "target_lang": "zh-TW",
        "source_text": "User manual",
        "target_text": "使用者手冊",
    }
    upsert_tm(good_entry)

    final_count = get_tm_count()
    print(f"初始筆數: {initial_count}, 最終筆數: {final_count}")

    if final_count == initial_count + 1:
        print("  [成功] 過濾器正確運作：攔截了 2 筆，准許了 1 筆。")
    else:
        print(f"  [失敗] 預期增加 1 筆，但增加了 {final_count - initial_count} 筆。")


if __name__ == "__main__":
    test_tm_filter()
