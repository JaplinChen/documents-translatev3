/**
 * API base URL configuration
 */
export const API_BASE = (typeof import.meta.env.VITE_API_BASE === "string" && import.meta.env.VITE_API_BASE !== "")
    ? import.meta.env.VITE_API_BASE
    : "";

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
 * Language options for dropdowns (Unified with labelKey)
 */
export const LANGUAGE_OPTIONS = [
    { code: "auto", labelKey: "language.options.auto", label: "自動 (Auto)" },
    { code: "zh-TW", labelKey: "language.options.zh_tw", label: "繁體中文" },
    { code: "zh-CN", labelKey: "language.options.zh_cn", label: "简体中文" },
    { code: "en", labelKey: "language.options.en", label: "English" },
    { code: "vi", labelKey: "language.options.vi", label: "Tiếng Việt" },
    { code: "ja", labelKey: "language.options.ja", label: "日本語" },
    { code: "ko", labelKey: "language.options.ko", label: "한국어" },
    { code: "th", labelKey: "language.options.th", label: "ไทย" },
    { code: "id", labelKey: "language.options.id", label: "Bahasa Indonesia" },
    { code: "ms", labelKey: "language.options.ms", label: "Bahasa Melayu" },
    { code: "de", labelKey: "language.options.de", label: "Deutsch" },
    { code: "fr", labelKey: "language.options.fr", label: "Français" },
    { code: "es", labelKey: "language.options.es", label: "Español" },
    { code: "pt", labelKey: "language.options.pt", label: "Português" },
    { code: "ru", labelKey: "language.options.ru", label: "Русский" },
    { code: "ar", labelKey: "language.options.ar", label: "العربية" }
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

/**
 * Default Font Mapping (aligned with backend)
 */
export const DEFAULT_FONT_MAPPING = {
    "vi": ["Arial", "Segoe UI", "Calibri"],
    "th": ["Leelawadee UI", "Tahoma", "Arial"],
    "ar": ["Arial", "Segoe UI"],
    "he": ["Arial", "Segoe UI"],
    "ja": ["Meiryo", "Yu Gothic", "MS PGothic"],
    "ko": ["Malgun Gothic", "Gulim"],
    "en": ["Arial", "Calibri", "Segoe UI"],
};
