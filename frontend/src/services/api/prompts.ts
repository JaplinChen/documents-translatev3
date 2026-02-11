import { getJson, postJson } from './core';
import type { PromptContent } from '../api.types';

export const promptsApi = {
    async list(): Promise<string[]> {
        return getJson<string[]>('/api/prompts');
    },

    async get(name: string): Promise<PromptContent> {
        return getJson<PromptContent>(`/api/prompts/${encodeURIComponent(name)}`);
    },

    async save(name: string, content: string): Promise<{ status: string }> {
        return postJson<{ status: string }>(
            `/api/prompts/${encodeURIComponent(name)}`,
            { content }
        );
    },
};
