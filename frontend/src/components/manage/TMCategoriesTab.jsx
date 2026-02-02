import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus } from "lucide-react";

import { API_BASE } from "../../constants";
import { DataTable } from "../common/DataTable";
import { CategoryPill } from "./CategoryPill";

export default function TMCategoriesTab({ categories, onRefresh }) {
    const { t } = useTranslation();
    const [editingId, setEditingId] = useState(null);
    const [draft, setDraft] = useState(null);
    const [saving, setSaving] = useState(false);
    const [selectedIds, setSelectedIds] = useState([]);

    // Sort state
    const [sortKey, setSortKey] = useState(null);
    const [sortDir, setSortDir] = useState("asc");

    // Compact mode state
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem("manage_table_compact_categories");
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

    const handleKeyDown = (e, saveFn, cancelFn) => {
        if (e.key === "Enter") {
            e.preventDefault();
            saveFn();
        } else if (e.key === "Escape") {
            e.preventDefault();
            cancelFn();
        }
    };

    const handleCreate = async () => {
        setSaving(true);
        try {
            const res = await fetch(`${API_BASE}/api/tm/categories`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: t("manage.categories.new_category"), sort_order: 0 })
            });
            if (res.ok) {
                onRefresh();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    const handleSave = async () => {
        if (!draft?.name?.trim()) return;
        setSaving(true);
        try {
            const res = await fetch(`${API_BASE}/api/tm/categories/${editingId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: draft.name.trim(), sort_order: draft.sort_order })
            });
            if (res.ok) {
                setEditingId(null);
                setDraft(null);
                onRefresh();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t("manage.confirm.delete"))) return;
        try {
            const res = await fetch(`${API_BASE}/api/tm/categories/${id}`, {
                method: "DELETE"
            });
            if (res.ok) onRefresh();
        } catch (err) {
            console.error(err);
        }
    };

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir(p => p === "asc" ? "desc" : "asc");
        } else {
            setSortKey(key);
            setSortDir("asc");
        }
    };

    // Client-side sorting
    const sortedCategories = React.useMemo(() => {
        if (!categories) return [];
        const items = [...categories];
        if (!sortKey) return items;

        items.sort((a, b) => {
            const valA = a[sortKey];
            const valB = b[sortKey];
            const dir = sortDir === "asc" ? 1 : -1;

            if (sortKey === "sort_order" || sortKey === "glossary_count" || sortKey === "tm_count" || sortKey === "unified_term_count") {
                return (Number(valA || 0) - Number(valB || 0)) * dir;
            }
            return String(valA || "").localeCompare(String(valB || ""), "zh-Hant") * dir;
        });
        return items;
    }, [categories, sortKey, sortDir]);

    const columns = [
        {
            key: "name",
            label: t("manage.categories.name"),
            width: "1fr",
            sortable: true,
            render: (value, item) => editingId === item.id ? (
                <input
                    className="data-input !bg-white !border-blue-200 font-bold w-full"
                    value={draft.name}
                    onChange={(e) => setDraft(prev => ({ ...prev, name: e.target.value }))}
                    onKeyDown={(e) => handleKeyDown(e, handleSave, () => { setEditingId(null); setDraft(null); })}
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                />
            ) : value
        },
        {
            key: "preview",
            label: t("manage.categories.preview"),
            width: "120px",
            render: (_, item) => <CategoryPill name={item.name} />
        },
        {
            key: "usage",
            label: `${t("manage.categories.usage")} (G/TM/U)`,
            width: "180px",
            render: (_, item) => (
                <div className="flex gap-1 text-[10px] text-slate-500 font-mono">
                    <span className="text-blue-600 font-bold" title="Glossary">{item.glossary_count || 0}</span>
                    <span>/</span>
                    <span className="text-emerald-600 font-bold" title="TM">{item.tm_count || 0}</span>
                    <span>/</span>
                    <span className="text-amber-600 font-bold" title="Unified Terms">{item.unified_term_count || 0}</span>
                </div>
            )
        },
        {
            key: "sort_order",
            label: t("manage.categories.sort_order"),
            width: "80px",
            sortable: true,
            cellClass: "text-center",
            render: (value, item) => editingId === item.id ? (
                <input
                    className="data-input !text-center !bg-white !border-blue-200 font-bold w-full"
                    type="number"
                    value={draft.sort_order}
                    onChange={(e) => setDraft(prev => ({ ...prev, sort_order: parseInt(e.target.value) || 0 }))}
                    onKeyDown={(e) => handleKeyDown(e, handleSave, () => { setEditingId(null); setDraft(null); })}
                    onClick={(e) => e.stopPropagation()}
                />
            ) : value
        },
        {
            key: "actions",
            label: t("manage.categories.actions"),
            width: "100px",
            render: (_, item) => (
                <div className="flex justify-end gap-1">
                    {editingId === item.id ? (
                        <>
                            <button className="action-btn-sm success" onClick={(e) => { e.stopPropagation(); handleSave(); }} disabled={saving} title={t("manage.actions.save")}>
                                <img src="https://emojicdn.elk.sh/✅?style=apple" className="w-5 h-5 object-contain" alt="Save" />
                            </button>
                            <button className="action-btn-sm" onClick={(e) => { e.stopPropagation(); setEditingId(null); setDraft(null); }} title={t("manage.actions.cancel")}>
                                <img src="https://emojicdn.elk.sh/❌?style=apple" className="w-5 h-5 object-contain" alt="Cancel" />
                            </button>
                        </>
                    ) : (
                        <>
                            <button className="action-btn-sm success" onClick={(e) => { e.stopPropagation(); handleCreate(); }} disabled={saving} title={t("manage.categories.add_category")}>
                                <Plus size={18} className="text-emerald-600" />
                            </button>
                            <button className="action-btn-sm" onClick={(e) => { e.stopPropagation(); setEditingId(item.id); setDraft({ ...item }); }} title={t("manage.actions.edit")}>
                                <img src="https://emojicdn.elk.sh/✏️?style=apple" className="w-5 h-5 object-contain" alt="Edit" />
                            </button>
                            <button className="action-btn-sm danger" onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }} title={t("manage.actions.delete")}>
                                <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                            </button>
                        </>
                    )}
                </div>
            )
        }
    ];

    return (
        <DataTable
            columns={columns}
            data={sortedCategories}
            rowKey="id"
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={toggleSort}
            storageKey="manage_categories_table_cols"
            compact={compactTable}
            onCompactChange={(checked) => {
                setCompactTable(checked);
                try {
                    localStorage.setItem("manage_table_compact_categories", JSON.stringify(checked));
                } catch { }
            }}
            emptyState={t("manage.categories.empty")}
            className="is-tm"
        />
    );
}
