import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { API_BASE } from '../../constants';
import { useTerms } from '../../hooks/useTerms';
import { DataTable } from '../common/DataTable';
import { buildTermsColumns } from './termsTabColumns.jsx';
import { TermsFiltersBar } from './TermsFiltersBar';
import { TermsImportDialog } from './TermsImportDialog';
import { TermsBatchActions } from './TermsBatchActions';
import { TermsVersionsPanel } from './TermsVersionsPanel';
import { buildMappingFromRows, detectConflict } from './termsTabHelpers.jsx';

export default function TermsTab() {
    const { t } = useTranslation();
    const {
        terms,
        categories,
        filters,
        setFilters,
        selectedIds,
        setSelectedIds,
        loading,
        form,
        setForm,
        editingId,
        setEditingId,
        preview,
        setPreview,
        upsert,
        resetForm,
        remove,
        batchUpdate,
        batchDelete,
        exportCsv,
        previewImport,
        importCsv,
    } = useTerms();

    const [importFile, setImportFile] = useState(null);
    const [mappingText, setMappingText] = useState('');
    const [versions, setVersions] = useState(null);
    const [batchCategory, setBatchCategory] = useState('');
    const [batchSource, setBatchSource] = useState('');
    const [isSyncing, setIsSyncing] = useState(false);
    const [importResult, setImportResult] = useState(null);
    const [mappingRows, setMappingRows] = useState([
        { from: '', to: 'term' },
        { from: '', to: 'category' },
        { from: '', to: 'languages' },
        { from: '', to: 'source' },
        { from: '', to: 'filename' },
        { from: '', to: 'created_by' },
    ]);
    const [errorMsg, setErrorMsg] = useState('');
    const [showImport, setShowImport] = useState(false);
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem('manage_table_compact_terms');
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });
    const [importStep, setImportStep] = useState(1);
    const [visibleCount, setVisibleCount] = useState(200);

    const [sortKey, setSortKey] = useState(null);
    const [sortDir, setSortDir] = useState('asc');

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir((p) => p === 'asc' ? 'desc' : 'asc');
        } else {
            setSortKey(key);
            setSortDir('asc');
        }
    };

    const sortedTerms = useMemo(() => {
        if (!terms) return [];
        const list = [...terms];
        if (!sortKey) return list;

        list.sort((a, b) => {
            const valA = a[sortKey];
            const valB = b[sortKey];
            const dir = sortDir === 'asc' ? 1 : -1;

            if (sortKey === 'priority') {
                return (Number(valA || 0) - Number(valB || 0)) * dir;
            }
            return String(valA || '').localeCompare(String(valB || ''), 'zh-Hant') * dir;
        });
        return list;
    }, [terms, sortKey, sortDir]);

    const visibleTerms = useMemo(() => sortedTerms.slice(0, visibleCount), [sortedTerms, visibleCount]);

    const startEdit = (item) => {
        setEditingId(item.id);
        setErrorMsg('');
        setForm({
            term: item.term || '',
            category_id: item.category_id || null,
            category_name: item.category_name || '',
            languages: item.languages || [{ lang_code: 'zh-TW', value: '' }],
            created_by: item.created_by || '',
            source: item.source || '',
            source_lang: item.source_lang || '',
            target_lang: item.target_lang || '',
            case_rule: item.case_rule || 'preserve',
            priority: item.priority ?? 5,
            filename: item.filename || '',
        });
    };

    const handlePreview = async () => {
        if (!importFile) return;
        const mapping = mappingText
            ? JSON.parse(mappingText)
            : buildMappingFromRows(mappingRows);
        await previewImport(importFile, mapping);
    };

    const handleImport = async () => {
        if (!importFile) return;
        const mapping = mappingText
            ? JSON.parse(mappingText)
            : buildMappingFromRows(mappingRows);
        const result = await importCsv(importFile, mapping);
        setImportResult(result);
        setPreview(null);
    };

    const loadVersions = async (termId) => {
        const res = await fetch(`${API_BASE}/api/terms/${termId}/versions`);
        const data = await res.json();
        setVersions({ termId, items: data.items || [] });
    };

    const handleUpsert = async () => {
        const conflict = detectConflict({ form, terms, editingId, t });
        if (conflict) {
            setErrorMsg(conflict);
            return;
        }
        setErrorMsg('');
        await upsert();
    };

    const handleFullSync = async () => {
        if (!window.confirm(t('manage.terms_tab.sync_confirm'))) return;
        setIsSyncing(true);
        try {
            const res = await fetch(`${API_BASE}/api/terms/sync-all`, { method: 'POST' });
            if (res.ok) {
                alert(t('manage.terms_tab.sync_complete'));
                setFilters((p) => ({ ...p, _refresh: Date.now() }));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsSyncing(false);
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

    const addMappingRow = () => {
        setMappingRows((prev) => [...prev, { from: '', to: '' }]);
    };

    const updateMappingRow = (index, key, value) => {
        setMappingRows((prev) => {
            const next = [...prev];
            next[index] = { ...next[index], [key]: value };
            return next;
        });
    };

    const removeMappingRow = (index) => {
        setMappingRows((prev) => prev.filter((_, i) => i !== index));
    };

    const columns = buildTermsColumns({
        t,
        categories,
        editingId,
        form,
        setForm,
        handleKeyDown,
        handleUpsert,
        resetForm,
        startEdit,
        loadVersions,
        remove,
    });

    return (
        <div className="flex flex-col h-full min-h-0 overflow-hidden px-1">
            <TermsFiltersBar
                t={t}
                filters={filters}
                setFilters={setFilters}
                categories={categories}
                isSyncing={isSyncing}
                handleFullSync={handleFullSync}
                errorMsg={errorMsg}
                exportCsv={exportCsv}
                onOpenImport={() => {
                    setShowImport(true);
                    setImportStep(1);
                }}
            />

            <TermsImportDialog
                t={t}
                show={showImport}
                onClose={() => setShowImport(false)}
                importStep={importStep}
                setImportStep={setImportStep}
                importFile={importFile}
                setImportFile={setImportFile}
                mappingRows={mappingRows}
                setMappingRows={setMappingRows}
                updateMappingRow={updateMappingRow}
                removeMappingRow={removeMappingRow}
                addMappingRow={addMappingRow}
                setMappingText={setMappingText}
                buildMappingFromRows={() => buildMappingFromRows(mappingRows)}
                handlePreview={handlePreview}
                handleImport={handleImport}
                preview={preview}
                importResult={importResult}
            />

            <TermsBatchActions
                t={t}
                categories={categories}
                selectedIds={selectedIds}
                batchCategory={batchCategory}
                setBatchCategory={setBatchCategory}
                batchSource={batchSource}
                setBatchSource={setBatchSource}
                batchUpdate={batchUpdate}
                batchDelete={batchDelete}
            />

            <div className="manage-scroll-area flex-1 pr-1 flex flex-col min-h-0">
                <DataTable
                    columns={columns}
                    data={visibleTerms}
                    rowKey="id"
                    selectedIds={selectedIds}
                    onSelectionChange={(ids) => setSelectedIds(ids)}
                    loading={loading}
                    storageKey="manage_terms_table_cols_v2"
                    compact={compactTable}
                    onCompactChange={(checked) => {
                        setCompactTable(checked);
                        try {
                            localStorage.setItem('manage_table_compact_terms', JSON.stringify(checked));
                        } catch { }
                    }}
                    sortKey={sortKey}
                    sortDir={sortDir}
                    onSort={toggleSort}
                    canLoadMore={visibleCount < sortedTerms.length}
                    totalCount={sortedTerms.length}
                    onLoadMore={() => setVisibleCount((prev) => prev + 200)}
                    emptyState={t('manage.terms_tab.loading')}
                    className="is-glossary"
                />

                <TermsVersionsPanel
                    t={t}
                    versions={versions}
                    onClose={() => setVersions(null)}
                />
            </div>
        </div>
    );
}
