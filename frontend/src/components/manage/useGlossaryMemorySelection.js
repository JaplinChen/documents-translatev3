import { useState } from 'react';

export function useGlossaryMemorySelection(items) {
    const [selectedIds, setSelectedIds] = useState([]);

    const handleSelectRow = (id, checked) => {
        if (checked) setSelectedIds((prev) => [...prev, id]);
        else setSelectedIds((prev) => prev.filter((x) => x !== id));
    };

    const handleSelectAll = (checked) => {
        if (checked) setSelectedIds(items.map((i) => i.id));
        else setSelectedIds([]);
    };

    return { selectedIds, setSelectedIds, handleSelectRow, handleSelectAll };
}
