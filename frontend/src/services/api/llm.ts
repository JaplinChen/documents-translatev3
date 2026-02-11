import { postForm } from './core';
import type { LlmModelsParams, LlmModelsResponse } from '../api.types';

export const llmApi = {
    async models(params: LlmModelsParams): Promise<LlmModelsResponse> {
        return postForm<LlmModelsResponse>('/api/llm/models', params);
    },
};
