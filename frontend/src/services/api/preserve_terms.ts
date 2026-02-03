import { API_BASE_URL, handleResponse } from './core';
import type { ConvertToGlossaryRequest, PreserveTerm, PreserveTermBatchRequest, PreserveTermBatchResponse, PreserveTermsResponse } from '../api.types';

export const preserveTermsApi = {
    async list(): Promise<PreserveTermsResponse> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms`);
        return handleResponse<PreserveTermsResponse>(response);
    },

    async create(term: PreserveTerm): Promise<{ term: PreserveTerm }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(term),
        });
        return handleResponse<{ term: PreserveTerm }>(response);
    },

    async batch(
        request: PreserveTermBatchRequest
    ): Promise<PreserveTermBatchResponse> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        return handleResponse<PreserveTermBatchResponse>(response);
    },

    async update(id: string, term: PreserveTerm): Promise<{ term: PreserveTerm }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(term),
        });
        return handleResponse<{ term: PreserveTerm }>(response);
    },

    async delete(id: string): Promise<{ deleted: boolean }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/${id}`, {
            method: 'DELETE',
        });
        return handleResponse<{ deleted: boolean }>(response);
    },

    async deleteAll(): Promise<{ message: string }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms`, {
            method: 'DELETE',
        });
        return handleResponse<{ message: string }>(response);
    },

    async export(): Promise<string> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/export`);
        if (!response.ok) {
            throw new Error('Export failed');
        }
        return response.text();
    },

    async import(
        csvData: string
    ): Promise<{ imported: number; skipped: number; total: number }> {
        const response = await fetch(`${API_BASE_URL}/api/preserve-terms/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'text/plain' },
            body: csvData,
        });
        return handleResponse<{
            imported: number;
            skipped: number;
            total: number;
        }>(response);
    },

    async convertFromGlossary(
        sourceText: string,
        category?: string,
        caseSensitive?: boolean
    ): Promise<{ term: PreserveTerm; message: string }> {
        const params = new URLSearchParams({ source_text: sourceText });
        if (category) params.append('category', category);
        if (caseSensitive !== undefined) {
            params.append('case_sensitive', String(caseSensitive));
        }

        const response = await fetch(
            `${API_BASE_URL}/api/preserve-terms/convert-from-glossary?${params}`,
            { method: 'POST' }
        );
        return handleResponse<{ term: PreserveTerm; message: string }>(response);
    },

    async convertToGlossary(
        request: ConvertToGlossaryRequest
    ): Promise<{ status: string; source_lang: string; target_lang: string }> {
        const response = await fetch(
            `${API_BASE_URL}/api/preserve-terms/convert-to-glossary`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
            }
        );
        return handleResponse<{
            status: string;
            source_lang: string;
            target_lang: string;
        }>(response);
    },
};
