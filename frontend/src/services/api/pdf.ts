import { API_BASE_URL, createFormData, getBlob, postFile, postForm, startJsonLineStream } from './core';
import type { PdfApplyParams, PdfApplyResponse, PdfExtractResponse, PptxTranslateParams, TranslateProgressEvent } from '../api.types';

export const pdfApi = {
    async extract(file: File): Promise<PdfExtractResponse> {
        return postFile<PdfExtractResponse>('/api/pdf/extract', file);
    },

    async apply(params: PdfApplyParams): Promise<PdfApplyResponse> {
        return postForm<PdfApplyResponse>('/api/pdf/apply', params);
    },

    async download(filename: string): Promise<Blob> {
        return getBlob(`/api/pdf/download/${encodeURIComponent(filename)}`);
    },

    translateStream(
        params: PptxTranslateParams,
        onEvent: (event: TranslateProgressEvent) => void,
        onError?: (error: Error) => void
    ): { abort: () => void } {
        const formData = createFormData(params);
        return startJsonLineStream(
            `${API_BASE_URL}/api/pdf/translate-stream`,
            formData,
            onEvent,
            onError
        );
    },
};
