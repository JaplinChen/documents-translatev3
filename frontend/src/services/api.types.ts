/**
 * API Types - TypeScript Interface 定義
 *
 * 此檔案由 /ui-ship 流水線自動生成
 * 根據 backend/api/ 目錄的 API 端點定義
 */

// =============================================================================
// Common Types
// =============================================================================

/** API 通用回應類型 */
export interface ApiResponse<T = unknown> {
  status?: string;
  message?: string;
  data?: T;
}

/** API 錯誤類型 */
export interface ApiError {
  detail: string;
  status_code?: number;
}

/** 分頁參數 */
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

/** 語言摘要 */
export interface LanguageSummary {
  [langCode: string]: number;
}

// =============================================================================
// Block Types (共用)
// =============================================================================

/** 文本區塊 */
export interface TextBlock {
  id: string;
  source_text: string;
  translated_text?: string;
  slide_index?: number;
  page_index?: number;
  sheet_index?: number;
  shape_id?: string;
  cell_ref?: string;
  position?: BlockPosition;
  style?: BlockStyle;
}

/** 區塊位置 */
export interface BlockPosition {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
}

/** 區塊樣式 */
export interface BlockStyle {
  font_size?: number;
  font_name?: string;
  font_color?: string;
  bold?: boolean;
  italic?: boolean;
}

// =============================================================================
// PPTX API Types
// =============================================================================

/** PPTX 提取回應 */
export interface PptxExtractResponse {
  blocks: TextBlock[];
  language_summary: LanguageSummary;
  slide_width: number;
  slide_height: number;
}

/** PPTX 語言偵測回應 */
export interface PptxLanguagesResponse {
  language_summary: LanguageSummary;
}

/** PPTX 套用請求參數 */
export interface PptxApplyParams {
  file: File;
  blocks: string;
  mode?: 'bilingual' | 'correction' | 'translated';
  bilingual_layout?: 'inline' | 'side-by-side';
  fill_color?: string;
  text_color?: string;
  line_color?: string;
  line_dash?: string;
  font_mapping?: string;
  target_language?: string;
}

/** PPTX 套用回應 */
export interface PptxApplyResponse {
  status: string;
  filename: string;
  download_url: string;
  version?: string;
}

/** PPTX 翻譯請求參數 */
export interface PptxTranslateParams {
  blocks: string;
  source_language?: string;
  secondary_language?: string;
  target_language?: string;
  mode?: 'bilingual' | 'translated' | 'correction';
  use_tm?: boolean;
  provider?: string;
  model?: string;
  api_key?: string;
  base_url?: string;
  ollama_fast_mode?: boolean;
  tone?: string;
  vision_context?: boolean;
  smart_layout?: boolean;
  refresh?: boolean;
  similarity_threshold?: number;
  completed_ids?: string;
}

/** PPTX 歷史項目 */
export interface PptxHistoryItem {
  filename: string;
  created_at: string;
  size: number;
  download_url: string;
}

/** PPTX 歷史回應 */
export interface PptxHistoryResponse {
  items: PptxHistoryItem[];
}

/** PPTX 提取詞彙回應 */
export interface PptxExtractGlossaryResponse {
  terms: GlossaryTerm[];
  error?: string;
}

// =============================================================================
// DOCX API Types
// =============================================================================

/** DOCX 提取回應 */
export interface DocxExtractResponse {
  blocks: TextBlock[];
  language_summary: LanguageSummary;
}

/** DOCX 套用請求參數 */
export interface DocxApplyParams {
  file: File;
  blocks: string;
  mode?: 'bilingual' | 'translated';
  target_language?: string;
}

/** DOCX 套用回應 */
export interface DocxApplyResponse {
  status: string;
  filename: string;
  download_url: string;
}

// =============================================================================
// PDF API Types
// =============================================================================

/** PDF 提取回應 */
export interface PdfExtractResponse {
  blocks: TextBlock[];
  language_summary: LanguageSummary;
  page_count: number;
}

/** PDF 套用請求參數 */
export interface PdfApplyParams {
  file: File;
  blocks: string;
  mode?: 'bilingual' | 'translated';
}

/** PDF 套用回應 */
export interface PdfApplyResponse {
  status: string;
  filename: string;
  download_url: string;
}

// =============================================================================
// XLSX API Types
// =============================================================================

/** XLSX 提取回應 */
export interface XlsxExtractResponse {
  blocks: TextBlock[];
  language_summary: LanguageSummary;
  sheet_count: number;
}

/** XLSX 套用請求參數 */
export interface XlsxApplyParams {
  file: File;
  blocks: string;
  mode?: 'bilingual' | 'translated';
  bilingual_layout?: 'inline' | 'side-by-side';
  target_language?: string;
}

/** XLSX 套用回應 */
export interface XlsxApplyResponse {
  status: string;
  filename: string;
  download_url: string;
}

// =============================================================================
// LLM API Types
// =============================================================================

/** LLM 模型資訊 */
export interface LlmModel {
  id: string;
  name?: string;
  description?: string;
}

/** LLM 模型列表請求參數 */
export interface LlmModelsParams {
  provider: string;
  api_key?: string;
  base_url?: string;
}

/** LLM 模型列表回應 */
export interface LlmModelsResponse {
  models: LlmModel[];
}

// =============================================================================
// Export API Types
// =============================================================================

/** 匯出格式 */
export interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mime_type: string;
}

/** 匯出格式列表回應 */
export interface ExportFormatsResponse {
  formats: ExportFormat[];
}

/** 匯出請求 */
export interface ExportRequest {
  blocks: TextBlock[];
}

/** 術語建議 */
export interface TermSuggestion {
  term: string;
  category: string;
  confidence: number;
  context: string;
  suggested_action: string;
}

