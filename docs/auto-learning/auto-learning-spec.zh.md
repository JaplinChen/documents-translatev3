# 自動學習系統規格書（Draft v1）

## 1. 目的
建立完全自動的學習管線，提升術語抽取、翻譯一致性與分類品質，且不需人工審核。系統需安全、自我修正並可擴展於多人使用情境。

## 2. 範圍
- 納入範圍：
  - 來自雙語內容與使用者回饋的自動學習
  - 術語抽取強化（提示脈絡 + 資料品質）
  - 翻譯記憶（TM）品質提升
  - 自動領域/類別分類
  - PostgreSQL 遷移與 Docker 佈署
- 不在範圍：
  - 模型微調或外部 ML 訓練管線
  - 人工審核流程

## 3. 現況摘要（Baseline）
- 學習為事件觸發，無背景 worker。
- term_feedback 累積到固定門檻即自動升級 glossary。
- 翻譯完成後寫入 TM，以精確匹配使用。
- 領域判斷為關鍵字規則。
- 資料儲存在 SQLite（translation_memory.db、terms.db）。

## 4. 目標與非目標
### 目標
- 完全自動化學習、不需人工介入。
- 降低噪音與錯誤學習，提升正確率。
- 支援多人/多專案規模。
- 具備自動回滾與衰減機制。

### 非目標
- 不進行語言模型微調或訓練。
- 不引入人工審核流程。

## 5. 高階架構
- 服務：
  - API（backend）
  - Worker（排程或常駐）
  - PostgreSQL
- 儲存：
  - translation_memory 系列表（tm、glossary、term_feedback）
  - terms（統一術語中心）
  - learning_events、learning_stats

## 6. 自動學習管線（8 階段）
1) 資料進入
- 來源：雙語文件、翻譯結果、使用者修正
- 正規化並切段成對齊的 source/target

2) 清洗與去噪
- 去除空白、純數字、語言不匹配
- 過濾低品質 TM
- 依 (source, target, lang) 去重

3) 術語抽取
- 規則抽取（縮寫、品牌、技術詞）
- LLM 抽取（樣本文本）

4) 自動分類
- 規則 + embedding/LLM 分類
- 紀錄 domain_score、category_score

5) 自動升級
- 依權重分數評估
- 升級到：
  - 候選池
  - TM
  - Glossary（高分門檻）

6) 自動衰減與淘汰
- 依時間/未命中衰減
- 高覆寫率移除

7) 回饋迴圈
- 將學習結果注入提示語境
- 使用 TM/Glossary 引導翻譯

8) 監控與自動調參
- 追蹤命中率、覆寫率、一致性
- 自動調整門檻

## 7. 評分與升級規則
- 候選分數 = 出現次數 × 語境相似度 × 對齊品質 × 新鮮度
- 範例門檻：
  - score >= 0.85 -> glossary
  - score >= 0.65 -> TM
  - score >= 0.45 -> staging

## 8. 資料模型（提案）
### 核心表
- tm
- glossary
- term_feedback
- terms

### 新增表
- learning_candidates
- learning_events
- learning_stats

### 關鍵欄位（例）
- source_text, target_text, source_lang, target_lang
- domain, category, confidence, last_used_at, overwrite_count
- source_type（auto|feedback|import）
- scope_id（project/user）

## 9. 資料生命週期
- 新資料先進候選池，再升級。
- 過期或高覆寫條目自動移除。
- learning_events 保留追溯性。

## 10. 營運需求
- 支援多人併發。
- DB 可擴展至百萬級 TM。
- PostgreSQL 必須有備份機制。

## 11. 成功指標（KPI）
- TM 命中率
- Glossary 命中率
- 覆寫率
- 術語抽取準確率（抽樣）

## 12. 風險與對策
- 風險：噪音資料導致錯誤學習
  - 對策：加權評分 + 衰減 + 覆寫偵測
- 風險：資料庫膨脹
  - 對策：衰減/淘汰與歸檔

