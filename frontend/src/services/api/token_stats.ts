import { getJson, postJson } from './core';
import type { TokenEstimateResponse, TokenRecordRequest, TokenStatsResponse } from '../api.types';

export const tokenStatsApi = {
    async get(): Promise<TokenStatsResponse> {
        return getJson<TokenStatsResponse>('/api/token-stats');
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
        return postJson<{
            recorded: boolean;
            usage: { total_tokens: number; estimated_cost_usd: number };
        }>(`/api/token-stats/record?${params.toString()}`);
    },

    async estimate(
        text: string,
        provider: string = 'openai'
    ): Promise<TokenEstimateResponse> {
        const params = new URLSearchParams({ text, provider });
        return postJson<TokenEstimateResponse>(
            `/api/token-stats/estimate?${params.toString()}`
        );
    },
};
