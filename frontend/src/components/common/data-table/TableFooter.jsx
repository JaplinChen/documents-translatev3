import React from 'react';

export function TableFooter({
    dataLength,
    totalCount,
    canLoadMore,
    onLoadMore,
    compact,
    onCompactChange,
    t,
}) {
    return (
        <div className="shrink-0 border-t border-slate-200 bg-white p-2 text-xs text-slate-500 flex justify-between items-center h-10">
            <div className="flex items-center gap-4">
                <span className="font-medium bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                    {t('manage.list_summary', {
                        shown: dataLength,
                        total: totalCount || dataLength,
                    })}
                </span>
                {canLoadMore && onLoadMore && (
                    <button
                        className="text-blue-600 hover:text-blue-800 font-bold hover:underline py-1 px-2 rounded hover:bg-blue-50 transition-colors"
                        onClick={onLoadMore}
                    >
                        {t('manage.actions.load_more', '載入更多')}
                    </button>
                )}
            </div>
            {onCompactChange && (
                <label className="flex items-center gap-2 cursor-pointer select-none py-1 px-2 hover:bg-slate-50 rounded">
                    <input type="checkbox" checked={compact} onChange={(e) => onCompactChange(e.target.checked)} />
                    {t('manage.table.compact', '緊湊模式')}
                </label>
            )}
        </div>
    );
}
