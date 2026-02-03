export interface ApiResponse<T = unknown> {
  status?: string;
  message?: string;
  data?: T;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface LanguageSummary {
  [langCode: string]: number;
}

export interface TextBlock {
  id: string;
  source_text: string;
  translated_text?: string;
  slide_index?: number;
  page_index?: number;
  sheet_index?: number;
  shape_id?: string;
  cell_ref?: string;
  position?: BlockPosition;
  style?: BlockStyle;
}

export interface BlockPosition {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
}

export interface BlockStyle {
  font_size?: number;
  font_name?: string;
  font_color?: string;
  bold?: boolean;
  italic?: boolean;
}
