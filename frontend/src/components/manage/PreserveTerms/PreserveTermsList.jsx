import React from "react";
import { useTranslation } from "react-i18next";
import { Edit, Trash2, Check, X, Table } from "lucide-react";

export function PreserveTermsList({ filteredTerms, filterText, filterCategory, editingId, setEditingId, editForm, setEditForm, selectedIds, setSelectedIds, categories, getCategoryLabel, handleUpdate, handleDelete, onConvertToGlossary, t }) {
    const allSelected = filteredTerms.length > 0 && selectedIds.length === filteredTerms.length;

    const handleSelectAll = (checked) => {
        if (checked) setSelectedIds(filteredTerms.map(t => t.id));
        else setSelectedIds([]);
    };

    const handleSelectRow = (id, checked) => {
        if (checked) setSelectedIds(prev => [...prev, id]);
        else setSelectedIds(prev => prev.filter(i => i !== id));
    };
    if (filteredTerms.length === 0) {
        return (
            <div className="flex-grow flex flex-col items-center justify-center p-12 text-slate-300">
                <p className="text-lg font-bold">{filterText || filterCategory !== "all" ? t("manage.preserve.no_results") : t("manage.preserve.empty")}</p>
            </div>
        );
    }

    return (
        <div className="flex-grow overflow-auto">
            <table className="w-full text-left border-collapse border-spacing-0">
                <thead className="sticky top-0 bg-white/95 backdrop-blur-md z-10 border-b border-slate-100/50">
                    <tr className="text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">
                        <th className="py-4 px-4 w-10 text-center">
                            <input type="checkbox" checked={allSelected} onChange={(e) => handleSelectAll(e.target.checked)} />
                        </th>
                        <th className="py-4 px-4">{t("manage.preserve.table.term")}</th>
                        <th className="py-4 px-2 w-32 text-center">{t("manage.preserve.table.category")}</th>
                        <th className="py-4 px-2 w-24 text-center">{t("manage.preserve.table.case")}</th>
                        <th className="py-4 px-2 w-36 text-center">{t("manage.preserve.table.date")}</th>
                        <th className="py-4 px-4 w-32 text-right">{t("manage.preserve.table.actions")}</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                    {filteredTerms.map((term) => {
                        const isSelected = selectedIds.includes(term.id);
                        return (
                            <tr key={term.id} className={`group hover: bg - blue - 50 / 30 transition - colors ${isSelected ? "bg-blue-50/50" : ""} `}>
                                <td className="py-4 px-4 text-center">
                                    <input type="checkbox" checked={isSelected} onChange={(e) => handleSelectRow(term.id, e.target.checked)} />
                                </td>
                                <td className="py-4 px-4">
                                    {editingId === term.id ? (
                                        <input
                                            className="text-input w-full !text-sm !py-1 !px-2 font-bold !bg-white border-blue-200"
                                            value={editForm.term}
                                            onChange={(e) => setEditForm({ ...editForm, term: e.target.value })}
                                            autoFocus
                                        />
                                    ) : (
                                        <span className="text-sm font-bold text-slate-700">{term.source_text}</span>
                                    )}
                                </td>
                                <td className="py-4 px-2 text-center">
                                    {editingId === term.id ? (
                                        <select
                                            className="select-input !text-[11px] !py-1 !px-2 w-full !bg-white border-blue-200 font-bold"
                                            value={editForm.category}
                                            onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                                        >
                                            {categories.map(cat => (
                                                <option key={cat} value={cat}>{getCategoryLabel(cat)}</option>
                                            ))}
                                        </select>
                                    ) : (
                                        <span className={`text - [10px] font - black px - 2.5 py - 1 rounded - full uppercase tracking - wider ${term.category === "產品名稱" ? "bg-blue-100 text-blue-700" :
                                                term.category === "技術縮寫" ? "bg-indigo-100 text-indigo-700" :
                                                    term.category === "專業術語" ? "bg-purple-100 text-purple-700" :
                                                        term.category === "翻譯術語" ? "bg-emerald-100 text-emerald-700" :
                                                            "bg-slate-100 text-slate-600"
                                            } `}>
                                            {getCategoryLabel(term.category)}
                                        </span>
                                    )}
                                </td>
                                <td className="py-4 px-2 text-center">
                                    {editingId === term.id ? (
                                        <input
                                            type="checkbox"
                                            className="w-4 h-4 rounded border-slate-300 text-blue-600"
                                            checked={editForm.case_sensitive}
                                            onChange={(e) => setEditForm({ ...editForm, case_sensitive: e.target.checked })}
                                        />
                                    ) : (
                                        <span className={`text - [10px] font - bold ${term.case_sensitive ? "text-blue-500" : "text-slate-300"} `}>
                                            {term.case_sensitive ? t("manage.preserve.table.yes") : t("manage.preserve.table.no")}
                                        </span>
                                    )}
                                </td>
                                <td className="py-4 px-2 text-center text-[10px] font-medium text-slate-400">
                                    {new Date(term.created_at || Date.now()).toLocaleDateString()}
                                </td>
                                <td className="py-4 px-6 text-right">
                                    <div className="flex justify-end gap-1.5">
                                        {editingId === term.id ? (
                                            <>
                                                <button className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors" onClick={handleUpdate} title={t("manage.actions.save")}>
                                                    <Check size={16} strokeWidth={2.5} />
                                                </button>
                                                <button className="p-1.5 text-slate-400 hover:bg-slate-50 rounded-lg transition-colors" onClick={() => setEditingId(null)} title={t("manage.actions.cancel")}>
                                                    <X size={16} strokeWidth={2.5} />
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <button className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" onClick={() => {
                                                    setEditingId(term.id);
                                                    setEditForm({ term: term.source_text, category: term.category, case_sensitive: term.case_sensitive });
                                                }} title={t("manage.actions.edit")}>
                                                    <Edit size={16} />
                                                </button>
                                                <button className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" onClick={() => onConvertToGlossary(term)} title={t("manage.actions.convert_glossary")}>
                                                    <Table size={18} />
                                                </button>
                                                <button className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors" onClick={() => handleDelete(term.id)} title={t("common.delete")}>
                                                    <Trash2 size={16} />
                                                </button>
                                            </>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </div>
    );
}
