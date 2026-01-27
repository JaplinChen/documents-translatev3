import { useState, useEffect } from "react";
import { API_BASE } from "../constants";
import { useUIStore } from "../store/useUIStore";
import { useSettingsStore } from "../store/useSettingsStore";
import { useFileStore } from "../store/useFileStore";

export function useTerminology() {
    const [glossaryItems, setGlossaryItems] = useState([]);
    const [tmItems, setTmItems] = useState([]);

    // Store Integration
    const { setManageOpen, setManageTab, manageOpen, manageTab, sourceLang, targetLang } = useUIStore();
    const { useTm, setUseTm } = useSettingsStore();

    // --- Initial Load ---
    useEffect(() => {
        loadGlossary();
        loadMemory();
    }, []);

    const loadGlossary = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/tm/glossary`);
            const data = await response.json();
            setGlossaryItems(data.items || []);
        } catch (error) {
            console.error("Failed to load glossary:", error);
        }
    };

    const loadMemory = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/tm/memory`);
            const data = await response.json();
            setTmItems(data.items || []);
        } catch (error) {
            console.error("Failed to load memory:", error);
        }
    };

    const upsertGlossary = async (blockOrEntry) => {
        console.log("Upserting glossary with input:", blockOrEntry);
        // Ensure we prioritize data directly from the block to avoid stale context issues
        const entry = {
            id: blockOrEntry.id, // Support updating existing records
            source_lang: blockOrEntry.source_lang || sourceLang || "vi",
            target_lang: blockOrEntry.target_lang || targetLang || "zh-TW",
            source_text: (blockOrEntry.source_text || blockOrEntry.text || "").trim(),
            target_text: (blockOrEntry.target_text || blockOrEntry.translated_text || "").trim(),
            priority: blockOrEntry.priority != null ? Number(blockOrEntry.priority) : 0
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
                alert("儲存術語失敗: " + err);
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
        const entry = {
            source_lang: blockOrEntry.source_lang || sourceLang || "vi",
            target_lang: blockOrEntry.target_lang || targetLang || "zh-TW",
            source_text: (blockOrEntry.source_text || blockOrEntry.text || "").trim(),
            target_text: (blockOrEntry.target_text || blockOrEntry.translated_text || "").trim()
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
                alert("儲存記憶失敗: " + err);
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
        if (!window.confirm("確定要清除全部翻譯記憶嗎？此動作無法復原。")) return;
        await fetch(`${API_BASE}/api/tm/memory/clear`, { method: "DELETE" });
        await loadMemory();
    };

    const convertMemoryToGlossary = async (item) => {
        if (!item?.source_text || !item?.target_text) return;
        await upsertGlossary({
            source_lang: item.source_lang,
            target_lang: item.target_lang,
            source_text: item.source_text,
            target_text: item.target_text,
            priority: 0
        });
        if (item.id) await deleteMemory({ id: item.id });
    };

    const convertGlossaryToPreserveTerm = async (item) => {
        if (!item?.source_text) return;
        try {
            const params = new URLSearchParams();
            params.append("source_text", item.source_text);
            params.append("category", "翻譯術語");
            params.append("case_sensitive", "true");

            const response = await fetch(`${API_BASE}/api/preserve-terms/convert-from-glossary?${params.toString()}`, {
                method: "POST"
            });

            if (!response.ok) {
                const error = await response.json();
                alert(error.detail || "轉換失敗");
                return;
            }

            const data = await response.json();
            // Automatically delete from glossary after successful conversion to preserve term
            if (item.id) {
                await deleteGlossary({ id: item.id });
            }
            alert(data.message || `已將 "${item.source_text}" 添加到保留術語`);
        } catch (error) {
            console.error("Failed to convert to preserve term:", error);
            alert("轉換失敗：" + error.message);
        }
    };

    const handleSeedTm = async () => {
        await fetch(`${API_BASE}/api/tm/seed`, { method: "POST" });
        await loadGlossary();
        await loadMemory();
    };

    const clearGlossary = async () => {
        if (!window.confirm("確定要清除全部術語嗎？此動作無法復原。")) return;
        await fetch(`${API_BASE}/api/tm/glossary/clear`, { method: "DELETE" });
        await loadGlossary();
    };

    const batchUpsertGlossary = async (entries) => {
        if (!entries || entries.length === 0) return;
        await fetch(`${API_BASE}/api/tm/glossary/batch`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(entries)
        });
        await loadGlossary();
    };

    const handleExtractGlossary = async ({ blocks, targetLang, llmProvider, llmApiKey, llmBaseUrl, llmModel, setStatus, setBusy }) => {
        if (!blocks || blocks.length === 0) {
            setStatus("請先抽取區塊");
            return;
        }
        setBusy(true);
        setStatus("正在智慧提取術語...");
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

            if (!response.ok) throw new Error("提取失敗");
            const data = await response.json();
            const rawTerms = data.terms || [];

            if (rawTerms.length === 0) {
                setStatus("未偵測到明顯術語");
            } else {
                // Client-side de-duplication based on source text
                const uniqueTermsMap = new Map();
                rawTerms.forEach(t => {
                    const key = t.source.toLowerCase().trim();
                    if (!uniqueTermsMap.has(key)) {
                        uniqueTermsMap.set(key, {
                            source_lang: "auto",
                            target_lang: targetLang,
                            source_text: t.source,
                            target_text: t.target,
                            priority: 5
                        });
                    }
                });

                const termsToUpsert = Array.from(uniqueTermsMap.values());
                await batchUpsertGlossary(termsToUpsert);

                setStatus(`智慧提取成功，新增 ${termsToUpsert.length} 筆術語`);
                setManageOpen(true);
                setManageTab("glossary");
            }
        } catch (error) {
            console.error("Failed to extract glossary:", error);
            setStatus(`提取失敗：${error.message}`);
        } finally {
            setBusy(false);
        }
    };

    return {
        glossaryItems, tmItems,
        useTm, setUseTm,
        manageOpen, setManageOpen, // Exposed via store, but can also be accessed directly
        manageTab, setManageTab,

        loadGlossary, loadMemory,
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
