import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import BlockCard from "./BlockCard";
import { BatchReplaceToolbar } from "./BatchReplaceToolbar";
import { SlidePreview } from "./SlidePreview";
import { FileUp, Search, Layers, Layout } from "lucide-react";

export function EditorPanel({
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

    // Filter blocks for the current slide to show in preview
    const previewSlideIndex = parseInt(filterSlide) - 1;
    const currentSlideBlocks = filteredBlocks.filter(b => b.slide_index === previewSlideIndex);

    return (
        <section className="panel panel-right">
            <div className="panel-header">
                <div className="flex flex-col">
                    <h2 className="text-xl font-bold text-slate-800 tracking-tight">{t("editor.title")}</h2>
                    <p className="text-xs text-slate-500 mt-1">{t("editor.summary", { total: blockCount, filtered: filteredBlocks.length })}</p>
                </div>
            </div>

            {blockCount === 0 ? (
                <div className="empty-state-v2 flex flex-col items-center justify-center h-[calc(100%-80px)] text-center p-8 bg-white/50 animate-in fade-in zoom-in-95 duration-500">
                    <div className="w-20 h-20 bg-blue-50 text-blue-500 rounded-3xl flex items-center justify-center mb-6 shadow-xl shadow-blue-500/10 ring-1 ring-blue-100">
                        <FileUp size={40} strokeWidth={1.5} />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800 mb-2">{t("editor.empty.title")}</h3>
                    <p className="text-sm text-slate-500 max-w-[280px] leading-relaxed mb-6">{t("editor.empty.hint")}</p>
                    <div className="grid grid-cols-2 gap-4 w-full max-w-sm">
                        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col items-center gap-2">
                            <Layout size={20} className="text-slate-400" />
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">視覺預覽</span>
                        </div>
                        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 flex flex-col items-center gap-2">
                            <Layers size={20} className="text-slate-400" />
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">批次編輯</span>
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
                    {slideDimensions?.width > 0 ? (
                        currentSlideBlocks.length > 0 ? (
                            <div className="editor-preview-section p-4 bg-slate-50 border-b border-slate-200">
                                <SlidePreview
                                    dimensions={slideDimensions}
                                    blocks={currentSlideBlocks}
                                    activeBlockId={activeBlockId}
                                />
                            </div>
                        ) : null
                    ) : null}

                    <div className="block-list">
                        {(filteredBlocks || []).map((block, index) => (
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
                                    onEditorInput={(idx, val) => onBlockChange(block._uid, val)}
                                    onOutputModeChange={(idx, val) => onOutputModeChange(block._uid, val)}
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


