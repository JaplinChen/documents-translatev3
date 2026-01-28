import React, { useState } from "react";
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

    return (
        <div className="modal-body">
            <div className="action-row flex items-center justify-between gap-2">
                <div className="flex gap-2 items-center">
                    <input
                        className="text-input w-48"
                        placeholder="搜尋術語/別名"
                        value={filters.q}
                        onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value }))}
                    />
                    <select
                        className="select-input w-32"
                        value={filters.category_id}
                        onChange={(e) => setFilters((p) => ({ ...p, category_id: e.target.value }))}
                    >
                        <option value="">全部分類</option>
                        {categories.map((c) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>
                    <select
                        className="select-input w-28"
                        value={filters.status}
                        onChange={(e) => setFilters((p) => ({ ...p, status: e.target.value }))}
                    >
                        <option value="">全部狀態</option>
                        <option value="active">active</option>
                        <option value="inactive">inactive</option>
                    </select>
                    <input
                        className="text-input w-28"
                        placeholder="缺語言 e.g. en"
                        value={filters.missing_lang}
                        onChange={(e) => setFilters((p) => ({ ...p, missing_lang: e.target.value }))}
                    />
                </div>
                <div className="flex gap-2 items-center">
                    <button className="btn ghost" type="button" onClick={exportCsv}>匯出 CSV</button>
                    <label className="btn ghost">
                        匯入 CSV
                        <input type="file" accept=".csv" className="hidden-input" onChange={(e) => setImportFile(e.target.files?.[0] || null)} />
                    </label>
                    <button className="btn ghost" type="button" onClick={handlePreview} disabled={!importFile}>預覽</button>
                </div>
            </div>

            {importFile && (
                <div className="mt-2 p-2 border border-slate-200 rounded-lg">
                    <div className="text-xs text-slate-500 mb-1">欄位映射（可選）</div>
                    <div className="grid grid-cols-12 gap-2">
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
                    <div className="mt-2 flex gap-2">
                        <button className="btn ghost compact" type="button" onClick={addMappingRow}>新增映射</button>
                        <button className="btn ghost compact" type="button" onClick={() => setMappingText(JSON.stringify(buildMappingFromRows()))}>套用為 JSON</button>
                        <button className="btn ghost compact" type="button" onClick={() => setMappingRows([])}>清空映射</button>
                    </div>
                    <div className="text-xs text-slate-400 mt-2">如需直接貼 JSON，可在下方輸入</div>
                    <textarea
                        className="text-input w-full h-20 mt-1"
                        value={mappingText}
                        onChange={(e) => setMappingText(e.target.value)}
                        placeholder='{"術語":"term","分類":"category","中文":"lang_zh-TW"}'
                    />
                    <div className="flex gap-2 mt-2">
                        <button className="btn primary" type="button" onClick={handleImport}>確認匯入</button>
                        {preview?.summary && (
                            <span className="text-xs text-slate-500">
                                總筆數 {preview.summary.total}｜有效 {preview.summary.valid}｜錯誤 {preview.summary.invalid}
                            </span>
                        )}
                    </div>
                    {importResult && (
                        <div className="mt-2 text-xs text-slate-600">
                            匯入完成：成功 {importResult.imported} 筆，失敗 {importResult.failed?.length || 0} 筆
                        </div>
                    )}
                </div>
            )}

            <div className="create-row mt-3">
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
                        <button className="btn primary flex-1" type="button" onClick={handleUpsert}>{editingId ? "更新" : "新增"}</button>
                    </div>
                </div>
            </div>
            {errorMsg && (
                <div className="mt-2 text-xs text-rose-600">{errorMsg}</div>
            )}

            <div className="mt-2 p-2 border border-slate-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-bold">語言欄位</div>
                    <button className="btn ghost compact" type="button" onClick={addLanguage}>新增語言</button>
                </div>
                <div className="space-y-2">
                    {form.languages.map((lang, idx) => (
                        <div key={`${lang.lang_code}-${idx}`} className="grid grid-cols-12 gap-2">
                            <input className="text-input col-span-3" value={lang.lang_code} placeholder="lang_code" onChange={(e) => updateLanguage(idx, "lang_code", e.target.value)} />
                            <input className="text-input col-span-8" value={lang.value} placeholder="value" onChange={(e) => updateLanguage(idx, "value", e.target.value)} />
                            <button className="btn ghost compact col-span-1" type="button" onClick={() => removeLanguage(idx)}>刪除</button>
                        </div>
                    ))}
                </div>
            </div>

            {selectedIds.length > 0 && (
                <div className="batch-actions flex gap-2 mt-3">
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

            <div className="data-table is-glossary mt-3">
                <div className="flex flex-wrap gap-2 mb-2 text-xs text-slate-600">
                    {Object.keys(visibleCols).map((key) => (
                        <label key={key} className="flex items-center gap-1">
                            <input
                                type="checkbox"
                                checked={visibleCols[key]}
                                onChange={(e) =>
                                    setVisibleCols((p) => {
                                        const next = { ...p, [key]: e.target.checked };
                                        localStorage.setItem(
                                            "terms_visible_cols",
                                            JSON.stringify(next)
                                        );
                                        return next;
                                    })
                                }
                            />
                            {key}
                        </label>
                    ))}
                </div>
                <div className="data-row data-header">
                    <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                        <input type="checkbox" checked={terms.length > 0 && selectedIds.length === terms.length} onChange={(e) => toggleSelectAll(e.target.checked)} />
                    </div>
                    {visibleCols.term && <div className="data-cell">術語</div>}
                    {visibleCols.category && <div className="data-cell">分類</div>}
                    {visibleCols.status && <div className="data-cell">狀態</div>}
                    {visibleCols.languages && <div className="data-cell">語言</div>}
                    {visibleCols.aliases && <div className="data-cell">別名</div>}
                    {visibleCols.note && <div className="data-cell">備註</div>}
                    {visibleCols.created_by && <div className="data-cell">建立者</div>}
                    <div className="data-cell data-actions">操作</div>
                </div>
                {loading && <div className="data-empty">載入中...</div>}
                {!loading && terms.map((item) => (
                    <div className="data-row" key={item.id}>
                        <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                            <input type="checkbox" checked={selectedIds.includes(item.id)} onChange={(e) => toggleSelect(item.id, e.target.checked)} />
                        </div>
                        {visibleCols.term && <div className="data-cell">{item.term}</div>}
                        {visibleCols.category && <div className="data-cell">{item.category_name || "-"}</div>}
                        {visibleCols.status && <div className="data-cell">{item.status}</div>}
                        {visibleCols.languages && (
                            <div className="data-cell">
                                {(item.languages || []).map((l) => `${l.lang_code}:${l.value}`).join(" / ")}
                            </div>
                        )}
                        {visibleCols.aliases && <div className="data-cell">{(item.aliases || []).join(" | ")}</div>}
                        {visibleCols.note && <div className="data-cell">{item.note || ""}</div>}
                        {visibleCols.created_by && <div className="data-cell">{item.created_by || ""}</div>}
                        <div className="data-cell data-actions">
                            <button className="btn ghost compact" onClick={() => startEdit(item)}>編輯</button>
                            <button className="btn ghost compact" onClick={() => loadVersions(item.id)}>版本</button>
                            <button className="btn ghost compact !text-red-500" onClick={() => remove(item.id)}>刪除</button>
                        </div>
                    </div>
                ))}
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
}
