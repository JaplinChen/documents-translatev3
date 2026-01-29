import React, { useEffect, useRef, useState } from "react";
import { Check, Edit, History, Trash2, X } from "lucide-react";
import { IconButton } from "../common/IconButton";
import { CategoryPill } from "./CategoryPill";
import { API_BASE } from "../../constants";
import { useTerms } from "../../hooks/useTerms";

export default function TermsTab() {
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
    const [batchCaseRule, setBatchCaseRule] = useState("");
    const [importResult, setImportResult] = useState(null);
    const [mappingRows, setMappingRows] = useState([
        { from: "", to: "term" },
        { from: "", to: "category" },
        { from: "", to: "status" },
        { from: "", to: "case_rule" },
        { from: "", to: "note" },
        { from: "", to: "aliases" },
    ]);
    const [errorMsg, setErrorMsg] = useState("");
    const [showLanguages, setShowLanguages] = useState(false);
    const [showImport, setShowImport] = useState(false);
    const [compactTable, setCompactTable] = useState(false);
    const [showCreate, setShowCreate] = useState(false);
    const [showColPanel, setShowColPanel] = useState(false);
    const [importStep, setImportStep] = useState(1);
    const [colWidths, setColWidths] = useState(() => {
        try {
            const saved = localStorage.getItem("manage_terms_table_cols");
            return saved ? JSON.parse(saved) : {};
        } catch {
            return {};
        }
    });
    const resizingRef = useRef(null);
    const [visibleCols, setVisibleCols] = useState(() => {
        try {
            const saved = localStorage.getItem("terms_visible_cols");
            return saved
                ? JSON.parse(saved)
                : {
                    term: true,
                    category: true,
                    status: true,
                    languages: true,
                    aliases: false,
                    note: false,
                    created_by: false,
                };
        } catch {
            return {
                term: true,
                category: true,
                status: true,
                languages: true,
                aliases: false,
                note: false,
                created_by: false,
            };
        }
    });
    const colLabels = {
        term: "術語",
        category: "分類",
        status: "狀態",
        languages: "語言",
        aliases: "別名",
        note: "備註",
        created_by: "建立者",
    };

    useEffect(() => {
        try {
            const saved = localStorage.getItem("manage_terms_table_cols");
            setColWidths(saved ? JSON.parse(saved) : {});
        } catch {
            setColWidths({});
        }
    }, []);

    const columnKeys = [
        "select",
        "term",
        "category",
        "status",
        "languages",
        "aliases",
        "note",
        "created_by",
        "actions"
    ].filter((key) => {
        if (key === "select" || key === "actions") return true;
        return visibleCols[key];
    });
    const baseWidths = {
        select: "40px",
        term: "1.4fr",
        category: "100px",
        status: "90px",
        languages: "1fr",
        aliases: "1.2fr",
        note: "1.2fr",
        created_by: "100px",
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
            status: item.status || "active",
            case_rule: item.case_rule || "",
            note: item.note || "",
            aliases: (item.aliases || []).join("|"),
            languages: item.languages || [{ lang_code: "zh-TW", value: "" }],
            created_by: item.created_by || "",
        });
    };

    const addLanguage = () => {
        setForm((prev) => ({
            ...prev,
            languages: [...prev.languages, { lang_code: "", value: "" }],
        }));
    };

    const updateLanguage = (index, key, value) => {
        setForm((prev) => {
            const next = [...prev.languages];
            next[index] = { ...next[index], [key]: value };
            return { ...prev, languages: next };
        });
    };

    const removeLanguage = (index) => {
        setForm((prev) => ({
            ...prev,
            languages: prev.languages.filter((_, i) => i !== index),
        }));
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

    const setVisibleColsSafe = (next) => {
        const nextState = { ...next };
        const hasAny = Object.values(nextState).some(Boolean);
        if (!hasAny) {
            nextState.term = true;
        }
        setVisibleCols(nextState);
        localStorage.setItem("terms_visible_cols", JSON.stringify(nextState));
        return nextState;
    };

    const startResize = (key, event) => {
        event.preventDefault();
        event.stopPropagation();
        const startX = event.clientX;
        const currentWidth = event.currentTarget.parentElement?.offsetWidth || 120;
        resizingRef.current = { key, startX, startWidth: currentWidth };
        const handleMove = (moveEvent) => {
            if (!resizingRef.current) return;
            const delta = moveEvent.clientX - resizingRef.current.startX;
            const nextWidth = Math.max(60, resizingRef.current.startWidth + delta);
            setColWidths((prev) => {
                const next = { ...(prev || {}), [key]: nextWidth };
                try {
                    localStorage.setItem("manage_terms_table_cols", JSON.stringify(next));
                } catch {
                    // 忽略儲存失敗
                }
                return next;
            });
        };
        const handleUp = () => {
            resizingRef.current = null;
            document.removeEventListener("mousemove", handleMove);
            document.removeEventListener("mouseup", handleUp);
        };
        document.addEventListener("mousemove", handleMove);
        document.addEventListener("mouseup", handleUp);
    };

    const setPreset = (preset) => {
        if (preset === "basic") {
            return setVisibleColsSafe({
                term: true,
                category: true,
                status: true,
                languages: true,
                aliases: false,
                note: false,
                created_by: false,
            });
        }
        if (preset === "advanced") {
            return setVisibleColsSafe({
                term: true,
                category: true,
                status: true,
                languages: true,
                aliases: true,
                note: true,
                created_by: true,
            });
        }
        return setVisibleColsSafe(
            Object.keys(visibleCols).reduce(
                (acc, key) => ({ ...acc, [key]: true }),
                {}
            )
        );
    };

    return (
        <div className="space-y-4 max-h-[70vh] overflow-auto pr-1">
            <div className="action-row flex items-center justify-between gap-3 bg-slate-50/70 border border-slate-200/70 rounded-2xl px-4 py-3 sticky top-0 z-20">
                <div className="flex flex-wrap gap-2 items-center">
                    <input
                        className="text-input w-52"
                        placeholder="搜尋術語/別名"
                        value={filters.q}
                        onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value }))}
                    />
                    <select
                        className="select-input w-36"
                        value={filters.category_id}
                        onChange={(e) => setFilters((p) => ({ ...p, category_id: e.target.value }))}
                    >
                        <option value="">全部分類</option>
                        {categories.map((c) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>
                    <select
                        className="select-input w-32"
                        value={filters.status}
                        onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value }))}
                    >
                        <option value="">全部狀態</option>
                        <option value="active">active</option>
                        <option value="inactive">inactive</option>
                    </select>
                    <input
                        className="text-input w-36"
                        placeholder="缺語言 e.g. en"
                        value={filters.missing_lang}
                        onChange={(e) => setFilters((p) => ({ ...p, missing_lang: e.target.value }))}
                    />
                </div>
                <div className="flex gap-2 items-center">
                    <button className="btn ghost" type="button" onClick={exportCsv}>匯出 CSV</button>
                    <button className="btn ghost" type="button" onClick={() => {
                        setShowImport(true);
                        setImportStep(1);
                    }}>
                        匯入 CSV
                    </button>
                </div>
            </div>

            {showImport && (
                <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/20">
                    <div className="w-[720px] max-h-[80vh] overflow-auto bg-white rounded-2xl border border-slate-200 shadow-xl p-5">
                        <div className="flex items-center justify-between mb-3">
                            <div className="text-sm font-bold text-slate-700">CSV 匯入（步驟 {importStep}/3）</div>
                            <button className="btn ghost compact" type="button" onClick={() => setShowImport(false)}>關閉</button>
                        </div>
                        {importStep === 1 && (
                            <div className="space-y-3">
                                <label className="btn ghost w-fit">
                                    選擇 CSV
                                    <input type="file" accept=".csv" className="hidden-input" onChange={(e) => setImportFile(e.target.files?.[0] || null)} />
                                </label>
                                <div className="text-xs text-slate-500">選擇檔案後進入欄位對應</div>
                                <button className="btn primary" type="button" onClick={() => setImportStep(2)} disabled={!importFile}>下一步</button>
                            </div>
                        )}
                        {importStep === 2 && (
                            <div className="space-y-3">
                                <div className="text-xs text-slate-500">欄位對應（可選）</div>
                                <div className="grid grid-cols-12 gap-2 max-h-48 overflow-auto pr-1">
                                    {mappingRows.map((row, idx) => (
                                        <React.Fragment key={`${row.to}-${idx}`}>
                                            <input
                                                className="text-input col-span-5"
                                                placeholder="CSV 欄位名稱"
                                                value={row.from}
                                                onChange={(e) => updateMappingRow(idx, "from", e.target.value)}
                                            />
                                            <input
                                                className="text-input col-span-5"
                                                placeholder="系統欄位（term/category/lang_zh-TW）"
                                                value={row.to}
                                                onChange={(e) => updateMappingRow(idx, "to", e.target.value)}
                                            />
                                            <button
                                                className="btn ghost compact col-span-2"
                                                type="button"
                                                onClick={() => removeMappingRow(idx)}
                                            >
                                                刪除
                                            </button>
                                        </React.Fragment>
                                    ))}
                                </div>
                                <div className="flex gap-2">
                                    <button className="btn ghost compact" type="button" onClick={addMappingRow}>新增對應</button>
                                    <button className="btn ghost compact" type="button" onClick={() => setMappingText(JSON.stringify(buildMappingFromRows()))}>套用為 JSON</button>
                                    <button className="btn ghost compact" type="button" onClick={() => setMappingRows([])}>清空對應</button>
                                </div>
                                <div className="flex gap-2">
                                    <button className="btn ghost" type="button" onClick={() => setImportStep(1)}>上一步</button>
                                    <button className="btn primary" type="button" onClick={async () => {
                                        await handlePreview();
                                        setImportStep(3);
                                    }}>下一步</button>
                                </div>
                            </div>
                        )}
                        {importStep === 3 && (
                            <div className="space-y-3">
                                <div className="text-xs text-slate-500">預覽結果</div>
                                {preview?.summary && (
                                    <div className="text-xs text-slate-600">
                                        總筆數 {preview.summary.total}｜有效 {preview.summary.valid}｜錯誤 {preview.summary.invalid}
                                    </div>
                                )}
                                <div className="flex gap-2">
                                    <button className="btn ghost" type="button" onClick={() => setImportStep(2)}>上一步</button>
                                    <button className="btn primary" type="button" onClick={handleImport}>確認匯入</button>
                                </div>
                                {importResult && (
                                    <div className="text-xs text-slate-600">
                                        匯入完成：成功 {importResult.imported} 筆，失敗 {importResult.failed?.length || 0} 筆
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="p-4 border border-slate-200 rounded-2xl bg-white shadow-sm">
                <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-bold text-slate-700">新增 / 編輯術語</div>
                    <button className="btn ghost compact" type="button" onClick={() => setShowCreate((v) => !v)}>
                        {showCreate ? "收合" : "展開"}
                    </button>
                </div>
                {showCreate && (
                    <div className="space-y-2">
                        <div className="create-fields grid grid-cols-12 gap-2 w-full items-center">
                            <input className="text-input col-span-3" value={form.term} placeholder="術語" onChange={(e) => setForm((p) => ({ ...p, term: e.target.value }))} />
                            <select className="select-input col-span-2" value={form.category_id || ""} onChange={(e) => setForm((p) => ({ ...p, category_id: e.target.value }))}>
                                <option value="">分類</option>
                                {categories.map((c) => (
                                    <option key={c.id} value={c.id}>{c.name}</option>
                                ))}
                            </select>
                            <select className="select-input col-span-2" value={form.status} onChange={(e) => setForm((p) => ({ ...p, status: e.target.value }))}>
                                <option value="active">active</option>
                                <option value="inactive">inactive</option>
                            </select>
                            <select className="select-input col-span-2" value={form.case_rule} onChange={(e) => setForm((p) => ({ ...p, case_rule: e.target.value }))}>
                                <option value="">大小寫規則</option>
                                <option value="preserve">preserve</option>
                                <option value="uppercase">uppercase</option>
                                <option value="lowercase">lowercase</option>
                            </select>
                            <input className="text-input col-span-3" value={form.aliases} placeholder="別名 (| 分隔)" onChange={(e) => setForm((p) => ({ ...p, aliases: e.target.value }))} />
                            <input className="text-input col-span-3" value={form.note} placeholder="備註" onChange={(e) => setForm((p) => ({ ...p, note: e.target.value }))} />
                            <div className="col-span-1 flex gap-1">
                                <button className="btn primary flex-1 text-lg" type="button" onClick={handleUpsert}>
                                    {editingId ? "更新" : "+"}
                                </button>
                            </div>
                        </div>
                        {errorMsg && (
                            <div className="mt-2 text-xs text-rose-600">{errorMsg}</div>
                        )}
                        <div className="mt-3 p-3 border border-slate-200 rounded-xl bg-slate-50/50">
                            <div className="flex items-center justify-between mb-2">
                                <div className="text-sm font-bold">語言欄位</div>
                                <div className="flex gap-2">
                                    <button className="btn ghost compact" type="button" onClick={() => setShowLanguages((v) => !v)}>
                                        {showLanguages ? "收合" : "展開"}
                                    </button>
                                    <button className="btn ghost compact" type="button" onClick={addLanguage}>新增語言</button>
                                </div>
                            </div>
                            {showLanguages && (
                                <div className="space-y-2">
                                    {form.languages.map((lang, idx) => (
                                        <div key={`${lang.lang_code}-${idx}`} className="grid grid-cols-12 gap-2">
                                            <input className="text-input col-span-3" value={lang.lang_code} placeholder="lang_code" onChange={(e) => updateLanguage(idx, "lang_code", e.target.value)} />
                                            <input className="text-input col-span-8" value={lang.value} placeholder="value" onChange={(e) => updateLanguage(idx, "value", e.target.value)} />
                                            <button className="btn ghost compact col-span-1" type="button" onClick={() => removeLanguage(idx)}>刪除</button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {selectedIds.length > 0 && (
                <div className="batch-actions flex flex-wrap gap-2 mt-3">
                    <button className="btn ghost compact" onClick={() => batchUpdate({ status: "active" })}>批次啟用</button>
                    <button className="btn ghost compact" onClick={() => batchUpdate({ status: "inactive" })}>批次停用</button>
                    <select className="select-input w-36" value={batchCategory} onChange={(e) => setBatchCategory(e.target.value)}>
                        <option value="">批次分類</option>
                        {categories.map((c) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>
                    <button className="btn ghost compact" onClick={() => batchUpdate({ category_id: batchCategory })} disabled={!batchCategory}>套用分類</button>
                    <select className="select-input w-36" value={batchCaseRule} onChange={(e) => setBatchCaseRule(e.target.value)}>
                        <option value="">批次大小寫規則</option>
                        <option value="preserve">preserve</option>
                        <option value="uppercase">uppercase</option>
                        <option value="lowercase">lowercase</option>
                    </select>
                    <button className="btn ghost compact" onClick={() => batchUpdate({ case_rule: batchCaseRule })} disabled={!batchCaseRule}>套用規則</button>
                    <button className="btn ghost compact !text-red-500" onClick={() => {
                        if (!window.confirm(`確定要刪除選取的 ${selectedIds.length} 筆術語嗎？`)) return;
                        batchDelete();
                    }}>批次刪除</button>
                </div>
            )}

            <div className={`data-table is-glossary mt-3 ${compactTable ? "is-compact text-xs" : "text-sm"}`}>
                <div className="flex items-center justify-between mb-2 sticky top-[72px] bg-white/90 backdrop-blur px-2 py-2 rounded-xl border border-slate-200/60">
                    <div className="flex flex-wrap gap-2 text-xs text-slate-600 items-center">
                        <button className="btn ghost compact !text-blue-600 font-bold" type="button" onClick={() => setShowColPanel((v) => !v)}>
                            顯示欄位
                        </button>
                        {!showColPanel && (
                            <span className="text-xs text-slate-400">勾選後立即生效</span>
                        )}
                    </div>
                    <label className="flex items-center gap-2 text-xs text-slate-600">
                        <input type="checkbox" checked={compactTable} onChange={(e) => setCompactTable(e.target.checked)} />
                        緊湊模式
                    </label>
                </div>
                {showColPanel && (
                    <div className="w-full mt-2 mb-3 bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
                        <div className="flex items-center justify-between mb-2">
                            <div className="text-sm font-bold">顯示欄位</div>
                            <button className="btn ghost compact" type="button" onClick={() => setShowColPanel(false)}>關閉</button>
                        </div>
                        <div className="text-xs text-slate-500 mb-3">勾選後立即生效，至少保留一欄</div>
                        <div className="flex flex-wrap gap-2 mb-3">
                            <button className="btn ghost compact" type="button" onClick={() => setPreset("basic")}>基本</button>
                            <button className="btn ghost compact" type="button" onClick={() => setPreset("advanced")}>進階</button>
                            <button className="btn ghost compact" type="button" onClick={() => setPreset("all")}>全部</button>
                        </div>
                        <div className="text-xs font-bold text-slate-500 mb-2">常用</div>
                        <div className="grid grid-cols-2 gap-2 mb-3">
                            {["term", "category", "status", "languages"].map((key) => (
                                <label key={key} className="flex items-center gap-2 border border-slate-200 rounded-lg px-2 py-1">
                                    <input
                                        type="checkbox"
                                        checked={visibleCols[key]}
                                        onChange={(e) =>
                                            setVisibleColsSafe({ ...visibleCols, [key]: e.target.checked })
                                        }
                                    />
                                    {colLabels[key]}
                                </label>
                            ))}
                        </div>
                        <div className="text-xs font-bold text-slate-500 mb-2">進階</div>
                        <div className="grid grid-cols-2 gap-2 mb-3">
                            {["aliases", "note", "created_by"].map((key) => (
                                <label key={key} className="flex items-center gap-2 border border-slate-200 rounded-lg px-2 py-1">
                                    <input
                                        type="checkbox"
                                        checked={visibleCols[key]}
                                        onChange={(e) =>
                                            setVisibleColsSafe({ ...visibleCols, [key]: e.target.checked })
                                        }
                                    />
                                    {colLabels[key]}
                                    {key === "aliases" && <span className="text-[10px] text-slate-400">多個以 | 分隔</span>}
                                </label>
                            ))}
                        </div>
                        <div className="text-xs font-bold text-slate-500 mb-2">表頭預覽</div>
                        <div className="text-[11px] text-slate-600 mb-3">
                            {Object.keys(visibleCols)
                                .filter((k) => visibleCols[k])
                                .map((k) => colLabels[k])
                                .join(" / ")}
                        </div>
                        <div className="flex gap-2">
                            <button className="btn ghost compact" type="button" onClick={() => {
                                setPreset("basic");
                            }}>恢復預設</button>
                            <button className="btn ghost compact" type="button" onClick={() => {
                                setPreset("all");
                            }}>全選</button>
                            <button className="btn ghost compact" type="button" onClick={() => {
                                setVisibleColsSafe(
                                    Object.keys(visibleCols).reduce(
                                        (acc, key) => ({ ...acc, [key]: false }),
                                        {}
                                    )
                                );
                            }}>全不選</button>
                        </div>
                    </div>
                )}
                <div className="data-row data-header" style={{ gridTemplateColumns }}>
                    <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                        <input type="checkbox" checked={terms.length > 0 && selectedIds.length === terms.length} onChange={(e) => toggleSelectAll(e.target.checked)} />
                        <span className="col-resizer" onMouseDown={(e) => startResize("select", e)} />
                    </div>
                    {visibleCols.term && <div className="data-cell">術語<span className="col-resizer" onMouseDown={(e) => startResize("term", e)} /></div>}
                    {visibleCols.category && <div className="data-cell">分類<span className="col-resizer" onMouseDown={(e) => startResize("category", e)} /></div>}
                    {visibleCols.status && <div className="data-cell">狀態<span className="col-resizer" onMouseDown={(e) => startResize("status", e)} /></div>}
                    {visibleCols.languages && <div className="data-cell">語言<span className="col-resizer" onMouseDown={(e) => startResize("languages", e)} /></div>}
                    {visibleCols.aliases && <div className="data-cell">別名<span className="col-resizer" onMouseDown={(e) => startResize("aliases", e)} /></div>}
                    {visibleCols.note && <div className="data-cell">備註<span className="col-resizer" onMouseDown={(e) => startResize("note", e)} /></div>}
                    {visibleCols.created_by && <div className="data-cell">建立者<span className="col-resizer" onMouseDown={(e) => startResize("created_by", e)} /></div>}
                    <div className="data-cell data-actions">操作<span className="col-resizer" onMouseDown={(e) => startResize("actions", e)} /></div>
                </div>
                {loading && <div className="data-empty">載入中...</div>}
                {!loading && terms.map((item, idx) => {
                    const isEditing = editingId === item.id;
                    const languageText = formatLanguages(isEditing ? form.languages : item.languages);
                    return (
                    <div
                        className={`data-row ${idx % 2 === 1 ? "is-zebra" : ""}`}
                        key={item.id}
                        style={{
                            gridTemplateColumns,
                            backgroundColor: idx % 2 === 1 ? "rgba(226, 232, 240, 0.7)" : undefined,
                        }}
                    >
                        <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                            <input type="checkbox" checked={selectedIds.includes(item.id)} onChange={(e) => toggleSelect(item.id, e.target.checked)} />
                        </div>
                        {visibleCols.term && (
                            <div className="data-cell">
                                {isEditing ? (
                                    <input
                                        className="data-input !bg-white !border-blue-200 font-bold"
                                        value={form.term || ""}
                                        onChange={(e) => setForm((p) => ({ ...p, term: e.target.value }))}
                                    />
                                ) : item.term}
                            </div>
                        )}
                        {visibleCols.category && (
                            <div className="data-cell">
                                {isEditing ? (
                                    <select
                                        className="data-input !bg-white !border-blue-200 font-bold !text-[12px]"
                                        value={form.category_id || ""}
                                        onChange={(e) => setForm((p) => ({ ...p, category_id: e.target.value ? parseInt(e.target.value) : null }))}
                                    >
                                        <option value="">分類</option>
                                        {categories.map((c) => (
                                            <option key={`cat-edit-${c.id}`} value={c.id}>{c.name}</option>
                                        ))}
                                    </select>
                                ) : (
                                    <CategoryPill name={item.category_name} />
                                )}
                            </div>
                        )}
                        {visibleCols.status && (
                            <div className="data-cell">
                                {isEditing ? (
                                    <select
                                        className="data-input !bg-white !border-blue-200 font-bold !text-[12px]"
                                        value={form.status || "active"}
                                        onChange={(e) => setForm((p) => ({ ...p, status: e.target.value }))}
                                    >
                                        <option value="active">active</option>
                                        <option value="inactive">inactive</option>
                                    </select>
                                ) : (
                                    <span className={`status-pill ${item.status}`}>{item.status}</span>
                                )}
                            </div>
                        )}
                        {visibleCols.languages && (
                            <div className="data-cell">
                                {isEditing ? (
                                    <input
                                        className="data-input !bg-white !border-blue-200 font-bold"
                                        value={languageText}
                                        onChange={(e) => setForm((p) => ({ ...p, languages: parseLanguages(e.target.value) }))}
                                    />
                                ) : (
                                    (item.languages || []).map((l) => `${l.lang_code}:${l.value}`).join(" / ")
                                )}
                            </div>
                        )}
                        {visibleCols.aliases && (
                            <div className="data-cell">
                                {isEditing ? (
                                    <input
                                        className="data-input !bg-white !border-blue-200 font-bold"
                                        value={form.aliases || ""}
                                        onChange={(e) => setForm((p) => ({ ...p, aliases: e.target.value }))}
                                    />
                                ) : (
                                    (item.aliases || []).join(" | ")
                                )}
                            </div>
                        )}
                        {visibleCols.note && (
                            <div className="data-cell">
                                {isEditing ? (
                                    <input
                                        className="data-input !bg-white !border-blue-200 font-bold"
                                        value={form.note || ""}
                                        onChange={(e) => setForm((p) => ({ ...p, note: e.target.value }))}
                                    />
                                ) : (
                                    item.note || ""
                                )}
                            </div>
                        )}
                        {visibleCols.created_by && <div className="data-cell">{item.created_by || ""}</div>}
                        <div className="data-cell data-actions">
                            {isEditing ? (
                                <>
                                    <IconButton icon={Check} variant="action" size="sm" onClick={handleUpsert} title="儲存" />
                                    <IconButton icon={X} size="sm" onClick={resetForm} title="取消" />
                                </>
                            ) : (
                                <>
                                    <IconButton icon={Edit} size="sm" onClick={() => startEdit(item)} title="編輯" />
                                    <IconButton icon={History} size="sm" onClick={() => loadVersions(item.id)} title="版本" />
                                    <IconButton icon={Trash2} variant="danger" size="sm" onClick={() => remove(item.id)} title="刪除" />
                                </>
                            )}
                        </div>
                    </div>
                )})}
            </div>

            {versions && (
                <div className="mt-3 p-3 border border-slate-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                        <div className="text-sm font-bold">版本紀錄</div>
                        <button className="btn ghost compact" onClick={() => setVersions(null)}>關閉</button>
                    </div>
                    <div className="space-y-2 text-xs text-slate-600">
                        {versions.items.length === 0 && <div>尚無版本紀錄</div>}
                        {versions.items.map((v) => (
                            <div key={v.id} className="p-2 rounded bg-slate-50 border border-slate-200">
                                <div>時間：{v.created_at}</div>
                                <div>操作者：{v.created_by || "-"}</div>
                                <div className="mt-2">
                                    {renderDiff(v.diff)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );

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
            return <div className="text-xs text-slate-400">無差異資料</div>;
        }
        const before = diff.before || {};
        const after = diff.after || {};
        const fields = ["term", "category_name", "status", "case_rule", "note", "aliases"];
        return (
            <div className="space-y-1">
                {fields.map((field) => {
                    const b = before[field];
                    const a = after[field];
                    if (JSON.stringify(b) === JSON.stringify(a)) return null;
                    return (
                        <div key={field} className="flex gap-2">
                            <span className="w-24 text-slate-400">{field}</span>
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
        if (!termValue) return "術語不可為空";
        const aliasValues = form.aliases
            .split("|")
            .map((a) => normalize(a))
            .filter(Boolean);
        const existing = terms.filter((t) => t.id !== editingId);
        const termSet = new Set(existing.map((t) => normalize(t.term)));
        if (termSet.has(termValue)) {
            return "術語已存在";
        }
        for (const alias of aliasValues) {
            if (termSet.has(alias)) {
                return "別名與現有術語衝突";
            }
        }
        const aliasSet = new Set(
            existing.flatMap((t) => (t.aliases || []).map((a) => normalize(a)))
        );
        for (const alias of aliasValues) {
            if (aliasSet.has(alias)) {
                return "別名已存在";
            }
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
}
