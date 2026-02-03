import { API_BASE_URL, handleResponse } from './core';
import type { PromptContent } from '../api.types';

export const promptsApi = {
    async list(): Promise<string[]> {
        const response = await fetch(`${API_BASE_URL}/api/prompts`);
        return handleResponse<string[]>(response);
    },

    async get(name: string): Promise<PromptContent> {
        const response = await fetch(
            `${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}`
        );
        return handleResponse<PromptContent>(response);
    },

    async save(name: string, content: string): Promise<{ status: string }> {
        const response = await fetch(
            `${API_BASE_URL}/api/prompts/${encodeURIComponent(name)}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }),
            }
        );
        return handleResponse<{ status: string }>(response);
    },
};
