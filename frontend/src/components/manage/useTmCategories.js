import { useCallback, useEffect, useState } from 'react';
import { API_BASE } from '../../constants';

const sortCategories = (items) => {
    const next = Array.isArray(items) ? items : [];
    next.sort((a, b) => {
        const ao = Number(a?.sort_order ?? 0);
        const bo = Number(b?.sort_order ?? 0);
        if (ao !== bo) return ao - bo;
        const an = String(a?.name ?? '');
        const bn = String(b?.name ?? '');
        return an.localeCompare(bn, 'zh-Hant', { numeric: true, sensitivity: 'base' });
    });
    return next;
};

export function useTmCategories(open) {
    const [tmCategories, setTmCategories] = useState([]);

    const fetchTmCategories = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/tm/categories`);
            const data = await res.json();
            setTmCategories(sortCategories(data.items));
        } catch (err) {
            console.error(err);
        }
    }, []);

    useEffect(() => {
        if (open) fetchTmCategories();
    }, [open, fetchTmCategories]);

    return { tmCategories, refreshTmCategories: fetchTmCategories };
}
