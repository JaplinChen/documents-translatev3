import React from "react";
import { useTranslation } from "react-i18next";

export function PreserveTermsHeader({ filterText, setFilterText, filterCategory, setFilterCategory, categories, getCategoryLabel, handleExport, handleImport }) {
    const { t } = useTranslation();
    return (
        <div className="action-row flex items-center justify-between">
            <div className="flex items-center gap-3">
                <input
                    className="select-input w-48 !pl-3 focus:ring-2 focus:ring-blue-100 transition-all"
                    type="text"
                    placeholder={t("manage.preserve.search_placeholder")}
                    value={filterText}
                    onChange={(e) => setFilterText(e.target.value)}
                />
                <select
                    className="select-input w-36 focus:ring-2 focus:ring-blue-100 transition-all font-medium text-slate-700"
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                >
                    <option value="all">{t("manage.preserve.category_all")}</option>
                    {categories.map(cat => (
                        <option key={cat} value={cat}>{getCategoryLabel(cat)}</option>
                    ))}
                </select>
            </div>
            <div className="flex gap-4 pr-2">
                <button className="text-xs font-bold text-slate-400 hover:text-blue-600 uppercase tracking-wider transition-all" type="button" onClick={handleExport}>
                    {t("manage.actions.export_csv")}
                </button>
                <label className="text-xs font-bold text-slate-400 hover:text-blue-600 uppercase tracking-wider cursor-pointer transition-all">
                    {t("manage.actions.import_csv")}
                    <input type="file" accept=".csv" onChange={handleImport} style={{ display: "none" }} />
                </label>
            </div>
        </div>
    );
}
