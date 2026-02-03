export interface OcrSettings {
  dpi?: number;
  lang?: string;
  conf_min?: number;
  psm?: number;
  engine?: 'tesseract' | 'paddle';
  poppler_path?: string;
}
