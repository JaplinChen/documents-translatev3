import type { LanguageSummary, TextBlock } from './common';

export interface DocxExtractResponse {
  blocks: TextBlock[];
  language_summary: LanguageSummary;
}

export interface DocxApplyParams {
  file: File;
  blocks: string;
  mode?: 'bilingual' | 'translated';
  bilingual_layout?: 'inline';
  layout_id?: string;
  layout_params?: string;
  target_language?: string;
}

export interface DocxApplyResponse {
  status: string;
  filename: string;
  download_url: string;
}
