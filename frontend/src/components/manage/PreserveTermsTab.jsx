import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { usePreserveTerms } from '../../hooks/usePreserveTerms';
import { API_BASE } from '../../constants';
import { useUIStore } from '../../store/useUIStore';
import { useSettingsStore } from '../../store/useSettingsStore';
import { DataTable } from '../common/DataTable';
import { buildPreserveColumns } from './preserveTabColumns.jsx';
import { getCategoryLabel, sortPreserveTerms } from './preserveTabHelpers';
import { PreserveFiltersBar } from './PreserveFiltersBar';
import { PreserveBatchBar } from './PreserveBatchBar';

export default function PreserveTermsTab({ onClose }) {
    const { t } = useTranslation();
    const targetLang = useUIStore((state) => state.targetLang);
    const setLastGlossaryAt = useUIStore((state) => state.setLastGlossaryAt);
    const correctionFillColor = useSettingsStore((state) => state.correction.fillColor);
    const {
        filteredTerms,
        loading,
        filterText,
        setFilterText,
        filterCategory,
        setFilterCategory,
        editingId,
        setEditingId,
        editForm,
        setEditForm,
        newTerm,
        setNewTerm,
        categories,
        handleAdd,
        handleDelete,
        handleUpdate,
        handleExport,
        handleImport,
        handleConvertToGlossary,
        refreshTerms,
    } = usePreserveTerms();

    const [selectedIds, setSelectedIds] = useState([]);
    const [visibleCount, setVisibleCount] = useState(200);
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem('manage_table_compact_preserve');
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

    const [sortKey, setSortKey] = useState(null);
    const [sortDir, setSortDir] = useState('asc');

    React.useEffect(() => {
        setVisibleCount(200);
    }, [filterText, filterCategory]);

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
        } else {
            setSortKey(key);
            setSortDir('asc');
        }
    };

    const sortedTerms = useMemo(() => sortPreserveTerms({ terms: filteredTerms, sortKey, sortDir }), [filteredTerms, sortKey, sortDir]);
    const visibleTerms = useMemo(() => sortedTerms.slice(0, visibleCount), [sortedTerms, visibleCount]);
    const totalCount = filteredTerms ? filteredTerms.length : 0;
    const shownCount = visibleTerms.length;

    const handleBatchDelete = async () => {
        if (!selectedIds.length) return;
        if (!window.confirm(t('manage.preserve.alerts.delete_confirm'))) return;
        try {
            await Promise.all(
                selectedIds.map((id) =>
                    fetch(`${API_BASE}/api/preserve-terms/${id}`, {
                        method: 'DELETE',
                    })
                )
            );
            setSelectedIds([]);
            refreshTerms();
        } catch (err) {
            console.error(err);
        }
    };

    const handleBatchConvertToGlossary = async () => {
        if (!selectedIds.length) return;
        if (!window.confirm(t('manage.preserve.alerts.batch_convert_confirm'))) return;

        try {
            setLastGlossaryAt(Date.now());
            await Promise.all(
                selectedIds.map(async (id) => {
                    const term = filteredTerms.find((item) => item.id === id);
                    if (!term) return;
                    await fetch(`${API_BASE}/api/preserve-terms/convert-to-glossary`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id: term.id,
                            target_lang: targetLang || 'zh-TW',
                            priority: 10,
                        }),
                    });
                })
            );
            setSelectedIds([]);
            refreshTerms();
        } catch (err) {
            console.error(err);
        }
    };

    const handleKeyDown = (e, saveFn, cancelFn) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveFn();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelFn();
        }
    };

    const columns = buildPreserveColumns({
        t,
        editingId,
        editForm,
        setEditForm,
        setEditingId,
        handleKeyDown,
        handleUpdate,
        handleAdd,
        handleConvertToGlossary,
        handleDelete,
        categories,
    });

    return (
        <div className="flex flex-col flex-1 min-h-0 overflow-hidden px-1">
            <PreserveFiltersBar
                t={t}
                filterText={filterText}
                setFilterText={setFilterText}
                filterCategory={filterCategory}
                setFilterCategory={setFilterCategory}
                categories={categories}
                handleAdd={handleAdd}
                handleExport={handleExport}
                handleImport={handleImport}
            />

            <div className="manage-toolbar flex items-center gap-2 mb-2">
                <PreserveBatchBar
                    t={t}
                    selectedIds={selectedIds}
                    handleBatchConvertToGlossary={handleBatchConvertToGlossary}
                    handleBatchDelete={handleBatchDelete}
                />
            </div>

            <div className="manage-scroll-area flex-1 pr-1 flex flex-col min-h-0">
                <DataTable
                    columns={columns}
                    data={visibleTerms}
                    rowKey="id"
                    selectedIds={selectedIds}
                    onSelectionChange={setSelectedIds}
                    sortKey={sortKey}
                    sortDir={sortDir}
                    onSort={toggleSort}
                    storageKey="manage_preserve_table_cols"
                    compact={compactTable}
                    onCompactChange={(checked) => {
                        setCompactTable(checked);
                        try {
                            localStorage.setItem('manage_table_compact_preserve', JSON.stringify(checked));
                        } catch { }
                    }}
                    highlightColor={correctionFillColor}
                    emptyState={
                        <div className="flex-grow flex flex-col items-center justify-center p-12 text-slate-300">
                            <p className="text-lg font-bold">
                                {filterText || filterCategory !== 'all'
                                    ? t('manage.preserve.no_results')
                                    : t('manage.preserve.empty')}
                            </p>
                        </div>
                    }
                    className="is-tm"
                    canLoadMore={shownCount < totalCount}
                    totalCount={totalCount}
                    onLoadMore={() => setVisibleCount((prev) => prev + 200)}
                />
            </div>
        </div>
    );
}
