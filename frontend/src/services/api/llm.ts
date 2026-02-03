import { API_BASE_URL, createFormData, handleResponse } from './core';
import type { LlmModelsParams, LlmModelsResponse } from '../api.types';

export const llmApi = {
    async models(params: LlmModelsParams): Promise<LlmModelsResponse> {
        const formData = createFormData(params);
        const response = await fetch(`${API_BASE_URL}/api/llm/models`, {
            method: 'POST',
            body: formData,
        });
        return handleResponse<LlmModelsResponse>(response);
    },
};
