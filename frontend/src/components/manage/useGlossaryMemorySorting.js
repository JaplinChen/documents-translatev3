import { useMemo, useState } from 'react';

export function useGlossaryMemorySorting(items, defaultKey) {
    const [sortKey, setSortKey] = useState(defaultKey);
    const [sortDir, setSortDir] = useState('asc');

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir((p) => p === 'asc' ? 'desc' : 'asc');
        } else {
            setSortKey(key);
            setSortDir('asc');
        }
    };

    const sortedItems = useMemo(() => {
        if (!items) return [];
        const list = [...items];
        if (!sortKey) return list;

        list.sort((a, b) => {
            const valA = a[sortKey];
            const valB = b[sortKey];
            const dir = sortDir === 'asc' ? 1 : -1;

            if (sortKey === 'priority' || sortKey === 'category_id') {
                return (Number(valA || 0) - Number(valB || 0)) * dir;
            }
            return String(valA || '').localeCompare(String(valB || ''), 'zh-Hant') * dir;
        });
        return list;
    }, [items, sortKey, sortDir]);

    return { sortKey, sortDir, toggleSort, sortedItems };
}
