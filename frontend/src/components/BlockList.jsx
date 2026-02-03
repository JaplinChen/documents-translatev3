import { useTranslation } from "react-i18next";
import BlockCard from "./BlockCard";

/**
 * List of translation blocks with filter controls
 */
export default function BlockList({
    blocks,
    filteredBlocks,
    mode,
    sourceLang,
    secondaryLang,
    targetLang,
    editorRefs,
    filterText,
    filterType,
    filterSlide,
    onFilterTextChange,
    onFilterTypeChange,
    onFilterSlideChange,
    onSelectAll,
    onClearSelection,
    onBlockSelect,
    onBlockChange,
    onOutputModeChange,
    onEditorInput,
    onAddGlossary,
    onAddMemory
}) {
    const { t } = useTranslation();
    return (
        <>
            <div className="filter-row">
                <div className="filter-item">
                    <label className="field-label" htmlFor="filter-text">{t("editor.filter.search")}</label>
                    <input
                        id="filter-text"
                        className="select-input"
                        type="text"
                        value={filterText}
                        placeholder={t("editor.search_placeholder")}
                        onChange={(e) => onFilterTextChange(e.target.value)}
                    />
                </div>
                <div className="filter-item">
                    <label className="field-label" htmlFor="filter-type">{t("editor.filter.type")}</label>
                    <select id="filter-type" className="select-input" value={filterType} onChange={(e) => onFilterTypeChange(e.target.value)}>
                        <option value="all">{t("editor.filter_type")}</option>
                        <option value="textbox">{t("components.editor.filter_textbox")}</option>
                        <option value="table_cell">{t("components.editor.filter_table")}</option>
                        <option value="notes">{t("components.editor.filter_notes")}</option>
                    </select>
                </div>
                <div className="filter-item">
                    <label className="field-label" htmlFor="filter-slide">{t("editor.filter.slide")}</label>
                    <input id="filter-slide" className="select-input" type="number" value={filterSlide} placeholder="0" onChange={(e) => onFilterSlideChange(e.target.value)} />
                </div>
                <div className="filter-actions">
                    <button className="btn ghost" type="button" onClick={onSelectAll}>{t("editor.select_all")}</button>
                    <button className="btn ghost" type="button" onClick={onClearSelection}>{t("editor.clear_selection")}</button>
                </div>
            </div>

            <div className="block-list">
                {filteredBlocks.length === 0 ? (
                    <div className="empty-state">
                        <p>{t("editor.empty.title")}</p>
                        <span>{t("editor.empty.hint")}</span>
                    </div>
                ) : (() => {
                    // Optimization: Build a UID -> Index map to avoid O(N^2) lookups
                    const blocksMap = new Map();
                    blocks.forEach((item, idx) => {
                        blocksMap.set(item._uid, idx);
                    });

                    // Optimization: Limit rendering to keep UI snappy for 1000+ blocks
                    // We render more as translation progresses or user scrolls if we had virtualization,
                    // but for a quick fix, let's at least optimize the logic.
                    return filteredBlocks.map((block, filteredIndex) => {
                        const originalIndex = blocksMap.get(block._uid) ?? filteredIndex;
                        return (
                            <BlockCard
                                key={block._uid || `block-${filteredIndex}`}
                                block={block}
                                index={originalIndex}
                                mode={mode}
                                sourceLang={sourceLang}
                                secondaryLang={secondaryLang}
                                targetLang={targetLang}
                                editorRefs={editorRefs}
                                onBlockSelect={onBlockSelect}
                                onBlockChange={onBlockChange}
                                onOutputModeChange={onOutputModeChange}
                                onEditorInput={onEditorInput}
                                onAddGlossary={onAddGlossary}
                                onAddMemory={onAddMemory}
                            />
                        );
                    });
                })()}
            </div>
        </>
    );
}
