import React, { useLayoutEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * SlidePreview - A high-fidelity visualization of a PPTX slide layout.
 * Uses Points as coordinates to mirror PowerPoint's positioning.
 */
export function SlidePreview({ dimensions, blocks, activeBlockId, thumbnailUrl, totalPages, currentPage, onPageChange }) {
    const { t } = useTranslation();
    const { width, height } = dimensions;
    const canvasRef = useRef(null);
    const blockRefs = useRef(new Map());

    const hasNavigation = totalPages > 1;

    if (!width || !height) return (
        <div className="bg-slate-100 border border-dashed border-slate-300 rounded-lg p-8 text-center">
            <p className="text-slate-400 text-sm">{t("editor.preview_no_dims", "Slide dimensions not available. Please extract again.")}</p>
        </div>
    );

    useLayoutEffect(() => {
        if (!canvasRef.current) return;
        const el = canvasRef.current;
        el.style.aspectRatio = `${width}/${height}`;
        el.style.backgroundColor = '#fff';
        el.style.backgroundSize = '100% 100%';
        el.style.backgroundRepeat = 'no-repeat';
        el.style.backgroundPosition = 'center';
        el.style.backgroundImage = thumbnailUrl
            ? `url("${thumbnailUrl}")`
            : 'linear-gradient(to right, #f8fafc 1px, transparent 1px), linear-gradient(to bottom, #f8fafc 1px, transparent 1px)';
    }, [width, height, thumbnailUrl]);

    useLayoutEffect(() => {
        blockRefs.current.forEach((el, key) => {
            if (!el) return;
            const block = blocks.find((b) => b._uid === key);
            if (!block) return;
            const left = (block.x / width) * 100;
            const top = (block.y / height) * 100;
            const w = (block.width / width) * 100;
            const h = (block.height / height) * 100;
            el.style.left = `${left}%`;
            el.style.top = `${top}%`;
            el.style.width = `${w}%`;
            el.style.height = `${h}%`;
        });
    }, [blocks, width, height]);

    return (
        <div className="slide-preview-container mb-2">
            <div className="flex items-center justify-between mb-1 sticky top-0 z-30 bg-white/90 backdrop-blur-sm py-1 px-3 -mx-1 border-b border-slate-200">
                <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    {t("editor.preview_title", "Slide Preview")}
                </h3>
                {hasNavigation && (
                    <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-2 py-0.5 shadow-sm">
                        <button
                            className="p-0.5 hover:bg-slate-100 rounded text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            onClick={() => onPageChange && onPageChange(currentPage - 1)}
                            disabled={currentPage <= 0}
                            title={t("editor.prev_page", "Previous Page")}
                        >
                            <span className="text-sm font-bold">←</span>
                        </button>
                        <span className="text-[10px] font-mono font-bold text-blue-600 px-1">
                            {currentPage + 1} / {totalPages}
                        </span>
                        <button
                            className="p-0.5 hover:bg-slate-100 rounded text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            onClick={() => onPageChange && onPageChange(currentPage + 1)}
                            disabled={currentPage >= totalPages - 1}
                            title={t("editor.next_page", "Next Page")}
                        >
                            <span className="text-sm font-bold">→</span>
                        </button>
                    </div>
                )}
            </div>

            <div
                ref={canvasRef}
                className="slide-canvas relative bg-white border border-slate-200 shadow-xl mx-auto overflow-hidden"
            >
                {blocks.length === 0 && (
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-slate-300 text-[10px]">{t("editor.preview_no_blocks", "No editable blocks on this slide")}</span>
                    </div>
                )}
                {blocks.map((block) => {
                    const isActive = block._uid === activeBlockId;

                    return (
                        <div
                            key={block._uid}
                            ref={(el) => {
                                if (el) blockRefs.current.set(block._uid, el);
                                else blockRefs.current.delete(block._uid);
                            }}
                            className={`absolute transition-all duration-200 cursor-pointer 
                            ${isActive
                                    ? 'border-2 border-blue-500 bg-blue-500/20 z-10 shadow-sm'
                                    : 'border border-transparent hover:border-blue-300 hover:bg-blue-500/5'
                                }`}
                            title={block.source_text?.substring(0, 50)}
                            onClick={() => document.getElementById(`block-${block._uid}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })}
                        />
                    );
                })}
            </div>

            <div className="sticky bottom-0 z-20 flex justify-between items-center mt-1 px-3 py-1 bg-white/90 backdrop-blur-sm -mx-1 border-t border-slate-200">
                <span className="text-[9px] font-mono text-slate-400">
                    {Math.round(width)}pt x {Math.round(height)}pt
                </span>
                <span className="text-[9px] text-slate-400">
                    {t("editor.preview_hint", "Positions are approximate (Points)")}
                </span>
            </div>
        </div>
    );
}
