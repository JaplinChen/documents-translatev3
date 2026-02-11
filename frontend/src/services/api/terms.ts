import { deleteJson, getJson, getText, postForm, postJson, putJson } from './core';
import type { BatchDeleteRequest, TermBatchPayload, TermCategory, TermCategoryResponse, TermImportPreviewResponse, TermImportResponse, TermItem, TermListParams, TermListResponse, TermPayload } from '../api.types';

export const termsApi = {
    async list(params?: TermListParams): Promise<TermListResponse> {
        const searchParams = new URLSearchParams();
        if (params) {
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                    searchParams.append(key, String(value));
                }
            });
        }
        const query = searchParams.toString();
        return getJson<TermListResponse>(`/api/terms/${query ? `?${query}` : ''}`);
    },

    async create(payload: TermPayload): Promise<{ item: TermItem }> {
        return postJson<{ item: TermItem }>('/api/terms/', payload);
    },

    async update(id: number, payload: TermPayload): Promise<{ item: TermItem }> {
        return putJson<{ item: TermItem }>(`/api/terms/${id}`, payload);
    },

    async delete(id: number): Promise<{ status: string }> {
        return deleteJson<{ status: string }>(`/api/terms/${id}`);
    },

    async versions(id: number): Promise<{ versions: unknown[] }> {
        return getJson<{ versions: unknown[] }>(`/api/terms/${id}/versions`);
    },

    async batchUpdate(payload: TermBatchPayload): Promise<{ updated: number }> {
        return postJson<{ updated: number }>('/api/terms/batch/', payload);
    },

    async batchDelete(payload: BatchDeleteRequest): Promise<{ deleted: number }> {
        return deleteJson<{ deleted: number }>('/api/terms/batch/', payload);
    },

    async syncAll(): Promise<{ synced: number }> {
        return postJson<{ synced: number }>('/api/terms/sync-all/');
    },

    async getCategories(): Promise<TermCategoryResponse> {
        return getJson<TermCategoryResponse>('/api/terms/categories/');
    },

    async createCategory(
        name: string,
        sortOrder?: number
    ): Promise<{ item: TermCategory }> {
        return postJson<{ item: TermCategory }>(
            '/api/terms/categories/',
            { name, sort_order: sortOrder }
        );
    },

    async updateCategory(
        id: number,
        name: string,
        sortOrder?: number
    ): Promise<{ item: TermCategory }> {
        return putJson<{ item: TermCategory }>(
            `/api/terms/categories/${id}`,
            { name, sort_order: sortOrder }
        );
    },

    async deleteCategory(id: number): Promise<{ status: string }> {
        return deleteJson<{ status: string }>(`/api/terms/categories/${id}`);
    },

    async importPreview(
        file: File,
        mapping?: Record<string, string>
    ): Promise<TermImportPreviewResponse> {
        const payload: Record<string, unknown> = { file };
        if (mapping) {
            payload.mapping = mapping;
        }
        return postForm<TermImportPreviewResponse>(
            '/api/terms/import/preview/',
            payload
        );
    },

    async import(
        file: File,
        mapping?: Record<string, string>
    ): Promise<TermImportResponse> {
        const payload: Record<string, unknown> = { file };
        if (mapping) {
            payload.mapping = mapping;
        }
        return postForm<TermImportResponse>(
            '/api/terms/import/',
            payload
        );
    },

    async importErrors(): Promise<{ errors: unknown[] }> {
        return getJson<{ errors: unknown[] }>('/api/terms/import/errors/');
    },

    async export(): Promise<string> {
        return getText('/api/terms/export');
    },

    async upsert(payload: TermPayload & { category_name?: string }): Promise<{ item: TermItem }> {
        return postJson<{ item: TermItem }>('/api/terms/upsert/', payload);
    },
};
