import { API_BASE_URL, ApiClientError, createFormData, handleResponse, startJsonLineStream } from './core';
import type {
    PptxApplyParams,
    PptxApplyResponse,
    PptxExtractGlossaryResponse,
    PptxExtractResponse,
    PptxHistoryResponse,
    PptxLanguagesResponse,
    PptxTranslateParams,
    TextBlock,
    TranslateProgressEvent,
} from '../api.types';

export const pptxApi = {
    async extract(file: File): Promise<PptxExtractResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/pptx/extract`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PptxExtractResponse>(response);
    },

    async languages(file: File): Promise<PptxLanguagesResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/pptx/languages`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PptxLanguagesResponse>(response);
    },

    async apply(params: PptxApplyParams): Promise<PptxApplyResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/pptx/apply`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PptxApplyResponse>(response);
    },

    async download(filename: string): Promise<Blob> {
        const response = await fetch(
            `${API_BASE_URL}/api/pptx/download/${encodeURIComponent(filename)}`
        );
        if (!response.ok) {
            throw new ApiClientError('Download failed', response.status);
        }
        return response.blob();
    },

    async history(): Promise<PptxHistoryResponse> {
        const response = await fetch(`${API_BASE_URL}/api/pptx/history`);
        return handleResponse<PptxHistoryResponse>(response);
    },

    async deleteHistory(filename: string): Promise<{ status: string }> {
        const response = await fetch(
            `${API_BASE_URL}/api/pptx/history/${encodeURIComponent(filename)}`,
            { method: 'DELETE' }
        );
        return handleResponse<{ status: string }>(response);
    },

    async translate(params: PptxTranslateParams): Promise<{ results: TextBlock[] }> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/pptx/translate`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<{ results: TextBlock[] }>(response);
    },

    translateStream(
        params: PptxTranslateParams,
        onEvent: (event: TranslateProgressEvent) => void,
        onError?: (error: Error) => void
    ): { abort: () => void } {
        const formData = createFormData(params);
        return startJsonLineStream(
            `${API_BASE_URL}/api/pptx/translate-stream`,
            formData,
            onEvent,
            onError
        );
    },

    async extractGlossary(
        blocks: string,
        targetLanguage: string = 'zh-TW',
        options?: {
            provider?: string;
            model?: string;
            api_key?: string;
            base_url?: string;
        }
    ): Promise<PptxExtractGlossaryResponse> {
        const formData = createFormData({
            blocks,
            target_language: targetLanguage,
            ...options,
        });
        const response = await fetch(`${API_BASE_URL}/api/pptx/extract-glossary`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<PptxExtractGlossaryResponse>(response);
    },
};
