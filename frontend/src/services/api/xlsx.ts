import { API_BASE_URL, ApiClientError, createFormData, handleResponse, startJsonLineStream } from './core';
import type { PptxTranslateParams, TranslateProgressEvent, XlsxApplyParams, XlsxApplyResponse, XlsxExtractResponse } from '../api.types';

export const xlsxApi = {
    async extract(file: File): Promise<XlsxExtractResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/xlsx/extract`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<XlsxExtractResponse>(response);
    },

    async apply(params: XlsxApplyParams): Promise<XlsxApplyResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/xlsx/apply`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<XlsxApplyResponse>(response);
    },

    async download(filename: string): Promise<Blob> {
        const response = await fetch(
            `${API_BASE_URL}/api/xlsx/download/${encodeURIComponent(filename)}`
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
            `${API_BASE_URL}/api/xlsx/translate-stream`,
            formData,
            onEvent,
            onError
        );
    },
};
