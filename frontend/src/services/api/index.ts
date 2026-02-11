import { pptxApi } from './pptx';
import { docxApi } from './docx';
import { pdfApi } from './pdf';
import { xlsxApi } from './xlsx';
import { llmApi } from './llm';
import { layoutsApi } from './layouts';
import { exportApi } from './export';
import { tmApi } from './tm';
import { termsApi } from './terms';
import { preserveTermsApi } from './preserve_terms';
import { promptsApi } from './prompts';
import { styleApi } from './style';
import { ocrApi } from './ocr';
import { tokenStatsApi } from './token_stats';

export { pptxApi } from './pptx';
export { docxApi } from './docx';
export { pdfApi } from './pdf';
export { xlsxApi } from './xlsx';
export { llmApi } from './llm';
export { layoutsApi } from './layouts';
export { exportApi } from './export';
export { tmApi } from './tm';
export { termsApi } from './terms';
export { preserveTermsApi } from './preserve_terms';
export { promptsApi } from './prompts';
export { styleApi } from './style';
export { ocrApi } from './ocr';
export { tokenStatsApi } from './token_stats';

const api = {
    pptx: pptxApi,
    docx: docxApi,
    pdf: pdfApi,
    xlsx: xlsxApi,
    llm: llmApi,
    layouts: layoutsApi,
    export: exportApi,
    tm: tmApi,
    terms: termsApi,
    preserveTerms: preserveTermsApi,
    prompts: promptsApi,
    style: styleApi,
    ocr: ocrApi,
    tokenStats: tokenStatsApi,
};

export default api;
