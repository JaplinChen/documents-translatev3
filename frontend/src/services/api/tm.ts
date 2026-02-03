import { API_BASE_URL, ApiClientError, handleResponse } from './core';
import type {
    GlossaryEntry,
    GlossaryResponse,
    MemoryEntry,
    MemoryResponse,
    TmCategory,
    TmCategoryResponse,
} from '../api.types';

export const tmApi = {
    async seed(): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/seed`, {
            method: 'POST',
        });
        return handleResponse<{ status: string }>(response);
    },

    async getGlossary(limit: number = 200): Promise<GlossaryResponse> {
        const response = await fetch(
            `${API_BASE_URL}/api/tm/glossary?limit=${limit}`
        );
        return handleResponse<GlossaryResponse>(response);
    },

    async upsertGlossary(entry: GlossaryEntry): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry),
        });
        return handleResponse<{ status: string }>(response);
    },

    async batchUpsertGlossary(
        entries: GlossaryEntry[]
    ): Promise<{ status: string; count: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entries),
        });
        return handleResponse<{ status: string; count: number }>(response);
    },

    async deleteGlossary(id: number): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id }),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    async batchDeleteGlossary(ids: number[]): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/batch`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids }),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    async clearGlossary(): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/clear`, {
            method: 'DELETE',
        });
        return handleResponse<{ deleted: number }>(response);
    },

    async importGlossary(
        file: File
    ): Promise<{ status: string; count: number }> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/import`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<{ status: string; count: number }>(response);
    },

    async exportGlossary(): Promise<string> {
        const response = await fetch(`${API_BASE_URL}/api/tm/glossary/export`);
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.text();
    },

    async getMemory(limit: number = 200): Promise<MemoryResponse> {
        const response = await fetch(
            `${API_BASE_URL}/api/tm/memory?limit=${limit}`
        );
        return handleResponse<MemoryResponse>(response);
    },

    async upsertMemory(entry: MemoryEntry): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry),
        });
        return handleResponse<{ status: string }>(response);
    },

    async deleteMemory(id: number): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id }),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    async batchDeleteMemory(ids: number[]): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory/batch`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids }),
        });
        return handleResponse<{ deleted: number }>(response);
    },

    async clearMemory(): Promise<{ deleted: number }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory/clear`, {
            method: 'DELETE',
        });
        return handleResponse<{ deleted: number }>(response);
    },

    async importMemory(file: File): Promise<{ status: string; count: number }> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/tm/memory/import`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<{ status: string; count: number }>(response);
    },

    async exportMemory(): Promise<string> {
        const response = await fetch(`${API_BASE_URL}/api/tm/memory/export`);
        if (!response.ok) {
            throw new ApiClientError('Export failed', response.status);
        }
        return response.text();
    },

    async getCategories(): Promise<TmCategoryResponse> {
        const response = await fetch(`${API_BASE_URL}/api/tm/categories`);
        return handleResponse<TmCategoryResponse>(response);
    },

    async createCategory(
        name: string,
        sortOrder?: number
    ): Promise<{ item: TmCategory }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/categories`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, sort_order: sortOrder ?? 0 }),
        });
        return handleResponse<{ item: TmCategory }>(response);
    },

    async updateCategory(
        id: number,
        name: string,
        sortOrder?: number
    ): Promise<{ item: TmCategory }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/categories/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, sort_order: sortOrder ?? 0 }),
        });
        return handleResponse<{ item: TmCategory }>(response);
    },

    async deleteCategory(id: number): Promise<{ status: string }> {
        const response = await fetch(`${API_BASE_URL}/api/tm/categories/${id}`, {
            method: 'DELETE',
        });
        return handleResponse<{ status: string }>(response);
    },
};
