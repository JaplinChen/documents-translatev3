import React, { useLayoutEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

export function ColumnPanel({
    show,
    onClose,
    columns,
    visibleCols,
    toggleColumn,
    anchorRef,
    t,
}) {
    const panelRef = useRef(null);

    useLayoutEffect(() => {
        if (!show || !panelRef.current || !anchorRef.current) return;
        const rect = anchorRef.current.getBoundingClientRect();
        const top = rect.bottom + 8;
        const left = Math.min(rect.left, window.innerWidth - 340);
        panelRef.current.style.top = `${top}px`;
        panelRef.current.style.left = `${left}px`;
    }, [show, anchorRef]);

    if (!show) return null;

    return createPortal(
        <>
            <div className="fixed inset-0 z-[9998]" onClick={onClose}></div>
            <div
                ref={panelRef}
                className="fixed bg-white rounded-2xl border border-slate-200 shadow-2xl z-[9999] transition-all p-4 w-[320px]"
            >
                <div className="flex items-center justify-between border-b border-slate-100 mb-3 pb-2">
                    <div className="text-sm font-bold text-slate-700">
                        {t('manage.terms_tab.columns_panel.title', '顯示欄位')}
                    </div>
                    <button className="btn ghost compact" onClick={onClose}>
                        <X size={14} />
                    </button>
                </div>
                <div className="flex flex-col gap-1 max-h-[300px] overflow-y-auto">
                    {columns.map((col) => (
                        <label
                            key={col.key}
                            className="flex items-center gap-2 px-2 py-1.5 hover:bg-slate-50 rounded cursor-pointer"
                        >
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
    );
}
