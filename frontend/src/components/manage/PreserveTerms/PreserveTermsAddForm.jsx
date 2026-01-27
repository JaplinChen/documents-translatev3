import React from "react";
import { useTranslation } from "react-i18next";
import { Plus } from "lucide-react";

export function PreserveTermsAddForm({ newTerm, setNewTerm, categories, getCategoryLabel, handleAdd, loading }) {
    const { t } = useTranslation();
    return (
        <div className="create-row bg-slate-50/80 p-3 px-5 rounded-2xl border border-slate-200/50 flex items-center gap-5 shadow-inner">
            <div className="flex-grow flex items-center gap-6">
                <div className="flex-1 space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.1em] ml-1">{t("manage.preserve.term_placeholder")}</label>
                    <input
                        className="text-input !py-2 !px-4 w-full !bg-white !border-slate-200 hover:border-blue-300 focus:ring-4 focus:ring-blue-50/50 transition-all outline-none text-sm"
                        type="text"
                        placeholder="e.g. Notion"
                        value={newTerm.term}
                        onChange={(e) => setNewTerm({ ...newTerm, term: e.target.value })}
                    />
                </div>
                <div className="w-32 space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.1em] ml-1">{t("manage.preserve.table.category")}</label>
                    <select
                        className="select-input !py-2 !px-3 w-full !bg-white !border-slate-200 hover:border-blue-300 transition-all outline-none text-sm font-medium"
                        value={newTerm.category}
                        onChange={(e) => setNewTerm({ ...newTerm, category: e.target.value })}
                    >
                        {categories.map(cat => (
                            <option key={cat} value={cat}>{getCategoryLabel(cat)}</option>
                        ))}
                    </select>
                </div>
                <div className="flex items-center gap-5 pt-5">
                    <label className="toggle-check flex items-center gap-2 cursor-pointer select-none group">
                        <input
                            type="checkbox"
                            className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 transition-all cursor-pointer"
                            checked={newTerm.case_sensitive}
                            onChange={(e) => setNewTerm({ ...newTerm, case_sensitive: e.target.checked })}
                        />
                        <span className="text-[11px] font-bold text-slate-500 group-hover:text-blue-600 transition-colors whitespace-nowrap">{t("manage.preserve.case_sensitive")}</span>
                    </label>
                    <button className="btn primary !h-10 !w-10 !p-0 rounded-xl shadow-lg shadow-blue-500/10 hover:shadow-blue-500/20 active:scale-95 transition-all duration-200 flex items-center justify-center" type="button" onClick={handleAdd} disabled={loading || !newTerm.term.trim()}>
                        <Plus size={20} strokeWidth={3} />
                    </button>
                </div>
            </div>
        </div>
    );
}
