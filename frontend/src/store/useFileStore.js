import { create } from 'zustand';

export const useFileStore = create((set) => ({
    file: null,
    blocks: [],

    // --- Actions ---
    setFile: (file) => set({ file, blocks: [] }),
    setBlocks: (blocks) => set(state => ({
        blocks: typeof blocks === 'function' ? blocks(state.blocks) : blocks
    })),

    updateBlock: (uid, updates) => set(state => ({
        blocks: state.blocks.map(b => b._uid === uid ? { ...b, ...updates } : b)
    })),

    selectBlock: (uid, selected) => set(state => ({
        blocks: state.blocks.map(b => b._uid === uid ? { ...b, selected } : b)
    })),

    selectAllBlocks: (selected = true) => set(state => ({
        blocks: state.blocks.map(b => ({ ...b, selected }))
    })),

    clearExtraction: () => set({ file: null, blocks: [] }),

    /**
     * Batch replace text in translated_text of selected (or all) blocks
     * @param {string} searchText - Text to search for
     * @param {string} replaceText - Text to replace with
     * @param {object} options - { useRegex: boolean, caseSensitive: boolean, selectedOnly: boolean }
     * @returns {number} - Count of replacements made
     */
    batchReplace: (searchText, replaceText, options = {}) => {
        const { useRegex = false, caseSensitive = true, selectedOnly = true } = options;
        let replaceCount = 0;

        set(state => {
            const newBlocks = state.blocks.map(block => {
                // Skip if selectedOnly and block not selected
                if (selectedOnly && block.selected === false) return block;

                const text = block.translated_text || '';
                if (!text) return block;

                let newText;
                if (useRegex) {
                    try {
                        const flags = caseSensitive ? 'g' : 'gi';
                        const regex = new RegExp(searchText, flags);
                        const matches = text.match(regex);
                        if (matches) replaceCount += matches.length;
                        newText = text.replace(regex, replaceText);
                    } catch (e) {
                        // Invalid regex, skip
                        return block;
                    }
                } else {
                    const searchLower = searchText.toLowerCase();
                    const textLower = text.toLowerCase();

                    if (caseSensitive) {
                        const parts = text.split(searchText);
                        if (parts.length > 1) {
                            replaceCount += parts.length - 1;
                            newText = parts.join(replaceText);
                        } else {
                            return block;
                        }
                    } else {
                        // Case-insensitive exact match
                        let result = '';
                        let lastIndex = 0;
                        let idx = textLower.indexOf(searchLower);
                        while (idx !== -1) {
                            replaceCount++;
                            result += text.substring(lastIndex, idx) + replaceText;
                            lastIndex = idx + searchText.length;
                            idx = textLower.indexOf(searchLower, lastIndex);
                        }
                        result += text.substring(lastIndex);
                        newText = result;
                    }
                }

                if (newText !== text) {
                    return { ...block, translated_text: newText };
                }
                return block;
            });

            return { blocks: newBlocks };
        });

        return replaceCount;
    }
}));

