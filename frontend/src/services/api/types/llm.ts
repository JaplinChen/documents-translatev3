export interface LlmModel {
  id: string;
  name?: string;
  description?: string;
}

export interface LlmModelsParams {
  provider: string;
  api_key?: string;
  base_url?: string;
}

export interface LlmModelsResponse {
  models: LlmModel[];
}
