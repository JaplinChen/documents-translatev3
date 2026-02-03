import React from 'react';

export function TermsBatchActions({
    t,
    categories,
    selectedIds,
    batchCategory,
    setBatchCategory,
    batchSource,
    setBatchSource,
    batchUpdate,
    batchDelete,
}) {
    if (!selectedIds.length) return null;

    return (
        <div className="batch-actions flex flex-wrap gap-2 mt-3">
            <select className="select-input w-36 compact" value={batchCategory} onChange={(e) => setBatchCategory(e.target.value)}>
                <option value="">{t('manage.terms_tab.batch.category')}</option>
                {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                ))}
            </select>
            <button className="btn ghost compact" onClick={() => batchUpdate({ category_id: batchCategory })} disabled={!batchCategory}>
                {t('manage.terms_tab.batch.apply_category')}
            </button>
            <select className="select-input w-28 compact" value={batchSource} onChange={(e) => setBatchSource(e.target.value)}>
                <option value="">{t('manage.terms_tab.batch.source')}</option>
                <option value="reference">{t('manage.terms_tab.filter_source_reference')}</option>
                <option value="terminology">{t('manage.terms_tab.filter_source_terminology')}</option>
                <option value="manual">{t('manage.terms_tab.filter_source_manual')}</option>
            </select>
            <button className="btn ghost compact" onClick={() => batchUpdate({ source: batchSource })} disabled={!batchSource}>
                {t('manage.terms_tab.batch.apply_source')}
            </button>
            <button className="btn ghost compact !text-red-500" onClick={() => {
                if (!window.confirm(t('manage.terms_tab.batch.delete_confirm', { count: selectedIds.length }))) return;
                batchDelete();
            }}>{t('manage.terms_tab.batch.delete')}</button>
        </div>
    );
}
