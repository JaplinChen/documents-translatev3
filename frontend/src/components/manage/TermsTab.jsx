import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { X } from "lucide-react";
import { CategoryPill } from "./CategoryPill";
import { API_BASE } from "../../constants";
import { useTerms } from "../../hooks/useTerms";
import { DataTable } from "../common/DataTable";

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
    const [mappingText, setMappingText] = useState("");
    const [versions, setVersions] = useState(null);
    const [batchCategory, setBatchCategory] = useState("");
    const [batchSource, setBatchSource] = useState("");
    const [isSyncing, setIsSyncing] = useState(false);
    const [importResult, setImportResult] = useState(null);
    const [mappingRows, setMappingRows] = useState([
        { from: "", to: "term" },
        { from: "", to: "category" },
        { from: "", to: "languages" },
        { from: "", to: "source" },
        { from: "", to: "filename" },
        { from: "", to: "created_by" },
    ]);
    const [errorMsg, setErrorMsg] = useState("");
    const [showImport, setShowImport] = useState(false);
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem("manage_table_compact_terms");
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });
    const [importStep, setImportStep] = useState(1);
    const [visibleCount, setVisibleCount] = useState(200);

    // Sort state
    const [sortKey, setSortKey] = useState(null);
    const [sortDir, setSortDir] = useState("asc");

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir(p => p === "asc" ? "desc" : "asc");
        } else {
            setSortKey(key);
            setSortDir("asc");
        }
    };

    const sortedTerms = React.useMemo(() => {
        if (!terms) return [];
        const list = [...terms];
        if (!sortKey) return list;

        list.sort((a, b) => {
            const valA = a[sortKey];
            const valB = b[sortKey];
            const dir = sortDir === "asc" ? 1 : -1;

            if (sortKey === "priority") {
                return (Number(valA || 0) - Number(valB || 0)) * dir;
            }
            return String(valA || "").localeCompare(String(valB || ""), "zh-Hant") * dir;
        });
        return list;
    }, [terms, sortKey, sortDir]);

    const visibleTerms = React.useMemo(() => sortedTerms.slice(0, visibleCount), [sortedTerms, visibleCount]);

    const toggleSelect = (ids) => {
        setSelectedIds(ids);
    };

    const startEdit = (item) => {
        setEditingId(item.id);
        setErrorMsg("");
        setForm({
            term: item.term || "",
            category_id: item.category_id || null,
            category_name: item.category_name || "",
            languages: item.languages || [{ lang_code: "zh-TW", value: "" }],
            created_by: item.created_by || "",
            source: item.source || "",
            source_lang: item.source_lang || "",
            target_lang: item.target_lang || "",
            case_rule: item.case_rule || "preserve",
            priority: item.priority ?? 5,
            filename: item.filename || ""
        });
    };

    const handlePreview = async () => {
        if (!importFile) return;
        const mapping = mappingText
            ? JSON.parse(mappingText)
            : buildMappingFromRows();
        await previewImport(importFile, mapping);
    };

    const handleImport = async () => {
        if (!importFile) return;
        const mapping = mappingText
            ? JSON.parse(mappingText)
            : buildMappingFromRows();
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
        const conflict = detectConflict();
        if (conflict) {
            setErrorMsg(conflict);
            return;
        }
        setErrorMsg("");
        await upsert();
    };

    const handleFullSync = async () => {
        if (!window.confirm(t("manage.terms_tab.sync_confirm"))) return;
        setIsSyncing(true);
        try {
            const res = await fetch(`${API_BASE}/api/terms/sync-all`, { method: "POST" });
            if (res.ok) {
                alert(t("manage.terms_tab.sync_complete"));
                setFilters(p => ({ ...p, _refresh: Date.now() }));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsSyncing(false);
        }
    };

    const handleKeyDown = (e, saveFn, cancelFn) => {
        if (e.key === "Enter") {
            e.preventDefault();
            saveFn();
        } else if (e.key === "Escape") {
            e.preventDefault();
            cancelFn();
        }
    };

    function addMappingRow() {
        setMappingRows((prev) => [...prev, { from: "", to: "" }]);
    }

    function updateMappingRow(index, key, value) {
        setMappingRows((prev) => {
            const next = [...prev];
            next[index] = { ...next[index], [key]: value };
            return next;
        });
    }

    function removeMappingRow(index) {
        setMappingRows((prev) => prev.filter((_, i) => i !== index));
    }

    function buildMappingFromRows() {
        const mapping = {};
        mappingRows.forEach((row) => {
            const from = (row.from || "").trim();
            const to = (row.to || "").trim();
            if (from && to) mapping[from] = to;
        });
        return mapping;
    }

    function renderDiff(diff) {
        if (!diff || !diff.before || !diff.after) {
            return <div className="text-xs text-slate-400">{t("manage.terms_tab.no_diff")}</div>;
        }
        const before = diff.before || {};
        const after = diff.after || {};
        const fields = ["term", "category_name", "source_lang", "target_lang", "priority", "source", "case_rule", "filename"];
        return (
            <div className="space-y-1">
                {fields.map((field) => {
                    const b = before[field];
                    const a = after[field];
                    if (JSON.stringify(b) === JSON.stringify(a)) return null;
                    return (
                        <div key={field} className="flex gap-2">
                            <span className="w-24 text-slate-400 font-mono text-[10px]">{field}</span>
                            <span className="line-through text-rose-500">{String(b ?? "")}</span>
                            <span className="text-emerald-600">{String(a ?? "")}</span>
                        </div>
                    );
                })}
            </div>
        );
    }

    function detectConflict() {
        const normalize = (text) => (text || "").trim().toLowerCase();
        const termValue = normalize(form.term);
        if (!termValue) return t("manage.terms_tab.validation.term_required");
        const existing = terms.filter((t) => t.id !== editingId);
        const termSet = new Set(existing.map((t) => normalize(t.term)));
        if (termSet.has(termValue)) {
            return t("manage.terms_tab.validation.term_exists");
        }
        return "";
    }

    function formatLanguages(langs) {
        return (langs || []).map((l) => `${l.lang_code}:${l.value}`).join(" / ");
    }

    function parseLanguages(text) {
        return (text || "")
            .split("/")
            .map((raw) => raw.trim())
            .filter(Boolean)
            .map((chunk) => {
                const [code, ...rest] = chunk.split(":");
                const value = rest.join(":").trim();
                if (!code) return null;
                return { lang_code: code.trim(), value };
            })
            .filter(Boolean);
    }

    // Define columns for DataTable
    const columns = [
        {
            key: "source_lang",
            label: t("manage.table.source_lang"),
            width: "80px",
            sortable: true,
            cellClass: "text-slate-500 font-mono text-[11px]",
            render: (value, item) => editingId === item.id ? (
                <input
                    className="data-input !bg-white !border-blue-200 font-bold w-full"
                    value={form.source_lang || ""}
                    onChange={(e) => setForm((p) => ({ ...p, source_lang: e.target.value }))}
                    onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                    onClick={(e) => e.stopPropagation()}
                />
            ) : (value || "")
        },
        {
            key: "target_lang",
            label: t("manage.table.target_lang"),
            width: "80px",
            sortable: true,
            cellClass: "text-slate-500 font-mono text-[11px]",
            render: (value, item) => editingId === item.id ? (
                <input
                    className="data-input !bg-white !border-blue-200 font-bold w-full"
                    value={form.target_lang || ""}
                    onChange={(e) => setForm((p) => ({ ...p, target_lang: e.target.value }))}
                    onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                    onClick={(e) => e.stopPropagation()}
                />
            ) : (value || "")
        },
        {
            key: "term",
            label: t("manage.terms_tab.columns.term"),
            width: "1.2fr",
            sortable: true,
            render: (value, item) => editingId === item.id ? (
                <input
                    className="data-input !bg-white !border-blue-200 font-bold w-full"
                    value={form.term || ""}
                    onChange={(e) => setForm((p) => ({ ...p, term: e.target.value }))}
                    onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                />
            ) : value
        },
        {
            key: "languages",
            label: t("manage.terms_tab.columns.languages"),
            width: "1.2fr",
            render: (value, item) => editingId === item.id ? (
                <input
                    className="data-input !bg-white !border-blue-200 font-bold w-full"
                    value={formatLanguages(form.languages)}
                    onChange={(e) => setForm((p) => ({ ...p, languages: parseLanguages(e.target.value) }))}
                    placeholder="zh-TW:值 / en:Value"
                    onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                    onClick={(e) => e.stopPropagation()}
                />
            ) : ((value || []).map((l) => l.value).join(" / "))
        },
        {
            key: "priority",
            label: t("manage.table.priority"),
            width: "60px",
            sortable: true,
            cellClass: "text-center",
            render: (value, item) => editingId === item.id ? (
                <input
                    type="number"
                    className="data-input !bg-white !border-blue-200 font-bold !text-center w-full"
                    value={form.priority || 0}
                    onChange={(e) => setForm((p) => ({ ...p, priority: parseInt(e.target.value) || 0 }))}
                    onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                    onClick={(e) => e.stopPropagation()}
                />
            ) : (
                <span className="text-slate-400 font-mono text-[11px]">{value ?? 0}</span>
            )
        },
        {
            key: "source",
            label: t("manage.terms_tab.columns.source"),
            width: "80px",
            sortable: true,
            render: (value, item) => editingId === item.id ? (
                <select
                    className="data-input !bg-white !border-blue-200 font-bold !text-[12px] w-full"
                    value={form.source || ""}
                    onChange={(e) => setForm((p) => ({ ...p, source: e.target.value }))}
                    onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                    onClick={(e) => e.stopPropagation()}
                >
                    <option value="">{t("manage.terms_tab.columns.source")}</option>
                    <option value="reference">{t("manage.terms_tab.filter_source_reference")}</option>
                    <option value="terminology">{t("manage.terms_tab.filter_source_terminology")}</option>
                    <option value="manual">{t("manage.terms_tab.filter_source_manual")}</option>
                </select>
            ) : (
                value && (
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${value === "reference" ? "bg-blue-50 text-blue-600 border border-blue-100" :
                        value === "terminology" ? "bg-purple-50 text-purple-600 border border-purple-100" :
                            "bg-slate-50 text-slate-500 border border-slate-100"
                        }`}>
                        {value === "reference" ? t("manage.terms_tab.source_labels.reference") :
                            value === "terminology" ? t("manage.terms_tab.source_labels.terminology") : t("manage.terms_tab.source_labels.manual")}
                    </span>
                )
            )
        },
        {
            key: "case_rule",
            label: t("manage.table.case"),
            width: "80px",
            sortable: true,
            render: (value, item) => editingId === item.id ? (
                <select
                    className="data-input !bg-white !border-blue-200 font-bold !text-[12px] w-full"
                    value={form.case_rule || "preserve"}
                    onChange={(e) => setForm((p) => ({ ...p, case_rule: e.target.value }))}
                    onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                    onClick={(e) => e.stopPropagation()}
                >
                    <option value="preserve">{t("manage.terms_tab.case_rules.preserve")}</option>
                    <option value="lowercase">{t("manage.terms_tab.case_rules.lowercase")}</option>
                    <option value="uppercase">{t("manage.terms_tab.case_rules.uppercase")}</option>
                </select>
            ) : (
                <span className="text-[10px] text-slate-500">{t(`manage.terms_tab.case_rules.${value || "preserve"}`)}</span>
            )
        },
        {
            key: "category",
            label: t("manage.terms_tab.columns.category"),
            width: "100px",
            sortable: true,
            render: (value, item) => editingId === item.id ? (
                <select
                    className="data-input !bg-white !border-blue-200 font-bold !text-[12px] w-full"
                    value={form.category_id || ""}
                    onChange={(e) => setForm((p) => ({ ...p, category_id: e.target.value ? parseInt(e.target.value) : null }))}
                    onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                    onClick={(e) => e.stopPropagation()}
                >
                    <option value="">{t("manage.terms_tab.columns.category")}</option>
                    {categories.map((c) => (
                        <option key={`cat-edit-${c.id}`} value={c.id}>{c.name}</option>
                    ))}
                </select>
            ) : (
                <CategoryPill name={item.category_name} />
            )
        },
        {
            key: "filename",
            label: t("manage.terms_tab.columns.filename"),
            width: "120px",
            sortable: true,
            cellClass: "text-slate-500 font-mono text-[11px] truncate",
            render: (value) => <span title={value}>{value || ""}</span>
        },
        {
            key: "created_by",
            label: t("manage.terms_tab.columns.created_by"),
            width: "90px",
            sortable: true,
            cellClass: "text-slate-400 text-[11px]",
            render: (value) => value || ""
        },
        {
            key: "actions",
            label: t("manage.terms_tab.columns.actions"),
            width: "140px",
            render: (_, item) => (
                <div className="flex justify-end gap-1">
                    {editingId === item.id ? (
                        <>
                            <button className="action-btn-sm success" onClick={(e) => { e.stopPropagation(); handleUpsert(); }} title={t("manage.actions.save")}>
                                <img src="https://emojicdn.elk.sh/✅?style=apple" className="w-5 h-5 object-contain" alt="Save" />
                            </button>
                            <button className="action-btn-sm" onClick={(e) => { e.stopPropagation(); resetForm(); }} title={t("manage.actions.cancel")}>
                                <img src="https://emojicdn.elk.sh/❌?style=apple" className="w-5 h-5 object-contain" alt="Cancel" />
                            </button>
                        </>
                    ) : (
                        <>
                            <button className="action-btn-sm" onClick={(e) => { e.stopPropagation(); startEdit(item); }} title={t("manage.actions.edit")}>
                                <img src="https://emojicdn.elk.sh/✏️?style=apple" className="w-5 h-5 object-contain" alt="Edit" />
                            </button>
                            <button className="action-btn-sm" onClick={(e) => { e.stopPropagation(); loadVersions(item.id); }} title={t("manage.terms_tab.version_btn")}>
                                <img src="https://emojicdn.elk.sh/📜?style=apple" className="w-5 h-5 object-contain" alt="Version" />
                            </button>
                            <button className="action-btn-sm danger" onClick={(e) => { e.stopPropagation(); remove(item.id); }} title={t("manage.actions.delete")}>
                                <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                            </button>
                        </>
                    )}
                </div>
            )
        }
    ];

    return (
        <div className="flex flex-col h-full min-h-0 overflow-hidden px-1">
            <div className="action-row flex items-center justify-between gap-3 bg-slate-50/70 border border-slate-200/70 rounded-2xl px-4 py-3 mb-4 shrink-0">
                <div className="flex flex-wrap gap-2 items-center">
                    <input
                        className="text-input w-52 compact"
                        placeholder={t("manage.terms_tab.search_placeholder")}
                        value={filters.q}
                        onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value }))}
                        onKeyDown={(e) => e.key === "Enter" && setFilters((p) => ({ ...p, _refresh: Date.now() }))}
                    />
                    <select
                        className="select-input w-36 compact"
                        value={filters.category_id}
                        onChange={(e) => setFilters((p) => ({ ...p, category_id: e.target.value }))}
                    >
                        <option value="">{t("manage.terms_tab.filter_category_all")}</option>
                        {categories.map((c) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>
                    <select
                        className="select-input w-28 compact"
                        value={filters.source}
                        onChange={(e) => setFilters((p) => ({ ...p, source: e.target.value }))}
                    >
                        <option value="">{t("manage.terms_tab.filter_source_all")}</option>
                        <option value="reference">{t("manage.terms_tab.filter_source_reference")}</option>
                        <option value="terminology">{t("manage.terms_tab.filter_source_terminology")}</option>
                        <option value="manual">{t("manage.terms_tab.filter_source_manual")}</option>
                    </select>
                    <button
                        className={`btn ghost compact whitespace-nowrap ${isSyncing ? "loading" : ""}`}
                        onClick={handleFullSync}
                        disabled={isSyncing}
                    >
                        {isSyncing ? t("manage.terms_tab.syncing") : t("manage.terms_tab.sync_data")}
                    </button>
                    {errorMsg && <div className="text-xs text-red-500 font-bold ml-2">{errorMsg}</div>}
                </div>
                <div className="flex items-center gap-2">

                    <div className="flex gap-2 items-center">
                        <button className="btn ghost compact" type="button" onClick={exportCsv}>{t("manage.actions.export_csv")}</button>
                        <button className="btn ghost compact" type="button" onClick={() => {
                            setShowImport(true);
                            setImportStep(1);
                        }}>
                            {t("manage.actions.import_csv")}
                        </button>
                    </div>
                </div>
            </div>

            {showImport && (
                <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/20">
                    <div className="w-[720px] max-h-[80vh] overflow-auto bg-white rounded-2xl border border-slate-200 shadow-xl p-5">
                        {/* Import Dialog Content */}
                        <div className="flex items-center justify-between mb-3">
                            <div className="text-sm font-bold text-slate-700">{t("manage.terms_tab.import.title", { step: importStep })}</div>
                            <button className="btn ghost compact" type="button" onClick={() => setShowImport(false)}>{t("manage.terms_tab.import.close")}</button>
                        </div>
                        {importStep === 1 && (
                            <div className="space-y-3">
                                <label className="btn ghost w-fit">
                                    {t("manage.terms_tab.import.select_csv")}
                                    <input type="file" accept=".csv" className="hidden-input" onChange={(e) => setImportFile(e.target.files?.[0] || null)} />
                                </label>
                                <div className="text-xs text-slate-500">{t("manage.terms_tab.import.select_hint")}</div>
                                <button className="btn primary" type="button" onClick={() => setImportStep(2)} disabled={!importFile}>{t("manage.terms_tab.import.next")}</button>
                            </div>
                        )}
                        {importStep === 2 && (
                            <div className="space-y-3">
                                <div className="text-xs text-slate-500">{t("manage.terms_tab.import.mapping_hint")}</div>
                                <div className="grid grid-cols-12 gap-2 max-h-48 overflow-auto pr-1">
                                    {mappingRows.map((row, idx) => (
                                        <React.Fragment key={`${row.to}-${idx}`}>
                                            <input
                                                className="text-input col-span-5"
                                                placeholder={t("manage.terms_tab.import.csv_column")}
                                                value={row.from}
                                                onChange={(e) => updateMappingRow(idx, "from", e.target.value)}
                                            />
                                            <input
                                                className="text-input col-span-5"
                                                placeholder={t("manage.terms_tab.import.system_column")}
                                                value={row.to}
                                                onChange={(e) => updateMappingRow(idx, "to", e.target.value)}
                                            />
                                            <button
                                                className="btn ghost compact col-span-2"
                                                type="button"
                                                onClick={() => removeMappingRow(idx)}
                                            >
                                                {t("manage.actions.delete")}
                                            </button>
                                        </React.Fragment>
                                    ))}
                                </div>
                                <div className="flex gap-2">
                                    <button className="btn ghost compact" type="button" onClick={addMappingRow}>{t("manage.terms_tab.import.add_mapping")}</button>
                                    <button className="btn ghost compact" type="button" onClick={() => setMappingText(JSON.stringify(buildMappingFromRows()))}>{t("manage.terms_tab.import.apply_json")}</button>
                                    <button className="btn ghost compact" type="button" onClick={() => setMappingRows([])}>{t("manage.terms_tab.import.clear_mapping")}</button>
                                </div>
                                <div className="flex gap-2">
                                    <button className="btn ghost" type="button" onClick={() => setImportStep(1)}>{t("manage.terms_tab.import.prev")}</button>
                                    <button className="btn primary" type="button" onClick={async () => {
                                        await handlePreview();
                                        setImportStep(3);
                                    }}>{t("manage.terms_tab.import.next")}</button>
                                </div>
                            </div>
                        )}
                        {importStep === 3 && (
                            <div className="space-y-3">
                                <div className="text-xs text-slate-500">{t("manage.terms_tab.import.preview_result")}</div>
                                {preview?.summary && (
                                    <div className="text-xs text-slate-600">
                                        {t("manage.terms_tab.import.summary", { total: preview.summary.total, valid: preview.summary.valid, invalid: preview.summary.invalid })}
                                    </div>
                                )}
                                <div className="flex gap-2">
                                    <button className="btn ghost" type="button" onClick={() => setImportStep(2)}>{t("manage.terms_tab.import.prev")}</button>
                                    <button className="btn primary" type="button" onClick={handleImport}>{t("manage.terms_tab.import.confirm_import")}</button>
                                </div>
                                {importResult && (
                                    <div className="text-xs text-slate-600">
                                        {t("manage.terms_tab.import.import_complete", { imported: importResult.imported, failed: importResult.failed?.length || 0 })}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {selectedIds.length > 0 && (
                <div className="batch-actions flex flex-wrap gap-2 mt-3">
                    <select className="select-input w-36 compact" value={batchCategory} onChange={(e) => setBatchCategory(e.target.value)}>
                        <option value="">{t("manage.terms_tab.batch.category")}</option>
                        {categories.map((c) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>
                    <button className="btn ghost compact" onClick={() => batchUpdate({ category_id: batchCategory })} disabled={!batchCategory}>{t("manage.terms_tab.batch.apply_category")}</button>
                    <select className="select-input w-28 compact" value={batchSource} onChange={(e) => setBatchSource(e.target.value)}>
                        <option value="">{t("manage.terms_tab.batch.source")}</option>
                        <option value="reference">{t("manage.terms_tab.filter_source_reference")}</option>
                        <option value="terminology">{t("manage.terms_tab.filter_source_terminology")}</option>
                        <option value="manual">{t("manage.terms_tab.filter_source_manual")}</option>
                    </select>
                    <button className="btn ghost compact" onClick={() => batchUpdate({ source: batchSource })} disabled={!batchSource}>{t("manage.terms_tab.batch.apply_source")}</button>
                    <button className="btn ghost compact !text-red-500" onClick={() => {
                        if (!window.confirm(t("manage.terms_tab.batch.delete_confirm", { count: selectedIds.length }))) return;
                        batchDelete();
                    }}>{t("manage.terms_tab.batch.delete")}</button>
                </div>
            )}

            <div className="manage-scroll-area flex-1 pr-1 flex flex-col min-h-0">
                <DataTable
                    columns={columns}
                    data={visibleTerms}
                    rowKey="id"
                    selectedIds={selectedIds}
                    onSelectionChange={toggleSelect}
                    loading={loading}
                    storageKey="manage_terms_table_cols_v2"
                    compact={compactTable}
                    onCompactChange={(checked) => {
                        setCompactTable(checked);
                        try {
                            localStorage.setItem("manage_table_compact_terms", JSON.stringify(checked));
                        } catch { }
                    }}
                    sortKey={sortKey}
                    sortDir={sortDir}
                    onSort={toggleSort}
                    canLoadMore={visibleCount < sortedTerms.length}
                    totalCount={sortedTerms.length}
                    onLoadMore={() => setVisibleCount(prev => prev + 200)}
                    emptyState={t("manage.terms_tab.loading")}
                    className="is-glossary"
                />

                {versions && (
                    <div className="mt-3 p-3 border border-slate-200 rounded-lg bg-slate-50/50">
                        <div className="flex items-center justify-between mb-2">
                            <div className="text-sm font-bold">{t("manage.terms_tab.version.title")}</div>
                            <button className="btn ghost compact" onClick={() => setVersions(null)}>{t("manage.terms_tab.import.close")}</button>
                        </div>
                        <div className="space-y-2 text-xs text-slate-600">
                            {versions.items.length === 0 && <div>{t("manage.terms_tab.version.empty")}</div>}
                            {versions.items.map((v) => (
                                <div key={v.id} className="p-2 rounded bg-white border border-slate-200 shadow-sm">
                                    <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                                        <span>{t("manage.terms_tab.version.time")}：{v.created_at}</span>
                                        <span>{t("manage.terms_tab.version.operator")}：{v.created_by || "-"}</span>
                                    </div>
                                    <div className="mt-1">
                                        {renderDiff(v.diff)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
