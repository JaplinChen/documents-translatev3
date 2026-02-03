import type { LanguageSummary, TextBlock } from './common';

export interface XlsxExtractResponse {
  blocks: TextBlock[];
  language_summary: LanguageSummary;
  sheet_count: number;
}

export interface XlsxApplyParams {
  file: File;
  blocks: string;
  mode?: 'bilingual' | 'translated';
  bilingual_layout?: 'inline' | 'new_slide' | 'new_page' | 'new_sheet' | 'auto';
  target_language?: string;
}

export interface XlsxApplyResponse {
  status: string;
  filename: string;
  download_url: string;
}
