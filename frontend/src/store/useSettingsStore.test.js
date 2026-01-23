/**
 * Unit tests for useSettingsStore
 * Tests settings management: LLM, fonts, correction, AI options
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSettingsStore } from '../store/useSettingsStore';

// Mock fetch for API calls
global.fetch = vi.fn();

describe('useSettingsStore', () => {
    beforeEach(() => {
        // Reset store state before each test (simplified reset)
        useSettingsStore.setState({
            llmProvider: 'ollama',
            providers: {
                chatgpt: { apiKey: "", baseUrl: "https://api.openai.com/v1", model: "", fastMode: false },
                gemini: { apiKey: "", baseUrl: "https://generativelanguage.googleapis.com/v1beta", model: "", fastMode: false },
                ollama: { apiKey: "", baseUrl: "http://host.docker.internal:11434", model: "", fastMode: false }
            },
            llmModels: [],
            llmStatus: '',
            useTm: false,
            fontMapping: {},
            correction: {
                fillColor: "#FFF16A",
                textColor: "#D90000",
                borderColor: "#7B2CB9",
                borderStyle: "dash"
            },
            ai: {
                tone: "professional",
                useVision: true,
                useSmartLayout: true
            },
            similarityThreshold: 0.85
        });
        vi.resetAllMocks();
    });

    describe('LLM Provider Settings', () => {
        it('should set LLM provider', () => {
            useSettingsStore.getState().setLlmProvider('chatgpt');
            expect(useSettingsStore.getState().llmProvider).toBe('chatgpt');
        });

        it('should update provider settings', () => {
            useSettingsStore.getState().updateProviderSettings('chatgpt', {
                apiKey: 'test-key',
                model: 'gpt-4'
            });

            const settings = useSettingsStore.getState().providers.chatgpt;
            expect(settings.apiKey).toBe('test-key');
            expect(settings.model).toBe('gpt-4');
        });

        it('should preserve existing provider settings when updating', () => {
            useSettingsStore.getState().updateProviderSettings('chatgpt', { apiKey: 'key1' });
            useSettingsStore.getState().updateProviderSettings('chatgpt', { model: 'model1' });

            const settings = useSettingsStore.getState().providers.chatgpt;
            expect(settings.apiKey).toBe('key1');
            expect(settings.model).toBe('model1');
        });
    });

    describe('LLM Status Management', () => {
        it('should set LLM models', () => {
            const models = ['model-a', 'model-b', 'model-c'];
            useSettingsStore.getState().setLlmModels(models);
            expect(useSettingsStore.getState().llmModels).toEqual(models);
        });

        it('should set LLM status', () => {
            useSettingsStore.getState().setLlmStatus('模型偵測中...');
            expect(useSettingsStore.getState().llmStatus).toBe('模型偵測中...');
        });
    });

    describe('Font Mapping', () => {
        it('should set font mapping directly', () => {
            const mapping = { 'Arial': 'Noto Sans TC' };
            useSettingsStore.getState().setFontMapping(mapping);
            expect(useSettingsStore.getState().fontMapping).toEqual(mapping);
        });

        it('should support functional update for font mapping', () => {
            useSettingsStore.setState({ fontMapping: { 'Arial': 'Noto Sans TC' } });

            useSettingsStore.getState().setFontMapping((prev) => ({
                ...prev,
                'Times New Roman': 'Noto Serif TC'
            }));

            expect(useSettingsStore.getState().fontMapping).toEqual({
                'Arial': 'Noto Sans TC',
                'Times New Roman': 'Noto Serif TC'
            });
        });
    });

    describe('Correction Settings', () => {
        it('should set correction fill color', () => {
            useSettingsStore.getState().setCorrection('fillColor', '#FF0000');
            expect(useSettingsStore.getState().correction.fillColor).toBe('#FF0000');
        });

        it('should set correction text color', () => {
            useSettingsStore.getState().setCorrection('textColor', '#00FF00');
            expect(useSettingsStore.getState().correction.textColor).toBe('#00FF00');
        });

        it('should preserve other correction settings', () => {
            useSettingsStore.getState().setCorrection('fillColor', '#FF0000');

            // Other settings should remain unchanged
            expect(useSettingsStore.getState().correction.textColor).toBe('#D90000');
            expect(useSettingsStore.getState().correction.borderStyle).toBe('dash');
        });
    });

    describe('AI Settings', () => {
        it('should set AI tone', () => {
            useSettingsStore.getState().setAiOption('tone', 'casual');
            expect(useSettingsStore.getState().ai.tone).toBe('casual');
        });

        it('should toggle vision context', () => {
            useSettingsStore.getState().setAiOption('useVision', false);
            expect(useSettingsStore.getState().ai.useVision).toBe(false);
        });

        it('should toggle smart layout', () => {
            useSettingsStore.getState().setAiOption('useSmartLayout', false);
            expect(useSettingsStore.getState().ai.useSmartLayout).toBe(false);
        });
    });

    describe('useTm setting', () => {
        it('should initial as false', () => {
            expect(useSettingsStore.getState().useTm).toBe(false);
        });

        it('should update useTm status', () => {
            const { setUseTm } = useSettingsStore.getState();
            setUseTm(true);
            expect(useSettingsStore.getState().useTm).toBe(true);
            setUseTm(false);
            expect(useSettingsStore.getState().useTm).toBe(false);
        });
    });

    describe('detectModels', () => {

        it('should require API key for non-ollama providers', async () => {
            useSettingsStore.getState().setLlmProvider('chatgpt');

            await useSettingsStore.getState().detectModels();

            expect(useSettingsStore.getState().llmStatus).toBe('請先輸入 API Key');
        });

        it('should call API and set models on success', async () => {
            useSettingsStore.getState().setLlmProvider('ollama');

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ models: ['llama3', 'codellama'] })
            });

            await useSettingsStore.getState().detectModels();

            expect(global.fetch).toHaveBeenCalled();
            expect(useSettingsStore.getState().llmModels).toContain('llama3');
        });

        it('should set error status on API failure', async () => {
            useSettingsStore.getState().setLlmProvider('ollama');

            global.fetch.mockRejectedValueOnce(new Error('Network error'));

            await useSettingsStore.getState().detectModels();

            expect(useSettingsStore.getState().llmStatus).toBe('模型偵測失敗');
        });
    });
});
