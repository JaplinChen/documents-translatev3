import { API_BASE_URL, ApiClientError, handleResponse } from './core';
import type { ExportFormatsResponse, ExportRequest, SuggestTermsResponse, TextBlock } from '../api.types';

export const exportApi = {
    async formats(): Promise<ExportFormatsResponse> {
        const response = await fetch(`${API_BASE_URL}/api/export-formats`);
        return handleResponse<ExportFormatsResponse>(response);
    },

    async toDocx(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/docx`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    async toXlsx(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/xlsx`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    async toTxt(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/txt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    async toMd(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/md`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    async toPdf(request: ExportRequest): Promise<Blob> {
        const response = await fetch(`${API_BASE_URL}/api/export/pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.blob();
    },

    async suggestTerms(blocks: TextBlock[]): Promise<SuggestTermsResponse> {
        const response = await fetch(`${API_BASE_URL}/api/suggest-terms`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ blocks }),
        });
        return handleResponse<SuggestTermsResponse>(response);
    },
};