/** 術語建議回應 */
export interface SuggestTermsResponse {
  suggestions: TermSuggestion[];
}

// =============================================================================
// Translation Memory (TM) API Types
// =============================================================================

/** 詞彙表條目 */
export interface GlossaryEntry {
  id?: number;
  source_lang: string;
  target_lang: string;
  source_text: string;
  target_text: string;
  priority?: number;
  category_id?: number;
  created_at?: string;
  updated_at?: string;
}

/** 詞彙術語 */
export interface GlossaryTerm {
  term: string;
  translation?: string;
  category?: string;
}

/** 詞彙表回應 */
export interface GlossaryResponse {
  items: GlossaryEntry[];
  total: number;
  limit: number;
}

/** 翻譯記憶條目 */
export interface MemoryEntry {
  id?: number;
  source_lang: string;
  target_lang: string;
  source_text: string;
  target_text: string;
  category_id?: number;
  created_at?: string;
  updated_at?: string;
}

/** 翻譯記憶回應 */
export interface MemoryResponse {
  items: MemoryEntry[];
  total: number;
  limit: number;
}

/** TM 分類 */
export interface TmCategory {
  id: number;
  name: string;
  sort_order: number;
}

/** TM 分類列表回應 */
export interface TmCategoryResponse {
  items: TmCategory[];
}

/** 批次刪除請求 */
export interface BatchDeleteRequest {
  ids: number[];
}

// =============================================================================
// Terms API Types
// =============================================================================

/** 術語語言輸入 */
export interface TermLanguageInput {
  lang_code: string;
  value?: string;
}

/** 術語 Payload */
export interface TermPayload {
  term: string;
  category_id?: number;
  category_name?: string;
  status?: 'active' | 'inactive' | 'pending';
  case_rule?: string;
  note?: string;
  source?: string;
  aliases?: string[];
  languages?: TermLanguageInput[];
  created_by?: string;
}

/** 術語項目 */
export interface TermItem extends TermPayload {
  id: number;
  created_at?: string;
  updated_at?: string;
}

/** 術語列表請求參數 */
export interface TermListParams {
  q?: string;
  category_id?: number;
  status?: string;
  missing_lang?: string;
  has_alias?: boolean;
  created_by?: string;
  date_from?: string;
  date_to?: string;
}

/** 術語列表回應 */
export interface TermListResponse {
  items: TermItem[];
}

/** 術語分類 */
export interface TermCategory {
  id: number;
  name: string;
  sort_order?: number;
}

/** 術語分類回應 */
export interface TermCategoryResponse {
  items: TermCategory[];
}

/** 術語批次更新請求 */
export interface TermBatchPayload {
  ids: number[];
  category_id?: number;
  status?: string;
  case_rule?: string;
}

/** 術語匯入預覽回應 */
export interface TermImportPreviewResponse {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  sample_rows: Record<string, string>[];
  detected_columns: string[];
  errors: Array<{ row: number; message: string }>;
}

/** 術語匯入回應 */
export interface TermImportResponse {
  imported: number;
  skipped: number;
  failed: number;
  errors?: Array<{ term: string; message: string }>;
}

// =============================================================================
// Preserve Terms API Types
// =============================================================================

/** 保留術語 */
export interface PreserveTerm {
  id?: string;
  term: string;
  category?: string;
  case_sensitive?: boolean;
  created_at?: string;
}

/** 保留術語列表回應 */
export interface PreserveTermsResponse {
  terms: PreserveTerm[];
}

/** 保留術語批次請求 */
export interface PreserveTermBatchRequest {
  terms: PreserveTerm[];
}

/** 保留術語批次回應 */
export interface PreserveTermBatchResponse {
  created: number;
  skipped: number;
}

/** 轉換為詞彙表請求 */
export interface ConvertToGlossaryRequest {
  id: string;
  target_lang?: string;
  priority?: number;
}

// =============================================================================
// Prompts API Types
// =============================================================================

/** 提示內容 */
export interface PromptContent {
  name: string;
  content: string;
}

// =============================================================================
// Style API Types
// =============================================================================

/** 樣式建議請求 */
export interface StyleSuggestRequest {
  blocks: TextBlock[];
  provider?: string;
  model?: string;
}

/** 樣式建議回應 */
export interface StyleSuggestResponse {
  theme_name: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_recommendation: string;
  rationale: string;
}

// =============================================================================
// OCR Settings API Types
// =============================================================================

/** OCR 設定 */
export interface OcrSettings {
  dpi?: number;
  lang?: string;
  conf_min?: number;
  psm?: number;
  engine?: 'tesseract' | 'paddle';
  poppler_path?: string;
}

// =============================================================================
// Token Stats API Types
// =============================================================================

/** Token 使用統計 */
export interface TokenUsage {
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  operation?: string;
  timestamp?: string;
}

/** Session 統計 */
export interface SessionStats {
  total_requests: number;
  total_tokens: number;
  total_cost_usd: number;
  by_provider: Record<string, TokenUsage>;
}

/** Token 統計回應 */
export interface TokenStatsResponse {
  session: SessionStats;
  all_time: SessionStats;
}

/** Token 記錄請求 */
export interface TokenRecordRequest {
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  operation?: string;
}

/** Token 估算回應 */
export interface TokenEstimateResponse {
  estimated_tokens: number;
  text_length: number;
}

// =============================================================================
// SSE Event Types (for streaming endpoints)
// =============================================================================

/** SSE 翻譯進度事件 */
export interface TranslateProgressEvent {
  type: 'progress' | 'result' | 'error' | 'complete';
  block_id?: string;
  translated_text?: string;
  progress?: number;
  total?: number;
  error?: string;
}
