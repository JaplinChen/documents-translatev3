import React from "react";
import { useTranslation } from "react-i18next";
import { CustomSelect } from "../common/CustomSelect";

export function SidebarStep2({
    open, toggle, isExtracted, mode, setMode, bilingualLayout, setBilingualLayout,
    languageOptions, sourceLang, setSourceLang, setSourceLocked, targetLang, setTargetLang,
    setTargetLocked, useTm, setUseTm, blockCount, onExtract
}) {
    const { t } = useTranslation();
    return (
        <div className={`accordion-section ${open ? "is-open" : ""} ${isExtracted ? "is-done" : ""}`}>
            <div className="accordion-header" onClick={toggle} data-testid="step2-header">
                <div className="flex items-center gap-2">
                    <span className={`step-number ${open ? "is-active" : ""} ${isExtracted ? "is-done" : ""}`}>
                        {isExtracted ? "✓" : "2"}
                    </span>
                    <span className="step-label">{t("nav.step2")}</span>
                </div>
                <span className="accordion-indicator">▼</span>
            </div>
            <div className="accordion-content" style={{ maxHeight: open ? "800px" : "0", opacity: open ? 1 : 0 }}>
                <div className="space-y-5 pt-4 pb-2 px-1">
                    <div className="row-group">
                        <div className="form-group">
                            <label className="field-label">{t("sidebar.mode.label")}</label>
                            <CustomSelect options={[
                                { value: "bilingual", label: t("sidebar.mode.bilingual") },
                                { value: "translated", label: t("sidebar.mode.translated") },
                                { value: "correction", label: t("sidebar.mode.correction") }
                            ]} value={mode} onChange={(e) => setMode(e.target.value)} testId="mode-select" />
                        </div>
                        {mode === "bilingual" && (
                            <div className="form-group">
                                <label className="field-label">{t("sidebar.layout.label")}</label>
                                <CustomSelect options={[
                                    { value: "new_slide", label: t("sidebar.layout.new_slide") },
                                    { value: "inline", label: t("sidebar.layout.inline") },
                                    { value: "auto", label: t("sidebar.layout.auto") }
                                ]} value={bilingualLayout} onChange={(e) => setBilingualLayout(e.target.value)} testId="layout-select" />
                            </div>
                        )}
                    </div>
                    <div className="form-group">
                        <label className="field-label">{t("sidebar.lang.label")}</label>
                        <div className="row-group-3">
                            <CustomSelect options={languageOptions || []} value={sourceLang || "auto"} onChange={(e) => { setSourceLang(e.target.value); setSourceLocked(true); }} testId="source-lang-select" />
                            <div className="text-center font-bold text-slate-300">→</div>
                            <CustomSelect options={(languageOptions || []).filter(opt => opt.code !== "auto")} value={targetLang} onChange={(e) => { setTargetLang(e.target.value); setTargetLocked(true); }} testId="target-lang-select" />
                        </div>
                    </div>
                    <label className="toggle-check">
                        <input type="checkbox" checked={useTm} onChange={(e) => setUseTm(e.target.checked)} />
                        {t("sidebar.tm")}
                    </label>
                    <div className="flex flex-col gap-2 pt-2">
                        <div className="flex items-center justify-between">
                            <p className="field-hint mb-0">
                                {isExtracted ? t("sidebar.extract.summary", { count: blockCount }) : t("sidebar.hint.step1")}
                            </p>
                            <button
                                className={`btn compact ${!isExtracted ? "primary w-full" : "bg-blue-50 text-blue-600 hover:bg-blue-100 border border-blue-200"} transition-all flex items-center justify-center gap-1 px-3 py-1.5 rounded-xl`}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    if (!isExtracted || window.confirm(t("sidebar.extract.confirm_refresh"))) {
                                        onExtract(true);
                                    }
                                }}
                                title={t("sidebar.extract.refresh_hint")}
                                data-testid="extract-button"
                            >
                                <span className="text-sm">🔄</span>
                                <span className="font-bold whitespace-nowrap">{isExtracted ? t("sidebar.extract.refresh_button") : t("sidebar.extract.button")}</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
