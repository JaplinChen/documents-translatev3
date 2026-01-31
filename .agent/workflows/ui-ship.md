---
description: 🎨 前後端對接流水線 (Connect → i18n → Diagram)
---

# UI Ship Pipeline

這個流水線整合了從後端 API 對接到前端 i18n 與架構圖生成的完整流程。

## 執行步驟

1. **Connect**: 使用 `/ui-connect` 生成前端 API Client 與 Interface。
2. **i18n**: 使用 `/ui-i18n` 提取硬編碼文字並生成多語系鍵值。
3. **Diagram**: 使用 `/ui-diagram` 生成 API 呼叫的時序圖 (Sequence Diagram)。

## 驗證

- 確保 `api.client.ts` 可正常呼叫。
- 務必更新 `zh-TW.json`, `en-US.json`, `vi.json`。
- 產出 `api-sequence-diagram.md` 供文件備份。
