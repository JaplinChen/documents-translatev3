import React, { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import SettingsModal from "./components/SettingsModal";
import ManageModal from "./components/ManageModal";
import HistoryModal from "./components/HistoryModal";
import { Navbar } from "./components/Navbar";
import { Sidebar } from "./components/Sidebar";
import { EditorPanel } from "./components/EditorPanel";
import { API_BASE, APP_STATUS } from "./constants";
import { CJK_REGEX, VI_REGEX } from "./utils/regex";

// Hooks
import { useTerminology } from "./hooks/useTerminology";
import { useDocumentProcessor } from "./hooks/useDocumentProcessor";
import { usePanelResize } from "./hooks/usePanelResize";

// Stores
import { useFileStore } from "./store/useFileStore";
import { useSettingsStore } from "./store/useSettingsStore";
import { useUIStore } from "./store/useUIStore";

import { LANGUAGE_OPTIONS, extractLanguageLines } from "./utils/appHelpers";

function App() {
  const { t } = useTranslation();

  // --- Stores ---
  const fileStore = useFileStore();
  const settings = useSettingsStore();
  const ui = useUIStore();

  const leftPanelRef = useRef(null);
  const editorRefs = useRef({});

  // --- Logic Hooks ---
  const tm = useTerminology();
  const processor = useDocumentProcessor();

  usePanelResize(leftPanelRef, fileStore.blocks.length);

  const filteredBlocks = React.useMemo(() => {
    const { blocks } = fileStore;
    const { filterType, filterSlide, filterText } = ui;
    return blocks.filter((block) => {
      if (filterType !== "all" && block.block_type !== filterType) return false;
      if (filterSlide.trim() !== "") {
        const slideValue = Number(filterSlide);
        if (!Number.isNaN(slideValue) && block.slide_index !== slideValue) return false;
      }
      if (filterText.trim() !== "") {
        const needle = filterText.toLowerCase();
        const source = (block.source_text || "").toLowerCase();
        const translated = (block.translated_text || "").toLowerCase();
        if (!source.includes(needle) && !translated.includes(needle)) return false;
      }
      return true;
    });
  }, [fileStore.blocks, ui.filterText, ui.filterSlide, ui.filterType]);

  const applyDetectedLanguages = (summary) => {
    const primary = summary?.primary || "";
    const secondary = summary?.secondary || "";
    if (!ui.sourceLocked && primary) ui.setSourceLang(primary);
    if (!ui.secondaryLocked && secondary) ui.setSecondaryLang(secondary);
    if (!ui.targetLocked) ui.setTargetLang(secondary || "zh-TW");
  };

  // --- Initial Extract Effect ---
  useEffect(() => {
    if (!fileStore.file) return;
    processor.handleExtract().then(applyDetectedLanguages);
  }, [fileStore.file]);

  const handleBlockChange = (uid, value) => {
    fileStore.updateBlock(uid, { translated_text: value });
  };

  const handleBlockSelect = (uid, checked) => {
    fileStore.selectBlock(uid, checked);
  };

  const handleOutputModeChange = (uid, value) => {
    fileStore.updateBlock(uid, { output_mode: value });
  };

  // Robust stepper logic using Enum
  const isExportFinished = ui.appStatus === APP_STATUS.EXPORT_COMPLETED || ui.appStatus === APP_STATUS.EXPORTING;
  const isTranslatingOrDone = fileStore.blocks.some(b => b.translated_text) || ui.appStatus === APP_STATUS.TRANSLATING || ui.appStatus === APP_STATUS.TRANSLATION_COMPLETED;

  let currentStep = 1;
  if (isExportFinished) currentStep = 4;
  else if (isTranslatingOrDone) currentStep = 3;
  else if (fileStore.blocks.length > 0) currentStep = 2;

  const steps = [
    { id: 1, label: t("nav.step1") },
    { id: 2, label: t("nav.step2") },
    { id: 3, label: t("nav.step3") },
    { id: 4, label: t("nav.step4") }
  ];

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
          onOpenHistory={() => ui.setHistoryOpen(true)}
        />
      </div>

      <main className="main-grid">
        <Sidebar
          file={fileStore.file} setFile={fileStore.setFile}
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
            blocks: fileStore.blocks,
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
          canApply={fileStore.file && fileStore.blocks.length > 0 && !ui.busy}
          blockCount={fileStore.blocks.length}
          selectedCount={fileStore.blocks.filter(b => b.selected !== false).length}
          status={ui.status}
          appStatus={ui.appStatus}
          sidebarRef={leftPanelRef}
          modeDescription={ui.mode === "correction" ? t("sidebar.mode.correction") : t("sidebar.mode.translate")}
          llmTone={settings.ai.tone} setLlmTone={(v) => settings.setAiOption("tone", v)}
          useVisionContext={settings.ai.useVision} setUseVisionContext={(v) => settings.setAiOption("useVision", v)}
          useSmartLayout={settings.ai.useSmartLayout} setUseSmartLayout={(v) => settings.setAiOption("useSmartLayout", v)}
          blocks={fileStore.blocks}
        />

        <EditorPanel
          blockCount={fileStore.blocks.length}
          filteredBlocks={filteredBlocks}
          filterText={ui.filterText} setFilterText={ui.setFilterText}
          filterType={ui.filterType} setFilterType={ui.setFilterType}
          filterSlide={ui.filterSlide} setFilterSlide={ui.setFilterSlide}
          onSelectAll={() => fileStore.selectAllBlocks(true)}
          onClearSelection={() => fileStore.selectAllBlocks(false)}
          onBlockSelect={handleBlockSelect}
          onBlockChange={handleBlockChange}
          onOutputModeChange={handleOutputModeChange}
          onAddGlossary={tm.upsertGlossary}
          onAddMemory={tm.upsertMemory}
          onBatchReplace={fileStore.batchReplace}
          slideDimensions={ui.slideDimensions}
          mode={ui.mode}

          sourceLang={ui.sourceLang}
          secondaryLang={ui.secondaryLang}
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

        llmModels={settings.llmModels} llmStatus={settings.llmStatus}
        onDetect={settings.detectModels}
        onSave={() => {
          // Auto-saved by store action updates, just close?
          // But UI shows "Status: saved".
          // SettingsModal calls onSave manually.
          settings.setLlmStatus("已儲存設定"); // Fake status update
          ui.setLlmOpen(false);
        }}
        onSaveCorrection={() => {
          ui.setStatus(t("settings.status.saved"));
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

        llmTone={settings.ai.tone} setLlmTone={(v) => settings.setAiOption("tone", v)}
        useVisionContext={settings.ai.useVision} setUseVisionContext={(v) => settings.setAiOption("useVision", v)}
        useSmartLayout={settings.ai.useSmartLayout} setUseSmartLayout={(v) => settings.setAiOption("useSmartLayout", v)}

        onExtractGlossary={() => tm.handleExtractGlossary({
          blocks: fileStore.blocks,
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
      />

      <ManageModal
        open={ui.manageOpen} onClose={() => ui.setManageOpen(false)}
        tab={ui.manageTab} setTab={ui.setManageTab}
        languageOptions={LANGUAGE_OPTIONS}
        defaultSourceLang={ui.sourceLang || "vi"}
        defaultTargetLang={ui.targetLang || "zh-TW"}
        glossaryItems={tm.glossaryItems}
        tmItems={tm.tmItems}
        onSeed={tm.handleSeedTm}
        onUpsertGlossary={tm.upsertGlossary}
        onDeleteGlossary={tm.deleteGlossary}
        onClearGlossary={tm.clearGlossary}
        onUpsertMemory={tm.upsertMemory}
        onDeleteMemory={tm.deleteMemory}
        onClearMemory={tm.clearMemory}
        onConvertToGlossary={tm.convertMemoryToGlossary}
        onConvertToPreserveTerm={tm.convertGlossaryToPreserveTerm}
        onLoadFile={(file) => {
          fileStore.setFile(file);
          fileStore.setBlocks([]);
          ui.setAppStatus(APP_STATUS.IDLE);
          ui.setManageOpen(false); // Close modal on load
        }}
      />

      <HistoryModal
        open={ui.historyOpen}
        onClose={() => ui.setHistoryOpen(false)}
        onLoadFile={(file) => {
          fileStore.setFile(file);
          fileStore.setBlocks([]);
          ui.setAppStatus(APP_STATUS.IDLE);
        }}
      />

    </div>
  );
}

export default App;
