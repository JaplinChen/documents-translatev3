export { pptxApi } from './pptx';
export { docxApi } from './docx';
export { pdfApi } from './pdf';
export { xlsxApi } from './xlsx';
export { llmApi } from './llm';
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
