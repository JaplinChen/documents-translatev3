import { API_BASE_URL, handleResponse } from './core';
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
        const response = await fetch(
            `${API_BASE_URL}/api/terms${query ? `?${query}` : ''}`
        );
        return handleResponse<TermListResponse>(response);
    },

    async create(payload: TermPayload): Promise<{ item: TermItem }> {
        const response = await fetch(`${API_BASE_URL}/api/terms`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return handleResponse<{ item: TermItem }>(response);
    },

    async update(id: number, payload: TermPayload): Promise<{ item: TermItem }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return handleResponse<{ item: TermItem }>(response);
    },

    async delete(id: number): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/${id}`, {
            method: 'DELETE',
        });
        return handleResponse<{ status: string }>(response);
    },

    async versions(id: number): Promise<{ versions: unknown[] }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/${id}/versions`);
        return handleResponse<{ versions: unknown[] }>(response);
    },

    async batchUpdate(payload: TermBatchPayload): Promise<{ updated: number }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return handleResponse<{ updated: number }>(response);
    },

    async batchDelete(payload: BatchDeleteRequest): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/batch`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    async syncAll(): Promise<{ synced: number }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/sync-all`, {
            method: 'POST',
        });
        return handleResponse<{ synced: number }>(response);
    },

    async getCategories(): Promise<TermCategoryResponse> {
        const response = await fetch(`${API_BASE_URL}/api/terms/categories`);
        return handleResponse<TermCategoryResponse>(response);
    },

    async createCategory(
        name: string,
        sortOrder?: number
    ): Promise<{ item: TermCategory }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/categories`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, sort_order: sortOrder }),
        });
        return handleResponse<{ item: TermCategory }>(response);
    },

    async updateCategory(
        id: number,
        name: string,
        sortOrder?: number
    ): Promise<{ item: TermCategory }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/categories/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, sort_order: sortOrder }),
        });
        return handleResponse<{ item: TermCategory }>(response);
    },

    async deleteCategory(id: number): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/categories/${id}`, {
            method: 'DELETE',
        });
        return handleResponse<{ status: string }>(response);
    },

    async importPreview(
        file: File,
        mapping?: Record<string, string>
    ): Promise<TermImportPreviewResponse> {
        const formData = new FormData();
        formData.append('file', file);
        if (mapping) {
            formData.append('mapping', JSON.stringify(mapping));
        }
        const response = await fetch(`${API_BASE_URL}/api/terms/import/preview`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<TermImportPreviewResponse>(response);
    },

    async import(
        file: File,
        mapping?: Record<string, string>
    ): Promise<TermImportResponse> {
        const formData = new FormData();
        formData.append('file', file);
        if (mapping) {
            formData.append('mapping', JSON.stringify(mapping));
        }
        const response = await fetch(`${API_BASE_URL}/api/terms/import`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<TermImportResponse>(response);
    },

    async importErrors(): Promise<{ errors: unknown[] }> {
        const response = await fetch(`${API_BASE_URL}/api/terms/import/errors`);
        return handleResponse<{ errors: unknown[] }>(response);
    },

    async export(): Promise<string> {
        const response = await fetch(`${API_BASE_URL}/api/terms/export`);
        if (!response.ok) {
            throw new Error('Export failed');
        }
        return response.text();
    },
};
