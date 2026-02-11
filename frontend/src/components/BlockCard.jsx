import { useTranslation } from "react-i18next";
import { memo } from "react";
import { resolveOutputMode, stripBilingualText } from "../utils/appHelpers";

/**
 * Single block card for displaying/editing translation block
 */
const BlockCard = memo(({
    block,
    index,
    mode,
    sourceLang,
    secondaryLang,
    targetLang,
    editorRefs,
    onBlockSelect,
    onBlockChange,
    onOutputModeChange,
    onEditorInput,
    onAddGlossary,
    onAddMemory
}) => {
    const { t } = useTranslation();
    const outputMode = resolveOutputMode(block);
    const isBilingual = mode === "bilingual" || block.mode === "bilingual";
    const isCorrection = mode === "correction" || block.mode === "correction";
    const displayTranslatedText = stripBilingualText(block.source_text, block.translated_text, targetLang);

    return (
        <div className={`block-card 
            ${block.selected === false ? "is-muted" : ""} 
            ${block.isTranslating ? "is-translating" : ""}
            ${isBilingual ? "is-bilingual" : ""}
        `}>
            <div className="block-meta">
                <span className="block-number">#{index + 1}</span>
                <label className="select-box">
                    <input type="checkbox" checked={block.selected !== false} onChange={(e) => onBlockSelect(e.target.checked)} />
                    <span>{t("components.block_card.apply")}</span>
                </label>
                {block.block_type === "spreadsheet_cell" ? (
                    <>
                        {block.locations?.length > 1 && !block.locations.every(l => l.sheet_name === block.sheet_name) ? (
                            <span>{t("components.block_card.multi_sheets", "Multi-sheets")}</span>
                        ) : null}

                        <div className="flex flex-wrap gap-1 max-w-[280px]">
                            {(() => {
                                const colors = [
                                    "bg-blue-50 text-blue-700 border-blue-200",
                                    "bg-emerald-50 text-emerald-700 border-emerald-200",
                                    "bg-amber-50 text-amber-700 border-amber-200",
                                    "bg-purple-50 text-purple-700 border-purple-200",
                                    "bg-rose-50 text-rose-700 border-rose-200",
                                    "bg-cyan-50 text-cyan-700 border-cyan-200",
                                ];
                                const getSheetColor = (name) => {
                                    if (!name) return "";
                                    let hash = 0;
                                    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
                                    return colors[Math.abs(hash) % colors.length];
                                };

                                const locs = (block.locations && block.locations.length > 0)
                                    ? block.locations
                                    : [{ sheet_name: block.sheet_name, cell_address: block.cell_address }];

                                return locs.slice(0, 3).map((loc, i) => (
                                    <span key={i} className={`pill font-mono text-[10px] py-0.5 border ${getSheetColor(loc.sheet_name)}`}>
                                        {loc.sheet_name ? `${loc.sheet_name}!${loc.cell_address}` : loc.cell_address}
                                    </span>
                                ));
                            })()}
                            {block.locations?.length > 3 && (
                                <span className="pill font-mono text-[10px] py-0.5" title={block.locations.slice(3).map(l => `${l.sheet_name}!${l.cell_address}`).join(", ")}>
                                    +{block.locations.length - 3}
                                </span>
                            )}
                        </div>
                    </>
                ) : (
                    <>
                        <span>{t("components.block_card.slide")} {block.slide_index}</span>
                        <span>{t("components.block_card.shape")} {block.shape_id}</span>
                        <span className="pill">{block.block_type}</span>
                    </>
                )}
                {isBilingual && <span className="pill bg-indigo-100 text-indigo-700 border border-indigo-200">{t("components.block_card.bilingual")}</span>}
                {isCorrection && <span className="pill bg-violet-100 text-violet-700 border border-violet-200">{t("components.block_card.correction")}</span>}
                {block.isTranslating ? (
                    <span className="status-pill is-running">{t("components.block_card.translating")}</span>
                ) : block.updatedAt ? (
                    <span className="status-pill">{t("components.block_card.updated_at", { time: block.updatedAt })}</span>
                ) : null}
                {mode === "correction" && block.correction_temp ? (
                    <span className="status-pill bg-emerald-50 text-emerald-600">{t("components.block_card.draft")}</span>
                ) : null}

                <div className="block-meta-tools ml-auto flex gap-1">
                    <button className="btn-tool" type="button" onClick={() => onAddGlossary(block)} title={t("components.block_card.tools_glossary_title")}>
                        <span className="icon">📖</span> {t("components.block_card.glossary")}
                    </button>
                    <button className="btn-tool" type="button" onClick={() => onAddMemory(block)} title={t("components.block_card.tools_memory_title")}>
                        <span className="icon">🧠</span> {t("components.block_card.memory")}
                    </button>
                </div>
            </div>
            <div className="block-body h-full">
                {/* Source Column */}
                <div className="flex flex-col h-full min-h-0">
                    <div className="field-label-row shrink-0">
                        <span className="field-label">{t("components.block_card.source")}</span>
                        {mode === "correction" && (
                            <label className="toggle-check">
                                <input
                                    type="checkbox"
                                    checked={outputMode === "source"}
                                    onChange={() => onOutputModeChange("source")}
                                    disabled={block.isTranslating}
                                />
                                <span>{t("components.block_card.output")}</span>
                            </label>
                        )}
                    </div>
                    {/* Source Content - adaptive height */}
                    <div className="readonly-box shrink-0 overflow-y-auto" data-testid="block-source-text">{block.source_text}</div>
                </div>

                {/* Target Column */}
                <div className="flex flex-col min-h-0">
                    <div className="field-label-row shrink-0 text-[10px] mb-1">
                        <span className="field-label">{t("components.block_card.target")}</span>
                        {mode === "correction" && (
                            <label className="toggle-check">
                                <input
                                    type="checkbox"
                                    checked={outputMode === "translated"}
                                    onChange={() => onOutputModeChange("translated")}
                                    disabled={block.isTranslating}
                                />
                                <span>{t("components.block_card.output")}</span>
                            </label>
                        )}
                    </div>
                    {/* Target Content - adaptive height */}
                    <textarea
                        className={`${isCorrection ? "correction-editor" : "textarea"} focus:ring-2 focus:ring-blue-100 outline-none resize-y`}
                        value={displayTranslatedText || ""}
                        onChange={(e) => onBlockChange(e.target.value)}
                        placeholder={t("components.block_card.placeholder")}
                        disabled={block.isTranslating}
                        data-testid="block-target-text"
                        data-uid={block._uid}
                        ref={(node) => { if (editorRefs.current) editorRefs.current[block._uid] = node; }}
                    />
                </div>
            </div>
        </div>
    );
});

export default BlockCard;
