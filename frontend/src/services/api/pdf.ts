import { API_BASE_URL, ApiClientError, createFormData, handleResponse, startJsonLineStream } from './core';
import type { PdfApplyParams, PdfApplyResponse, PdfExtractResponse, PptxTranslateParams, TranslateProgressEvent } from '../api.types';

export const pdfApi = {
    async extract(file: File): Promise<PdfExtractResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/pdf/extract`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PdfExtractResponse>(response);
    },

    async apply(params: PdfApplyParams): Promise<PdfApplyResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/pdf/apply`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PdfApplyResponse>(response);
    },

    async download(filename: string): Promise<Blob> {
        const response = await fetch(
            `${API_BASE_URL}/api/pdf/download/${encodeURIComponent(filename)}`
        );
        if (!response.ok) {
            throw new ApiClientError('Download failed', response.status);
        }
        return response.blob();
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
