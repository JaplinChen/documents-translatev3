import { deleteJson, getJson, getText, postFile, postJson, putJson } from './core';
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
        return postJson<{ status: string }>('/api/tm/seed/');
    },

    async getGlossary(limit: number = 200, offset: number = 0): Promise<GlossaryResponse> {
        const params = new URLSearchParams({ limit: String(limit) });
        if (offset) params.append('offset', String(offset));
        return getJson<GlossaryResponse>(`/api/tm/glossary?${params.toString()}`);
    },

    async upsertGlossary(entry: GlossaryEntry): Promise<{ status: string }> {
        return postJson<{ status: string }>('/api/tm/glossary/', entry);
    },

    async batchUpsertGlossary(
        entries: GlossaryEntry[]
    ): Promise<{ status: string; count: number }> {
        return postJson<{ status: string; count: number }>(
            '/api/tm/glossary/batch/',
            entries
        );
    },

    async deleteGlossary(id: number): Promise<{ deleted: number }> {
        return deleteJson<{ deleted: number }>('/api/tm/glossary/', { id });
    },

    async batchDeleteGlossary(ids: number[]): Promise<{ deleted: number }> {
        return deleteJson<{ deleted: number }>(
            '/api/tm/glossary/batch/',
            { ids }
        );
    },

    async clearGlossary(): Promise<{ deleted: number }> {
        return deleteJson<{ deleted: number }>('/api/tm/glossary/clear/');
    },

    async importGlossary(
        file: File
    ): Promise<{ status: string; count: number }> {
        return postFile<{ status: string; count: number }>(
            '/api/tm/glossary/import/',
            file
        );
    },

    async exportGlossary(): Promise<string> {
        return getText('/api/tm/glossary/export/');
    },

    async getMemory(limit: number = 200, offset: number = 0): Promise<MemoryResponse> {
        const params = new URLSearchParams({ limit: String(limit) });
        if (offset) params.append('offset', String(offset));
        return getJson<MemoryResponse>(`/api/tm/memory?${params.toString()}`);
    },

    async upsertMemory(entry: MemoryEntry): Promise<{ status: string }> {
        return postJson<{ status: string }>('/api/tm/memory/', entry);
    },

    async deleteMemory(id: number): Promise<{ deleted: number }> {
        return deleteJson<{ deleted: number }>('/api/tm/memory/', { id });
    },

    async batchDeleteMemory(ids: number[]): Promise<{ deleted: number }> {
        return deleteJson<{ deleted: number }>(
            '/api/tm/memory/batch/',
            { ids }
        );
    },

    async clearMemory(): Promise<{ deleted: number }> {
        return deleteJson<{ deleted: number }>('/api/tm/memory/clear/');
    },

    async importMemory(file: File): Promise<{ status: string; count: number }> {
        return postFile<{ status: string; count: number }>(
            '/api/tm/memory/import/',
            file
        );
    },

    async exportMemory(): Promise<string> {
        return getText('/api/tm/memory/export/');
    },

    async getCategories(): Promise<TmCategoryResponse> {
        return getJson<TmCategoryResponse>('/api/tm/categories/');
    },

    async createCategory(
        name: string,
        sortOrder?: number
    ): Promise<{ item: TmCategory }> {
        return postJson<{ item: TmCategory }>(
            '/api/tm/categories/',
            { name, sort_order: sortOrder ?? 0 }
        );
    },

    async updateCategory(
        id: number,
        name: string,
        sortOrder?: number
    ): Promise<{ item: TmCategory }> {
        return putJson<{ item: TmCategory }>(
            `/api/tm/categories/${id}`,
            { name, sort_order: sortOrder ?? 0 }
        );
    },

    async deleteCategory(id: number): Promise<{ status: string }> {
        return deleteJson<{ status: string }>(`/api/tm/categories/${id}`);
    },

    async feedback(payload: {
        source: string;
        target: string;
        source_lang: string;
        target_lang: string;
    }): Promise<{ status: string }> {
        return postJson<{ status: string }>('/api/tm/feedback/', payload);
    },

    async getLearningStats(params: {
        limit?: number;
        offset?: number;
        scope_type?: string;
        scope_id?: string;
        date_from?: string;
        date_to?: string;
        sort_by?: string;
        sort_dir?: string;
    }): Promise<{ items: unknown[]; total?: number; offset?: number }> {
        const search = new URLSearchParams();
        Object.entries(params || {}).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                search.set(key, String(value));
            }
        });
        const query = search.toString();
        return getJson<{ items: unknown[]; total?: number; offset?: number }>(
            `/api/tm/learning-stats${query ? `?${query}` : ''}`
        );
    },

    async getLearningEvents(params: {
        limit?: number;
        offset?: number;
        event_type?: string;
        entity_type?: string;
        scope_type?: string;
        scope_id?: string;
        source_lang?: string;
        target_lang?: string;
        q?: string;
        date_from?: string;
        date_to?: string;
        sort_by?: string;
        sort_dir?: string;
    }): Promise<{ items: unknown[]; total?: number; offset?: number }> {
        const search = new URLSearchParams();
        Object.entries(params || {}).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                search.set(key, String(value));
            }
        });
        const query = search.toString();
        return getJson<{ items: unknown[]; total?: number; offset?: number }>(
            `/api/tm/learning-events${query ? `?${query}` : ''}`
        );
    },
};
