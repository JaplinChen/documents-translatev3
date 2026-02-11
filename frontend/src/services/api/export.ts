import { API_BASE_URL, ApiClientError, getJson, postJson, postJsonBlob } from './core';
import type { ExportFormatsResponse, ExportRequest, SuggestTermsResponse, TextBlock } from '../api.types';

export const exportApi = {
    async formats(): Promise<ExportFormatsResponse> {
        return getJson<ExportFormatsResponse>('/api/export-formats');
    },

    async exportByFormat(formatId: string, request: ExportRequest): Promise<Blob> {
        return postJsonBlob(`/api/export/${formatId}`, request);
    },

    async exportByFormatWithHeaders(
        formatId: string,
        request: ExportRequest
    ): Promise<Response> {
        const response = await fetch(`${API_BASE_URL}/api/export/${formatId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response;
    },

    async toDocx(request: ExportRequest): Promise<Blob> {
        return postJsonBlob('/api/export/docx', request);
    },

    async toXlsx(request: ExportRequest): Promise<Blob> {
        return postJsonBlob('/api/export/xlsx', request);
    },

    async toTxt(request: ExportRequest): Promise<Blob> {
        return postJsonBlob('/api/export/txt', request);
    },

    async toMd(request: ExportRequest): Promise<Blob> {
        return postJsonBlob('/api/export/md', request);
    },

    async toPdf(request: ExportRequest): Promise<Blob> {
        return postJsonBlob('/api/export/pdf', request);
    },

    async suggestTerms(blocks: TextBlock[]): Promise<SuggestTermsResponse> {
        return postJson<SuggestTermsResponse>('/api/suggest-terms', { blocks });
    },
};
