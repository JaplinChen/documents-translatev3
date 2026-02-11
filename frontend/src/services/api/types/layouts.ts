export interface LayoutParamSchemaField {
  type?: 'string' | 'number' | 'integer' | 'boolean';
  title?: string;
  description?: string;
  default?: unknown;
  enum?: Array<string | number>;
  minimum?: number;
  maximum?: number;
  step?: number;
}

export interface LayoutParamSchema {
  type?: 'object';
  properties?: Record<string, LayoutParamSchemaField>;
  additionalProperties?: boolean;
}

export interface LayoutDefinition {
  id: string;
  name: string;
  file_type: 'pptx' | 'xlsx' | 'docx' | 'pdf';
  modes: string[];
  apply_value: string;
  enabled: boolean;
  is_custom: boolean;
  params_schema?: LayoutParamSchema;
}

export interface LayoutListResponse {
  layouts: LayoutDefinition[];
}

export interface LayoutUpsertRequest {
  id: string;
  name: string;
  file_type: 'pptx' | 'xlsx' | 'docx' | 'pdf';
  modes?: string[];
  apply_value: string;
  enabled?: boolean;
  params_schema?: LayoutParamSchema;
}

export interface LayoutUpsertResponse {
  status: string;
  layout: LayoutDefinition;
}

export interface LayoutPatchRequest {
  name?: string;
  enabled?: boolean;
  apply_value?: string;
  modes?: string[];
  params_schema?: LayoutParamSchema;
}

export interface LayoutExportResponse {
  layouts: LayoutDefinition[];
}

export interface LayoutImportRequest {
  layouts: LayoutDefinition[];
  mode?: 'merge' | 'replace';
  file_type?: 'pptx' | 'xlsx' | 'docx' | 'pdf';
  decisions?: Record<string, 'overwrite' | 'keep_existing'>;
}

export interface LayoutImportResponse {
  status: string;
  received: number;
  upserted: number;
  created: number;
  skipped_by_decision?: number;
}

export interface LayoutImportPreviewResponse {
  status: string;
  received: number;
  valid: number;
  skipped: number;
  created: number;
  updated: number;
  unchanged: number;
  replace_scope_existing: number;
  details: Array<{
    file_type: string;
    id: string;
    key?: string;
    action: 'create' | 'update' | 'unchanged';
    name: string;
    changed_fields?: string[];
  }>;
}
