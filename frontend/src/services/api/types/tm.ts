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

export interface GlossaryTerm {
  term: string;
  translation?: string;
  category?: string;
}

export interface GlossaryResponse {
  items: GlossaryEntry[];
  total: number;
  limit: number;
}

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

export interface MemoryResponse {
  items: MemoryEntry[];
  total: number;
  limit: number;
}

export interface TmCategory {
  id: number;
  name: string;
  sort_order: number;
}

export interface TmCategoryResponse {
  items: TmCategory[];
}

export interface BatchDeleteRequest {
  ids: number[];
}
