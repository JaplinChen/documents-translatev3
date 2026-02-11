import { API_BASE_URL, createFormData, deleteJson, getBlob, getJson, postFile, postForm, startJsonLineStream } from './core';
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
        return postFile<PptxExtractResponse>('/api/pptx/extract', file);
    },

    async languages(file: File): Promise<PptxLanguagesResponse> {
        return postFile<PptxLanguagesResponse>('/api/pptx/languages', file);
    },

    async apply(params: PptxApplyParams): Promise<PptxApplyResponse> {
        return postForm<PptxApplyResponse>('/api/pptx/apply', params);
    },

    async download(filename: string): Promise<Blob> {
        return getBlob(`/api/pptx/download/${encodeURIComponent(filename)}`);
    },

    async history(): Promise<PptxHistoryResponse> {
        return getJson<PptxHistoryResponse>('/api/pptx/history');
    },

    async deleteHistory(filename: string): Promise<{ status: string }> {
        return deleteJson<{ status: string }>(
            `/api/pptx/history/${encodeURIComponent(filename)}`
        );
    },

    async translate(params: PptxTranslateParams): Promise<{ results: TextBlock[] }> {
        return postForm<{ results: TextBlock[] }>('/api/pptx/translate', params);
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
        return postForm<PptxExtractGlossaryResponse>('/api/pptx/extract-glossary', {
            blocks,
            target_language: targetLanguage,
            ...options,
        });
    },
};
