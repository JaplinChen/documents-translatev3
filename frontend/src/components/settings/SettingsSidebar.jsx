import React from "react";
import { useTranslation } from "react-i18next";

export function SettingsSidebar({
    tab, setTab, PROVIDERS, llmProvider, setLlmProvider,
    promptList, selectedPrompt, setSelectedPrompt, PROMPT_LABELS
}) {
    const { t } = useTranslation();
    return (
        <aside className="settings-sidebar">
            <h4 className="sidebar-title">{t("settings.title")}</h4>
            <div className="sidebar-tabs">
                {["llm", "ai", "ocr", "fonts", "layouts", "correction", "prompt"].map((tKey) => (
                    <button key={tKey} className={`sidebar-tab ${tab === tKey ? "active" : ""}`} type="button" onClick={() => setTab(tKey)}>
                        {t(`settings.tabs.${tKey}`)}
                    </button>
                ))}
            </div>
            {tab === "llm" && (
                <div className="sidebar-list">
                    {PROVIDERS.map((item) => (
                        <button key={item.id} className={`sidebar-item ${llmProvider === item.id ? "active" : ""}`} type="button" onClick={() => setLlmProvider(item.id)}>
                            <span className="sidebar-icon">{item.icon}</span>
                            <div className="sidebar-text">
                                <div className="sidebar-name">{item.name}</div>
                                <div className="sidebar-sub">{t(`settings.providers.${item.id}`)}</div>
                            </div>
                        </button>
                    ))}
                </div>
            )}
            {tab === "prompt" && (
                <div className="sidebar-list">
                    {(promptList || []).length === 0 ? (
                        <div className="sidebar-empty">{t("settings.prompt.empty")}</div>
                    ) : (
                        (promptList || []).map((name) => (
                            <button key={name} className={`sidebar-item ${selectedPrompt === name ? "active" : ""}`} type="button" onClick={() => setSelectedPrompt(name)}>
                                <span className="sidebar-icon">🧩</span>
                                <div className="sidebar-text">
                                    <div className="sidebar-name">{PROMPT_LABELS[name] || name}</div>
                                    <div className="sidebar-sub">{name}</div>
                                </div>
                            </button>
                        ))
                    )}
                </div>
            )}
        </aside>
    );
}
