import type { LanguageSummary, TextBlock } from './common';

export interface DocxExtractResponse {
  blocks: TextBlock[];
  language_summary: LanguageSummary;
}

export interface DocxApplyParams {
  file: File;
  blocks: string;
  mode?: 'bilingual' | 'translated';
  target_language?: string;
}

export interface DocxApplyResponse {
  status: string;
  filename: string;
  download_url: string;
}
