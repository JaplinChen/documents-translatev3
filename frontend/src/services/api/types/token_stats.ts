export interface TokenUsage {
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  operation?: string;
  timestamp?: string;
}

export interface SessionStats {
  total_requests: number;
  total_tokens: number;
  total_cost_usd: number;
  by_provider: Record<string, TokenUsage>;
}

export interface TokenStatsResponse {
  session: SessionStats;
  all_time: SessionStats;
}

export interface TokenRecordRequest {
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  operation?: string;
}

export interface TokenEstimateResponse {
  estimated_tokens: number;
  text_length: number;
}
