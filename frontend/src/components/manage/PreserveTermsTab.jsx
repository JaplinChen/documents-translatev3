import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { usePreserveTerms } from '../../hooks/usePreserveTerms';
import { preserveTermsApi } from '../../services/api/preserve_terms';
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
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(200);
    const [editingField, setEditingField] = useState(null);
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
        setPage(1);
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
    const visibleTerms = useMemo(() => {
        const start = Math.max(0, (page - 1) * pageSize);
        return sortedTerms.slice(start, start + pageSize);
    }, [sortedTerms, page, pageSize]);
    const totalCount = filteredTerms ? filteredTerms.length : 0;

    const handleBatchDelete = async () => {
        if (!selectedIds.length) return;
        if (!window.confirm(t('manage.preserve.alerts.delete_confirm'))) return;
        try {
            await Promise.all(
                selectedIds.map((id) =>
                    preserveTermsApi.delete(String(id))
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
                    await preserveTermsApi.convertToGlossary({
                        id: term.id,
                        target_lang: targetLang || 'zh-TW',
                        priority: 10,
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

    const startEdit = (item, fieldKey = 'term') => {
        if (!item) return;
        setEditingId(item.id);
        setEditingField(fieldKey);
        setEditForm({
            term: item.term,
            category: item.category,
            case_sensitive: item.case_sensitive,
        });
    };

    const handleRowClick = (item, colKey) => {
        const nextField = colKey || 'term';
        if (editingId !== item.id) {
            startEdit(item, nextField);
            return;
        }
        setEditingField(nextField);
    };

    React.useEffect(() => {
        if (!editingId) setEditingField(null);
    }, [editingId]);

    const columns = buildPreserveColumns({
        t,
        editingId,
        editingField,
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
                    totalCount={totalCount}
                    page={page}
                    pageSize={pageSize}
                    onPageChange={(nextPage) => setPage(nextPage)}
                    onPageSizeChange={(nextSize) => {
                        setPageSize(nextSize);
                        setPage(1);
                    }}
                    onRowClick={handleRowClick}
                />
            </div>
        </div>
    );
}
