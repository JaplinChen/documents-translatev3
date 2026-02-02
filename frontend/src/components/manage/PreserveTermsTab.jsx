import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePreserveTerms } from "../../hooks/usePreserveTerms";
import { API_BASE } from "../../constants";
import { useUIStore } from "../../store/useUIStore";
import { useSettingsStore } from "../../store/useSettingsStore";
import { DataTable } from "../common/DataTable";
import { CategoryPill } from "./CategoryPill";
import { Plus } from "lucide-react";

export default function PreserveTermsTab({ onClose }) {
    const { t } = useTranslation();
    const targetLang = useUIStore((state) => state.targetLang);
    const setLastGlossaryAt = useUIStore((state) => state.setLastGlossaryAt);
    const correctionFillColor = useSettingsStore((state) => state.correction.fillColor);
    const {
        filteredTerms, loading, filterText, setFilterText, filterCategory, setFilterCategory,
        editingId, setEditingId, editForm, setEditForm, newTerm, setNewTerm, categories,
        handleAdd, handleDelete, handleUpdate, handleExport, handleImport, handleConvertToGlossary,
        refreshTerms
    } = usePreserveTerms();

    const [selectedIds, setSelectedIds] = React.useState([]);
    const [visibleCount, setVisibleCount] = React.useState(200);
    const [compactTable, setCompactTable] = React.useState(() => {
        try {
            const saved = localStorage.getItem("manage_table_compact_preserve");
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

    // Sorting state
    const [sortKey, setSortKey] = useState(null);
    const [sortDir, setSortDir] = useState("asc");

    React.useEffect(() => {
        setVisibleCount(200);
    }, [filterText, filterCategory]);

    const categoryKeyMap = {
        "產品名稱": "product", "產品": "product",
        "技術縮寫": "abbr", "技術": "abbr",
        "專業術語": "special", "專業": "special",
        "翻譯術語": "trans", "翻譯": "trans",
        "公司名稱": "company", "公司": "company",
        "網絡術語": "network", "網絡": "network",
        "其他": "other"
    };
    const getCategoryLabel = (cat) => {
        const key = categoryKeyMap[cat];
        if (key) return t(`manage.preserve.categories.${key}`);
        return cat || t("manage.preserve.categories.other");
    };

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
        } else {
            setSortKey(key);
            setSortDir("asc");
        }
    };

    // Memoize sorted terms
    const sortedTerms = useMemo(() => {
        // Slice for "visibleCount" logic is handled by "data" prop of DataTable if needed?
        // But for sorting, we need full list first, then slice. 
        // Actually, user's previous implementation used slice(0, visibleCount) BEFORE passing to child components.
        // We should follow pattern - sort first, then DataTable can handle everything or we pass sorted list.
        // Since DataTable doesn't do pagination internally (it scrolls), passing all items is fine IF not too heavy.
        // BUT prev impl had "load more" button. Let's keep "visibleTerms" logic for now to respect performance.

        if (!filteredTerms) return [];
        let list = [...filteredTerms];

        if (sortKey) {
            const dir = sortDir === "asc" ? 1 : -1;
            list.sort((a, b) => {
                const av = a[sortKey];
                const bv = b[sortKey];

                if (sortKey === "case_sensitive") {
                    // boolean
                    const an = av ? 1 : 0;
                    const bn = bv ? 1 : 0;
                    return (an - bn) * dir;
                } else if (sortKey === "created_at") {
                    // date string or number
                    const ad = new Date(av || 0).getTime();
                    const bd = new Date(bv || 0).getTime();
                    return (ad - bd) * dir;
                } else {
                    // string default
                    return String(av || "").localeCompare(String(bv || ""), "zh-Hant") * dir;
                }
            });
        }
        return list;
        // Logic note: slice happens separately? No, `visibleTerms` below slices `filteredTerms`. we need to slice `sortedTerms`.
    }, [filteredTerms, sortKey, sortDir]);

    const visibleTerms = useMemo(() => sortedTerms.slice(0, visibleCount), [sortedTerms, visibleCount]);
    const totalCount = filteredTerms ? filteredTerms.length : 0;
    const shownCount = visibleTerms.length;

    const handleBatchDelete = async () => {
        if (!selectedIds.length) return;
        if (!window.confirm(t("manage.preserve.alerts.delete_confirm"))) return;
        try {
            await Promise.all(
                selectedIds.map((id) =>
                    fetch(`${API_BASE}/api/preserve-terms/${id}`, {
                        method: "DELETE",
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
        if (!window.confirm(t("manage.preserve.alerts.batch_convert_confirm"))) return;

        try {
            setLastGlossaryAt(Date.now());
            await Promise.all(
                selectedIds.map(async (id) => {
                    const term = filteredTerms.find((item) => item.id === id);
                    if (!term) return;
                    await fetch(`${API_BASE}/api/preserve-terms/convert-to-glossary`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            id: term.id,
                            target_lang: targetLang || "zh-TW",
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
        if (e.key === "Enter") {
            e.preventDefault();
            saveFn();
        } else if (e.key === "Escape") {
            e.preventDefault();
            cancelFn();
        }
    };

    const columns = [
        {
            key: "term",
            label: t("manage.preserve.table.term"),
            width: "1.5fr",
            sortable: true,
            cellClass: "font-bold text-slate-700",
            render: (value, item) => editingId === item.id ? (
                <input
                    className="data-input !bg-white !border-blue-200 w-full"
                    value={editForm.term}
                    onChange={(e) => setEditForm({ ...editForm, term: e.target.value })}
                    onKeyDown={(e) => handleKeyDown(e, handleUpdate, () => setEditingId(null))}
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                />
            ) : value
        },
        {
            key: "category",
            label: t("manage.preserve.table.category"),
            width: "100px",
            sortable: true,
            cellClass: "text-center",
            render: (value, item) => editingId === item.id ? (
                <select
                    className="data-input !text-[11px] !py-1 !px-2 w-full !bg-white border-blue-200 font-bold"
                    value={editForm.category}
                    onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                    onKeyDown={(e) => handleKeyDown(e, handleUpdate, () => setEditingId(null))}
                    onClick={(e) => e.stopPropagation()}
                >
                    {categories.map(cat => (
                        <option key={cat} value={cat}>{getCategoryLabel(cat)}</option>
                    ))}
                </select>
            ) : (
                <CategoryPill name={getCategoryLabel(value)} />
            )
        },
        {
            key: "case_sensitive",
            label: t("manage.preserve.table.case"),
            width: "80px",
            sortable: true,
            cellClass: "text-center",
            render: (value, item) => editingId === item.id ? (
                <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-slate-300 text-blue-600"
                    checked={editForm.case_sensitive}
                    onChange={(e) => setEditForm({ ...editForm, case_sensitive: e.target.checked })}
                    onKeyDown={(e) => handleKeyDown(e, handleUpdate, () => setEditingId(null))}
                    onClick={(e) => e.stopPropagation()}
                />
            ) : (
                <span className={`text-[10px] font-black uppercase tracking-wider ${value ? "text-blue-600" : "text-slate-300"}`}>
                    {value ? t("manage.preserve.table.yes") : t("manage.preserve.table.no")}
                </span>
            )
        },
        {
            key: "created_at",
            label: t("manage.preserve.table.date"),
            width: "100px",
            sortable: true,
            cellClass: "text-center text-[10px] font-medium text-slate-400",
            render: (value) => new Date(value || Date.now()).toLocaleDateString()
        },
        {
            key: "actions",
            label: t("manage.preserve.table.actions"),
            width: "120px",
            render: (_, item) => (
                <div className="flex justify-end gap-1.5">
                    {editingId === item.id ? (
                        <>
                            <button className="action-btn-sm success" onClick={(e) => { e.stopPropagation(); handleUpdate(); }} title={t("manage.actions.save")}>
                                <img src="https://emojicdn.elk.sh/✅?style=apple" className="w-5 h-5 object-contain" alt="Save" />
                            </button>
                            <button className="action-btn-sm" onClick={(e) => { e.stopPropagation(); setEditingId(null); }} title={t("manage.actions.cancel")}>
                                <img src="https://emojicdn.elk.sh/❌?style=apple" className="w-5 h-5 object-contain" alt="Cancel" />
                            </button>
                        </>
                    ) : (
                        <>
                            <button className="action-btn-sm success" onClick={(e) => { e.stopPropagation(); handleAdd(item); }} title={t("manage.actions.add")}>
                                <Plus size={18} className="text-emerald-600" />
                            </button>
                            <button className="action-btn-sm" onClick={(e) => {
                                e.stopPropagation();
                                setEditingId(item.id);
                                setEditForm({ term: item.term, category: item.category, case_sensitive: item.case_sensitive });
                            }} title={t("manage.actions.edit")}>
                                <img src="https://emojicdn.elk.sh/✏️?style=apple" className="w-5 h-5 object-contain" alt="Edit" />
                            </button>
                            <button className="action-btn-sm primary" onClick={(e) => { e.stopPropagation(); handleConvertToGlossary(item); }} title={t("manage.actions.convert_glossary")}>
                                <img src="https://emojicdn.elk.sh/📑?style=apple" className="w-5 h-5 object-contain" alt="To Glossary" />
                            </button>
                            <button className="action-btn-sm danger" onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }} title={t("common.delete")}>
                                <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                            </button>
                        </>
                    )}
                </div>
            )
        }
    ];

    return (
        <div className="flex flex-col flex-1 min-h-0 overflow-hidden px-1">
            <div className="action-row flex items-center gap-2 w-full justify-between flex-wrap bg-slate-50/70 border border-slate-200/70 rounded-2xl px-4 py-3 mb-4 shrink-0">
                <div className="flex items-center gap-2 flex-wrap">
                    <input
                        className="text-input w-48 compact"
                        type="text"
                        placeholder={t("manage.preserve.search_placeholder")}
                        value={filterText}
                        onChange={(e) => setFilterText(e.target.value)}
                    />
                    <select
                        className="select-input w-36 compact"
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                    >
                        <option value="all">{t("manage.preserve.category_all")}</option>
                        {categories.map(cat => (
                            <option key={cat} value={cat}>{getCategoryLabel(cat)}</option>
                        ))}
                    </select>
                    <button className="btn primary compact !px-3" type="button" onClick={() => handleAdd()} title={t("manage.actions.add")}>
                        <Plus size={16} />
                    </button>
                </div>
                <div className="flex items-center gap-2">
                    <button className="btn ghost compact" type="button" onClick={handleExport}>
                        {t("manage.actions.export_csv")}
                    </button>
                    <label className="btn ghost compact">
                        {t("manage.actions.import_csv")}
                        <input type="file" accept=".csv" className="hidden-input" onChange={handleImport} />
                    </label>
                </div>
            </div>

            <div className="manage-toolbar flex items-center gap-2 mb-2">
                {selectedIds.length > 0 && (
                    <div className="ml-auto flex items-center gap-2 animate-in fade-in slide-in-from-right-2">
                        <button className="btn ghost compact !text-blue-600 text-xs font-bold" onClick={handleBatchConvertToGlossary}>{t("manage.batch.to_glossary")}</button>
                        <button className="btn ghost compact !text-red-500 text-xs font-bold" onClick={handleBatchDelete}>{t("manage.batch.delete")}</button>
                    </div>
                )}
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
                            localStorage.setItem("manage_table_compact_preserve", JSON.stringify(checked));
                        } catch { }
                    }}
                    highlightColor={correctionFillColor}
                    emptyState={
                        <div className="flex-grow flex flex-col items-center justify-center p-12 text-slate-300">
                            <p className="text-lg font-bold">{filterText || filterCategory !== "all" ? t("manage.preserve.no_results") : t("manage.preserve.empty")}</p>
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
