import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import BlockCard from "./BlockCard";
import { BatchReplaceToolbar } from "./BatchReplaceToolbar";
import { SlidePreview } from "./SlidePreview";
import { FileUp, Layers, Layout } from "lucide-react";
import { API_BASE } from "../constants";

export function EditorPanel({
    blocks,
    blockCount,
    filteredBlocks,
    filterText, setFilterText,
    filterType, setFilterType,
    filterSlide, setFilterSlide,
    onSelectAll,
    onClearSelection,
    onBlockSelect,
    onBlockChange,
    onOutputModeChange,
    onAddGlossary,
    onAddMemory,
    onBatchReplace,
    slideDimensions,
    mode,
    sourceLang,
    secondaryLang,
    extractLanguageLines,
    editorRefs
}) {
    const { t } = useTranslation();
    const [activeBlockId, setActiveBlockId] = useState(null);
    const [manualSlideIndex, setManualSlideIndex] = useState(null);

    // Reset manual index when blocks change or when filters change significantly
    useEffect(() => {
        setManualSlideIndex(null);
    }, [blockCount, filterSlide]);

    // Total pages calculation (from slideDimensions metadata or inferred)
    const totalPages = slideDimensions?.thumbnails?.length || 0;

    // Dynamic active slide index: follows active block (Hover), manual nav, or filter
    const activeBlock = activeBlockId ? blocks.find(b => b._uid === activeBlockId) : null;
    const filterIdx = (filterSlide && !isNaN(parseInt(filterSlide))) ? (parseInt(filterSlide) - 1) : null;

    // Priority:
    // 1. Hovered block's slide (activeBlock)
    // 2. Manual navigation (manualSlideIndex) - if something was clicked
    // 3. Filter slide (filterIdx)
    // 4. Default to first filtered block's slide
    const activeSlideIndex = activeBlock ? activeBlock.slide_index :
        (manualSlideIndex !== null ? manualSlideIndex :
            (filterIdx !== null ? filterIdx : (filteredBlocks[0]?.slide_index || 0)));

    const currentSlideBlocks = blocks.filter(b => b.slide_index === activeSlideIndex);

    // Stable thumbnail URL calculation
    const currentThumbPath = slideDimensions?.thumbnails?.[activeSlideIndex];
    // Ensure we handle absolute and relative paths correctly
    const thumbnailUrl = currentThumbPath ? (currentThumbPath.startsWith('http') ? currentThumbPath : (`${API_BASE}${currentThumbPath}`)) : null;

    return (
        <section className="panel panel-right">
            <div className="panel-header flex items-center justify-between border-b border-slate-200 pb-3 mb-2">
                <div className="flex flex-col">
                    <h2 className="text-xl font-bold text-slate-800 tracking-tight">{t("editor.title")}</h2>
                    <p className="text-xs text-slate-500 mt-1">{t("editor.summary", { total: blockCount, filtered: filteredBlocks.length })}</p>
                </div>
                {blockCount > 0 && (
                    <button
                        className="btn primary px-4 py-2 rounded-xl flex items-center gap-2 shadow-sm transition-all hover:scale-105 active:scale-95"
                        onClick={() => onSelectAll && onSelectAll("EXTRACT")}
                        title={t("sidebar.extract.refresh_hint")}
                    >
                        <Layers size={18} />
                        <span className="font-bold">{t("sidebar.extract.refresh_button")}</span>
                    </button>
                )}
            </div>

            {blockCount === 0 ? (
                <div className="empty-state-v2 flex flex-col items-center justify-center text-center p-8 animate-in fade-in zoom-in-95 duration-500" style={{ height: "calc(100% - var(--spacing-xl) * 2.5)" }}>
                    <div className="w-20 h-20 bg-blue-50 text-blue-500 rounded-3xl flex items-center justify-center mb-6 shadow-xl shadow-blue-500/10 ring-1 ring-blue-100 cursor-pointer hover:bg-blue-100 transition-all" onClick={() => onSelectAll && onSelectAll("EXTRACT")}>
                        <FileUp size={40} strokeWidth={1.5} />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800 mb-2">{t("editor.empty.title")}</h3>
                    <p className="text-sm text-slate-500 max-w-[280px] leading-relaxed mb-6">{t("editor.empty.hint")}</p>
                    <button className="btn primary px-8 py-3 rounded-2xl shadow-lg shadow-blue-500/20 mb-8" onClick={() => onSelectAll && onSelectAll("EXTRACT")}>
                        {t("sidebar.extract.refresh_button")}
                    </button>
                    <div className="grid grid-cols-2 gap-4 w-full max-w-sm">
                        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col items-center gap-2">
                            <Layout size={20} className="text-slate-400" />
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{t("editor.empty.preview")}</span>
                        </div>
                        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col items-center gap-2">
                            <Layers size={20} className="text-slate-400" />
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{t("editor.empty.batch")}</span>
                        </div>
                    </div>
                </div>
            ) : (
                <>
                    <div className="filter-row">
                        <div className="filter-item">
                            <label className="field-label">{t("editor.filter.search")}</label>
                            <input
                                className="select-input"
                                type="text"
                                value={filterText}
                                placeholder={t("editor.search_placeholder")}
                                onChange={(e) => setFilterText(e.target.value)}
                            />
                        </div>
                        <div className="filter-item">
                            <label className="field-label">{t("editor.filter.type")}</label>
                            <select className="select-input" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                                <option value="all">{t("editor.filter_type")}</option>
                                <option value="textbox">{t("components.editor.filter_textbox")}</option>
                                <option value="table_cell">{t("components.editor.filter_table")}</option>
                                <option value="notes">{t("components.editor.filter_notes")}</option>
                            </select>
                        </div>
                        <div className="filter-item">
                            <label className="field-label">{t("editor.filter.slide")}</label>
                            <input
                                className="select-input"
                                type="number"
                                value={filterSlide}
                                placeholder="0"
                                onChange={(e) => setFilterSlide(e.target.value)}
                            />
                        </div>
                        <div className="filter-actions flex gap-2 ml-auto">
                            <button className="btn ghost compact" type="button" onClick={onSelectAll}>{t("editor.select_all")}</button>
                            <button className="btn ghost compact" type="button" onClick={onClearSelection}>{t("editor.clear_selection")}</button>
                            {onBatchReplace && (
                                <BatchReplaceToolbar onReplace={onBatchReplace} disabled={blockCount === 0} />
                            )}
                        </div>
                    </div>

                    {/* High-Fidelity Preview Integration */}
                    {slideDimensions?.width > 0 && currentSlideBlocks.length > 0 ? (
                        <div className="editor-preview-outer-container max-h-[50vh] overflow-y-auto shadow-inner bg-slate-100/50 rounded-xl mb-4 border border-slate-200">
                            <div className="editor-preview-section p-4 pb-12">
                                <SlidePreview
                                    dimensions={slideDimensions}
                                    blocks={currentSlideBlocks}
                                    activeBlockId={activeBlockId}
                                    thumbnailUrl={thumbnailUrl}
                                    totalPages={totalPages}
                                    currentPage={activeSlideIndex}
                                    onPageChange={(index) => setManualSlideIndex(index)}
                                />
                            </div>
                        </div>
                    ) : null}

                    <div className="block-list">
                        {filteredBlocks.length > 200 && (
                            <div className="p-3 bg-amber-50 border-b border-amber-100 text-amber-700 text-xs text-center flex items-center justify-center gap-2">
                                <Layers size={14} />
                                <span>{t("editor.rendering_limit_hint", "Large document detected. Showing first 200 blocks for stability. Use search or slide filters to find other blocks.")}</span>
                            </div>
                        )}
                        {filteredBlocks.slice(0, 200).map((block, index) => (
                            <div
                                key={block._uid}
                                onMouseEnter={() => setActiveBlockId(block._uid)}
                                onMouseLeave={() => setActiveBlockId(null)}
                                className={activeBlockId === block._uid ? "ring-2 ring-blue-500 rounded-lg" : ""}
                            >
                                <BlockCard
                                    block={block}
                                    index={index}
                                    mode={mode}
                                    sourceLang={sourceLang}
                                    secondaryLang={secondaryLang}
                                    extractLanguageLines={extractLanguageLines}
                                    editorRefs={editorRefs}
                                    onBlockSelect={(checked) => onBlockSelect(block._uid, checked)}
                                    onBlockChange={(val) => onBlockChange(block._uid, val)}
                                    onEditorInput={(val) => onBlockChange(block._uid, val)}
                                    onOutputModeChange={(val) => onOutputModeChange(block._uid, val)}
                                    onAddGlossary={() => onAddGlossary(block)}
                                    onAddMemory={() => onAddMemory(block)}
                                />
                            </div>
                        ))}
                    </div>
                </>
            )}
        </section>
    );
}
