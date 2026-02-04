import React from 'react';

export function TableFooter({
    dataLength,
    totalCount,
    canLoadMore,
    onLoadMore,
    compact,
    onCompactChange,
    t,
    page,
    pageSize,
    onPageChange,
    onPageSizeChange,
    pageSizeOptions = [50, 100, 200, 500],
}) {
    const effectiveTotal = totalCount ?? dataLength;
    const effectivePageSize = pageSize || dataLength || 1;
    const totalPages = Math.max(1, Math.ceil(effectiveTotal / Math.max(1, effectivePageSize)));
    const currentPage = Math.min(Math.max(page || 1, 1), totalPages);
    const showPagination = typeof onPageChange === 'function' && effectiveTotal > 0;

    return (
        <div className="shrink-0 border-t border-slate-200 bg-white p-2 text-xs text-slate-500 flex justify-between items-center h-10">
            <div className="flex items-center gap-4">
                <span className="font-medium bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                    {t('manage.list_summary', {
                        shown: dataLength,
                        total: effectiveTotal,
                    })}
                </span>
                {!showPagination && canLoadMore && onLoadMore && (
                    <button
                        className="text-blue-600 hover:text-blue-800 font-bold hover:underline py-1 px-2 rounded hover:bg-blue-50 transition-colors"
                        onClick={onLoadMore}
                    >
                        {t('manage.actions.load_more', '載入更多')}
                    </button>
                )}
                {showPagination && (
                    <div className="flex items-center gap-2">
                        <button
                            className="btn ghost compact"
                            type="button"
                            onClick={() => onPageChange(currentPage - 1)}
                            disabled={currentPage <= 1}
                        >
                            {t('manage.learning.prev_page', '上一頁')}
                        </button>
                        <span className="text-slate-400">
                            {t('manage.learning.page', { page: currentPage, total: totalPages })}
                        </span>
                        <button
                            className="btn ghost compact"
                            type="button"
                            onClick={() => onPageChange(currentPage + 1)}
                            disabled={currentPage >= totalPages}
                        >
                            {t('manage.learning.next_page', '下一頁')}
                        </button>
                        {onPageSizeChange && (
                            <select
                                className="select-input compact w-20"
                                value={effectivePageSize}
                                onChange={(e) => onPageSizeChange(Number(e.target.value))}
                            >
                                {pageSizeOptions.map((size) => (
                                    <option key={`page-size-${size}`} value={size}>{size}</option>
                                ))}
                            </select>
                        )}
                    </div>
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
