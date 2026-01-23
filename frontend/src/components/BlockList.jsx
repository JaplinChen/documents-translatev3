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
    return (
        <>
            <div className="filter-row">
                <div className="filter-item">
                    <label className="field-label" htmlFor="filter-text">搜尋</label>
                    <input
                        id="filter-text"
                        className="select-input"
                        type="text"
                        value={filterText}
                        placeholder="搜尋原文/翻譯"
                        onChange={(e) => onFilterTextChange(e.target.value)}
                    />
                </div>
                <div className="filter-item">
                    <label className="field-label" htmlFor="filter-type">類型</label>
                    <select id="filter-type" className="select-input" value={filterType} onChange={(e) => onFilterTypeChange(e.target.value)}>
                        <option value="all">全部</option>
                        <option value="textbox">textbox</option>
                        <option value="table_cell">table_cell</option>
                        <option value="notes">notes</option>
                    </select>
                </div>
                <div className="filter-item">
                    <label className="field-label" htmlFor="filter-slide">Slide</label>
                    <input id="filter-slide" className="select-input" type="number" value={filterSlide} placeholder="0" onChange={(e) => onFilterSlideChange(e.target.value)} />
                </div>
                <div className="filter-actions">
                    <button className="btn ghost" type="button" onClick={onSelectAll}>全選</button>
                    <button className="btn ghost" type="button" onClick={onClearSelection}>清除</button>
                </div>
            </div>

            <div className="block-list">
                {filteredBlocks.length === 0 ? (
                    <div className="empty-state">
                        <p>尚未抽取任何文字區塊</p>
                        <span>請先上傳文件並按下「提取術語」</span>
                    </div>
                ) : (
                    filteredBlocks.map((block, filteredIndex) => {
                        const index = blocks.findIndex((item) => item._uid === block._uid);
                        return (
                            <BlockCard
                                key={block._uid || `${block.slide_index}-${block.shape_id}-${filteredIndex}`}
                                block={block}
                                index={index}
                                mode={mode}
                                sourceLang={sourceLang}
                                secondaryLang={secondaryLang}
                                editorRefs={editorRefs}
                                onBlockSelect={onBlockSelect}
                                onBlockChange={onBlockChange}
                                onOutputModeChange={onOutputModeChange}
                                onEditorInput={onEditorInput}
                                onAddGlossary={onAddGlossary}
                                onAddMemory={onAddMemory}
                            />
                        );
                    })
                )}
            </div>
        </>
    );
}
