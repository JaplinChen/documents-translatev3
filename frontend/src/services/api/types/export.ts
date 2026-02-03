import type { TextBlock } from './common';

export interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mime_type: string;
}

export interface ExportFormatsResponse {
  formats: ExportFormat[];
}

export interface ExportRequest {
  blocks: TextBlock[];
}

export interface TermSuggestion {
  term: string;
  category: string;
  confidence: number;
  context: string;
  suggested_action: string;
}

export interface SuggestTermsResponse {
  suggestions: TermSuggestion[];
}
