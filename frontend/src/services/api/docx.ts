import { API_BASE_URL, createFormData, deleteJson, getBlob, getJson, postFile, postForm, startJsonLineStream } from './core';
import type { DocxApplyParams, DocxApplyResponse, DocxExtractResponse, PptxTranslateParams, TranslateProgressEvent } from '../api.types';

export const docxApi = {
    async extract(file: File): Promise<DocxExtractResponse> {
        return postFile<DocxExtractResponse>('/api/docx/extract', file);
    },

    async apply(params: DocxApplyParams): Promise<DocxApplyResponse> {
        return postForm<DocxApplyResponse>('/api/docx/apply', params);
    },

    async download(filename: string): Promise<Blob> {
        return getBlob(`/api/docx/download/${encodeURIComponent(filename)}`);
    },

    async history(): Promise<{ items: unknown[] }> {
        return getJson<{ items: unknown[] }>('/api/docx/history');
    },

    async deleteHistory(filename: string): Promise<{ status: string }> {
        return deleteJson<{ status: string }>(
            `/api/docx/history/${encodeURIComponent(filename)}`
        );
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
