import { deleteJson, getJson, getText, postJson, postText, putJson } from './core';
import type { ConvertToGlossaryRequest, PreserveTerm, PreserveTermBatchRequest, PreserveTermBatchResponse, PreserveTermsResponse } from '../api.types';

export const preserveTermsApi = {
    async list(): Promise<PreserveTermsResponse> {
        return getJson<PreserveTermsResponse>('/api/preserve-terms/');
    },

    async create(term: PreserveTerm): Promise<{ term: PreserveTerm }> {
        return postJson<{ term: PreserveTerm }>('/api/preserve-terms/', term);
    },

    async batch(
        request: PreserveTermBatchRequest
    ): Promise<PreserveTermBatchResponse> {
        return postJson<PreserveTermBatchResponse>(
            '/api/preserve-terms/batch/',
            request
        );
    },

    async update(id: string, term: PreserveTerm): Promise<{ term: PreserveTerm }> {
        return putJson<{ term: PreserveTerm }>(`/api/preserve-terms/${id}`, term);
    },

    async delete(id: string): Promise<{ deleted: boolean }> {
        return deleteJson<{ deleted: boolean }>(`/api/preserve-terms/${id}`);
    },

    async deleteAll(): Promise<{ message: string }> {
        return deleteJson<{ message: string }>('/api/preserve-terms/');
    },

    async export(): Promise<string> {
        return getText('/api/preserve-terms/export/');
    },

    async import(
        csvData: string
    ): Promise<{ imported: number; skipped: number; total: number }> {
        return postText<{
            imported: number;
            skipped: number;
            total: number;
        }>('/api/preserve-terms/import/', csvData);
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

        return postJson<{ term: PreserveTerm; message: string }>(
            `/api/preserve-terms/convert-from-glossary?${params.toString()}`
        );
    },

    async convertToGlossary(
        request: ConvertToGlossaryRequest
    ): Promise<{ status: string; source_lang: string; target_lang: string }> {
        return postJson<{
            status: string;
            source_lang: string;
            target_lang: string;
        }>('/api/preserve-terms/convert-to-glossary/', request);
    },
};
