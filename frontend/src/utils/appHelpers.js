import { CJK_REGEX, VI_REGEX } from "./regex";

/**
 * Get display label for an option (supports i18n labelKey)
 */
export const getOptionLabel = (t, option) => {
    if (!option) return "";
    if (option.labelKey) return t(option.labelKey, option.label || option.name);
    return option.label || option.name || "";
};

/**
 * Extract lines from text based on language
 */
export const extractLanguageLines = (text, lang) => {
    const lines = (text || "").split("\n").map(l => l.trim()).filter(Boolean);
    if (!lang || lang === "auto") return lines;
    if (lang.startsWith("zh")) return lines.filter(l => CJK_REGEX.test(l));
    if (lang === "vi") return lines.filter(l => VI_REGEX.test(l));
    return lines;
};

/**
 * Normalize text by removing whitespace and extra spaces
 */
export function normalizeText(text) {
    return (text || "").replace(/\s+/g, "").trim();
}

/**
 * Check if error message indicates connection refused
 */
export function isConnectionRefused(message) {
    return /WinError 10061|ECONNREFUSED|Connection refused|Errno 111/i.test(message || "");
}

/**
 * Format hint message for model detection errors
 * @param {Function} t - Translation function
 */
export function formatModelDetectHint(t, message) {
    if (isConnectionRefused(message) || (message || "").includes("Ollama")) {
        return t("utils.model_detect_hint.ollama");
    }
    return t("utils.model_detect_hint.generic");
}

/**
 * Read error detail from API response
 */
export async function readErrorDetail(response, fallback) {
    const errorText = await response.text();
    if (!errorText) return fallback;
    try {
        const errorData = JSON.parse(errorText);
        return errorData.detail || errorText;
    } catch {
        return errorText;
    }
}

/**
 * Build unique ID for block
 */
export function buildBlockUid(block, fallbackIndex) {
    return block._uid || block.client_id ||
        `${block.slide_index ?? "x"}-${block.shape_id ?? "x"}-${block.block_type ?? "x"}-${fallbackIndex}`;
}

/**
 * Resolve output mode from block
 */
export function resolveOutputMode(block) {
    if (block.output_mode) return block.output_mode;
    const translatedText = (block.translated_text || "").trim();
    return translatedText ? "translated" : "source";
}

/**
 * Infer fallback language based on primary language
 */
export function inferFallbackLanguage(primaryLang, targetLang) {
    if (primaryLang === targetLang) return "";
    if (primaryLang === "en") return "zh-TW";
    if (primaryLang === "vi") return "zh-TW";
    if (primaryLang.startsWith("zh")) return "";
    return "";
}
