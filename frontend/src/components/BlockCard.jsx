import { useTranslation } from "react-i18next";
import { resolveOutputMode, normalizeText } from "../utils/appHelpers";

/**
 * Single block card for displaying/editing translation block
 */
export default function BlockCard({
    block,
    index,
    mode,
    sourceLang,
    secondaryLang,
    editorRefs,
    onBlockSelect,
    onBlockChange,
    onOutputModeChange,
    onEditorInput,
    onAddGlossary,
    onAddMemory
}) {
    const { t } = useTranslation();
    const outputMode = resolveOutputMode(block);
    const isBilingual = mode === "bilingual" || block.mode === "bilingual";
    const isCorrection = mode === "correction" || block.mode === "correction";

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
                <span>{t("components.block_card.slide")} {block.slide_index}</span>
                <span>{t("components.block_card.shape")} {block.shape_id}</span>
                {block.is_table && block.row_no != null && block.col_no != null && (
                    <span className="pill">{`R${block.row_no}C${block.col_no}`}</span>
                )}
                <span className="pill">{block.block_type}</span>
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
                    {/* Source Content - filled height */}
                    <div className="readonly-box flex-1 h-full overflow-y-auto">{block.source_text}</div>
                </div>

                {/* Target Column */}
                <div className="flex flex-col h-full min-h-0">
                    <div className="field-label-row shrink-0">
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
                    {/* Target Content - filled height */}
                    <textarea
                        className={`${isCorrection ? "correction-editor" : "textarea"} flex-1 h-full focus:ring-2 focus:ring-blue-100 outline-none resize-none`}
                        value={block.translated_text || ""}
                        onChange={(e) => onBlockChange(e.target.value)}
                        placeholder={t("components.block_card.placeholder")}
                        disabled={block.isTranslating}
                        ref={(node) => { if (editorRefs.current) editorRefs.current[block._uid] = node; }}
                    />
                </div>
            </div>
        </div>
    );
}
