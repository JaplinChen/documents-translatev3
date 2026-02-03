import { API_BASE_URL, handleResponse } from './core';
import type { TokenEstimateResponse, TokenRecordRequest, TokenStatsResponse } from '../api.types';

export const tokenStatsApi = {
    async get(): Promise<TokenStatsResponse> {
        const response = await fetch(`${API_BASE_URL}/api/token-stats`);
        return handleResponse<TokenStatsResponse>(response);
    },

    async record(
        request: TokenRecordRequest
    ): Promise<{ recorded: boolean; usage: { total_tokens: number; estimated_cost_usd: number } }> {
        const params = new URLSearchParams({
            provider: request.provider,
            model: request.model,
            prompt_tokens: String(request.prompt_tokens),
            completion_tokens: String(request.completion_tokens),
        });
        if (request.operation) {
            params.append('operation', request.operation);
        }
        const response = await fetch(
            `${API_BASE_URL}/api/token-stats/record?${params}`,
            { method: 'POST' }
        );
        return handleResponse<{
            recorded: boolean;
            usage: { total_tokens: number; estimated_cost_usd: number };
        }>(response);
    },

    async estimate(
        text: string,
        provider: string = 'openai'
    ): Promise<TokenEstimateResponse> {
        const params = new URLSearchParams({ text, provider });
        const response = await fetch(
            `${API_BASE_URL}/api/token-stats/estimate?${params}`,
            { method: 'POST' }
        );
        return handleResponse<TokenEstimateResponse>(response);
    },
};
