from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = BASE_DIR / "prompts"


DEFAULT_PROMPTS = {
    "translate_json": (
        """# 任務指令
請將提供的 JSON `payload` 中每個文字區塊翻譯為目標語言 {target_language_label}。

## 核心翻譯準則
1. **術語優先**：若提供 `preferred_terms`（術語表），必須「嚴格優先」使用其中的翻譯，
確保全文件一致。
2. **占位符保護**：若原文含 `placeholder_tokens`，必須完整保留至翻譯結果中，不可改動其語法結構。
3. **情境遵從**：若提供 `context`（如幻燈片標題、備註），請利用這些背景資訊
來更精準地抓取語意，但無需翻譯 Context。
4. **語言範例**：請參考以下目標語言的正確輸出風格：
{language_example}

## 輸出規範
- 只輸出 JSON 數據，不包含任何額外說明文字。
- 嚴禁輸出 Markdown 代碼塊標籤（如 ```json）。
- 翻譯內容請符合當地的商務/專業對話習慣。

## 參數與數據
- 目標語言：{target_language_label} ({target_language_code})
- 輔助提示：{language_hint}

{payload}"""
    ),
    "system_message": (
        """
你是一位具備 20 年經驗的資深專業翻譯家，
專長於技術文件、商務簡報與學術論文的本地化處理。
你的任務是將輸入的文字區塊翻譯為指定的目標語言，
同時嚴格遵守以下準則：
1. **精準原意**：保留原文的專業術語、語氣與語義深度，
   不進行額外的解釋或對話。
2. **格式安全**：只輸出合法的 JSON 物件，嚴禁包含任何 Markdown
   格式標籤（如 ```json）或引導文、結束語。
3. **區塊完整性**：確保翻譯後的文字長度與原文相近，
   以避免破壞文件（如 PPTX/PDF）的排版美感。
4. **占位符保護**：絕對不可翻譯或修改 {{ }} 或 { } 括號內的
   占位符。
5. **語言與標點**：必須符合目標語言當地的標點符號規範與
   技術習慣。
6. **雙語保留原則 (Bilingual Preservation)**：若原文區塊同時包含
   第一語言(如越文)與第二語言(如中文)，在翻譯或「校正模式」下，
   你**必須字節不差地在輸出中保留原文的第一語言部分**，
   僅對第二語言進行校正或翻譯。
   輸出應呈現為「原文第一語言 + 修訂後第二語言」的格式。
你的回答必須且只能是一個符合 Schema 規範 accessor 的 JSON。"""
    ),
    "ollama_batch": (
        """# 專業翻譯任務
你正處於批次處理模式。請將以下區塊翻譯為：{target_language_label} ({target_language_code})。

## 操作指南
- 嚴格依照提示的區塊格式輸出翻譯結果。
- 不要對翻譯內容進行任何評論、確認或解釋。
- 保持原文的標點符號風格，除非目標語言有特殊排版規範。
- {language_hint}
- {language_guard}

## 輸出範例
{language_example}

---
## 待翻譯區塊
{blocks}"""
    ),
    "glossary_extraction": (
        """# 任務：術語提取與初步翻譯
請分析以下簡報內容，提取出對翻譯一致性至關重要的核心術語、專有名詞或技術縮寫。

## 提取準則
1. **核心價值**：只提取真正頻繁出現或具備特定定義的專有名詞。
2. **翻譯精準**：針對每個提取的術語，提供最符合專業語境的目標語言 {target_language} 建議翻譯。
3. **因果說明**：簡短說明為何提取此術語（如：技術架構核心、公司專用縮寫）。

## 提示與要求
{language_hint}

## 輸出結構規範
輸出必須且僅能是一個 JSON 陣列，格式如下：
[
  {
    "source": "原文術語",
    "target": "建議翻譯",
    "reason": "提取原因"
  }
]

## 待分析簡報內容
---
{text_sample}
---"""
    ),
    "style_suggestion": (
        """
# 任務：文件視覺風格分析與建議
請分析以下文件內容的產業屬性、主題語氣與結構特徵，
並建議一套適合的 UI/文件視覺主題。

## 建議要求
- **配色方案**：提供主色 (Primary)、輔色 (Secondary) 與強調色
  (Accent) 的 Hex 碼。
- **字體建議**：推薦一款最能體現該文件風格的現代字體
  （如 Inter, Roboto, Playfair Display 等）。
- **設計理念**：簡述為何這些配色與字體適合該文件內容。

## 輸出結構規範
輸出必須且僅能是一個 JSON 物件，包含以下鍵值：
"theme_name", "primary_color", "secondary_color", "accent_color",
"font_recommendation", "rationale"。

## 待分析內容
{context}"""
    ),
}


def _ensure_dir() -> None:
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_defaults() -> None:
    _ensure_dir()
    for name, content in DEFAULT_PROMPTS.items():
        path = PROMPTS_DIR / f"{name}.md"
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def list_prompts() -> list[str]:
    _ensure_defaults()
    return sorted([path.stem for path in PROMPTS_DIR.glob("*.md")])


def get_prompt(name: str) -> str:
    _ensure_defaults()
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {name}")
    return path.read_text(encoding="utf-8")


def save_prompt(name: str, content: str) -> None:
    _ensure_dir()
    path = PROMPTS_DIR / f"{name}.md"
    path.write_text(content, encoding="utf-8")


def render_prompt(name: str, variables: dict[str, str]) -> str:
    template = get_prompt(name)
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{key}}}", value)
    return rendered
