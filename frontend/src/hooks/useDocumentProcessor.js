import { useState } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE, APP_STATUS } from "../constants";
import { useFileStore } from "../store/useFileStore";
import { useSettingsStore } from "../store/useSettingsStore";
import { useUIStore } from "../store/useUIStore";
import { readErrorDetail, buildBlockUid, resolveOutputMode, stripBilingualText } from "../utils/appHelpers";

export function useDocumentProcessor() {
    const { t } = useTranslation();
    const [progress, setProgress] = useState(0);

    const { file, blocks, setBlocks } = useFileStore();
    const { llmProvider, providers, correction, fontMapping, ai } = useSettingsStore();
    const currentProvider = providers[llmProvider] || {};
    const { apiKey: llmApiKey, baseUrl: llmBaseUrl, model: llmModel, fastMode: llmFastMode } = currentProvider;
    const {
        sourceLang, secondaryLang, targetLang, mode, bilingualLayout,
        setStatus, setAppStatus, setBusy, setSlideDimensions, setLastTranslationAt
    } = useUIStore();

    const useTm = useSettingsStore(s => s.useTm);
    const { fillColor, textColor, lineColor, lineDash } = correction;

    const getFileType = () => {
        if (!file) return null;
        const ext = file.name.split('.').pop().toLowerCase();
        const supported = ['pptx', 'docx', 'xlsx', 'pdf'];
        return supported.includes(ext) ? ext : null;
    };

    const handleExtract = async (refresh = false) => {
        if (!file) { setStatus(t("status.no_file")); return; }
        const fileType = getFileType();
        if (!fileType) { setStatus(t("status.format_error")); return; }

        setBusy(true); setStatus(t("status.extracting")); setAppStatus(APP_STATUS.EXTRACTING);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const response = await fetch(`${API_BASE}/api/${fileType}/extract?refresh=${refresh}`, { method: "POST", body: formData });
            if (!response.ok) throw new Error(await readErrorDetail(response, t("status.extract_failed")));
            const data = await response.json();
            const nextBlocks = (data.blocks || []).map((block, idx) => {
                const uid = buildBlockUid(block, idx);
                return {
                    ...block, _uid: uid, client_id: block.client_id || uid, selected: block.selected !== false,
                    output_mode: resolveOutputMode(block), isTranslating: false
                };
            });
            setBlocks(nextBlocks);
            setSlideDimensions({
                width: data.slide_width,
                height: data.slide_height,
                thumbnails: data.thumbnail_urls || []
            });
            setStatus({ key: "sidebar.extract.summary", params: { count: data.blocks?.length || 0 } });
            setAppStatus(APP_STATUS.IDLE);
            return data.language_summary;
        } catch (error) {
            setStatus(`${t("status.extract_failed")}：${error.message}`);
            setAppStatus(APP_STATUS.ERROR);
        } finally { setBusy(false); }
    };

    const handleTranslate = async (refresh = false) => {
        if (blocks.length === 0) { setStatus(t("status.no_blocks")); return; }
        if (llmProvider !== "ollama" && !llmApiKey) { setStatus(t("status.api_key_missing")); return; }

        const fileType = getFileType();
        setLastTranslationAt(Date.now());
        setBusy(true); setProgress(0); setStatus(t("sidebar.translate.preparing")); setAppStatus(APP_STATUS.TRANSLATING);

        // 取得待翻譯區塊：若不是 refresh 模式，則排除已有翻譯內容的區塊（支援續傳）
        const pendingBlocks = refresh ? blocks : blocks.filter(b => !b.translated_text);
        if (pendingBlocks.length === 0) {
            setStatus(t("sidebar.translate.completed"));
            setAppStatus(APP_STATUS.TRANSLATION_COMPLETED); setBusy(false);
            return;
        }

        setBlocks(prev => prev.map(b => pendingBlocks.some(p => p.client_id === b.client_id) ? { ...b, isTranslating: true } : b));

        let completedIds = [], retryCount = 0, maxRetries = 3;
        const BATCH_SIZE = 20;

        const finalizeTranslation = (finalBlocks = []) => {
            setBlocks(prev => prev.map((b) => {
                const match = finalBlocks.find(f => f.client_id === b.client_id || f._uid === b._uid);
                if (!match) return b;
                const hasT = Object.prototype.hasOwnProperty.call(match, "translated_text");
                const rawTranslated = hasT ? match.translated_text : b.translated_text;
                const cleanedTranslated = hasT
                    ? stripBilingualText(b.source_text, rawTranslated, targetLang)
                    : b.translated_text;
                return {
                    ...b,
                    translated_text: cleanedTranslated,
                    correction_temp: match.correction_temp ?? b.correction_temp,
                    temp_translated_text: match.temp_translated_text ?? b.temp_translated_text,
                    isTranslating: false,
                    updatedAt: (hasT && cleanedTranslated) ? new Date().toLocaleTimeString("zh-TW", { hour12: false }) : b.updatedAt
                };
            }));
        };

        const runTranslationBatch = async (batchBlocks) => {
            try {
                const payload = {
                    blocks: batchBlocks,
                    source_language: sourceLang || "auto",
                    secondary_language: secondaryLang || "auto",
                    target_language: targetLang,
                    mode: mode,
                    use_tm: !!useTm,
                    provider: llmProvider,
                    model: llmModel || null,
                    api_key: llmApiKey || null,
                    base_url: llmBaseUrl || null,
                    ollama_fast_mode: !!llmFastMode,
                    refresh: !!refresh,
                    vision_context: !!ai.useVision,
                    smart_layout: !!ai.useSmartLayout,
                    similarity_threshold: parseFloat(correction.similarityThreshold?.toString() || "0.75"),
                    completed_ids: null // 批次請求不需傳入已完成 ID，因為 payload 本身就是分段的
                };

                const response = await fetch(`${API_BASE}/api/${fileType}/translate-stream`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (!response.ok) throw new Error(await readErrorDetail(response, t("status.translate_failed")));

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        if (buffer.trim()) {
                            const lines = buffer.split("\n\n");
                            for (const line of lines) {
                                if (!line.trim()) continue;
                                const eventMatch = line.match(/^event: (.*)$/m);
                                const dataMatch = line.match(/^data: (.*)$/m);
                                if (eventMatch && dataMatch && eventMatch[1] === "complete") { finalizeTranslation(JSON.parse(dataMatch[1]).blocks); return; }
                            }
                        }
                        return; // Batch done
                    }

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split("\n\n");
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (!line.trim()) continue;
                        const eventMatch = line.match(/^event: (.*)$/m), dataMatch = line.match(/^data: (.*)$/m);
                        if (!eventMatch || !dataMatch) continue;
                        const eventType = eventMatch[1], eventData = JSON.parse(dataMatch[1]);

                        if (eventType === "progress") {
                            const c_ids = eventData.completed_ids || eventData.completed_indices?.map(idx => batchBlocks[idx]?.client_id);
                            c_ids?.forEach(id => { if (id && !completedIds.includes(id)) completedIds.push(id); });

                            if (eventData.completed_blocks?.length) {
                                finalizeTranslation(eventData.completed_blocks);
                            }

                            // 節流更新：每 5 個區塊更新一次 UI 狀態，減少頻繁渲染
                            if (completedIds.length % 5 === 0 || completedIds.length === batchBlocks.length) {
                                const totalDone = blocks.filter(b => b.translated_text).length + completedIds.length;
                                setProgress(Math.round((totalDone / blocks.length) * 100));
                                setStatus(t("sidebar.translate.translating", { current: totalDone, total: blocks.length }));
                            }
                        } else if (eventType === "complete") {
                            finalizeTranslation(eventData.blocks);
                            return;
                        } else if (eventType === "error") {
                            throw new Error(eventData.detail || t("status.translate_failed"));
                        }
                    }
                }
            } catch (error) {
                const isRetryable = error.message.includes("Failed to fetch") || error.message.includes("500") || error.message.includes("timeout");
                if (isRetryable && retryCount < maxRetries) {
                    retryCount++;
                    setStatus({ key: "status.retrying", params: { count: retryCount } });
                    await new Promise(r => setTimeout(r, 2000));
                    return await runTranslationBatch(batchBlocks);
                }
                throw error;
            }
        };

        try {
            // 將待翻譯區塊拆分為批次
            for (let i = 0; i < pendingBlocks.length; i += BATCH_SIZE) {
                const batch = pendingBlocks.slice(i, i + BATCH_SIZE);
                retryCount = 0; // 重置每個批次的重試次數
                await runTranslationBatch(batch);
                // 批次間加入微小停頓以釋放 UI 線程
                if (i + BATCH_SIZE < pendingBlocks.length) {
                    await new Promise(r => setTimeout(r, 500));
                }
            }
            setProgress(100); setStatus(t("sidebar.translate.completed"));
            setAppStatus(APP_STATUS.TRANSLATION_COMPLETED); setBusy(false);
        } catch (error) {
            setStatus(`${t("status.translate_failed")}：${error.message}`);
            setAppStatus(APP_STATUS.ERROR); setBusy(false);
        }
    };

    const handleApply = async () => {
        if (!file || blocks.length === 0) return;
        const fileType = getFileType();
        setBusy(true); setStatus(t("sidebar.apply.applying")); setAppStatus(APP_STATUS.EXPORTING);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const cleanedBlocks = blocks.map(b => ({
                ...b,
                translated_text: stripBilingualText(b.source_text, b.translated_text, targetLang)
            }));
            const applyBlocks = mode === "correction"
                ? cleanedBlocks.map(b => resolveOutputMode(b) === "source" ? { ...b, apply: false } : b)
                : cleanedBlocks;
            formData.append("blocks", JSON.stringify(applyBlocks));
            formData.append("target_language", targetLang);
            formData.append("mode", mode);
            if (mode === "correction") {
                formData.append("fill_color", fillColor); formData.append("text_color", textColor);
                formData.append("line_color", lineColor); formData.append("line_dash", lineDash);
            }
            if (mode === "bilingual") formData.append("bilingual_layout", bilingualLayout);
            if (fontMapping) formData.append("font_mapping", JSON.stringify(fontMapping));

            const res = await fetch(`${API_BASE}/api/${fileType}/apply`, { method: "POST", body: formData });
            if (!res.ok) {
                const detail = await readErrorDetail(res, t("status.apply_failed"));
                throw new Error(detail);
            }
            const result = await res.json();
            if (result.status !== "success" || !result.download_url) throw new Error(t("status.backend_generate_failed"));

            // --- New Selective Download Logic ---
            const downloadRes = await fetch(`${API_BASE}${result.download_url}`);
            if (!downloadRes.ok) throw new Error("Download failed");

            // Extract filename from header
            const disposition = downloadRes.headers.get('Content-Disposition');
            let filename = result.filename || `translation.${fileType}`;
            if (disposition && disposition.includes('filename*=')) {
                filename = decodeURIComponent(disposition.split("filename*=UTF-8''")[1]);
            } else if (disposition && disposition.includes('filename=')) {
                filename = disposition.split('filename=')[1].replace(/["']/g, '');
            }

            const blob = await downloadRes.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            setStatus(t("sidebar.apply.completed")); setAppStatus(APP_STATUS.EXPORT_COMPLETED);
        } catch (error) {
            setStatus(`${t("status.apply_failed")}：${error.message}`); setAppStatus(APP_STATUS.ERROR);
        } finally { setBusy(false); }
    };

    return { handleExtract, handleTranslate, handleApply, progress };
}
