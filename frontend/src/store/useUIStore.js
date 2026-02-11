import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { APP_STATUS } from '../constants';

export const useUIStore = create(persist((set) => ({
    // --- Global Status ---
    status: "",
    appStatus: APP_STATUS.IDLE,
    busy: false,
    setStatus: (status) => set({ status }),
    setAppStatus: (appStatus) => set({ appStatus }),
    setBusy: (busy) => set({ busy }),

    // --- Modals ---
    llmOpen: false,
    manageOpen: false,
    setLlmOpen: (open) => set({ llmOpen: open }),
    setManageOpen: (open) => set({ manageOpen: open }),

    // --- Tabs ---
    llmTab: "llm",
    manageTab: "glossary",
    slideDimensions: { width: 0, height: 0 },
    setLlmTab: (tab) => set({ llmTab: tab }),
    setManageTab: (tab) => set({ manageTab: tab }),
    setSlideDimensions: (dims) => set({ slideDimensions: dims }),


    // --- Processing Settings ---
    mode: "bilingual",
    bilingualLayout: "new_slide",
    layoutParams: {},
    sourceLang: "",
    secondaryLang: "",
    targetLang: "zh-TW",
    sourceLocked: false,
    secondaryLocked: false,
    targetLocked: false,
    layoutDefs: [],

    setMode: (mode) => set({ mode }),
    setBilingualLayout: (layout) => set({ bilingualLayout: layout }),
    setLayoutParams: (params) => set((state) => ({
        layoutParams: typeof params === 'function' ? params(state.layoutParams) : (params || {})
    })),
    setSourceLang: (lang) => set({ sourceLang: lang }),
    setSecondaryLang: (lang) => set({ secondaryLang: lang }),
    setTargetLang: (lang) => set({ targetLang: lang }),
    setSourceLocked: (locked) => set({ sourceLocked: locked }),
    setSecondaryLocked: (locked) => set({ secondaryLocked: locked }),
    setTargetLocked: (locked) => set({ targetLocked: locked }),
    setLayoutDefs: (defs) => set({ layoutDefs: defs || [] }),

    // --- Filters ---
    filterText: "",
    filterType: "all",
    filterSlide: "",
    setFilterText: (text) => set({ filterText: text }),
    setFilterType: (type) => set({ filterType: type }),
    setFilterSlide: (slide) => set({ filterSlide: slide }),

    // --- TM Highlight ---
    lastTranslationAt: null,
    setLastTranslationAt: (timestamp) => set({ lastTranslationAt: timestamp }),
    lastGlossaryAt: null,
    setLastGlossaryAt: (timestamp) => set({ lastGlossaryAt: timestamp }),
    lastMemoryAt: null,
    setLastMemoryAt: (timestamp) => set({ lastMemoryAt: timestamp }),
    lastPreserveAt: null,
    setLastPreserveAt: (timestamp) => set({ lastPreserveAt: timestamp }),
}), {
    name: "ui_store",
    partialize: (state) => ({
        manageOpen: state.manageOpen,
        manageTab: state.manageTab,
        mode: state.mode,
        bilingualLayout: state.bilingualLayout,
        layoutParams: state.layoutParams,
        sourceLang: state.sourceLang,
        secondaryLang: state.secondaryLang,
        targetLang: state.targetLang,
        sourceLocked: state.sourceLocked,
        secondaryLocked: state.secondaryLocked,
        targetLocked: state.targetLocked,
    }),
}));
