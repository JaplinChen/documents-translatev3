import React from 'react';

export function TableRows({
    data,
    getRowId,
    selectedIds,
    onSelectionChange,
    handleSelectRow,
    effectiveColumns,
    gridTemplateColumns,
    onRowClick,
}) {
    return data.map((row) => {
        const rowId = getRowId(row);
        const isSelected = selectedIds.includes(rowId);

        return (
            <div
                key={rowId}
                className={`unified-data-row ${isSelected ? 'is-selected' : ''} hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-0`}
                style={{ gridTemplateColumns }}
                onClick={() => onRowClick && onRowClick(row)}
            >
                {onSelectionChange && (
                    <div
                        className="data-cell w-10 shrink-0 flex items-center justify-center border-r border-slate-100"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => handleSelectRow(rowId, e.target.checked)}
                        />
                    </div>
                )}

                {effectiveColumns.map((col) => (
                    <div key={col.key} className={`data-cell ${col.cellClass || ''} overflow-hidden`}>
                        {col.render ? col.render(row[col.key], row) : row[col.key]}
                    </div>
                ))}
            </div>
        );
    });
}
