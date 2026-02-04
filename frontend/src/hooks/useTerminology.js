import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { API_BASE } from '../constants';
import { useUIStore } from '../store/useUIStore';
import { useSettingsStore } from '../store/useSettingsStore';
import { useFileStore } from '../store/useFileStore';
import { loadGlossaryItems, loadMemoryItems } from './terminology/loaders';
import { extractGlossaryFromBlocks } from './terminology/extractGlossary';
import { recordFeedbackWithDebounce } from './terminology/feedback';
import { buildGlossaryEntry, buildMemoryEntry, PRESERVE_CATEGORY_TRANSLATION } from './terminology/helpers';

export function useTerminology() {
    const { t } = useTranslation();
    const [glossaryItems, setGlossaryItems] = useState([]);
    const [tmItems, setTmItems] = useState([]);
    const [glossaryTotal, setGlossaryTotal] = useState(0);
    const [tmTotal, setTmTotal] = useState(0);
    const [glossaryLimit, setGlossaryLimit] = useState(200);
    const [tmLimit, setTmLimit] = useState(200);
    const [glossaryOffset, setGlossaryOffset] = useState(0);
    const [tmOffset, setTmOffset] = useState(0);
    const [glossaryPage, setGlossaryPage] = useState(1);
    const [tmPage, setTmPage] = useState(1);

    const {
        setManageOpen, setManageTab, manageOpen, manageTab, sourceLang, targetLang,
        setLastGlossaryAt, setLastMemoryAt, setLastPreserveAt, lastGlossaryAt, lastMemoryAt
    } = useUIStore();
    const { useTm, setUseTm } = useSettingsStore();
    const feedbackTimerRef = useRef(null);
    const glossaryReqRef = useRef(0);
    const memoryReqRef = useRef(0);

    useEffect(() => {
        loadGlossary();
        loadMemory();
    }, []);

    useEffect(() => {
        if (!lastGlossaryAt) return;
        loadGlossary();
    }, [lastGlossaryAt]);

    useEffect(() => {
        if (!lastMemoryAt) return;
        loadMemory();
    }, [lastMemoryAt]);

    const loadGlossary = async (options = {}) => {
        const limit = options.limit ?? glossaryLimit;
        const offset = options.offset ?? glossaryOffset;
        const reqId = ++glossaryReqRef.current;
        await loadGlossaryItems({
            limit,
            offset,
            setGlossaryItems,
            setGlossaryTotal,
            setGlossaryLimit,
            setGlossaryOffset,
            isLatest: () => glossaryReqRef.current === reqId,
        });
    };

    const loadMemory = async (options = {}) => {
        const limit = options.limit ?? tmLimit;
        const offset = options.offset ?? tmOffset;
        const reqId = ++memoryReqRef.current;
        await loadMemoryItems({
            limit,
            offset,
            setTmItems,
            setTmTotal,
            setTmLimit,
            setTmOffset,
            isLatest: () => memoryReqRef.current === reqId,
        });
    };

    const upsertGlossary = async (blockOrEntry) => {
        setLastGlossaryAt(Date.now());
        const entry = buildGlossaryEntry({
            blockOrEntry,
            sourceLang,
            targetLang,
            filename: useFileStore.getState().file?.name || '',
        });

        if (!entry.source_text) {
            console.error('Glossary source_text is empty, aborting upsert', entry);
            return;
        }

        try {
            const resp = await fetch(`${API_BASE}/api/tm/glossary`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(entry),
            });
            if (!resp.ok) {
                const err = await resp.text();
                console.error('Glossary upsert failed server-side:', err);
                alert(t('manage.alerts.save_glossary_failed', { message: err }));
            } else {
                await loadGlossary();
            }
        } catch (error) {
            console.error('Fetch error during glossary upsert:', error);
        }
    };

    const deleteGlossary = async (entry) => {
        await fetch(`${API_BASE}/api/tm/glossary`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry),
        });
        await loadGlossary();
    };

    const upsertMemory = async (blockOrEntry) => {
        setLastMemoryAt(Date.now());
        const entry = buildMemoryEntry({ blockOrEntry, sourceLang, targetLang });

        if (!entry.source_text) {
            console.error('Memory source_text is empty, aborting upsert', entry);
            return;
        }

        try {
            const resp = await fetch(`${API_BASE}/api/tm/memory`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(entry),
            });
            if (!resp.ok) {
                const err = await resp.text();
                console.error('Memory upsert failed server-side:', err);
                alert(t('manage.alerts.save_memory_failed', { message: err }));
            } else {
                await loadMemory();
            }
        } catch (error) {
            console.error('Fetch error during memory upsert:', error);
        }
    };

    const deleteMemory = async (entry) => {
        await fetch(`${API_BASE}/api/tm/memory`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry),
        });
        await loadMemory();
    };

    const clearMemory = async () => {
        if (!window.confirm(t('manage.confirm.clear_memory'))) return;
        await fetch(`${API_BASE}/api/tm/memory/clear`, { method: 'DELETE' });
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
            priority: 0,
        });
        if (item.id) await deleteMemory({ id: item.id });
    };

    const convertGlossaryToPreserveTerm = async (item, options = {}) => {
        const { silent = false } = options;
        if (!item?.source_text) return;
        try {
            setLastPreserveAt(Date.now());
            const params = new URLSearchParams();
            params.append('source_text', item.source_text);
            params.append('category', PRESERVE_CATEGORY_TRANSLATION);
            params.append('case_sensitive', 'true');

            const response = await fetch(`${API_BASE}/api/preserve-terms/convert-from-glossary?${params.toString()}`, {
                method: 'POST',
            });

            if (!response.ok) {
                const error = await response.json();
                const msg = error.detail || t('manage.alerts.convert_failed');
                if (!silent) alert(msg);
                return { ok: false, error: msg };
            }

            const data = await response.json();
            if (item.id) {
                await deleteGlossary({ id: item.id });
            }
            if (!silent) alert(data.message || t('manage.alerts.convert_success', { text: item.source_text }));
            return { ok: true, message: data.message };
        } catch (error) {
            console.error('Failed to convert to preserve term:', error);
            if (!silent) {
                alert(t('manage.alerts.convert_failed_detail', { message: error.message }));
            }
            return { ok: false, error: error.message };
        }
    };

    const handleSeedTm = async () => {
        const now = Date.now();
        setLastGlossaryAt(now);
        setLastMemoryAt(now);
        await fetch(`${API_BASE}/api/tm/seed`, { method: 'POST' });
        await loadGlossary();
        await loadMemory();
    };

    const clearGlossary = async () => {
        if (!window.confirm(t('manage.confirm.clear_glossary'))) return;
        await fetch(`${API_BASE}/api/tm/glossary/clear`, { method: 'DELETE' });
        await loadGlossary();
    };

    const batchUpsertGlossary = async (entries) => {
        if (!entries || entries.length === 0) return;
        setLastGlossaryAt(Date.now());
        await fetch(`${API_BASE}/api/tm/glossary/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entries),
        });
        await loadGlossary();
    };

    const handleExtractGlossary = async ({
        blocks,
        sourceLang: extractSourceLang,
        targetLang: extractTargetLang,
        llmProvider,
        llmApiKey,
        llmBaseUrl,
        llmModel,
        setStatus,
        setBusy,
    }) => {
        await extractGlossaryFromBlocks({
            blocks,
            sourceLang: extractSourceLang,
            targetLang: extractTargetLang,
            llmProvider,
            llmApiKey,
            llmBaseUrl,
            llmModel,
            t,
            setStatus,
            setBusy,
            setLastPreserveAt,
            setManageOpen,
            setManageTab,
        });
    };

    const loadGlossaryPage = async (page, pageSize = glossaryLimit) => {
        const nextOffset = Math.max(0, (page - 1) * pageSize);
        setGlossaryPage(page);
        await loadGlossary({ limit: pageSize, offset: nextOffset });
    };

    const loadMemoryPage = async (page, pageSize = tmLimit) => {
        const nextOffset = Math.max(0, (page - 1) * pageSize);
        setTmPage(page);
        await loadMemory({ limit: pageSize, offset: nextOffset });
    };

    const setGlossaryPageSize = async (size) => {
        setGlossaryLimit(size);
        setGlossaryPage(1);
        await loadGlossary({ limit: size, offset: 0 });
    };

    const setTmPageSize = async (size) => {
        setTmLimit(size);
        setTmPage(1);
        await loadMemory({ limit: size, offset: 0 });
    };

    const recordFeedback = async ({ source, target, sourceLang: fbSource, targetLang: fbTarget }) => {
        recordFeedbackWithDebounce({
            feedbackTimerRef,
            source,
            target,
            sourceLang: fbSource,
            targetLang: fbTarget,
        });
    };

    return {
        glossaryItems, tmItems,
        glossaryTotal, tmTotal,
        glossaryLimit, tmLimit,
        glossaryOffset, tmOffset,
        glossaryPage, tmPage,
        useTm, setUseTm,
        manageOpen, setManageOpen,
        manageTab, setManageTab,
        loadGlossary, loadMemory,
        loadGlossaryPage, loadMemoryPage,
        setGlossaryPageSize, setTmPageSize,
        upsertGlossary, deleteGlossary,
        upsertMemory, deleteMemory,
        clearMemory,
        clearGlossary,
        batchUpsertGlossary,
        convertMemoryToGlossary,
        convertGlossaryToPreserveTerm,
        handleSeedTm,
        handleExtractGlossary,
        recordFeedback,
    };
}
