export const PRESERVE_CATEGORY_TRANSLATION = '翻譯';

export const buildGlossaryEntry = ({
    blockOrEntry,
    sourceLang,
    targetLang,
    filename,
}) => {
    const rawCategoryId = blockOrEntry.category_id;
    return {
        id: blockOrEntry.id,
        source_lang: blockOrEntry.source_lang || sourceLang || 'vi',
        target_lang: blockOrEntry.target_lang || targetLang || 'zh-TW',
        source_text: (blockOrEntry.source_text || blockOrEntry.text || '').trim(),
        target_text: (blockOrEntry.target_text || blockOrEntry.translated_text || '').trim(),
        priority: blockOrEntry.priority != null ? Number(blockOrEntry.priority) : 0,
        category_id: rawCategoryId === '' || rawCategoryId == null ? null : Number(rawCategoryId),
        filename: blockOrEntry.filename || filename || '',
    };
};

export const buildMemoryEntry = ({
    blockOrEntry,
    sourceLang,
    targetLang,
}) => {
    const rawCategoryId = blockOrEntry.category_id;
    return {
        id: blockOrEntry.id,
        source_lang: blockOrEntry.source_lang || sourceLang || 'vi',
        target_lang: blockOrEntry.target_lang || targetLang || 'zh-TW',
        source_text: (blockOrEntry.source_text || blockOrEntry.text || '').trim(),
        target_text: (blockOrEntry.target_text || blockOrEntry.translated_text || '').trim(),
        category_id: rawCategoryId === '' || rawCategoryId == null ? null : Number(rawCategoryId),
    };
};
