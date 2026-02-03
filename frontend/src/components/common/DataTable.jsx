import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { ColumnPanel } from './data-table/ColumnPanel';
import { TableHeader } from './data-table/TableHeader';
import { TableRows } from './data-table/TableRows';
import { TableFooter } from './data-table/TableFooter';

export function DataTable({
    columns = [],
    data = [],
    rowKey = 'id',
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
    className = '',
    onRowClick,
    onLoadMore,
    canLoadMore = false,
    totalCount,
}) {
    const { t } = useTranslation();
    const resizingRef = useRef(null);
    const colBtnRef = useRef(null);
    const [showColPanel, setShowColPanel] = useState(false);

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
        if (!storageKey) {
            return columns.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
        }
        try {
            const saved = localStorage.getItem(`${storageKey}_visible`);
            const stored = saved ? JSON.parse(saved) : {};
            return columns.reduce((acc, col) => ({
                ...acc,
                [col.key]: stored[col.key] !== false,
            }), {});
        } catch {
            return columns.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
        }
    });

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

    const effectiveColumns = columns.filter((col) => visibleCols[col.key] !== false);

    const gridTemplateColumns = [
        onSelectionChange ? '40px' : null,
        ...effectiveColumns.map((col) => {
            const w = colWidths[col.key] ? `${colWidths[col.key]}px` : (col.width || '1fr');
            return w;
        }),
    ].filter(Boolean).join(' ');

    const getRowId = (row) => (typeof rowKey === 'function' ? rowKey(row) : row[rowKey]);

    const handleSelectAll = (checked) => {
        if (checked) {
            onSelectionChange(data.map((item) => getRowId(item)));
        } else {
            onSelectionChange([]);
        }
    };

    const handleSelectRow = (id, checked) => {
        if (checked) {
            onSelectionChange([...selectedIds, id]);
        } else {
            onSelectionChange(selectedIds.filter((sid) => sid !== id));
        }
    };

    const startResize = (key, event) => {
        event.preventDefault();
        event.stopPropagation();
        const startX = event.clientX;
        const parentCell = event.currentTarget.parentElement;
        const currentWidth = parentCell?.getBoundingClientRect().width || 100;

        resizingRef.current = { key, startX, startWidth: currentWidth };
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';

        const handleMove = (moveEvent) => {
            if (!resizingRef.current) return;
            const delta = moveEvent.clientX - resizingRef.current.startX;
            const nextWidth = Math.max(60, resizingRef.current.startWidth + delta);
            updateColWidth(resizingRef.current.key, nextWidth);
        };

        const handleUp = () => {
            resizingRef.current = null;
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
            document.removeEventListener('mousemove', handleMove);
            document.removeEventListener('mouseup', handleUp);
        };

        document.addEventListener('mousemove', handleMove);
        document.addEventListener('mouseup', handleUp);
    };

    const allSelected = data.length > 0 && selectedIds.length === data.length;

    return (
        <div className={`data-table-container flex flex-col h-full min-h-0 relative ${className}`}>
            <ColumnPanel
                show={showColPanel}
                onClose={() => setShowColPanel(false)}
                columns={columns}
                visibleCols={visibleCols}
                toggleColumn={toggleColumn}
                anchorRef={colBtnRef}
                t={t}
            />

            <div className={`data-table ${compact ? 'is-compact text-xs' : 'text-sm'} flex flex-col h-full min-h-0`}>
                <div className="flex-1 overflow-y-auto min-h-0 relative">
                    <TableHeader
                        gridTemplateColumns={gridTemplateColumns}
                        onSelectionChange={onSelectionChange}
                        allSelected={allSelected}
                        handleSelectAll={handleSelectAll}
                        effectiveColumns={effectiveColumns}
                        sortKey={sortKey}
                        sortDir={sortDir}
                        onSort={onSort}
                        storageKey={storageKey}
                        colBtnRef={colBtnRef}
                        setShowColPanel={setShowColPanel}
                        startResize={startResize}
                        t={t}
                    />

                    {loading && (
                        <div className="absolute inset-0 bg-white/50 z-30 flex items-center justify-center pt-10">
                            <div className="animate-spin text-2xl">⌛</div>
                        </div>
                    )}

                    {!loading && data.length === 0 && (
                        <div className="p-8 text-center text-slate-400">
                            {emptyState || t('common.no_data', '無資料')}
                        </div>
                    )}

                    {!loading && (
                        <TableRows
                            data={data}
                            getRowId={getRowId}
                            selectedIds={selectedIds}
                            onSelectionChange={onSelectionChange}
                            handleSelectRow={handleSelectRow}
                            effectiveColumns={effectiveColumns}
                            gridTemplateColumns={gridTemplateColumns}
                            onRowClick={onRowClick}
                        />
                    )}
                </div>

                <TableFooter
                    dataLength={data.length}
                    totalCount={totalCount}
                    canLoadMore={canLoadMore}
                    onLoadMore={onLoadMore}
                    compact={compact}
                    onCompactChange={onCompactChange}
                    t={t}
                />
            </div>
        </div>
    );
}
