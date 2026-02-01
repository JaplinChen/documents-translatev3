import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { X } from "lucide-react";
import { CategoryPill } from "./CategoryPill";
import { API_BASE } from "../../constants";
import { useTerms } from "../../hooks/useTerms";
import { createPortal } from "react-dom";

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
    const [compactTable, setCompactTable] = useState(false);
    const [showColPanel, setShowColPanel] = useState(false);
    const [importStep, setImportStep] = useState(1);
    const [colWidths, setColWidths] = useState(() => {
        try {
            const saved = localStorage.getItem("manage_terms_table_cols_v2");
            return saved ? JSON.parse(saved) : {};
        } catch {
            return {};
        }
    });
    const resizingRef = useRef(null);
    const colBtnRef = useRef(null);
    const [visibleCols, setVisibleCols] = useState(() => {
        try {
            const saved = localStorage.getItem("terms_visible_cols_v2");
            return saved
                ? JSON.parse(saved)
                : {
                    source_lang: true,
                    target_lang: true,
                    term: true,
                    languages: true,
                    priority: true,
                    source: true,
                    case_rule: true,
                    category: true,
                    filename: true,
                    created_by: true,
                };
        } catch {
            return {
                source_lang: true,
                target_lang: true,
                term: true,
                languages: true,
                priority: true,
                source: true,
                case_rule: true,
                category: true,
                filename: true,
                created_by: true,
            };
        }
    });

    useEffect(() => {
        try {
            const saved = localStorage.getItem("manage_terms_table_cols_v2");
            setColWidths(saved ? JSON.parse(saved) : {});
        } catch {
            setColWidths({});
        }
    }, []);

    const columnKeys = [
        "select",
        "source_lang",
        "target_lang",
        "term",
        "languages",
        "priority",
        "source",
        "case_rule",
        "category",
        "filename",
        "created_by",
        "actions"
    ].filter((key) => {
        if (key === "select" || key === "actions") return true;
        return visibleCols[key];
    });

    const baseWidths = {
        select: "40px",
        source_lang: "80px",
        target_lang: "80px",
        term: "1.2fr",
        languages: "1.2fr",
        priority: "60px",
        source: "80px",
        case_rule: "80px",
        category: "100px",
        filename: "120px",
        created_by: "90px",
        actions: "140px"
    };

    const gridTemplateColumns = columnKeys
        .map((key) => (colWidths?.[key] ? `${colWidths[key]}px` : baseWidths[key]))
        .join(" ");

    const toggleSelectAll = (checked) => {
        if (checked) setSelectedIds(terms.map((t) => t.id));
        else setSelectedIds([]);
    };

    const toggleSelect = (id, checked) => {
        if (checked) setSelectedIds((prev) => [...prev, id]);
        else setSelectedIds((prev) => prev.filter((item) => item !== id));
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

    const setVisibleColsSafe = (next) => {
        const nextState = { ...next };
        const hasAny = Object.values(nextState).some(Boolean);
        if (!hasAny) {
            nextState.term = true;
        }
        setVisibleCols(nextState);
        localStorage.setItem("terms_visible_cols_v2", JSON.stringify(nextState));
        return nextState;
    };

    const startResize = (key, event) => {
        event.preventDefault();
        event.stopPropagation();
        const startX = event.clientX;
        const currentWidth = event.currentTarget.parentElement?.offsetWidth || 120;
        resizingRef.current = { key, startX, startWidth: currentWidth };

        document.body.style.userSelect = "none";
        document.body.style.cursor = "col-resize";

        const handleMove = (moveEvent) => {
            if (!resizingRef.current) return;
            const delta = moveEvent.clientX - resizingRef.current.startX;
            const nextWidth = Math.max(60, resizingRef.current.startWidth + delta);
            setColWidths((prev) => {
                const next = { ...(prev || {}), [key]: nextWidth };
                try {
                    localStorage.setItem("manage_terms_table_cols_v2", JSON.stringify(next));
                } catch {
                    // ignore storage failure
                }
                return next;
            });
        };
        const handleUp = () => {
            resizingRef.current = null;
            document.body.style.userSelect = "";
            document.body.style.cursor = "";
            document.removeEventListener("mousemove", handleMove);
            document.removeEventListener("mouseup", handleUp);
        };
        document.addEventListener("mousemove", handleMove);
        document.addEventListener("mouseup", handleUp);
    };

    const setPreset = (preset) => {
        if (preset === "basic") {
            return setVisibleColsSafe({
                source_lang: true,
                target_lang: true,
                term: true,
                languages: true,
                priority: true,
                source: true,
                case_rule: true,
                category: true,
                filename: true,
                created_by: true,
            });
        }
        setVisibleColsSafe(
            Object.keys(visibleCols).reduce(
                (acc, key) => ({ ...acc, [key]: true }),
                {}
            )
        );
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
                    <span className="text-xs font-bold text-slate-400 whitespace-nowrap">
                        {t("manage.list_summary", { shown: terms.length, total: terms.length })}
                    </span>
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

            <div className="manage-scroll-area flex-1 pr-1">
                <div className={`data-table is-glossary ${compactTable ? "is-compact text-xs" : "text-sm"}`}>
                    <div className="flex items-center justify-between mb-2 sticky top-0 bg-white/95 backdrop-blur px-2 py-2 rounded-xl border border-slate-200/60 z-30 shadow-sm">
                        <div className="flex flex-wrap gap-2 text-xs text-slate-600 items-center relative">
                            <button
                                ref={colBtnRef}
                                className={`btn ghost compact font-bold ${showColPanel ? "bg-slate-100 text-blue-600" : "!text-blue-600"}`}
                                type="button"
                                onClick={() => setShowColPanel((v) => !v)}
                            >
                                {t("manage.terms_tab.columns_panel.show_columns")}
                            </button>
                            {showColPanel && createPortal(
                                <>
                                    <div className="fixed inset-0 z-[9998]" onClick={() => setShowColPanel(false)}></div>
                                    <div
                                        className={`fixed bg-white rounded-2xl border border-slate-200 shadow-2xl z-[9999] transition-all ${compactTable ? "p-3 w-[360px]" : "p-4 w-[420px]"}`}
                                        style={{
                                            top: (colBtnRef.current?.getBoundingClientRect().bottom || 0) + 8,
                                            left: Math.min(
                                                colBtnRef.current?.getBoundingClientRect().left || 0,
                                                window.innerWidth - (compactTable ? 380 : 440)
                                            )
                                        }}
                                    >
                                        <div className={`flex items-center justify-between border-b border-slate-100 ${compactTable ? "mb-2 pb-1.5" : "mb-3 pb-2"}`}>
                                            <div className={`${compactTable ? "text-xs" : "text-sm"} font-bold text-slate-700`}>{t("manage.terms_tab.columns_panel.title")}</div>
                                            <button className="btn ghost compact" type="button" onClick={() => setShowColPanel(false)}><X size={compactTable ? 12 : 14} /></button>
                                        </div>
                                        <div className={`grid grid-cols-2 gap-x-4 mb-4 overflow-y-auto max-h-[400px] p-1 ${compactTable ? "gap-y-1" : "gap-y-2"}`}>
                                            {[
                                                { key: "source_lang", label: t("manage.table.source_lang") },
                                                { key: "target_lang", label: t("manage.table.target_lang") },
                                                { key: "term", label: t("manage.terms_tab.columns.term") },
                                                { key: "languages", label: t("manage.terms_tab.columns.languages") },
                                                { key: "priority", label: t("manage.table.priority") },
                                                { key: "source", label: t("manage.terms_tab.columns.source") },
                                                { key: "case_rule", label: t("manage.table.case") },
                                                { key: "category", label: t("manage.terms_tab.columns.category") },
                                                { key: "filename", label: t("manage.terms_tab.columns.filename") },
                                                { key: "created_by", label: t("manage.terms_tab.columns.created_by") }
                                            ].map(({ key, label }) => (
                                                <label key={key} className={`flex items-center gap-2 cursor-pointer hover:bg-slate-50 rounded transition-colors border border-transparent hover:border-slate-100 ${compactTable ? "px-1.5 py-1" : "px-2 py-1.5"}`}>
                                                    <input
                                                        type="checkbox"
                                                        className={`${compactTable ? "w-3.5 h-3.5" : "w-4 h-4"} rounded border-slate-300 text-blue-600 focus:ring-blue-500`}
                                                        checked={!!visibleCols[key]}
                                                        onChange={(e) =>
                                                            setVisibleColsSafe({ ...visibleCols, [key]: e.target.checked })
                                                        }
                                                    />
                                                    <span className={`${compactTable ? "text-[11px]" : "text-sm"} text-slate-700 font-medium select-none`}>{label}</span>
                                                </label>
                                            ))}
                                        </div>
                                        <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                                            <div className="flex gap-2">
                                                <button className="btn ghost compact text-[11px]" type="button" onClick={() => setPreset("basic")}>{t("manage.terms_tab.columns_panel.preset_basic")}</button>
                                                <button className="btn ghost compact text-[11px]" type="button" onClick={() => setPreset("all")}>{t("manage.terms_tab.columns_panel.preset_all")}</button>
                                            </div>
                                        </div>
                                    </div>
                                </>,
                                document.body
                            )}
                        </div>
                        <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
                            <input type="checkbox" className="w-3.5 h-3.5" checked={compactTable} onChange={(e) => setCompactTable(e.target.checked)} />
                            {t("manage.table.compact")}
                        </label>
                    </div>

                    <div className="unified-data-row data-header sticky top-12 z-20 bg-white shadow-sm" style={{ gridTemplateColumns }}>
                        <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                            <input type="checkbox" checked={terms.length > 0 && selectedIds.length === terms.length} onChange={(e) => toggleSelectAll(e.target.checked)} />
                            <span className="col-resizer" onMouseDown={(e) => startResize("select", e)} />
                        </div>
                        {visibleCols.source_lang && <div className="data-cell">{t("manage.table.source_lang")}<span className="col-resizer" onMouseDown={(e) => startResize("source_lang", e)} /></div>}
                        {visibleCols.target_lang && <div className="data-cell">{t("manage.table.target_lang")}<span className="col-resizer" onMouseDown={(e) => startResize("target_lang", e)} /></div>}
                        {visibleCols.term && <div className="data-cell">{t("manage.terms_tab.columns.term")}<span className="col-resizer" onMouseDown={(e) => startResize("term", e)} /></div>}
                        {visibleCols.languages && <div className="data-cell">{t("manage.terms_tab.columns.languages")}<span className="col-resizer" onMouseDown={(e) => startResize("languages", e)} /></div>}
                        {visibleCols.priority && <div className="data-cell text-center">{t("manage.table.priority")}<span className="col-resizer" onMouseDown={(e) => startResize("priority", e)} /></div>}
                        {visibleCols.source && <div className="data-cell">{t("manage.terms_tab.columns.source")}<span className="col-resizer" onMouseDown={(e) => startResize("source", e)} /></div>}
                        {visibleCols.case_rule && <div className="data-cell">{t("manage.table.case")}<span className="col-resizer" onMouseDown={(e) => startResize("case_rule", e)} /></div>}
                        {visibleCols.category && <div className="data-cell">{t("manage.terms_tab.columns.category")}<span className="col-resizer" onMouseDown={(e) => startResize("category", e)} /></div>}
                        {visibleCols.filename && <div className="data-cell">{t("manage.terms_tab.columns.filename")}<span className="col-resizer" onMouseDown={(e) => startResize("filename", e)} /></div>}
                        {visibleCols.created_by && <div className="data-cell">{t("manage.terms_tab.columns.created_by")}<span className="col-resizer" onMouseDown={(e) => startResize("created_by", e)} /></div>}
                        <div className="data-cell data-actions">{t("manage.terms_tab.columns.actions")}<span className="col-resizer" onMouseDown={(e) => startResize("actions", e)} /></div>
                    </div>

                    {loading && <div className="data-empty">{t("manage.terms_tab.loading")}</div>}

                    {!loading && terms.map((item) => {
                        const isEditing = editingId === item.id;
                        const isSelected = selectedIds.includes(item.id);
                        const languageText = formatLanguages(isEditing ? form.languages : item.languages);

                        return (
                            <div
                                className={`unified-data-row ${isSelected ? "is-selected" : ""}`}
                                key={item.id}
                                style={{ gridTemplateColumns }}
                            >
                                <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                                    <input type="checkbox" checked={isSelected} onChange={(e) => toggleSelect(item.id, e.target.checked)} />
                                </div>

                                {visibleCols.source_lang && (
                                    <div className="data-cell text-slate-500 font-mono text-[11px]">
                                        {isEditing ? (
                                            <input
                                                className="data-input !bg-white !border-blue-200 font-bold"
                                                value={form.source_lang || ""}
                                                onChange={(e) => setForm((p) => ({ ...p, source_lang: e.target.value }))}
                                                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                                            />
                                        ) : item.source_lang || ""}
                                    </div>
                                )}

                                {visibleCols.target_lang && (
                                    <div className="data-cell text-slate-500 font-mono text-[11px]">
                                        {isEditing ? (
                                            <input
                                                className="data-input !bg-white !border-blue-200 font-bold"
                                                value={form.target_lang || ""}
                                                onChange={(e) => setForm((p) => ({ ...p, target_lang: e.target.value }))}
                                                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                                            />
                                        ) : item.target_lang || ""}
                                    </div>
                                )}

                                {visibleCols.term && (
                                    <div className="data-cell">
                                        {isEditing ? (
                                            <input
                                                className="data-input !bg-white !border-blue-200 font-bold"
                                                value={form.term || ""}
                                                onChange={(e) => setForm((p) => ({ ...p, term: e.target.value }))}
                                                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                                                autoFocus
                                            />
                                        ) : item.term}
                                    </div>
                                )}

                                {visibleCols.languages && (
                                    <div className="data-cell">
                                        {isEditing ? (
                                            <input
                                                className="data-input !bg-white !border-blue-200 font-bold"
                                                value={languageText}
                                                onChange={(e) => setForm((p) => ({ ...p, languages: parseLanguages(e.target.value) }))}
                                                placeholder="zh-TW:值 / en:Value"
                                                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                                            />
                                        ) : (
                                            (item.languages || []).map((l) => l.value).join(" / ")
                                        )}
                                    </div>
                                )}

                                {visibleCols.priority && (
                                    <div className="data-cell text-center">
                                        {isEditing ? (
                                            <input
                                                type="number"
                                                className="data-input !bg-white !border-blue-200 font-bold !text-center"
                                                value={form.priority || 0}
                                                onChange={(e) => setForm((p) => ({ ...p, priority: parseInt(e.target.value) || 0 }))}
                                                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                                            />
                                        ) : (
                                            <span className="text-slate-400 font-mono text-[11px]">{item.priority ?? 0}</span>
                                        )}
                                    </div>
                                )}

                                {visibleCols.source && (
                                    <div className="data-cell">
                                        {isEditing ? (
                                            <select
                                                className="data-input !bg-white !border-blue-200 font-bold !text-[12px]"
                                                value={form.source || ""}
                                                onChange={(e) => setForm((p) => ({ ...p, source: e.target.value }))}
                                                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                                            >
                                                <option value="">{t("manage.terms_tab.columns.source")}</option>
                                                <option value="reference">{t("manage.terms_tab.filter_source_reference")}</option>
                                                <option value="terminology">{t("manage.terms_tab.filter_source_terminology")}</option>
                                                <option value="manual">{t("manage.terms_tab.filter_source_manual")}</option>
                                            </select>
                                        ) : (
                                            item.source && (
                                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${item.source === "reference" ? "bg-blue-50 text-blue-600 border border-blue-100" :
                                                    item.source === "terminology" ? "bg-purple-50 text-purple-600 border border-purple-100" :
                                                        "bg-slate-50 text-slate-500 border border-slate-100"
                                                    }`}>
                                                    {item.source === "reference" ? t("manage.terms_tab.source_labels.reference") :
                                                        item.source === "terminology" ? t("manage.terms_tab.source_labels.terminology") : t("manage.terms_tab.source_labels.manual")}
                                                </span>
                                            )
                                        )}
                                    </div>
                                )}

                                {visibleCols.case_rule && (
                                    <div className="data-cell">
                                        {isEditing ? (
                                            <select
                                                className="data-input !bg-white !border-blue-200 font-bold !text-[12px]"
                                                value={form.case_rule || "preserve"}
                                                onChange={(e) => setForm((p) => ({ ...p, case_rule: e.target.value }))}
                                                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                                            >
                                                <option value="preserve">{t("manage.terms_tab.case_rules.preserve")}</option>
                                                <option value="lowercase">{t("manage.terms_tab.case_rules.lowercase")}</option>
                                                <option value="uppercase">{t("manage.terms_tab.case_rules.uppercase")}</option>
                                            </select>
                                        ) : (
                                            <span className="text-[10px] text-slate-500">{t(`manage.terms_tab.case_rules.${item.case_rule || "preserve"}`)}</span>
                                        )}
                                    </div>
                                )}

                                {visibleCols.category && (
                                    <div className="data-cell">
                                        {isEditing ? (
                                            <select
                                                className="data-input !bg-white !border-blue-200 font-bold !text-[12px]"
                                                value={form.category_id || ""}
                                                onChange={(e) => setForm((p) => ({ ...p, category_id: e.target.value ? parseInt(e.target.value) : null }))}
                                                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                                            >
                                                <option value="">{t("manage.terms_tab.columns.category")}</option>
                                                {categories.map((c) => (
                                                    <option key={`cat-edit-${c.id}`} value={c.id}>{c.name}</option>
                                                ))}
                                            </select>
                                        ) : (
                                            <CategoryPill name={item.category_name} />
                                        )}
                                    </div>
                                )}

                                {visibleCols.filename && (
                                    <div className="data-cell text-slate-500 font-mono text-[11px] truncate" title={item.filename}>
                                        {item.filename || ""}
                                    </div>
                                )}

                                {visibleCols.created_by && (
                                    <div className="data-cell text-slate-400 text-[11px]">
                                        {item.created_by || ""}
                                    </div>
                                )}

                                <div className="data-cell data-actions flex justify-end gap-1">
                                    {isEditing ? (
                                        <>
                                            <button className="action-btn-sm success" onClick={handleUpsert} title={t("manage.actions.save")}>
                                                <img src="https://emojicdn.elk.sh/✅?style=apple" className="w-5 h-5 object-contain" alt="Save" />
                                            </button>
                                            <button className="action-btn-sm" onClick={resetForm} title={t("manage.actions.cancel")}>
                                                <img src="https://emojicdn.elk.sh/❌?style=apple" className="w-5 h-5 object-contain" alt="Cancel" />
                                            </button>
                                        </>
                                    ) : (
                                        <>
                                            <button className="action-btn-sm" onClick={() => startEdit(item)} title={t("manage.actions.edit")}>
                                                <img src="https://emojicdn.elk.sh/✏️?style=apple" className="w-5 h-5 object-contain" alt="Edit" />
                                            </button>
                                            <button className="action-btn-sm" onClick={() => loadVersions(item.id)} title={t("manage.terms_tab.version_btn")}>
                                                <img src="https://emojicdn.elk.sh/📜?style=apple" className="w-5 h-5 object-contain" alt="Version" />
                                            </button>
                                            <button className="action-btn-sm danger" onClick={() => remove(item.id)} title={t("manage.actions.delete")}>
                                                <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>

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
