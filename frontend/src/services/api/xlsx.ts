import { API_BASE_URL, createFormData, getBlob, postFile, postForm, startJsonLineStream } from './core';
import type { PptxTranslateParams, TranslateProgressEvent, XlsxApplyParams, XlsxApplyResponse, XlsxExtractResponse } from '../api.types';

export const xlsxApi = {
    async extract(file: File): Promise<XlsxExtractResponse> {
        return postFile<XlsxExtractResponse>('/api/xlsx/extract', file);
    },

    async apply(params: XlsxApplyParams): Promise<XlsxApplyResponse> {
        return postForm<XlsxApplyResponse>('/api/xlsx/apply', params);
    },

    async download(filename: string): Promise<Blob> {
        return getBlob(`/api/xlsx/download/${encodeURIComponent(filename)}`);
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
