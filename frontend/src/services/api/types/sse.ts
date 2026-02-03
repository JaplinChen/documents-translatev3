export interface TranslateProgressEvent {
  type: 'progress' | 'result' | 'error' | 'complete';
  block_id?: string;
  translated_text?: string;
  progress?: number;
  total?: number;
  error?: string;
}
