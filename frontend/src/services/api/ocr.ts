import { API_BASE_URL, handleResponse } from './core';
import type { OcrSettings } from '../api.types';

export const ocrApi = {
    async getSettings(): Promise<OcrSettings> {
        const response = await fetch(`${API_BASE_URL}/api/ocr/settings`);
        return handleResponse<OcrSettings>(response);
    },

    async updateSettings(settings: OcrSettings): Promise<OcrSettings> {
        const response = await fetch(`${API_BASE_URL}/api/ocr/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings),
        });
        return handleResponse<OcrSettings>(response);
    },
};
