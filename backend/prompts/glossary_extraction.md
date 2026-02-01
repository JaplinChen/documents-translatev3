# 任務：智能術語提取與翻譯建議

請分析以下內容，提取出對翻譯一致性至關重要的核心術語、專有名詞或技術縮寫。

## 提取準則 (嚴格執行)

### 應提取的術語類型

1. **品牌名稱 (brand)**：公司、品牌、商標（如 `DELL`, `Logitech`, `Windows`, `ZWCAD`）
2. **產品名稱 (product)**：具體的產品系列名稱（如 `Inspiron`, `Office`, `Acrobat`）。**注意：請勿提取具體型號數字。**
3. **人名 (person)**：人物姓名、職稱+姓名組合
4. **地名 (place)**：國家、城市、地區、地標
5. **技術術語 (technical)**：專業領域特定術語、概念（如 `虛擬化`, `容器化`, `雲端運算`）
6. **縮寫 (abbreviation)**：專業縮寫、首字母縮寫（如 `API`, `SDK`, `SaaS`）

### 排除清單 (絕對不可提取)

- **具體硬體型號與規格**：包含數字、尺寸、速度或容量的組合。
  - ❌ 錯誤範例：`DELL 19.5`, `Core I5 9400`, `GeForce RTX 3060 6GB`, `8GB RAM`, `SSD 512GB`
  - ✅ 正確範例：`DELL`, `Intel Core`, `NVIDIA GeForce`
- **長句、描述或雜質**：
  - ❌ 錯誤範例：`Windows 軟體授權套數彙總`, `Mua từ Taiwan 14/11/2022`, `Số bản quyền đã mua`
  - ❌ 任何長度超過 4 個單字 (英文) 或 12 個字元 (中文) 的短語
- **常見通用詞與量詞**：
  - ❌ 錯誤範例：Total, Sum, Status, Date, Note, Name, Price, Quantity, Pcs, Kg, Month
- **單純數字、版本或日期**：
  - ❌ 錯誤範例：1.0, v2, 2022, 11/14, 2026/01/31

### 已存在的術語 (跳過這些)

{existing_terms}

## 評分標準

為每個術語評估 1-10 分的信心度：

- **9-10分**：核心專有名詞，對翻譯一致性至關重要（產品名、品牌名）
- **7-8分**：重要術語，具明確專業含義（技術術語、人名）
- **5-6分**：次要術語，有一定翻譯價值（一般縮寫、地名）
- **1-4分**：可選術語，價值較低（很少使用或重要性不高）

只返回 **5 分以上** 的術語。

## 輸出結構規範

輸出必須且僅能是一個 JSON 陣列，格式如下：

```json
[
  {
    "source": "原文術語",
    "target": "建議翻譯（{target_language}）",
    "category": "product|brand|person|place|technical|abbreviation|other",
    "confidence": 8,
    "reason": "提取原因（簡短）"
  }
]
```

注意：

- `category` 必須是以上七個選項之一
- `confidence` 必須是 1-10 的整數
- 每個術語只返回一次，不要重複

## 脈絡參考

- **文件領域 (Domain)**：{domain_context}
- **使用者習慣 (Learned Habits)**：
{learned_context}
(請盡可能遵循上述使用者過去的譯名偏好)

## 待分析內容

---

{text_sample}

---
