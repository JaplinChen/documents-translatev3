import React, { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Edit, Trash2, Check, X, Table, Plus } from "lucide-react";
import { CategoryPill } from "../CategoryPill";

export function PreserveTermsList({ filteredTerms, filterText, filterCategory, editingId, setEditingId, editForm, setEditForm, selectedIds, setSelectedIds, categories, getCategoryLabel, handleUpdate, handleDelete, onConvertToGlossary, onAdd, highlightColor, t, compact }) {
    const safeTerms = Array.isArray(filteredTerms) ? filteredTerms : [];
    const allSelected = safeTerms.length > 0 && selectedIds.length === safeTerms.length;
    const [sortKey, setSortKey] = React.useState(null);
    const [sortDir, setSortDir] = React.useState("asc");
    const [colWidths, setColWidths] = React.useState(() => {
        try {
            const saved = localStorage.getItem("manage_preserve_table_cols");
            return saved ? JSON.parse(saved) : {};
        } catch {
            return {};
        }
    });
    const resizingRef = useRef(null);

    const handleKeyDown = (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleUpdate();
        } else if (e.key === "Escape") {
            e.preventDefault();
            setEditingId(null);
        }
    };

    const handleSelectAll = (checked) => {
        if (checked) setSelectedIds(safeTerms.map(t => t.id));
        else setSelectedIds([]);
    };

    const handleSelectRow = (id, checked) => {
        if (checked) setSelectedIds(prev => [...prev, id]);
        else setSelectedIds(prev => prev.filter(i => i !== id));
    };
    const sortedTerms = React.useMemo(() => {
        if (!sortKey) return safeTerms;
        const withIndex = safeTerms.map((term, idx) => ({ term, idx }));
        const dir = sortDir === "asc" ? 1 : -1;
        return withIndex.sort((a, b) => {
            const av = a.term?.[sortKey];
            const bv = b.term?.[sortKey];
            if (sortKey === "case_sensitive") {
                const an = av ? 1 : 0;
                const bn = bv ? 1 : 0;
                if (an !== bn) return (an - bn) * dir;
            } else if (sortKey === "created_at") {
                const ad = new Date(av || 0).getTime();
                const bd = new Date(bv || 0).getTime();
                if (ad !== bd) return (ad - bd) * dir;
            } else {
                const as = String(av ?? "");
                const bs = String(bv ?? "");
                const cmp = as.localeCompare(bs, "zh-Hant", { numeric: true, sensitivity: "base" });
                if (cmp !== 0) return cmp * dir;
            }
            return (a.idx - b.idx) * dir;
        }).map(({ term }) => term);
    }, [safeTerms, sortKey, sortDir]);

    useEffect(() => {
        try {
            const saved = localStorage.getItem("manage_preserve_table_cols");
            setColWidths(saved ? JSON.parse(saved) : {});
        } catch {
            setColWidths({});
        }
    }, []);

    if (safeTerms.length === 0) {
        return (
            <div className="flex-grow flex flex-col items-center justify-center p-12 text-slate-300">
                <p className="text-lg font-bold">{filterText || filterCategory !== "all" ? t("manage.preserve.no_results") : t("manage.preserve.empty")}</p>
            </div>
        );
    }

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
        } else {
            setSortKey(key);
            setSortDir("asc");
        }
    };

    const sortIndicator = (key) => {
        if (sortKey !== key) return "↕";
        return sortDir === "asc" ? "▲" : "▼";
    };

    const columnKeys = ["select", "term", "category", "case_sensitive", "created_at", "actions"];
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
                    localStorage.setItem("manage_preserve_table_cols", JSON.stringify(next));
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

    const baseWidths = {
        select: "40px",
        term: "1.5fr",
        category: "100px",
        case_sensitive: "80px",
        created_at: "100px",
        actions: "120px"
    };
    const gridTemplateColumns = columnKeys
        .map((key) => (colWidths?.[key] ? `${colWidths[key]}px` : baseWidths[key]))
        .join(" ");

    return (
        <div className={`data-table is-tm w-full ${compact ? "is-compact text-xs" : "text-sm"}`}>
            <div className="unified-data-row data-header" style={{ gridTemplateColumns }}>
                <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                    <input type="checkbox" checked={allSelected} onChange={(e) => handleSelectAll(e.target.checked)} />
                    <span className="col-resizer" onMouseDown={(e) => startResize("select", e)} />
                </div>
                <div className="data-cell">
                    <button type="button" className="sort-btn" onClick={() => toggleSort("term")} aria-label={`${t("manage.preserve.table.term")} 排序`}>
                        {t("manage.preserve.table.term")}
                        <span className="sort-indicator">{sortIndicator("term")}</span>
                    </button>
                    <span className="col-resizer" onMouseDown={(e) => startResize("term", e)} />
                </div>
                <div className="data-cell justify-center">
                    <button type="button" className="sort-btn justify-center" onClick={() => toggleSort("category")} aria-label={`${t("manage.preserve.table.category")} 排序`}>
                        {t("manage.preserve.table.category")}
                        <span className="sort-indicator">{sortIndicator("category")}</span>
                    </button>
                    <span className="col-resizer" onMouseDown={(e) => startResize("category", e)} />
                </div>
                <div className="data-cell justify-center">
                    <button type="button" className="sort-btn justify-center" onClick={() => toggleSort("case_sensitive")} aria-label={`${t("manage.preserve.table.case")} 排序`}>
                        {t("manage.preserve.table.case")}
                        <span className="sort-indicator">{sortIndicator("case_sensitive")}</span>
                    </button>
                    <span className="col-resizer" onMouseDown={(e) => startResize("case_sensitive", e)} />
                </div>
                <div className="data-cell justify-center">
                    <button type="button" className="sort-btn justify-center" onClick={() => toggleSort("created_at")} aria-label={`${t("manage.preserve.table.date")} 排序`}>
                        {t("manage.preserve.table.date")}
                        <span className="sort-indicator">{sortIndicator("created_at")}</span>
                    </button>
                    <span className="col-resizer" onMouseDown={(e) => startResize("created_at", e)} />
                </div>
                <div className="data-cell data-actions">
                    {t("manage.preserve.table.actions")}
                    <span className="col-resizer" onMouseDown={(e) => startResize("actions", e)} />
                </div>
            </div>

            <div className="data-body overflow-visible">
                {sortedTerms.map((term) => {
                    const isSelected = selectedIds.includes(term.id);
                    const rowStyle = term.is_new ? { backgroundColor: highlightColor } : undefined;
                    return (
                        <div
                            key={term.id}
                            className={`unified-data-row ${isSelected ? "is-selected" : ""}`}
                            style={{ ...rowStyle, gridTemplateColumns }}
                        >
                            <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                                <input type="checkbox" checked={isSelected} onChange={(e) => handleSelectRow(term.id, e.target.checked)} />
                            </div>
                            <div className="data-cell font-bold text-slate-700">
                                {editingId === term.id ? (
                                    <input
                                        className="data-input !bg-white !border-blue-200"
                                        value={editForm.term}
                                        onChange={(e) => setEditForm({ ...editForm, term: e.target.value })}
                                        onKeyDown={handleKeyDown}
                                        autoFocus
                                    />
                                ) : (
                                    term.term
                                )}
                            </div>
                            <div className="data-cell justify-center">
                                {editingId === term.id ? (
                                    <select
                                        className="data-input !text-[11px] !py-1 !px-2 w-full !bg-white border-blue-200 font-bold"
                                        value={editForm.category}
                                        onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                                        onKeyDown={handleKeyDown}
                                    >
                                        {categories.map(cat => (
                                            <option key={cat} value={cat}>{getCategoryLabel(cat)}</option>
                                        ))}
                                    </select>
                                ) : (
                                    <CategoryPill name={getCategoryLabel(term.category)} />
                                )}
                            </div>
                            <div className="data-cell justify-center">
                                {editingId === term.id ? (
                                    <input
                                        type="checkbox"
                                        className="w-4 h-4 rounded border-slate-300 text-blue-600"
                                        checked={editForm.case_sensitive}
                                        onChange={(e) => setEditForm({ ...editForm, case_sensitive: e.target.checked })}
                                        onKeyDown={handleKeyDown}
                                    />
                                ) : (
                                    <span className={`text-[10px] font-black uppercase tracking-wider ${term.case_sensitive ? "text-blue-600" : "text-slate-300"}`}>
                                        {term.case_sensitive ? t("manage.preserve.table.yes") : t("manage.preserve.table.no")}
                                    </span>
                                )}
                            </div>
                            <div className="data-cell justify-center text-[10px] font-medium text-slate-400">
                                {new Date(term.created_at || Date.now()).toLocaleDateString()}
                            </div>
                            <div className="data-cell data-actions flex justify-end gap-1.5">
                                {editingId === term.id ? (
                                    <>
                                        <button className="action-btn-sm success" onClick={handleUpdate} title={t("manage.actions.save")}>
                                            <img src="https://emojicdn.elk.sh/✅?style=apple" className="w-5 h-5 object-contain" alt="Save" />
                                        </button>
                                        <button className="action-btn-sm" onClick={() => setEditingId(null)} title={t("manage.actions.cancel")}>
                                            <img src="https://emojicdn.elk.sh/❌?style=apple" className="w-5 h-5 object-contain" alt="Cancel" />
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <button className="action-btn-sm success" onClick={() => onAdd(term)} title={t("manage.actions.add")}>
                                            <Plus size={18} className="text-emerald-600" />
                                        </button>
                                        <button className="action-btn-sm" onClick={() => {
                                            setEditingId(term.id);
                                            setEditForm({ term: term.term, category: term.category, case_sensitive: term.case_sensitive });
                                        }} title={t("manage.actions.edit")}>
                                            <img src="https://emojicdn.elk.sh/✏️?style=apple" className="w-5 h-5 object-contain" alt="Edit" />
                                        </button>
                                        <button className="action-btn-sm primary" onClick={() => onConvertToGlossary(term)} title={t("manage.actions.convert_glossary")}>
                                            <img src="https://emojicdn.elk.sh/📑?style=apple" className="w-5 h-5 object-contain" alt="To Glossary" />
                                        </button>
                                        <button className="action-btn-sm danger" onClick={() => handleDelete(term.id)} title={t("common.delete")}>
                                            <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    );
}
