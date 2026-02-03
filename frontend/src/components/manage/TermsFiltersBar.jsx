import React from 'react';

export function TermsFiltersBar({
    t,
    filters,
    setFilters,
    categories,
    isSyncing,
    handleFullSync,
    errorMsg,
    exportCsv,
    onOpenImport,
}) {
    return (
        <div className="action-row flex items-center justify-between gap-3 bg-slate-50/70 border border-slate-200/70 rounded-2xl px-4 py-3 mb-4 shrink-0">
            <div className="flex flex-wrap gap-2 items-center">
                <input
                    className="text-input w-52 compact"
                    placeholder={t('manage.terms_tab.search_placeholder')}
                    value={filters.q}
                    onChange={(e) => setFilters((p) => ({ ...p, q: e.target.value }))}
                    onKeyDown={(e) => e.key === 'Enter' && setFilters((p) => ({ ...p, _refresh: Date.now() }))}
                />
                <select
                    className="select-input w-36 compact"
                    value={filters.category_id}
                    onChange={(e) => setFilters((p) => ({ ...p, category_id: e.target.value }))}
                >
                    <option value="">{t('manage.terms_tab.filter_category_all')}</option>
                    {categories.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                </select>
                <select
                    className="select-input w-28 compact"
                    value={filters.source}
                    onChange={(e) => setFilters((p) => ({ ...p, source: e.target.value }))}
                >
                    <option value="">{t('manage.terms_tab.filter_source_all')}</option>
                    <option value="reference">{t('manage.terms_tab.filter_source_reference')}</option>
                    <option value="terminology">{t('manage.terms_tab.filter_source_terminology')}</option>
                    <option value="manual">{t('manage.terms_tab.filter_source_manual')}</option>
                </select>
                <button
                    className={`btn ghost compact whitespace-nowrap ${isSyncing ? 'loading' : ''}`}
                    onClick={handleFullSync}
                    disabled={isSyncing}
                >
                    {isSyncing ? t('manage.terms_tab.syncing') : t('manage.terms_tab.sync_data')}
                </button>
                {errorMsg && <div className="text-xs text-red-500 font-bold ml-2">{errorMsg}</div>}
            </div>
            <div className="flex items-center gap-2">
                <div className="flex gap-2 items-center">
                    <button className="btn ghost compact" type="button" onClick={exportCsv}>{t('manage.actions.export_csv')}</button>
                    <button className="btn ghost compact" type="button" onClick={onOpenImport}>
                        {t('manage.actions.import_csv')}
                    </button>
                </div>
            </div>
        </div>
    );
}
