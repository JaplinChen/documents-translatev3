import React, { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

// Constants & Utils
import { API_BASE, APP_STATUS, LANGUAGE_OPTIONS } from "./constants";
import { CJK_REGEX, VI_REGEX } from "./utils/regex";
import { extractLanguageLines } from "./utils/appHelpers";

// Stores
import { useFileStore } from "./store/useFileStore";
import { useSettingsStore } from "./store/useSettingsStore";
import { useUIStore } from "./store/useUIStore";

// Hooks
import { useTerminology } from "./hooks/useTerminology";
import { useDocumentProcessor } from "./hooks/useDocumentProcessor";
import { usePanelResize } from "./hooks/usePanelResize";
import { useBlockFilter } from "./hooks/useBlockFilter";

// Components
import SettingsModal from "./components/SettingsModal";
import ManageModal from "./components/ManageModal";
import { Navbar } from "./components/Navbar";
import { Sidebar } from "./components/Sidebar";
import { EditorPanel } from "./components/EditorPanel";

function App() {
  const { t } = useTranslation();

  // --- Stores ---
  // Use selective subscription to avoid full app re-renders on every block change
  const file = useFileStore(state => state.file);
  const blocks = useFileStore(state => state.blocks);
  const updateBlock = useFileStore(state => state.updateBlock);
  const selectBlock = useFileStore(state => state.selectBlock);
  const setFile = useFileStore(state => state.setFile);
  const setBlocks = useFileStore(state => state.setBlocks);
  const selectAllBlocks = useFileStore(state => state.selectAllBlocks);
  const batchReplace = useFileStore(state => state.batchReplace);

  const settings = useSettingsStore(); // Settings don't change often, keep for now
  const ui = useUIStore(); // UI state changes often but usually isolated

  const leftPanelRef = useRef(null);
  const editorRefs = useRef({});

  // --- Logic Hooks ---
  const tm = useTerminology();
  const processor = useDocumentProcessor();


  usePanelResize(leftPanelRef, blocks.length);

  const filteredBlocks = useBlockFilter(blocks, ui.filterType, ui.filterSlide, ui.filterText);

  const applyDetectedLanguages = (summary) => {
    const primary = summary?.primary || "";
    const secondary = summary?.secondary || "";
    if (!ui.sourceLocked && primary) ui.setSourceLang(primary);
    if (!ui.secondaryLocked && secondary) ui.setSecondaryLang(secondary);
    if (!ui.targetLocked) ui.setTargetLang(secondary || "zh-TW");
  };

  // --- Initial Extract Effect ---
  useEffect(() => {
    if (!file) return;
    processor.handleExtract().then(applyDetectedLanguages);
  }, [file]);

  const handleBlockChange = (uid, value) => {
    // === 自動學習：捕捉用戶修正行為 ===
    const block = blocks.find(b => b._uid === uid || b.client_id === uid);
    if (block && block.translated_text && value && block.translated_text !== value) {
      // 簡易啟發式偵測：如果長度變化不大，可能是術語修正
      if (Math.abs(block.translated_text.length - value.length) < 10) {
        // 延遲紀錄，避免頻繁打字觸發 (此處由 debounce 邏輯處理或簡單包裝)
        tm.recordFeedback({
          source: block.source_text,
          target: value,
          sourceLang: ui.sourceLang,
          targetLang: ui.targetLang
        });
      }
    }
    updateBlock(uid, { translated_text: value });
  };

  const handleBlockSelect = (uid, checked) => {
    selectBlock(uid, checked);
  };

  const handleOutputModeChange = (uid, value) => {
    updateBlock(uid, { output_mode: value });
  };

  // Robust stepper logic using Enum
  const isExportFinished = ui.appStatus === APP_STATUS.EXPORT_COMPLETED || ui.appStatus === APP_STATUS.EXPORTING;
  const isTranslatingOrDone = blocks.some(b => b.translated_text) || ui.appStatus === APP_STATUS.TRANSLATING || ui.appStatus === APP_STATUS.TRANSLATION_COMPLETED;

  let currentStep = 1;
  if (isExportFinished) currentStep = 4;
  else if (isTranslatingOrDone) currentStep = 3;
  else if (blocks.length > 0) currentStep = 2;

  const steps = [
    { id: 1, label: t("nav.step1") },
    { id: 2, label: t("nav.step2") },
    { id: 3, label: t("nav.step3") },
    { id: 4, label: t("nav.step4") }
  ];

  // Helper to resolve translation objects from store
  const resolveStoreStatus = (status) => {
    if (!status) return "";
    if (typeof status === 'string') return status;
    if (status.key) return t(status.key, status.params);
    return "";
  };

  return (
    <div className="app">
      <div className="app-sticky-header">
        <Navbar
          currentStep={currentStep}
          steps={steps}
          status={ui.status}
          appStatus={ui.appStatus}
          progress={processor.progress}
          onOpenSettings={() => ui.setLlmOpen(true)}
          onOpenManage={() => ui.setManageOpen(true)}
        />
      </div>

      <main className="main-grid">
        <Sidebar
          file={file} setFile={setFile}
          mode={ui.mode} setMode={ui.setMode}
          bilingualLayout={ui.bilingualLayout} setBilingualLayout={ui.setBilingualLayout}
          sourceLang={ui.sourceLang} setSourceLang={ui.setSourceLang} setSourceLocked={ui.setSourceLocked}
          secondaryLang={ui.secondaryLang} setSecondaryLang={ui.setSecondaryLang} setSecondaryLocked={ui.setSecondaryLocked}
          targetLang={ui.targetLang} setTargetLang={ui.setTargetLang} setTargetLocked={ui.setTargetLocked}
          useTm={settings.useTm} setUseTm={settings.setUseTm}
          languageOptions={LANGUAGE_OPTIONS}
          busy={ui.busy}
          onExtract={processor.handleExtract}
          onExtractGlossary={() => tm.handleExtractGlossary({
            blocks: blocks,
            sourceLang: ui.sourceLang,
            targetLang: ui.targetLang,
            llmProvider: settings.llmProvider,
            llmApiKey: settings.providers[settings.llmProvider]?.apiKey,
            llmBaseUrl: settings.providers[settings.llmProvider]?.baseUrl,
            llmModel: settings.providers[settings.llmProvider]?.model,
            setStatus: ui.setStatus,
            setBusy: ui.setBusy
          })}
          onTranslate={processor.handleTranslate}
          onApply={processor.handleApply}
          canApply={file && blocks.length > 0 && !ui.busy}
          blockCount={blocks.length}
          selectedCount={blocks.filter(b => b.selected !== false).length}
          status={ui.status}
          appStatus={ui.appStatus}
          sidebarRef={leftPanelRef}
          modeDescription={ui.mode === "correction" ? t("sidebar.mode.correction") : t("sidebar.mode.translate")}
          llmTone={settings.ai.tone} setLlmTone={(v) => settings.setAiOption("tone", v)}
          useVisionContext={settings.ai.useVision} setUseVisionContext={(v) => settings.setAiOption("useVision", v)}
          useSmartLayout={settings.ai.useSmartLayout} setUseSmartLayout={(v) => settings.setAiOption("useSmartLayout", v)}
          blocks={blocks}
        />

        <EditorPanel
          blocks={blocks}
          blockCount={blocks.length}
          filteredBlocks={filteredBlocks}
          filterText={ui.filterText} setFilterText={ui.setFilterText}
          filterType={ui.filterType} setFilterType={ui.setFilterType}
          filterSlide={ui.filterSlide} setFilterSlide={ui.setFilterSlide}
          onSelectAll={(val) => {
            if (val === "EXTRACT") processor.handleExtract(true);
            else selectAllBlocks(true);
          }}
          onClearSelection={() => selectAllBlocks(false)}
          onBlockSelect={handleBlockSelect}
          onBlockChange={handleBlockChange}
          onOutputModeChange={handleOutputModeChange}
          onAddGlossary={tm.upsertGlossary}
          onAddMemory={tm.upsertMemory}
          onBatchReplace={batchReplace}
          slideDimensions={ui.slideDimensions}
          mode={ui.mode}

          sourceLang={ui.sourceLang}
          secondaryLang={ui.secondaryLang}
          targetLang={ui.targetLang}
          extractLanguageLines={extractLanguageLines}
          editorRefs={editorRefs}
        />
      </main>

      <SettingsModal
        open={ui.llmOpen} onClose={() => ui.setLlmOpen(false)}
        tab={ui.llmTab} setTab={ui.setLlmTab}

        // Pass entire settings or unpack? existing SettingsModal expects unpacked props
        llmProvider={settings.llmProvider} setLlmProvider={settings.setLlmProvider}
        llmApiKey={settings.providers[settings.llmProvider]?.apiKey || ""}
        setLlmApiKey={(v) => settings.updateProviderSettings(settings.llmProvider, { apiKey: v })}
        llmBaseUrl={settings.providers[settings.llmProvider]?.baseUrl || ""}
        setLlmBaseUrl={(v) => settings.updateProviderSettings(settings.llmProvider, { baseUrl: v })}
        llmModel={settings.providers[settings.llmProvider]?.model || ""}
        setLlmModel={(v) => settings.updateProviderSettings(settings.llmProvider, { model: v })}
        llmFastMode={settings.providers[settings.llmProvider]?.fastMode || false}
        setLlmFastMode={(v) => settings.updateProviderSettings(settings.llmProvider, { fastMode: v })}

        llmModels={settings.llmModels} llmStatus={resolveStoreStatus(settings.llmStatus)}
        onDetect={settings.detectModels}
        onSave={() => {
          settings.setLlmStatus({ key: "settings.status.saved" });
          ui.setLlmOpen(false);
        }}
        onSaveCorrection={() => {
          ui.setStatus({ key: "settings.status.saved" });
          ui.setLlmOpen(false);
        }}
        defaultBaseUrl={
          settings.llmProvider === "gemini" ? "https://generativelanguage.googleapis.com/v1beta" :
            settings.llmProvider === "ollama" ? "http://host.docker.internal:11434" :
              "https://api.openai.com/v1"
        }

        fillColor={settings.correction.fillColor} setFillColor={(v) => settings.setCorrection("fillColor", v)}
        textColor={settings.correction.textColor} setTextColor={(v) => settings.setCorrection("textColor", v)}
        lineColor={settings.correction.lineColor} setLineColor={(v) => settings.setCorrection("lineColor", v)}
        lineDash={settings.correction.lineDash} setLineDash={(v) => settings.setCorrection("lineDash", v)}
        similarityThreshold={settings.correction.similarityThreshold} setSimilarityThreshold={(v) => settings.setCorrection("similarityThreshold", v)}

        llmTone={settings.ai.tone} setLlmTone={(v) => settings.setAiOption("tone", v)}
        useVisionContext={settings.ai.useVision} setUseVisionContext={(v) => settings.setAiOption("useVision", v)}
        useSmartLayout={settings.ai.useSmartLayout} setUseSmartLayout={(v) => settings.setAiOption("useSmartLayout", v)}

        onExtractGlossary={() => tm.handleExtractGlossary({
          blocks: blocks,
          sourceLang: ui.sourceLang,
          targetLang: ui.targetLang,
          llmProvider: settings.llmProvider,
          llmApiKey: settings.providers[settings.llmProvider]?.apiKey,
          llmBaseUrl: settings.providers[settings.llmProvider]?.baseUrl,
          llmModel: settings.providers[settings.llmProvider]?.model,
          setStatus: ui.setStatus,
          setBusy: ui.setBusy
        })}
        busy={ui.busy}
        status={ui.status}
        apiBase={API_BASE}
        fontMapping={settings.fontMapping}
        setFontMapping={settings.setFontMapping}
        onSaveOcr={settings.saveOcrSettings}
        ocrStatus={resolveStoreStatus(settings.ocrStatus)}
      />

      <ManageModal
        open={ui.manageOpen} onClose={() => ui.setManageOpen(false)}
        tab={ui.manageTab} setTab={ui.setManageTab}
        languageOptions={LANGUAGE_OPTIONS}
        defaultSourceLang={ui.sourceLang || "vi"}
        defaultTargetLang={ui.targetLang || "zh-TW"}
        glossaryItems={tm.glossaryItems}
        tmItems={tm.tmItems}
        glossaryTotal={tm.glossaryTotal}
        tmTotal={tm.tmTotal}
        onLoadMoreGlossary={tm.loadMoreGlossary}
        onLoadMoreMemory={tm.loadMoreMemory}
        onRefreshGlossary={tm.loadGlossary}
        onRefreshMemory={tm.loadMemory}
        onSeed={tm.handleSeedTm}
        onUpsertGlossary={tm.upsertGlossary}
        onDeleteGlossary={tm.deleteGlossary}
        onClearGlossary={tm.clearGlossary}
        onUpsertMemory={tm.upsertMemory}
        onDeleteMemory={tm.deleteMemory}
        onClearMemory={tm.clearMemory}
        onConvertToGlossary={tm.convertMemoryToGlossary}
        onConvertToPreserveTerm={tm.convertGlossaryToPreserveTerm}
        onLoadFile={(f) => {
          setFile(f);
          setBlocks([]);
          ui.setAppStatus(APP_STATUS.IDLE);
          ui.setManageOpen(false); // Close modal on load
        }}
      />

    </div>
  );
}

export default App;
