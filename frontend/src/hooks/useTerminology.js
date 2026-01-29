import { useState, useEffect } from "react";
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
        const entry = {
            id: blockOrEntry.id, // Support updating existing records
            source_lang: blockOrEntry.source_lang || sourceLang || "vi",
            target_lang: blockOrEntry.target_lang || targetLang || "zh-TW",
            source_text: (blockOrEntry.source_text || blockOrEntry.text || "").trim(),
            target_text: (blockOrEntry.target_text || blockOrEntry.translated_text || "").trim(),
            priority: blockOrEntry.priority != null ? Number(blockOrEntry.priority) : 0,
            category_id: blockOrEntry.category_id
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
        const entry = {
            source_lang: blockOrEntry.source_lang || sourceLang || "vi",
            target_lang: blockOrEntry.target_lang || targetLang || "zh-TW",
            source_text: (blockOrEntry.source_text || blockOrEntry.text || "").trim(),
            target_text: (blockOrEntry.target_text || blockOrEntry.translated_text || "").trim(),
            category_id: blockOrEntry.category_id
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
            const formData = new FormData();
            formData.append("blocks", JSON.stringify(blocks));
            formData.append("target_language", targetLang);
            formData.append("provider", llmProvider);
            if (llmModel) formData.append("model", llmModel);
            if (llmApiKey) formData.append("api_key", llmApiKey);
            if (llmBaseUrl) formData.append("base_url", llmBaseUrl);

            const file = useFileStore.getState().file;
            const fileType = file?.name?.split('.').pop().toLowerCase() === 'docx' ? 'docx' : 'pptx';

            const response = await fetch(`${API_BASE}/api/${fileType}/extract-glossary`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) throw new Error(t("manage.glossary_extract.failed"));
            const data = await response.json();
            if (data.error) {
                setStatus(t("manage.glossary_extract.failed_detail", { message: data.error }));
                return;
            }
            const rawTerms = data.terms || [];

            if (rawTerms.length === 0) {
                setStatus(t("manage.glossary_extract.empty"));
            } else {
                // Client-side de-duplication based on source text
                const uniqueTermsMap = new Map();
                rawTerms.forEach(t => {
                    const key = t.source.toLowerCase().trim();
                    if (!uniqueTermsMap.has(key)) {
                        uniqueTermsMap.set(key, {
                            source_lang: sourceLang || "auto",
                            target_lang: targetLang,
                            source_text: t.source,
                            target_text: t.target,
                            priority: 5
                        });
                    }
                });

                const termsToUpsert = Array.from(uniqueTermsMap.values());
                const payload = {
                    terms: termsToUpsert.map((term) => ({
                        term: term.source_text,
                        category: PRESERVE_CATEGORY_TRANSLATION,
                        case_sensitive: true
                    }))
                };
                const resp = await fetch(`${API_BASE}/api/preserve-terms/batch`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (!resp.ok) throw new Error(t("manage.glossary_extract.failed"));
                const result = await resp.json();
                const createdCount = result.created ?? termsToUpsert.length;

                setStatus(t("manage.glossary_extract.success", { count: createdCount }));
                setManageOpen(true);
                setManageTab("preserve");
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
        handleExtractGlossary
    };
}
