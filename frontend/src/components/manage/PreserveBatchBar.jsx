import React from 'react';

export function PreserveBatchBar({
    t,
    selectedIds,
    handleBatchConvertToGlossary,
    handleBatchDelete,
}) {
    if (!selectedIds.length) return null;

    return (
        <div className="ml-auto flex items-center gap-2 animate-in fade-in slide-in-from-right-2">
            <button className="btn ghost compact !text-blue-600 text-xs font-bold" onClick={handleBatchConvertToGlossary}>
                {t('manage.batch.to_glossary')}
            </button>
            <button className="btn ghost compact !text-red-500 text-xs font-bold" onClick={handleBatchDelete}>
                {t('manage.batch.delete')}
            </button>
        </div>
    );
}
