import React, { useEffect, useMemo, useRef, useState } from 'react';
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
        totalCount,
        setPagination,
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
    const [editingField, setEditingField] = useState(null);
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem('manage_table_compact_terms');
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });
    const [importStep, setImportStep] = useState(1);
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(200);
    const tableScrollRef = useRef(null);
    const sourceLangRef = useRef('');
    const targetLangRef = useRef('');

    const [sortKey, setSortKey] = useState(null);
    const [sortDir, setSortDir] = useState('asc');
    const langListId = 'terms-lang-options';
    const recentLangsKey = 'manage_terms_recent_langs';
    const commonLangs = useMemo(() => ([
        'zh-TW',
        'zh-CN',
        'en',
        'vi',
        'ja',
        'ko',
        'th',
        'id',
        'ms',
        'de',
        'fr',
        'es',
    ]), []);
    const [recentLangs, setRecentLangs] = useState(() => {
        try {
            const raw = localStorage.getItem(recentLangsKey);
            const parsed = raw ? JSON.parse(raw) : [];
            return Array.isArray(parsed) ? parsed : [];
        } catch {
            return [];
        }
    });

    const rememberLang = (lang) => {
        if (!lang) return;
        setRecentLangs((prev) => {
            const next = [lang, ...prev.filter((item) => item !== lang)].slice(0, 6);
            try {
                localStorage.setItem(recentLangsKey, JSON.stringify(next));
            } catch { }
            return next;
        });
    };

    const langOptions = useMemo(() => {
        const set = new Set();
        commonLangs.forEach((lang) => set.add(lang));
        (terms || []).forEach((item) => {
            if (item?.source_lang) set.add(item.source_lang);
            if (item?.target_lang) set.add(item.target_lang);
            (item?.languages || []).forEach((lang) => {
                if (lang?.lang_code) set.add(lang.lang_code);
            });
        });
        (form?.languages || []).forEach((lang) => {
            if (lang?.lang_code) set.add(lang.lang_code);
        });
        return Array.from(set).sort((a, b) => String(a).localeCompare(String(b), 'zh-Hant'));
    }, [terms, form?.languages, commonLangs]);

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

    useEffect(() => {
        setPage(1);
    }, [filters]);

    useEffect(() => {
        const offset = Math.max(0, (page - 1) * pageSize);
        setPagination({ limit: pageSize, offset });
    }, [page, pageSize, setPagination]);

    const startEdit = (item, fieldKey = 'term') => {
        sourceLangRef.current = item.source_lang || '';
        targetLangRef.current = item.target_lang || '';
        const normalizedLanguages = (item.languages || []).map((lang) => ({
            ...lang,
            lang_code: item.target_lang || lang.lang_code || '',
        }));
        setEditingId(item.id);
        setErrorMsg('');
        setEditingField(fieldKey);
        setForm({
            term: item.term || '',
            category_id: item.category_id || null,
            category_name: item.category_name || '',
            languages: normalizedLanguages.length
                ? normalizedLanguages
                : [{ lang_code: item.target_lang || 'zh-TW', value: '' }],
            created_by: item.created_by || '',
            source: item.source || '',
            source_lang: item.source_lang || '',
            target_lang: item.target_lang || '',
            case_rule: item.case_rule || 'preserve',
            priority: item.priority ?? 5,
            filename: item.filename || '',
        });
    };

    const handleRowClick = (item, colKey) => {
        if (!item) return;
        const nextField = colKey || 'term';
        if (editingId !== item.id) {
            startEdit(item, nextField);
            return;
        }
        setEditingField(nextField);
    };

    useEffect(() => {
        if (!editingId) setEditingField(null);
    }, [editingId]);

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
        setForm((prev) => ({
            ...prev,
            source_lang: prev.source_lang || sourceLangRef.current || '',
            target_lang: prev.target_lang || targetLangRef.current || '',
        }));
        const prevScrollTop = tableScrollRef.current?.scrollTop ?? 0;
        setErrorMsg('');
        await upsert();
        requestAnimationFrame(() => {
            if (tableScrollRef.current) {
                tableScrollRef.current.scrollTop = prevScrollTop;
            }
        });
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
        editingField,
        form,
        setForm,
        handleKeyDown,
        handleUpsert,
        resetForm,
        startEdit,
        loadVersions,
        remove,
        langListId,
        commonLangs,
        recentLangs,
        langOptions,
        rememberLang,
        onSourceLangChange: (next) => {
            sourceLangRef.current = next;
            setForm((p) => ({ ...p, source_lang: next }));
        },
        onTargetLangChange: (next) => {
            targetLangRef.current = next;
            setForm((p) => {
                const nextLangs = (p.languages || []).map((lang) => ({
                    ...lang,
                    lang_code: next,
                }));
                return {
                    ...p,
                    target_lang: next,
                    languages: nextLangs.length ? nextLangs : [{ lang_code: next, value: '' }],
                };
            });
        },
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
            <datalist id={langListId}>
                {langOptions.map((lang) => (
                    <option key={`lang-opt-${lang}`} value={lang} />
                ))}
            </datalist>

            <div className="manage-scroll-area flex-1 pr-1 flex flex-col min-h-0">
                <DataTable
                    columns={columns}
                    data={sortedTerms}
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
                    totalCount={totalCount}
                    page={page}
                    pageSize={pageSize}
                    onPageChange={(nextPage) => setPage(nextPage)}
                    onPageSizeChange={(nextSize) => {
                        setPageSize(nextSize);
                        setPage(1);
                    }}
                    emptyState={t('manage.terms_tab.loading')}
                    className="is-glossary"
                    onRowClick={handleRowClick}
                    scrollRef={tableScrollRef}
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
