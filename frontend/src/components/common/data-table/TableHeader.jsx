import React, { useLayoutEffect, useRef } from 'react';
import { ArrowUpDown } from 'lucide-react';

export function TableHeader({
    gridTemplateColumns,
    onSelectionChange,
    allSelected,
    handleSelectAll,
    effectiveColumns,
    sortKey,
    sortDir,
    onSort,
    storageKey,
    colBtnRef,
    setShowColPanel,
    startResize,
    t,
}) {
    const rowRef = useRef(null);

    useLayoutEffect(() => {
        if (!rowRef.current) return;
        rowRef.current.style.gridTemplateColumns = gridTemplateColumns;
    }, [gridTemplateColumns]);

    return (
        <div
            ref={rowRef}
            className="unified-data-row data-header sticky top-0 z-20 bg-white shadow-sm shrink-0 border-b border-slate-200"
        >
            {onSelectionChange && (
                <div className="data-cell w-10 shrink-0 flex items-center justify-center border-r border-slate-100">
                    <input
                        type="checkbox"
                        checked={allSelected}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                    />
                </div>
            )}

            {effectiveColumns.map((col, idx) => {
                const colSortKey = col.sortKey ?? col.key;
                return (
                <div
                    key={col.key}
                    className={`data-cell relative flex items-center ${col.headerClass || ''} ${col.sortable ? 'cursor-pointer hover:bg-slate-50' : ''}`}
                    onClick={() => col.sortable && onSort && onSort(colSortKey)}
                >
                    <span className="truncate font-bold text-slate-700">{col.label}</span>
                    {col.sortable && (
                        <div className="ml-1.5 shrink-0 transition-opacity">
                            {sortKey === colSortKey ? (
                                <span className="text-[10px] text-blue-500 font-bold leading-none">
                                    {sortDir === 'asc' ? '▲' : '▼'}
                                </span>
                            ) : (
                                <ArrowUpDown size={12} className="text-slate-300 opacity-40 group-hover:opacity-100" />
                            )}
                        </div>
                    )}

                    {idx === effectiveColumns.length - 1 && storageKey && (
                        <button
                            ref={colBtnRef}
                            className="ml-auto opacity-50 hover:opacity-100 p-1"
                            onClick={(e) => {
                                e.stopPropagation();
                                setShowColPanel(true);
                            }}
                            title={t('manage.terms_tab.columns_panel.show_columns')}
                        >
                            <svg
                                width="12"
                                height="12"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            >
                                <circle cx="12" cy="12" r="3"></circle>
                                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                            </svg>
                        </button>
                    )}

                    {(col.resizable !== false) && (
                        <span
                            className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-400 opacity-0 hover:opacity-100 transition-opacity z-10"
                            onMouseDown={(e) => startResize(col.key, e)}
                            onClick={(e) => e.stopPropagation()}
                        />
                    )}
                </div>
            )})}
        </div>
    );
}
