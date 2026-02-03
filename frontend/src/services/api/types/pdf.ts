import type { LanguageSummary, TextBlock } from './common';

export interface PdfExtractResponse {
  blocks: TextBlock[];
  language_summary: LanguageSummary;
  page_count: number;
}

export interface PdfApplyParams {
  file: File;
  blocks: string;
  mode?: 'bilingual' | 'translated';
}

export interface PdfApplyResponse {
  status: string;
  filename: string;
  download_url: string;
}
