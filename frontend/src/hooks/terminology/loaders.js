import { API_BASE } from '../../constants';
import { useUIStore } from '../../store/useUIStore';

const parseCreatedAt = (value) => {
    if (!value) return null;
    const iso = value.replace(' ', 'T') + 'Z';
    const createdTs = Date.parse(iso);
    return Number.isNaN(createdTs) ? null : createdTs;
};

export const loadGlossaryItems = async ({
    limit,
    offset,
    setGlossaryItems,
    setGlossaryTotal,
    setGlossaryLimit,
    setGlossaryOffset,
    isLatest,
}) => {
    try {
        const response = await fetch(`${API_BASE}/api/tm/glossary?limit=${limit}&offset=${offset || 0}`);
        if (!response.ok) {
            throw new Error(`glossary_load_failed:${response.status}`);
        }
        const data = await response.json();
        if (isLatest && !isLatest()) return;
        const { lastGlossaryAt: latestGlossaryAt } = useUIStore.getState();
        const parsed = (data.items || []).map((item) => {
            if (!item?.created_at || !latestGlossaryAt) return { ...item, is_new: false };
            const createdTs = parseCreatedAt(item.created_at);
            return { ...item, is_new: createdTs !== null && createdTs >= latestGlossaryAt };
        });
        setGlossaryItems(parsed);
        setGlossaryTotal(data.total ?? parsed.length);
        setGlossaryLimit(limit);
        if (setGlossaryOffset) setGlossaryOffset(data.offset ?? (offset || 0));
    } catch (error) {
        console.error('Failed to load glossary:', error);
    }
};

export const loadMemoryItems = async ({
    limit,
    offset,
    setTmItems,
    setTmTotal,
    setTmLimit,
    setTmOffset,
    isLatest,
}) => {
    try {
        const response = await fetch(`${API_BASE}/api/tm/memory?limit=${limit}&offset=${offset || 0}`);
        if (!response.ok) {
            throw new Error(`memory_load_failed:${response.status}`);
        }
        const data = await response.json();
        if (isLatest && !isLatest()) return;
        const { lastTranslationAt: latestTranslationAt, lastMemoryAt: latestMemoryAt } = useUIStore.getState();
        const baseStamp = Math.max(latestTranslationAt || 0, latestMemoryAt || 0) || null;
        const parsed = (data.items || []).map((item) => {
            if (!item?.created_at || !baseStamp) return { ...item, is_new: false };
            const createdTs = parseCreatedAt(item.created_at);
            return { ...item, is_new: createdTs !== null && createdTs >= baseStamp };
        });
        setTmItems(parsed);
        setTmTotal(data.total ?? parsed.length);
        setTmLimit(limit);
        if (setTmOffset) setTmOffset(data.offset ?? (offset || 0));
    } catch (error) {
        console.error('Failed to load memory:', error);
    }
};
