/**
 * API base URL configuration
 */
export const API_BASE = (typeof import.meta.env.VITE_API_BASE === "string" && import.meta.env.VITE_API_BASE !== "")
    ? import.meta.env.VITE_API_BASE
    : (import.meta.env.VITE_API_BASE === "" ? "" : "http://localhost:5002");

/**
 * Default Ollama base URL
 */
export const DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434";

/**
 * Common Ollama Base URLs
 */
export const OLLAMA_BASE_URLS = [
    "http://127.0.0.1:11434",
    "http://localhost:11434",
    "http://host.docker.internal:11434",
    "http://192.168.90.168:11434"
];

/**
 * Default LLM provider
 */
export const DEFAULT_LLM_PROVIDER = "ollama";

/**
 * Language options for dropdowns
 */
export const LANGUAGE_OPTIONS = [
    { code: "auto", label: "自動" },
    { code: "zh-TW", label: "繁體中文" },
    { code: "zh-CN", label: "简体中文" },
    { code: "en", label: "English" },
    { code: "vi", label: "Tiếng Việt" },
    { code: "ja", label: "日本語" },
    { code: "ko", label: "한국어" },
    { code: "th", label: "ไทย" },
    { code: "id", label: "Bahasa Indonesia" },
    { code: "ms", label: "Bahasa Melayu" },
    { code: "de", label: "Deutsch" },
    { code: "fr", label: "Français" },
    { code: "es", label: "Español" },
    { code: "pt", label: "Português" },
    { code: "ru", label: "Русский" },
    { code: "ar", label: "العربية" }
];

/**
 * Output mode options
 */
export const OUTPUT_MODE_OPTIONS = [
    { value: "bilingual", label: "雙語輸出" },
    { value: "target", label: "僅譯文" },
    { value: "source", label: "僅原文" }
];

/**
 * Frame mode options
 */
export const FRAME_MODE_OPTIONS = [
    { value: "same", label: "同框" },
    { value: "separate", label: "分框" }
];

/**
 * Application Processing Status Enum
 * Used for deterministic UI state management independent of display language
 */
export const APP_STATUS = {
    IDLE: "idle",
    UPLOADING: "uploading",
    EXTRACTING: "extracting",
    TRANSLATING: "translating",
    EXPORTING: "exporting",
    TRANSLATION_COMPLETED: "translation_completed",
    EXPORT_COMPLETED: "export_completed",
    ERROR: "error"
};
