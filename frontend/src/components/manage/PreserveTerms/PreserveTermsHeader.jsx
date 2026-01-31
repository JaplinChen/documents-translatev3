import React from "react";
import { useTranslation } from "react-i18next";
import { Plus } from "lucide-react";

export function PreserveTermsHeader({
    filterText,
    setFilterText,
    filterCategory,
    setFilterCategory,
    categories,
    getCategoryLabel,
    handleExport,
    handleImport,
    shownCount,
    totalCount,
    canLoadMore,
    onLoadMore,
    onAdd,
    compactTable,
    setCompactTable
}) {
    const { t } = useTranslation();
    return (
        <div className="action-row flex items-center gap-2 w-full justify-between flex-wrap">
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
                <button className="btn primary compact !px-3" type="button" onClick={() => onAdd()} title={t("manage.actions.add")}>
                    <Plus size={16} />
                </button>
                <span className="text-xs font-bold text-slate-400">
                    {t("manage.list_summary", { shown: shownCount, total: totalCount })}
                </span>
            </div>
            <div className="flex items-center gap-2">
                <button className="btn ghost compact" type="button" onClick={handleExport}>
                    {t("manage.actions.export_csv")}
                </button>
                <label className="btn ghost compact">
                    {t("manage.actions.import_csv")}
                    <input type="file" accept=".csv" className="hidden-input" onChange={handleImport} />
                </label>
                <label className="flex items-center gap-2 px-2 text-xs text-slate-500 border-l border-slate-200 cursor-pointer whitespace-nowrap">
                    <input
                        type="checkbox"
                        checked={compactTable}
                        onChange={(e) => setCompactTable(e.target.checked)}
                    />
                    {t("manage.table.compact")}
                </label>
                {canLoadMore && (
                    <button className="btn ghost compact" type="button" onClick={onLoadMore}>
                        {t("manage.actions.load_more")}
                    </button>
                )}
            </div>
        </div>
    );
}
