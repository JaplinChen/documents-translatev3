import { useEffect, useState } from 'react';
import { useUIStore } from '../../store/useUIStore';
import { buildGlossaryMemoryColumns } from './glossaryMemoryColumns.jsx';
import { handleExport, handleImportFile } from './glossaryMemoryIO';
import { useGlossaryMemorySelection } from './useGlossaryMemorySelection';
import { useGlossaryMemorySorting } from './useGlossaryMemorySorting';
import { useGlossaryMemoryEditing } from './useGlossaryMemoryEditing';
import { useGlossaryMemoryBatch } from './useGlossaryMemoryBatch';

export function useGlossaryMemoryState({
    open,
    tab,
    glossaryItems,
    tmItems,
    glossaryTotal,
    tmTotal,
    defaultSourceLang,
    defaultTargetLang,
    tmCategories,
    onRefreshGlossary,
    onRefreshMemory,
    onSeed,
    onUpsertGlossary,
    onDeleteGlossary,
    onClearGlossary,
    onUpsertMemory,
    onDeleteMemory,
    onClearMemory,
    onConvertToGlossary,
    onConvertToPreserveTerm,
    t,
}) {
    const isGlossary = tab === 'glossary';
    const items = isGlossary ? glossaryItems : tmItems;
    const compactKey = isGlossary ? 'manage_table_compact_glossary' : 'manage_table_compact_tm';

    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem(compactKey);
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

    const { setLastGlossaryAt, setLastMemoryAt } = useUIStore();

    const selection = useGlossaryMemorySelection(items);
    const sorting = useGlossaryMemorySorting(items, isGlossary ? 'priority' : null);

    const editing = useGlossaryMemoryEditing({
        isGlossary,
        glossaryItems,
        tmItems,
        defaultSourceLang,
        defaultTargetLang,
        onUpsertGlossary,
        onDeleteGlossary,
        onUpsertMemory,
        onDeleteMemory,
        setLastGlossaryAt,
        setLastMemoryAt,
        t,
    });

    const batch = useGlossaryMemoryBatch({
        isGlossary,
        items,
        selectedIds: selection.selectedIds,
        setSelectedIds: selection.setSelectedIds,
        onSeed,
        onConvertToGlossary,
        onConvertToPreserveTerm,
        t,
    });

    useEffect(() => {
        if (!open) return;
        editing.setEditingKey(null);
        editing.setEditingOriginal(null);
        editing.setDraft(null);
        selection.setSelectedIds([]);
    }, [open, tab]);

    useEffect(() => {
        if (!open) return;
        if (tab === 'glossary' && onRefreshGlossary) onRefreshGlossary();
        if (tab === 'tm' && onRefreshMemory) onRefreshMemory();
    }, [open, tab, onRefreshGlossary, onRefreshMemory]);

    useEffect(() => {
        try {
            const saved = localStorage.getItem(compactKey);
            setCompactTable(saved ? JSON.parse(saved) : false);
        } catch {
            setCompactTable(false);
        }
    }, [compactKey]);

    const columns = buildGlossaryMemoryColumns({
        t,
        isGlossary,
        editingKey: editing.editingKey,
        editingField: editing.editingField,
        makeKey: editing.makeKey,
        draft: editing.draft,
        setDraft: editing.setDraft,
        handleKeyDown: editing.handleKeyDown,
        handleSave: editing.handleSave,
        handleCancel: editing.handleCancel,
        handleCreate: editing.handleCreate,
        handleEdit: editing.handleEdit,
        handleDelete: editing.handleDelete,
        onConvertToPreserveTerm,
        onConvertToGlossary,
        tmCategories,
        saving: editing.saving,
    });

    const handleImport = (event, path, reload) => {
        handleImportFile({
            event,
            path,
            reload,
            isGlossary,
            setLastGlossaryAt,
            setLastMemoryAt,
        });
    };

    return {
        isGlossary,
        items,
        compactKey,
        compactTable,
        setCompactTable,
        columns,
        sortedItems: (editing.editingKey?.startsWith('__clone__') && editing.draft) ? [editing.draft, ...sorting.sortedItems] : sorting.sortedItems,
        sortKey: sorting.sortKey,
        sortDir: sorting.sortDir,
        toggleSort: sorting.toggleSort,
        selectedIds: selection.selectedIds,
        setSelectedIds: selection.setSelectedIds,
        handleSelectRow: selection.handleSelectRow,
        handleSelectAll: selection.handleSelectAll,
        handleRowClick: editing.handleEdit,
        handleExport,
        handleImport,
        handleCreate: editing.handleCreate,
        handleBatchConvert: batch.handleBatchConvert,
        handleBatchDelete: batch.handleBatchDelete,
        glossaryTotal,
        tmTotal,
        onSeed,
        onClearGlossary,
        onClearMemory,
    };
}
