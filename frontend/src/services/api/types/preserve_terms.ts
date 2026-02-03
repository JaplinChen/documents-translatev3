export interface PreserveTerm {
  id?: string;
  term: string;
  category?: string;
  case_sensitive?: boolean;
  created_at?: string;
}

export interface PreserveTermsResponse {
  terms: PreserveTerm[];
}

export interface PreserveTermBatchRequest {
  terms: PreserveTerm[];
}

export interface PreserveTermBatchResponse {
  created: number;
  skipped: number;
}

export interface ConvertToGlossaryRequest {
  id: string;
  target_lang?: string;
  priority?: number;
}
