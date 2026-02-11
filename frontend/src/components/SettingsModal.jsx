import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import LlmTab from "./settings/LlmTab";
import CorrectionTab from "./settings/CorrectionTab";
import PromptTab from "./settings/PromptTab";
import OcrTab from "./settings/OcrTab";
import LayoutsTab from "./manage/LayoutsTab";

import AiTab from "./settings/AiTab";
import { FontSettings } from "./settings/FontSettings";

import { X, RotateCcw, Check, Monitor, Bot, Sparkles } from "lucide-react";
import { IconButton } from "./common/IconButton";
import { useSettingsPrompts } from "../hooks/useSettingsPrompts";
import { SettingsSidebar } from "./settings/SettingsSidebar";
import { useDraggableModal } from "../hooks/useDraggableModal";

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
  useSmartLayout, setUseSmartLayout, onExtractGlossary, busy, status,
  fontMapping, setFontMapping, similarityThreshold, setSimilarityThreshold,
  onSaveOcr
}) {
  const { t } = useTranslation();
  const { modalRef, position, setPosition, onMouseDown } = useDraggableModal(open, "settings_modal_state");
  const [showKey, setShowKey] = useState(false);
  const [modalSize, setModalSize] = useState(null);
  const lastSizeRef = useRef({ width: 0, height: 0 });
  const restoringRef = useRef(false);
  const hasSavedSizeRef = useRef(false);
  const resizingRef = useRef(false);
  const {
    promptList, selectedPrompt, setSelectedPrompt, promptContent, setPromptContent,
    promptStatus, promptLoading, handleSavePrompt, handleResetPrompt, PROMPT_LABELS
  } = useSettingsPrompts(open, tab);

  useLayoutEffect(() => {
    if (!open || !modalRef.current) return;
    const el = modalRef.current;
    el.style.top = `${position.top}px`;
    el.style.left = `${position.left}px`;
    if (modalSize?.width) el.style.width = `${modalSize.width}px`;
    else el.style.removeProperty("width");
    if (modalSize?.height) el.style.height = `${modalSize.height}px`;
    else el.style.removeProperty("height");
  }, [open, modalRef, position.top, position.left, modalSize?.width, modalSize?.height]);

  useLayoutEffect(() => {
    if (!open) return;
    restoringRef.current = true;
    try {
      const saved = localStorage.getItem("settings_modal_state");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed?.width && parsed?.height) {
          setModalSize({ width: parsed.width, height: parsed.height });
          lastSizeRef.current = { width: parsed.width, height: parsed.height };
          hasSavedSizeRef.current = true;
        }
        if (typeof parsed?.top === "number" && typeof parsed?.left === "number") {
          setPosition({ top: parsed.top, left: parsed.left });
        }
      }
    } catch {
      setModalSize(null);
    }
    requestAnimationFrame(() => {
      restoringRef.current = false;
    });
  }, [open, setPosition]);

  useEffect(() => {
    if (!open || !modalRef.current) return;
    const target = modalRef.current;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      if (restoringRef.current) return;
      if (hasSavedSizeRef.current && !resizingRef.current) return;
      const width = Math.round(entry.contentRect.width);
      const height = Math.round(entry.contentRect.height);
      const last = lastSizeRef.current;
      if (Math.abs(width - last.width) < 2 && Math.abs(height - last.height) < 2) return;
      lastSizeRef.current = { width, height };
      setModalSize({ width, height });
      try {
        const saved = localStorage.getItem("settings_modal_state");
        const parsed = saved ? JSON.parse(saved) : {};
        localStorage.setItem("settings_modal_state", JSON.stringify({ ...parsed, width, height }));
      } catch {
        // ignore
      }
    });
    observer.observe(target);
    return () => observer.disconnect();
  }, [open, modalRef]);

  useEffect(() => {
    if (!open) return;
    const handlePointerUp = () => {
      resizingRef.current = false;
    };
    window.addEventListener("pointerup", handlePointerUp);
    return () => window.removeEventListener("pointerup", handlePointerUp);
  }, [open]);

  if (!open) return null;

  const currentProvider = PROVIDERS.find((item) => item.id === llmProvider) || PROVIDERS[0];
  const displayedModels = [...(llmModels || [])];
  if (llmModel && !displayedModels.includes(llmModel)) displayedModels.unshift(llmModel);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal is-draggable is-settings"
        ref={modalRef}
        onPointerDown={(event) => {
          if (!modalRef.current) return;
          const rect = modalRef.current.getBoundingClientRect();
          const edge = 16;
          const nearRight = event.clientX >= rect.right - edge;
          const nearBottom = event.clientY >= rect.bottom - edge;
          if (nearRight || nearBottom) resizingRef.current = true;
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="settings-shell">
          <SettingsSidebar
            tab={tab} setTab={setTab} PROVIDERS={PROVIDERS}
            llmProvider={llmProvider} setLlmProvider={setLlmProvider}
            promptList={promptList} selectedPrompt={selectedPrompt}
            setSelectedPrompt={setSelectedPrompt} PROMPT_LABELS={PROMPT_LABELS}
          />
          <div className="settings-main">
            <div className="modal-header fancy draggable-handle" onMouseDown={onMouseDown}>
              <div className="header-title">
                {tab === "llm" && <h3>{currentProvider.name} {t("settings.title")}</h3>}
                {tab === "ai" && <h3>{t("settings.tabs.ai")}</h3>}
                {tab === "fonts" && <h3>{t("settings.tabs.fonts")}</h3>}
                {tab === "layouts" && <h3>{t("settings.tabs.layouts", { defaultValue: "版面管理" })}</h3>}
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
              {tab === "layouts" && (
                <LayoutsTab />
              )}
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
