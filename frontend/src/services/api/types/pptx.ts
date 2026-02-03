import type { GlossaryTerm } from './tm';
import type { LanguageSummary, TextBlock } from './common';

export interface PptxExtractResponse {
  blocks: TextBlock[];
  language_summary: LanguageSummary;
  slide_width: number;
  slide_height: number;
}

export interface PptxLanguagesResponse {
  language_summary: LanguageSummary;
}

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

export interface PptxApplyResponse {
  status: string;
  filename: string;
  download_url: string;
  version?: string;
}

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

export interface PptxHistoryItem {
  filename: string;
  created_at: string;
  size: number;
  download_url: string;
}

export interface PptxHistoryResponse {
  items: PptxHistoryItem[];
}

export interface PptxExtractGlossaryResponse {
  terms: GlossaryTerm[];
  error?: string;
}
