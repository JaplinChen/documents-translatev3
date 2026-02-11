import { getJson, postJson } from './core';
import type { OcrSettings } from '../api.types';

export const ocrApi = {
    async getSettings(): Promise<OcrSettings> {
        return getJson<OcrSettings>('/api/ocr/settings');
    },

    async updateSettings(settings: OcrSettings): Promise<OcrSettings> {
        return postJson<OcrSettings>('/api/ocr/settings', settings);
    },
};
