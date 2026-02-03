import React from 'react';
import { Plus } from 'lucide-react';
import { getCategoryLabel } from './preserveTabHelpers';

export function PreserveFiltersBar({
    t,
    filterText,
    setFilterText,
    filterCategory,
    setFilterCategory,
    categories,
    handleAdd,
    handleExport,
    handleImport,
}) {
    return (
        <div className="action-row flex items-center gap-2 w-full justify-between flex-wrap bg-slate-50/70 border border-slate-200/70 rounded-2xl px-4 py-3 mb-4 shrink-0">
            <div className="flex items-center gap-2 flex-wrap">
                <input
                    className="text-input w-48 compact"
                    type="text"
                    placeholder={t('manage.preserve.search_placeholder')}
                    value={filterText}
                    onChange={(e) => setFilterText(e.target.value)}
                />
                <select
                    className="select-input w-36 compact"
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                >
                    <option value="all">{t('manage.preserve.category_all')}</option>
                    {categories.map((cat) => (
                        <option key={cat} value={cat}>{getCategoryLabel(cat, t)}</option>
                    ))}
                </select>
                <button className="btn primary compact !px-3" type="button" onClick={() => handleAdd()} title={t('manage.actions.add')}>
                    <Plus size={16} />
                </button>
            </div>
            <div className="flex items-center gap-2">
                <button className="btn ghost compact" type="button" onClick={handleExport}>
                    {t('manage.actions.export_csv')}
                </button>
                <label className="btn ghost compact">
                    {t('manage.actions.import_csv')}
                    <input type="file" accept=".csv" className="hidden-input" onChange={handleImport} />
                </label>
            </div>
        </div>
    );
}
