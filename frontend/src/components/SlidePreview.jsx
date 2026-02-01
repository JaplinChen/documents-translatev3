import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * SlidePreview - A high-fidelity visualization of a PPTX slide layout.
 * Uses Points as coordinates to mirror PowerPoint's positioning.
 */
export function SlidePreview({ dimensions, blocks, activeBlockId, thumbnailUrl, totalPages, currentPage, onPageChange }) {
    const { t } = useTranslation();
    const { width, height } = dimensions;

    const hasNavigation = totalPages > 1;

    if (!width || !height) return (
        <div className="bg-slate-100 border border-dashed border-slate-300 rounded-lg p-8 text-center">
            <p className="text-slate-400 text-sm">{t("editor.preview_no_dims", "Slide dimensions not available. Please extract again.")}</p>
        </div>
    );

    // Fixed width for the preview container, height scales automatically to maintain ratio
    const PREVIEW_WIDTH = 480;
    const scale = PREVIEW_WIDTH / width;
    const previewHeight = height * scale;

    return (
        <div className="slide-preview-container mb-2">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    {t("editor.preview_title", "Slide Preview")}
                </h3>
                {hasNavigation && (
                    <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-2 py-1 shadow-sm">
                        <button
                            className="p-1 hover:bg-slate-100 rounded text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            onClick={() => onPageChange && onPageChange(currentPage - 1)}
                            disabled={currentPage <= 0}
                            title={t("editor.prev_page", "Previous Page")}
                        >
                            <span className="text-sm font-bold">←</span>
                        </button>
                        <span className="text-[10px] font-mono font-bold text-slate-500 px-1">
                            {currentPage + 1} / {totalPages}
                        </span>
                        <button
                            className="p-1 hover:bg-slate-100 rounded text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
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
                className="slide-canvas relative bg-white border border-slate-200 shadow-sm overflow-hidden"
                style={{
                    width: `${PREVIEW_WIDTH}px`,
                    height: `${previewHeight}px`,
                    backgroundSize: 'contain',
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'center',
                    backgroundColor: '#fff',
                    backgroundImage: thumbnailUrl ? `url("${thumbnailUrl}")` : 'linear-gradient(to right, #f8fafc 1px, transparent 1px), linear-gradient(to bottom, #f8fafc 1px, transparent 1px)',
                    backgroundSize: thumbnailUrl ? 'contain' : '20px 20px'
                }}
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
                            className={`absolute border transition-all duration-200 cursor-default group 
                                ${isActive ? 'border-blue-500 bg-blue-500/10 z-10 ring-2 ring-blue-500/20 shadow-lg' : 'border-slate-300/40 bg-slate-50/5 hover:border-slate-500 hover:bg-slate-100/10'}`}
                            style={{
                                left: `${block.x * scale}px`,
                                top: `${block.y * scale}px`,
                                width: `${block.width * scale}px`,
                                height: `${block.height * scale}px`,
                            }}
                            title={`Slide ${block.slide_index + 1}, Shape ${block.shape_id}`}
                        >
                            {/* Inner hint or placeholder if needed */}
                            <div className="w-full h-full overflow-hidden flex items-start justify-start p-0.5">
                                <span className={`text-[8px] font-medium leading-[1] truncate block 
                                    ${isActive ? 'text-blue-700 opacity-100 font-bold bg-white/60 rounded px-0.5' : 'text-slate-500 opacity-40 group-hover:opacity-100 bg-white/30 rounded px-0.5'}`}>
                                    {block.translated_text || block.source_text}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="flex justify-between items-center mt-1 px-1">
                <span className="text-[10px] text-slate-400 italic">
                    {Math.round(width)}pt x {Math.round(height)}pt
                </span>
                <span className="text-[10px] text-slate-400">
                    {t("editor.preview_hint", "Positions are approximate (Points)")}
                </span>
            </div>
        </div>
    );
}
