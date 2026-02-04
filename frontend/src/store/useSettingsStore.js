import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { API_BASE, DEFAULT_FONT_MAPPING } from '../constants';

const DEFAULT_PROVIDERS = {
    chatgpt: { apiKey: "", baseUrl: "https://api.openai.com/v1", model: "", fastMode: false },
    gemini: { apiKey: "", baseUrl: "https://generativelanguage.googleapis.com/v1beta", model: "", fastMode: false },
    ollama: { apiKey: "", baseUrl: "http://host.docker.internal:11434", model: "", fastMode: false }
};

export const useSettingsStore = create(
    persist(
        (set, get) => ({
            // --- LLM Settings ---
            llmProvider: 'ollama',
            providers: DEFAULT_PROVIDERS,

            // Transient (Non-persisted usually, but simplified here)
            llmModels: [],
            llmStatus: '',
            useTm: false,

            // Actions
            setLlmProvider: (provider) => set({ llmProvider: provider }),
            setUseTm: (value) => set({ useTm: value }),

            updateProviderSettings: (provider, settings) => set(state => ({
                providers: {
                    ...state.providers,
                    [provider]: { ...state.providers[provider], ...settings }
                }
            })),

            setLlmModels: (models) => set({ llmModels: models }),
            setLlmStatus: (status) => set({ llmStatus: status }),

            detectModels: async () => {
                const { llmProvider, providers } = get();
                const settings = providers[llmProvider];

                // Validation
                if (llmProvider !== 'ollama' && !settings.apiKey) {
                    set({ llmStatus: { key: "settings.status.api_key_missing" } });
                    return;
                }

                set({ llmStatus: { key: "settings.status.models_detecting" } });

                try {
                    const formData = new FormData();
                    formData.append("provider", llmProvider);
                    if (settings.apiKey) formData.append("api_key", settings.apiKey);

                    // Use default URL logic if empty
                    let baseUrl = settings.baseUrl;
                    if (!baseUrl) {
                        if (llmProvider === 'gemini') baseUrl = DEFAULT_PROVIDERS.gemini.baseUrl;
                        else if (llmProvider === 'ollama') baseUrl = DEFAULT_PROVIDERS.ollama.baseUrl;
                        else baseUrl = DEFAULT_PROVIDERS.chatgpt.baseUrl;
                    }
                    formData.append("base_url", baseUrl);

                    const response = await fetch(`${API_BASE}/api/llm/models`, {
                        method: "POST",
                        body: formData
                    });

                    if (!response.ok) throw new Error(await response.text() || "common.unknown_error");

                    const data = await response.json();
                    const models = data.models || [];

                    set({ llmModels: models });

                    // Auto-select model if valid
                    const currentModel = settings.model;
                    if (models.length) {
                        const validModel = models.includes(currentModel) ? currentModel : models[0];
                        get().updateProviderSettings(llmProvider, { model: validModel });
                    }

                    set({
                        llmStatus: models.length
                            ? { key: "settings.status.models_detected", params: { count: models.length } }
                            : { key: "settings.status.models_not_found" }
                    });
                } catch (error) {
                    set({ llmStatus: { key: "settings.status.models_detect_failed" } });
                    console.error("Detect Models Error:", error);
                }
            },

            // --- Font Settings ---
            fontMapping: DEFAULT_FONT_MAPPING,
            setFontMapping: (mapping) => {
                // Support functional update or value
                set(state => ({
                    fontMapping: typeof mapping === 'function' ? mapping(state.fontMapping) : mapping
                }));
            },

            // --- Correction Settings ---
            correction: {
                fillColor: "#FFF16A",
                textColor: "#D90000",
                lineColor: "#7B2CB9",
                lineDash: "dash",
                similarityThreshold: 0.75
            },
            setCorrection: (key, value) => set(state => ({
                correction: { ...state.correction, [key]: value }
            })),

            // --- AI Settings ---
            ai: {
                tone: "professional",
                useVision: true,
                useSmartLayout: true
            },
            setAiOption: (key, value) => set(state => ({
                ai: { ...state.ai, [key]: value }
            })),

            // --- OCR Settings ---
            ocr: {
                dpi: 300,
                lang: "chi_tra+vie+eng",
                confMin: 15,
                psm: 6,
                engine: "tesseract",
                popplerPath: ""
            },
            ocrStatus: "",
            setOcrOption: (key, value) => set(state => ({
                ocr: { ...state.ocr, [key]: value }
            })),
            setOcrStatus: (status) => set({ ocrStatus: status }),
            loadOcrSettings: async () => {
                try {
                    const response = await fetch(`${API_BASE}/api/ocr/settings`);
                    if (!response.ok) throw new Error("settings.status.ocr_load_failed");
                    const data = await response.json();
                    set({
                        ocr: {
                            dpi: data.dpi ?? 300,
                            lang: data.lang ?? "chi_tra+vie+eng",
                            confMin: data.conf_min ?? 15,
                            psm: data.psm ?? 6,
                            engine: data.engine ?? "tesseract",
                            popplerPath: data.poppler_path ?? ""
                        },
                        ocrStatus: ""
                    });
                } catch (error) {
                    set({ ocrStatus: { key: error.message || "settings.status.ocr_load_failed" } });
                }
            },
            saveOcrSettings: async () => {
                const { ocr } = get();
                try {
                    const response = await fetch(`${API_BASE}/api/ocr/settings`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            dpi: Number(ocr.dpi),
                            lang: ocr.lang,
                            conf_min: Number(ocr.confMin),
                            psm: Number(ocr.psm),
                            engine: ocr.engine,
                            poppler_path: ocr.popplerPath
                        })
                    });
                    if (!response.ok) throw new Error("settings.status.ocr_save_failed");
                    const data = await response.json();
                    set({
                        ocr: {
                            dpi: data.dpi ?? ocr.dpi,
                            lang: data.lang ?? ocr.lang,
                            confMin: data.conf_min ?? ocr.confMin,
                            psm: data.psm ?? ocr.psm,
                            engine: data.engine ?? ocr.engine,
                            popplerPath: data.poppler_path ?? ocr.popplerPath
                        },
                        ocrStatus: { key: "settings.status.saved" }
                    });
                } catch (error) {
                    set({ ocrStatus: { key: error.message || "settings.status.ocr_save_failed" } });
                }
            }
        }),
        {
            name: 'app-settings-storage', // Key in localStorage
            storage: createJSONStorage(() => localStorage),
            partialize: (state) => ({
                llmProvider: state.llmProvider,
                providers: state.providers,
                fontMapping: state.fontMapping,
                correction: state.correction,
                ai: state.ai,
                useTm: state.useTm
            }), // Only persist these fields, skip models/status

        }
    )
);
