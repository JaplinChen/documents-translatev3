import React from "react";
import { useTranslation } from "react-i18next";

export function useProcessorUtils() {
    const { t } = useTranslation();

    const readErrorDetail = async (response, fallback) => {
        const errorText = await response.text();
        if (!errorText) return fallback;

        if (errorText.includes("<html>")) {
            const titleMatch = errorText.match(/<title>(.*?)<\/title>/);
            if (titleMatch && titleMatch[1]) return `${t("status.server_error")}: ${titleMatch[1]}`;
            if (response.status === 502) return `${t("status.server_error")} (502 Bad Gateway)`;
            if (response.status === 504) return `${t("status.server_timeout")} (504 Gateway Timeout)`;
            return `${t("status.server_error")} (${response.status})`;
        }

        try {
            const errorData = JSON.parse(errorText);
            return errorData.detail || errorText;
        } catch {
            return errorText;
        }
    };

    const buildBlockUid = (block, fallbackIndex) =>
        block._uid ||
        block.client_id ||
        `${block.slide_index ?? "x"}-${block.shape_id ?? "x"}-${block.block_type ?? "x"}-${fallbackIndex}`;

    const resolveOutputMode = (block) => {
        if (block.output_mode) return block.output_mode;
        const translatedText = (block.translated_text || "").trim();
        return translatedText ? "translated" : "source";
    };

    return { readErrorDetail, buildBlockUid, resolveOutputMode };
}
