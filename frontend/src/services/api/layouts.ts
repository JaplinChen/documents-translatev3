import { deleteJson, getJson, patchJson, postJson } from './core';
import type {
    LayoutExportResponse,
    LayoutImportRequest,
    LayoutImportPreviewResponse,
    LayoutImportResponse,
    LayoutListResponse,
    LayoutPatchRequest,
    LayoutUpsertRequest,
    LayoutUpsertResponse,
} from '../api.types';

export const layoutsApi = {
    async list(fileType?: string, mode?: string, includeDisabled = false): Promise<LayoutListResponse> {
        const query = new URLSearchParams();
        if (fileType) query.set('file_type', fileType);
        if (mode) query.set('mode', mode);
        if (includeDisabled) query.set('include_disabled', 'true');
        const suffix = query.toString() ? `?${query.toString()}` : '';
        return getJson<LayoutListResponse>(`/api/layouts${suffix}`);
    },

    async upsertCustom(payload: LayoutUpsertRequest): Promise<LayoutUpsertResponse> {
        return postJson<LayoutUpsertResponse>('/api/layouts/custom', payload);
    },

    async patchCustom(fileType: string, layoutId: string, payload: LayoutPatchRequest): Promise<LayoutUpsertResponse> {
        return patchJson<LayoutUpsertResponse>(
            `/api/layouts/custom/${encodeURIComponent(fileType)}/${encodeURIComponent(layoutId)}`,
            payload
        );
    },

    async removeCustom(fileType: string, layoutId: string): Promise<{ status: string }> {
        return deleteJson<{ status: string }>(
            `/api/layouts/custom/${encodeURIComponent(fileType)}/${encodeURIComponent(layoutId)}`
        );
    },

    async exportCustom(fileType?: string): Promise<LayoutExportResponse> {
        const query = new URLSearchParams();
        if (fileType) query.set('file_type', fileType);
        const suffix = query.toString() ? `?${query.toString()}` : '';
        return getJson<LayoutExportResponse>(`/api/layouts/custom/export${suffix}`);
    },

    async importCustom(payload: LayoutImportRequest): Promise<LayoutImportResponse> {
        return postJson<LayoutImportResponse>('/api/layouts/custom/import', payload);
    },

    async previewImportCustom(payload: LayoutImportRequest): Promise<LayoutImportPreviewResponse> {
        return postJson<LayoutImportPreviewResponse>('/api/layouts/custom/import-preview', payload);
    },
};
