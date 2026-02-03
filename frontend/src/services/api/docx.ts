import { API_BASE_URL, ApiClientError, createFormData, handleResponse, startJsonLineStream } from './core';
import type { DocxApplyParams, DocxApplyResponse, DocxExtractResponse, PptxTranslateParams, TranslateProgressEvent } from '../api.types';

export const docxApi = {
    async extract(file: File): Promise<DocxExtractResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/docx/extract`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<DocxExtractResponse>(response);
    },

    async apply(params: DocxApplyParams): Promise<DocxApplyResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/docx/apply`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<DocxApplyResponse>(response);
    },

    async download(filename: string): Promise<Blob> {
        const response = await fetch(
            `${API_BASE_URL}/api/docx/download/${encodeURIComponent(filename)}`
        );
        if (!response.ok) {
            throw new ApiClientError('Download failed', response.status);
        }
        return response.blob();
    },

    async history(): Promise<{ items: unknown[] }> {
        const response = await fetch(`${API_BASE_URL}/api/docx/history`);
        return handleResponse<{ items: unknown[] }>(response);
    },

    async deleteHistory(filename: string): Promise<{ status: string }> {
        const response = await fetch(
            `${API_BASE_URL}/api/docx/history/${encodeURIComponent(filename)}`,
            { method: 'DELETE' }
        );
        return handleResponse<{ status: string }>(response);
    },

    translateStream(
        params: PptxTranslateParams,
        onEvent: (event: TranslateProgressEvent) => void,
        onError?: (error: Error) => void
    ): { abort: () => void } {
        const formData = createFormData(params);
        return startJsonLineStream(
            `${API_BASE_URL}/api/docx/translate-stream`,
            formData,
            onEvent,
            onError
        );
    },
};
