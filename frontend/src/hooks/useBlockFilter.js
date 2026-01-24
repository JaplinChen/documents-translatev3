import { useMemo } from 'react';

/**
 * Custom hook to filter translation blocks based on type, slide, and text search
 * @param {Array} blocks - Array of block objects
 * @param {string} filterType - Filter by block type ('all', 'textbox', 'table_cell', 'notes')
 * @param {string} filterSlide - Filter by slide index (empty string for no filter)
 * @param {string} filterText - Search text to filter by source or translated text
 * @returns {Array} Filtered array of blocks
 */
export function useBlockFilter(blocks, filterType, filterSlide, filterText) {
  return useMemo(() => {
    return blocks.filter((block) => {
      // Filter by block type
      if (filterType !== "all" && block.block_type !== filterType) {
        return false;
      }

      // Filter by slide index
      if (filterSlide.trim() !== "") {
        const slideValue = Number(filterSlide);
        if (!Number.isNaN(slideValue) && block.slide_index !== slideValue) {
          return false;
        }
      }

      // Filter by search text in source or translated text
      if (filterText.trim() !== "") {
        const needle = filterText.toLowerCase();
        const source = (block.source_text || "").toLowerCase();
        const translated = (block.translated_text || "").toLowerCase();
        if (!source.includes(needle) && !translated.includes(needle)) {
          return false;
        }
      }

      return true;
    });
  }, [blocks, filterType, filterSlide, filterText]);
}