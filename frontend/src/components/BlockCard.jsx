import { useTranslation } from "react-i18next";
import { resolveOutputMode, extractLanguageLines, normalizeText } from "../utils";

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



    return (
        <div className={`block-card ${block.selected === false ? "is-muted" : ""} ${block.isTranslating ? "is-translating" : ""}`}>
            <div className="block-meta">
                <span className="block-number">#{index + 1}</span>
                <label className="select-box">
                    <input type="checkbox" checked={block.selected !== false} onChange={(e) => onBlockSelect(index, e.target.checked)} />
                    <span>{t("components.block_card.apply")}</span>
                </label>
                <span>{t("components.block_card.slide")} {block.slide_index}</span>
                <span>{t("components.block_card.shape")} {block.shape_id}</span>
                <span className="pill">{block.block_type}</span>
                {block.isTranslating ? (
                    <span className="status-pill is-running">{t("components.block_card.translating")}</span>
                ) : block.updatedAt ? (
                    <span className="status-pill">{t("components.block_card.updated_at", { time: block.updatedAt })}</span>
                ) : null}
                {mode === "correction" && block.correction_temp ? (
                    <span className="status-pill">暫存</span>
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
                                <input type="checkbox" checked={outputMode === "source"} onChange={() => onOutputModeChange(index, "source")} />
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
                                <input type="checkbox" checked={outputMode === "translated"} onChange={() => onOutputModeChange(index, "translated")} />
                                <span>{t("components.block_card.output")}</span>
                            </label>
                        )}
                    </div>
                    {/* Target Content - filled height */}
                    {mode === "correction" ? (
                        <div
                            className="correction-editor flex-1 h-full overflow-y-auto border border-slate-300 rounded p-2"
                            contentEditable
                            role="textbox"
                            aria-multiline="true"
                            suppressContentEditableWarning
                            ref={(node) => { editorRefs.current[index] = node; }}
                            onInput={(e) => onEditorInput(index, e)}
                        >
                            {block.translated_text || ""}
                        </div>
                    ) : (
                        <textarea
                            className="textarea flex-1 h-full"
                            value={block.translated_text || ""}
                            onChange={(e) => onBlockChange(index, e.target.value)}
                            placeholder={t("components.block_card.placeholder")}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}
