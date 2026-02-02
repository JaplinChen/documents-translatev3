import React, { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { createPortal } from "react-dom";
import { X, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

/**
 * @typedef {Object} ColumnDef
 * @property {string} key - Unique key for the column
 * @property {string} [label] - Display label
 * @property {string} [width] - CSS grid width (e.g., "100px", "1fr")
 * @property {boolean} [sortable] - Whether the column is sortable
 * @property {boolean} [resizable] - Whether the column is resizable
 * @property {function(any, any): React.ReactNode} [render] - Custom renderer (value, row)
 * @property {string} [headerClass] - Custom class for header cell
 * @property {string} [cellClass] - Custom class for body cell
 */

/**
 * Generic Data Table Component
 * 
 * @param {Object} props
 * @param {ColumnDef[]} props.columns - Column definitions
 * @param {any[]} props.data - Data array
 * @param {string} props.rowKey - Key to use as unique row identifier (default: "id")
 * @param {string[]} props.selectedIds - Array of selected row IDs
 * @param {function(string[])} props.onSelectionChange - Callback for selection change
 * @param {string} [props.sortKey] - Current sort key
 * @param {string} [props.sortDir] - Current sort direction ("asc" | "desc")
 * @param {function(string)} props.onSort - Callback for sort toggle
 * @param {boolean} [props.loading] - Loading state
 * @param {string} [props.storageKey] - Key for localStorage persistence of column settings
 * @param {boolean} [props.compact] - Initial compact mode state
 * @param {function(boolean)} [props.onCompactChange] - Callback when compact mode changes
 * @param {Object} [props.emptyState] - Custom empty state content
 * @param {string} [props.className] - Extra CSS classes
 * @param {string} [props.highlightColor] - Background color for specific highlights
 * @param {function(any)} [props.onRowClick] - Callback for row click
 * @param {function} [props.onLoadMore] - Callback to load more data (pagination)
 * @param {boolean} [props.canLoadMore] - Whether more data is available
 * @param {number} [props.totalCount] - Total number of items (for footer display)
 */
export function DataTable({
    columns = [],
    data = [],
    rowKey = "id",
    selectedIds = [],
    onSelectionChange,
    sortKey,
    sortDir,
    onSort,
    loading = false,
    storageKey,
    compact = false,
    onCompactChange,
    emptyState,
    className = "",
    highlightColor,
    onRowClick,
    onLoadMore,
    canLoadMore = false,
    totalCount,
}) { // Added props for Load More
    const { t } = useTranslation();
    const resizingRef = useRef(null);
    const colBtnRef = useRef(null);
    const [showColPanel, setShowColPanel] = useState(false);

    // Internal state for column management if not controlled externally
    const [colWidths, setColWidths] = useState(() => {
        if (!storageKey) return {};
        try {
            const saved = localStorage.getItem(`${storageKey}_widths`);
            return saved ? JSON.parse(saved) : {};
        } catch {
            return {};
        }
    });

    const [visibleCols, setVisibleCols] = useState(() => {
        if (!storageKey) return columns.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
        try {
            const saved = localStorage.getItem(`${storageKey}_visible`);
            // Merge with current columns to ensure new columns appear
            const stored = saved ? JSON.parse(saved) : {};
            return columns.reduce((acc, col) => ({
                ...acc,
                [col.key]: stored[col.key] !== false // Default to true if not explicitly false
            }), {});
        } catch {
            return columns.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
        }
    });

    // Save column settings when changed
    const updateColWidth = (key, width) => {
        const newWidths = { ...colWidths, [key]: width };
        setColWidths(newWidths);
        if (storageKey) {
            localStorage.setItem(`${storageKey}_widths`, JSON.stringify(newWidths));
        }
    };

    const toggleColumn = (key, isVisible) => {
        const newVisible = { ...visibleCols, [key]: isVisible };
        setVisibleCols(newVisible);
        if (storageKey) {
            localStorage.setItem(`${storageKey}_visible`, JSON.stringify(newVisible));
        }
    };

    // Filter visible columns
    const effectiveColumns = columns.filter(col => visibleCols[col.key] !== false);

    // Calculate grid template
    const gridTemplateColumns = [
        onSelectionChange ? "40px" : null, // Selection column
        ...effectiveColumns.map(col => {
            const w = colWidths[col.key] ? `${colWidths[col.key]}px` : (col.width || "1fr");
            return w;
        })
    ].filter(Boolean).join(" ");

    // Handlers
    const handleSelectAll = (checked) => {
        if (checked) {
            onSelectionChange(data.map(item => item[rowKey]));
        } else {
            onSelectionChange([]);
        }
    };

    const handleSelectRow = (id, checked) => {
        if (checked) {
            onSelectionChange([...selectedIds, id]);
        } else {
            onSelectionChange(selectedIds.filter(sid => sid !== id));
        }
    };

    // Resize Logic
    const startResize = (key, event) => {
        event.preventDefault();
        event.stopPropagation();
        const startX = event.clientX;
        // Find parent cell width
        const parentCell = event.currentTarget.parentElement;
        const currentWidth = parentCell?.getBoundingClientRect().width || 100;

        resizingRef.current = { key, startX, startWidth: currentWidth };

        document.body.style.userSelect = "none";
        document.body.style.cursor = "col-resize";

        const handleMove = (moveEvent) => {
            if (!resizingRef.current) return;
            const delta = moveEvent.clientX - resizingRef.current.startX;
            const nextWidth = Math.max(60, resizingRef.current.startWidth + delta);
            updateColWidth(resizingRef.current.key, nextWidth);
        };

        const handleUp = () => {
            resizingRef.current = null;
            document.body.style.userSelect = "";
            document.body.style.cursor = "";
            document.removeEventListener("mousemove", handleMove);
            document.removeEventListener("mouseup", handleUp);
        };

        document.addEventListener("mousemove", handleMove);
        document.addEventListener("mouseup", handleUp);
    };

    const allSelected = data.length > 0 && selectedIds.length === data.length;

    return (
        <div className={`data-table-container flex flex-col h-full min-h-0 relative ${className}`}>
            {/* Columns Configuration Panel */}
            {showColPanel && createPortal(
                <>
                    <div className="fixed inset-0 z-[9998]" onClick={() => setShowColPanel(false)}></div>
                    <div
                        className={`fixed bg-white rounded-2xl border border-slate-200 shadow-2xl z-[9999] transition-all p-4 w-[320px]`}
                        style={{
                            top: (colBtnRef.current?.getBoundingClientRect().bottom || 0) + 8,
                            left: Math.min(
                                colBtnRef.current?.getBoundingClientRect().left || 0,
                                window.innerWidth - 340
                            )
                        }}
                    >
                        <div className="flex items-center justify-between border-b border-slate-100 mb-3 pb-2">
                            <div className="text-sm font-bold text-slate-700">{t("manage.terms_tab.columns_panel.title", "顯示欄位")}</div>
                            <button className="btn ghost compact" onClick={() => setShowColPanel(false)}><X size={14} /></button>
                        </div>
                        <div className="flex flex-col gap-1 max-h-[300px] overflow-y-auto">
                            {columns.map(col => (
                                <label key={col.key} className="flex items-center gap-2 px-2 py-1.5 hover:bg-slate-50 rounded cursor-pointer">
                                    <input
                                        type="checkbox"
                                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
                                        checked={visibleCols[col.key] !== false}
                                        onChange={(e) => toggleColumn(col.key, e.target.checked)}
                                    />
                                    <span className="text-sm text-slate-700">{col.label}</span>
                                </label>
                            ))}
                        </div>
                    </div>
                </>,
                document.body
            )}

            {/* Config Toolbar */}

            <div className={`data-table ${compact ? "is-compact text-xs" : "text-sm"} flex flex-col h-full min-h-0`}>

                {/* Scrollable Container (Header + Body) to ensure alignment */}
                <div className="flex-1 overflow-y-auto min-h-0 relative">

                    {/* Header - Sticky */}
                    <div className="unified-data-row data-header sticky top-0 z-20 bg-white shadow-sm shrink-0 border-b border-slate-200" style={{ gridTemplateColumns }}>
                        {onSelectionChange && (
                            <div className="data-cell w-10 shrink-0 flex items-center justify-center border-r border-slate-100">
                                <input type="checkbox" checked={allSelected} onChange={(e) => handleSelectAll(e.target.checked)} />
                            </div>
                        )}

                        {effectiveColumns.map((col, idx) => (
                            <div key={col.key} className={`data-cell relative flex items-center ${col.headerClass || ""} ${col.sortable ? "cursor-pointer hover:bg-slate-50" : ""}`}
                                onClick={() => col.sortable && onSort && onSort(col.key)}
                            >
                                <span className="truncate font-bold text-slate-700">{col.label}</span>
                                {col.sortable && (
                                    <div className="ml-1.5 shrink-0 transition-opacity">
                                        {sortKey === col.key ? (
                                            <span className="text-[10px] text-blue-500 font-bold leading-none">
                                                {sortDir === "asc" ? "▲" : "▼"}
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
                                        onClick={(e) => { e.stopPropagation(); setShowColPanel(true); }}
                                        title={t("manage.terms_tab.columns_panel.show_columns")}
                                    >
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                                    </button>
                                )}

                                {/* Resizer */}
                                {(col.resizable !== false) && (
                                    <span
                                        className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-400 opacity-0 hover:opacity-100 transition-opacity z-10"
                                        onMouseDown={(e) => startResize(col.key, e)}
                                        onClick={(e) => e.stopPropagation()}
                                    />
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Loading Overlay */}
                    {loading && (
                        <div className="absolute inset-0 bg-white/50 z-30 flex items-center justify-center pt-10">
                            <div className="animate-spin text-2xl">⌛</div>
                        </div>
                    )}

                    {/* Empty State */}
                    {!loading && data.length === 0 && (
                        <div className="p-8 text-center text-slate-400">
                            {emptyState || t("common.no_data", "無資料")}
                        </div>
                    )}

                    {/* Data Rows */}
                    {!loading && data.map((row, rowIdx) => {
                        const rowId = row[rowKey];
                        const isSelected = selectedIds.includes(rowId);

                        return (
                            <div
                                key={rowId}
                                className={`unified-data-row ${isSelected ? "is-selected" : ""} hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-0`}
                                style={{ gridTemplateColumns }}
                                onClick={() => onRowClick && onRowClick(row)}
                            >
                                {onSelectionChange && (
                                    <div className="data-cell w-10 shrink-0 flex items-center justify-center border-r border-slate-100" onClick={(e) => e.stopPropagation()}>
                                        <input type="checkbox" checked={isSelected} onChange={(e) => handleSelectRow(rowId, e.target.checked)} />
                                    </div>
                                )}

                                {effectiveColumns.map(col => (
                                    <div key={col.key} className={`data-cell ${col.cellClass || ""} overflow-hidden`}>
                                        {col.render ? col.render(row[col.key], row) : row[col.key]}
                                    </div>
                                ))}
                            </div>
                        );
                    })}
                </div>

                {/* Footer (Total count, etc) - optional */}
                <div className="shrink-0 border-t border-slate-200 bg-white p-2 text-xs text-slate-500 flex justify-between items-center h-10">
                    <div className="flex items-center gap-4">
                        <span className="font-medium bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                            {t("manage.list_summary", {
                                shown: data.length,
                                total: totalCount || data.length
                            })}
                        </span>
                        {canLoadMore && onLoadMore && (
                            <button
                                className="text-blue-600 hover:text-blue-800 font-bold hover:underline py-1 px-2 rounded hover:bg-blue-50 transition-colors"
                                onClick={onLoadMore}
                            >
                                {t("manage.actions.load_more", "載入更多")}
                            </button>
                        )}
                    </div>
                    {onCompactChange && (
                        <label className="flex items-center gap-2 cursor-pointer select-none py-1 px-2 hover:bg-slate-50 rounded">
                            <input type="checkbox" checked={compact} onChange={(e) => onCompactChange(e.target.checked)} />
                            {t("manage.table.compact", "緊湊模式")}
                        </label>
                    )}
                </div>
            </div>
        </div>
    );
}
