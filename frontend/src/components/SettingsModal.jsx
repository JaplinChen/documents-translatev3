import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import LlmTab from "./settings/LlmTab";
import CorrectionTab from "./settings/CorrectionTab";
import PromptTab from "./settings/PromptTab";
import OcrTab from "./settings/OcrTab";

import AiTab from "./settings/AiTab";
import { FontSettings } from "./settings/FontSettings";

import { X, RotateCcw, Check, Monitor, Bot, Sparkles } from "lucide-react";
import { IconButton } from "./common/IconButton";
import { useSettingsPrompts } from "../hooks/useSettingsPrompts";
import { SettingsSidebar } from "./settings/SettingsSidebar";

const PROVIDERS = [
  { id: "ollama", name: "Ollama", subKey: "ollama", icon: <Monitor size={20} /> },
  { id: "chatgpt", name: "ChatGPT (OpenAI)", subKey: "chatgpt", icon: <Bot size={20} /> },
  { id: "gemini", name: "Gemini", subKey: "gemini", icon: <Sparkles size={20} /> }
];

function SettingsModal({
  open, onClose, tab, setTab, llmProvider, setLlmProvider, llmApiKey, setLlmApiKey,
  llmBaseUrl, setLlmBaseUrl, llmModel, setLlmModel, llmFastMode, setLlmFastMode,
  llmModels, llmStatus, onDetect, onSave, onSaveCorrection, defaultBaseUrl,
  fillColor, setFillColor, textColor, setTextColor, lineColor, setLineColor,
  lineDash, setLineDash, llmTone, setLlmTone, useVisionContext, setUseVisionContext,
  useSmartLayout, setUseSmartLayout, onExtractGlossary, busy, status, apiBase,
  fontMapping, setFontMapping, similarityThreshold, setSimilarityThreshold,
  onSaveOcr
}) {
  const { t } = useTranslation();
  const [showKey, setShowKey] = useState(false);
  const {
    promptList, selectedPrompt, setSelectedPrompt, promptContent, setPromptContent,
    promptStatus, promptLoading, handleSavePrompt, handleResetPrompt, PROMPT_LABELS
  } = useSettingsPrompts(open, tab, apiBase);

  if (!open) return null;

  const currentProvider = PROVIDERS.find((item) => item.id === llmProvider) || PROVIDERS[0];
  const displayedModels = [...(llmModels || [])];
  if (llmModel && !displayedModels.includes(llmModel)) displayedModels.unshift(llmModel);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-wide" onClick={(e) => e.stopPropagation()}>
        <div className="settings-shell">
          <SettingsSidebar
            tab={tab} setTab={setTab} PROVIDERS={PROVIDERS}
            llmProvider={llmProvider} setLlmProvider={setLlmProvider}
            promptList={promptList} selectedPrompt={selectedPrompt}
            setSelectedPrompt={setSelectedPrompt} PROMPT_LABELS={PROMPT_LABELS}
          />
          <div className="settings-main">
            <div className="modal-header fancy">
              <div className="header-title">
                {tab === "llm" && <h3>{currentProvider.name} {t("settings.title")}</h3>}
                {tab === "ai" && <h3>{t("settings.tabs.ai")}</h3>}
                {tab === "fonts" && <h3>{t("settings.tabs.fonts")}</h3>}
                {tab === "ocr" && <h3>{t("settings.tabs.ocr")}</h3>}
                {tab === "correction" && <h3>{t("settings.tabs.correction")} {t("settings.title")}</h3>}
                {tab === "prompt" && <h3>{t("settings.tabs.prompt")} {t("settings.title")}</h3>}
              </div>
              <div className="header-actions flex gap-1">
                {tab === "prompt" ? (
                  <>
                    <span className="text-xs text-green-600 mr-2 flex items-center">{promptStatus}</span>
                    <IconButton icon={RotateCcw} onClick={handleResetPrompt} title={t("settings.prompt.reset")} size="sm" />
                    <IconButton icon={X} onClick={onClose} title={t("settings.prompt.close")} size="sm" />
                    <IconButton icon={Check} variant="action" onClick={() => handleSavePrompt(onClose)} title={t("settings.prompt.save")} size="sm" />
                  </>
                ) : (
                  <>
                    <IconButton icon={X} onClick={onClose} size="sm" />
                    <IconButton
                      icon={Check}
                      variant="action"
                      onClick={async () => {
                        if (tab === "llm") {
                          onSave();
                          return;
                        }
                        if (tab === "ocr") {
                          await onSaveOcr?.();
                          onClose();
                          return;
                        }
                        onSaveCorrection();
                      }}
                      size="sm"
                    />
                  </>
                )}
              </div>
            </div>
            <div className="settings-content">
              {tab === "llm" && (
                <LlmTab
                  llmProvider={llmProvider} llmApiKey={llmApiKey} setLlmApiKey={setLlmApiKey}
                  llmBaseUrl={llmBaseUrl} setLlmBaseUrl={setLlmBaseUrl} llmFastMode={llmFastMode}
                  setLlmFastMode={setLlmFastMode} llmModel={llmModel} setLlmModel={setLlmModel}
                  displayedModels={displayedModels} onDetect={onDetect} llmStatus={llmStatus}
                  defaultBaseUrl={defaultBaseUrl} showKey={showKey} setShowKey={setShowKey}
                />
              )}
              {tab === "ai" && (
                <AiTab
                  llmTone={llmTone} setLlmTone={setLlmTone} useVisionContext={useVisionContext}
                  setUseVisionContext={setUseVisionContext} useSmartLayout={useSmartLayout}
                  setUseSmartLayout={setUseSmartLayout} onExtractGlossary={onExtractGlossary}
                  busy={busy} status={status}
                />
              )}
              {tab === "ocr" && <OcrTab />}
              {tab === "fonts" && <FontSettings fontMapping={fontMapping} setFontMapping={setFontMapping} />}
              {tab === "correction" && (
                <CorrectionTab
                  fillColor={fillColor} setFillColor={setFillColor} textColor={textColor}
                  setTextColor={setTextColor} lineColor={lineColor} setLineColor={setLineColor}
                  lineDash={lineDash} setLineDash={setLineDash}
                  similarityThreshold={similarityThreshold} setSimilarityThreshold={setSimilarityThreshold}
                />
              )}
              {tab === "prompt" && (
                <PromptTab
                  promptList={promptList} selectedPrompt={selectedPrompt} setSelectedPrompt={setSelectedPrompt}
                  promptContent={promptContent} setPromptContent={setPromptContent}
                  promptLoading={promptLoading} PROMPT_LABELS={PROMPT_LABELS}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
