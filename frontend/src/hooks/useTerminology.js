import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../constants";
import { useUIStore } from "../store/useUIStore";
import { useSettingsStore } from "../store/useSettingsStore";
import { useFileStore } from "../store/useFileStore";

const PRESERVE_CATEGORY_TRANSLATION = "翻譯";

export function useTerminology() {
    const { t } = useTranslation();
    const [glossaryItems, setGlossaryItems] = useState([]);
    const [tmItems, setTmItems] = useState([]);
    const [glossaryTotal, setGlossaryTotal] = useState(0);
    const [tmTotal, setTmTotal] = useState(0);
    const [glossaryLimit, setGlossaryLimit] = useState(200);
    const [tmLimit, setTmLimit] = useState(200);

    // Store Integration
    const {
        setManageOpen, setManageTab, manageOpen, manageTab, sourceLang, targetLang,
        setLastGlossaryAt, setLastMemoryAt, setLastPreserveAt
    } = useUIStore();
    const { useTm, setUseTm } = useSettingsStore();
    const feedbackTimerRef = useRef(null);

    // --- Initial Load ---
    useEffect(() => {
        loadGlossary();
        loadMemory();
    }, []);

    const loadGlossary = async (limitOverride) => {
        const limit = limitOverride ?? glossaryLimit;
        try {
            const response = await fetch(`${API_BASE}/api/tm/glossary?limit=${limit}`);
            const data = await response.json();
            const { lastGlossaryAt: latestGlossaryAt } = useUIStore.getState();
            const parsed = (data.items || []).map((item) => {
                if (!item?.created_at || !latestGlossaryAt) return { ...item, is_new: false };
                const iso = item.created_at.replace(" ", "T") + "Z";
                const createdTs = Date.parse(iso);
                return { ...item, is_new: !Number.isNaN(createdTs) && createdTs >= latestGlossaryAt };
            });
            setGlossaryItems(parsed);
            setGlossaryTotal(data.total ?? parsed.length);
            setGlossaryLimit(limit);
        } catch (error) {
            console.error("Failed to load glossary:", error);
        }
    };

    const loadMemory = async (limitOverride) => {
        const limit = limitOverride ?? tmLimit;
        try {
            const response = await fetch(`${API_BASE}/api/tm/memory?limit=${limit}`);
            const data = await response.json();
            const { lastTranslationAt: latestTranslationAt, lastMemoryAt: latestMemoryAt } = useUIStore.getState();
            const baseStamp = Math.max(latestTranslationAt || 0, latestMemoryAt || 0) || null;
            const parsed = (data.items || []).map((item) => {
                if (!item?.created_at || !baseStamp) return { ...item, is_new: false };
                const iso = item.created_at.replace(" ", "T") + "Z";
                const createdTs = Date.parse(iso);
                return { ...item, is_new: !Number.isNaN(createdTs) && createdTs >= baseStamp };
            });
            setTmItems(parsed);
            setTmTotal(data.total ?? parsed.length);
            setTmLimit(limit);
        } catch (error) {
            console.error("Failed to load memory:", error);
        }
    };

    const upsertGlossary = async (blockOrEntry) => {
        console.log("Upserting glossary with input:", blockOrEntry);
        setLastGlossaryAt(Date.now());
        // Ensure we prioritize data directly from the block to avoid stale context issues
        const rawCategoryId = blockOrEntry.category_id;
        const entry = {
            id: blockOrEntry.id, // Support updating existing records
            source_lang: blockOrEntry.source_lang || sourceLang || "vi",
            target_lang: blockOrEntry.target_lang || targetLang || "zh-TW",
            source_text: (blockOrEntry.source_text || blockOrEntry.text || "").trim(),
            target_text: (blockOrEntry.target_text || blockOrEntry.translated_text || "").trim(),
            priority: blockOrEntry.priority != null ? Number(blockOrEntry.priority) : 0,
            // Fix: Convert empty string to null for category_id
            category_id: rawCategoryId === "" || rawCategoryId == null ? null : Number(rawCategoryId),
            filename: blockOrEntry.filename || useFileStore.getState().file?.name || ""
        };

        if (!entry.source_text) {
            console.error("Glossary source_text is empty, aborting upsert", entry);
            return;
        }

        try {
            const resp = await fetch(`${API_BASE}/api/tm/glossary`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(entry)
            });
            if (!resp.ok) {
                const err = await resp.text();
                console.error("Glossary upsert failed server-side:", err);
                alert(t("manage.alerts.save_glossary_failed", { message: err }));
            } else {
                console.log("Glossary upsert success");
                await loadGlossary();
            }
        } catch (error) {
            console.error("Fetch error during glossary upsert:", error);
        }
    };

    const deleteGlossary = async (entry) => {
        await fetch(`${API_BASE}/api/tm/glossary`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(entry)
        });
        await loadGlossary();
    };

    const upsertMemory = async (blockOrEntry) => {
        console.log("Upserting memory with input:", blockOrEntry);
        setLastMemoryAt(Date.now());
        const rawCategoryId = blockOrEntry.category_id;
        const entry = {
            id: blockOrEntry.id, // Support explicit update by ID
            source_lang: blockOrEntry.source_lang || sourceLang || "vi",
            target_lang: blockOrEntry.target_lang || targetLang || "zh-TW",
            source_text: (blockOrEntry.source_text || blockOrEntry.text || "").trim(),
            target_text: (blockOrEntry.target_text || blockOrEntry.translated_text || "").trim(),
            // Fix: Convert empty string to null for category_id
            category_id: rawCategoryId === "" || rawCategoryId == null ? null : Number(rawCategoryId)
        };

        if (!entry.source_text) {
            console.error("Memory source_text is empty, aborting upsert", entry);
            return;
        }

        try {
            const resp = await fetch(`${API_BASE}/api/tm/memory`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(entry)
            });
            if (!resp.ok) {
                const err = await resp.text();
                console.error("Memory upsert failed server-side:", err);
                alert(t("manage.alerts.save_memory_failed", { message: err }));
            } else {
                console.log("Memory upsert success");
                await loadMemory();
            }
        } catch (error) {
            console.error("Fetch error during memory upsert:", error);
        }
    };

    const deleteMemory = async (entry) => {
        await fetch(`${API_BASE}/api/tm/memory`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(entry)
        });
        await loadMemory();
    };

    const clearMemory = async () => {
        if (!window.confirm(t("manage.confirm.clear_memory"))) return;
        await fetch(`${API_BASE}/api/tm/memory/clear`, { method: "DELETE" });
        await loadMemory();
    };

    const convertMemoryToGlossary = async (item) => {
        if (!item?.source_text || !item?.target_text) return;
        setLastGlossaryAt(Date.now());
        await upsertGlossary({
            source_lang: item.source_lang,
            target_lang: item.target_lang,
            source_text: item.source_text,
            target_text: item.target_text,
            priority: 0
        });
        if (item.id) await deleteMemory({ id: item.id });
    };

    const convertGlossaryToPreserveTerm = async (item, options = {}) => {
        const { silent = false } = options;
        if (!item?.source_text) return;
        try {
            setLastPreserveAt(Date.now());
            const params = new URLSearchParams();
            params.append("source_text", item.source_text);
            params.append("category", PRESERVE_CATEGORY_TRANSLATION);
            params.append("case_sensitive", "true");

            const response = await fetch(`${API_BASE}/api/preserve-terms/convert-from-glossary?${params.toString()}`, {
                method: "POST"
            });

            if (!response.ok) {
                const error = await response.json();
                const msg = error.detail || t("manage.alerts.convert_failed");
                if (!silent) alert(msg);
                return { ok: false, error: msg };
            }

            const data = await response.json();
            // Automatically delete from glossary after successful conversion to preserve term
            if (item.id) {
                await deleteGlossary({ id: item.id });
            }
            if (!silent) alert(data.message || t("manage.alerts.convert_success", { text: item.source_text }));
            return { ok: true, message: data.message };
        } catch (error) {
            console.error("Failed to convert to preserve term:", error);
            if (!silent) alert(t("manage.alerts.convert_failed_detail", { message: error.message }));
            return { ok: false, error: error.message };
        }
    };

    const handleSeedTm = async () => {
        const now = Date.now();
        setLastGlossaryAt(now);
        setLastMemoryAt(now);
        await fetch(`${API_BASE}/api/tm/seed`, { method: "POST" });
        await loadGlossary();
        await loadMemory();
    };

    const clearGlossary = async () => {
        if (!window.confirm(t("manage.confirm.clear_glossary"))) return;
        await fetch(`${API_BASE}/api/tm/glossary/clear`, { method: "DELETE" });
        await loadGlossary();
    };

    const batchUpsertGlossary = async (entries) => {
        if (!entries || entries.length === 0) return;
        setLastGlossaryAt(Date.now());
        await fetch(`${API_BASE}/api/tm/glossary/batch`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(entries)
        });
        await loadGlossary();
    };

    const handleExtractGlossary = async ({ blocks, sourceLang, targetLang, llmProvider, llmApiKey, llmBaseUrl, llmModel, setStatus, setBusy }) => {
        if (!blocks || blocks.length === 0) {
            setStatus(t("status.no_blocks"));
            return;
        }
        setBusy(true);
        setLastPreserveAt(Date.now());
        setStatus(t("manage.glossary_extract.processing"));
        try {
            const payload = {
                blocks,
                target_language: targetLang,
                provider: llmProvider,
                model: llmModel,
                api_key: llmApiKey,
                base_url: llmBaseUrl
            };

            const response = await fetch(`${API_BASE}/api/tm/extract-glossary-stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || t("manage.glossary_extract.failed"));
            }

            // Read the stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let rawTerms = [];

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split("\n");

                let currentEvent = null;
                for (const line of lines) {
                    if (line.startsWith("event: ")) {
                        currentEvent = line.replace("event: ", "").trim();
                    } else if (line.startsWith("data: ")) {
                        const dataStr = line.replace("data: ", "").trim();
                        try {
                            const data = JSON.parse(dataStr);
                            if (currentEvent === "progress") {
                                setStatus(`${data.message} (${data.percent}%)`);
                            } else if (currentEvent === "complete") {
                                rawTerms = data.terms || [];
                                window._lastExtractionDomain = data.domain || "general";
                            } else if (currentEvent === "error") {
                                throw new Error(data.detail || t("manage.glossary_extract.failed"));
                            }
                        } catch (e) {
                            console.error("Failed to parse SSE data:", dataStr, e);
                        }
                    }
                }
            }

            if (rawTerms.length === 0) {
                setStatus(t("manage.glossary_extract.empty"));
            } else {
                // Client-side de-duplication based on source text
                const uniqueTermsMap = new Map();
                rawTerms.forEach(term => {
                    if (!term.source) return;
                    const key = term.source.toLowerCase().trim();
                    if (!uniqueTermsMap.has(key)) {
                        // Map category to display name
                        const categoryMap = {
                            product: "產品",
                            brand: "品牌",
                            person: "人名",
                            place: "地名",
                            technical: "技術",
                            abbreviation: "縮寫",
                            other: "其他"
                        };
                        const categoryName = categoryMap[term.category] || categoryMap.other;

                        uniqueTermsMap.set(key, {
                            source_lang: sourceLang || "auto",
                            target_lang: targetLang,
                            source_text: term.source,
                            target_text: term.target || "",
                            category_name: categoryName,
                            confidence: term.confidence || 5,
                            priority: term.confidence || 5,  // Use confidence as priority
                            reason: term.reason || ""
                        });
                    }
                });
                const termsToUpsert = Array.from(uniqueTermsMap.values());

                // Sort by confidence/priority descending
                termsToUpsert.sort((a, b) => (b.confidence || 0) - (a.confidence || 0));

                setStatus(t("status.saving"));
                const currentFilename = useFileStore.getState().file?.name || "";

                // Use a small delay to show the final result status
                let finalMsg = t("manage.glossary_extract.success", { count: termsToUpsert.length }) + " " +
                    t("manage.glossary_extract.learning_hint", { domain: window._lastExtractionDomain || "general" });
                setStatus(finalMsg);

                // Save to preserve terms (existing flow)
                const preservePayload = {
                    terms: termsToUpsert.map((term) => ({
                        term: term.source_text,
                        category: term.category_name || PRESERVE_CATEGORY_TRANSLATION,
                        case_sensitive: true
                    }))
                };
                await fetch(`${API_BASE}/api/preserve-terms/batch`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(preservePayload)
                });

                // ALSO Save to unified terms database (new requirement for "Translation Data")
                for (const term of termsToUpsert) {
                    await fetch(`${API_BASE}/api/terms/upsert`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            term: term.source_text,
                            category_name: term.category_name || PRESERVE_CATEGORY_TRANSLATION,
                            source: "terminology",
                            filename: currentFilename,
                            priority: term.priority,
                            note: term.reason,
                            languages: [{ lang_code: term.target_lang, value: term.target_text }]
                        })
                    });
                }

                finalMsg = t("manage.glossary_extract.success", { count: termsToUpsert.length }) + " " +
                    t("manage.glossary_extract.learning_hint", { domain: rawTerms[0]?.domain || "general" });
                setStatus(finalMsg);
                setManageOpen(true);
                setManageTab("terms"); // Open the unified view
            }
        } catch (error) {
            console.error("Failed to extract glossary:", error);
            setStatus(t("manage.glossary_extract.failed_detail", { message: error.message }));
        } finally {
            setBusy(false);
        }
    };

    const loadMoreGlossary = async () => {
        const next = glossaryLimit + 200;
        await loadGlossary(next);
    };

    const loadMoreMemory = async () => {
        const next = tmLimit + 200;
        await loadMemory(next);
    };

    const recordFeedback = async ({ source, target, sourceLang, targetLang }) => {
        if (!source || !target) return;
        if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
        feedbackTimerRef.current = setTimeout(async () => {
            try {
                const response = await fetch(`${API_BASE}/api/tm/feedback`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        source,
                        target,
                        source_lang: sourceLang,
                        target_lang: targetLang
                    })
                });
                if (!response.ok) {
                    console.warn("Feedback recording skipped or failed:", response.status);
                }
            } catch (error) {
                console.error("Failed to record feedback:", error);
            }
        }, 2000); // 2 秒防抖
    };

    return {
        glossaryItems, tmItems,
        glossaryTotal, tmTotal,
        glossaryLimit, tmLimit,
        useTm, setUseTm,
        manageOpen, setManageOpen, // Exposed via store, but can also be accessed directly
        manageTab, setManageTab,

        loadGlossary, loadMemory,
        loadMoreGlossary, loadMoreMemory,
        upsertGlossary, deleteGlossary,
        upsertMemory, deleteMemory,
        clearMemory,
        clearGlossary,
        batchUpsertGlossary,
        convertMemoryToGlossary,
        convertGlossaryToPreserveTerm,
        handleSeedTm,
        handleExtractGlossary,
        recordFeedback
    };
}
