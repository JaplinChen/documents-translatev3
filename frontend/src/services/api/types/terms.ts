export interface TermLanguageInput {
  lang_code: string;
  value?: string;
}

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

export interface TermItem extends TermPayload {
  id: number;
  created_at?: string;
  updated_at?: string;
}

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

export interface TermListResponse {
  items: TermItem[];
}

export interface TermCategory {
  id: number;
  name: string;
  sort_order?: number;
}

export interface TermCategoryResponse {
  items: TermCategory[];
}

export interface TermBatchPayload {
  ids: number[];
  category_id?: number;
  status?: string;
  case_rule?: string;
}

export interface TermImportPreviewResponse {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  sample_rows: Record<string, string>[];
  detected_columns: string[];
  errors: Array<{ row: number; message: string }>;
}

export interface TermImportResponse {
  imported: number;
  skipped: number;
  failed: number;
  errors?: Array<{ term: string; message: string }>;
}
