import { postJson } from './core';
import type { StyleSuggestRequest, StyleSuggestResponse } from '../api.types';

export const styleApi = {
    async suggest(request: StyleSuggestRequest): Promise<StyleSuggestResponse> {
        return postJson<StyleSuggestResponse>('/api/style/suggest', request);
    },
};
