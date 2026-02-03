import { API_BASE_URL, handleResponse } from './core';
import type { StyleSuggestRequest, StyleSuggestResponse } from '../api.types';

export const styleApi = {
    async suggest(request: StyleSuggestRequest): Promise<StyleSuggestResponse> {
        const response = await fetch(`${API_BASE_URL}/api/style/suggest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });
        return handleResponse<StyleSuggestResponse>(response);
    },
};
