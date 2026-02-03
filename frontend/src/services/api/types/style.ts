import type { TextBlock } from './common';

export interface StyleSuggestRequest {
  blocks: TextBlock[];
  provider?: string;
  model?: string;
}

export interface StyleSuggestResponse {
  theme_name: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_recommendation: string;
  rationale: string;
}
