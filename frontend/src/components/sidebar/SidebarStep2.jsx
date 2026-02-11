import React from "react";
import { useTranslation } from "react-i18next";
import { CustomSelect } from "../common/CustomSelect";

export function SidebarStep2({
    open, toggle, isExtracted, mode, setMode, bilingualLayout, setBilingualLayout,
    layoutOptions, layoutDefinition, layoutParams, setLayoutParams,
    fileType,
    languageOptions, sourceLang, setSourceLang, setSourceLocked, targetLang, setTargetLang,
    setTargetLocked, useTm, setUseTm
}) {
    const { t } = useTranslation();

    const resolvedLayoutOptions = layoutOptions?.length
        ? layoutOptions
        : [
            { value: "new_slide", label: t("sidebar.layout.new_slide") },
            { value: "inline", label: t("sidebar.layout.inline") },
            { value: "auto", label: t("sidebar.layout.auto") },
        ];

    const canCustomLayout = mode === "bilingual" && ["pptx", "docx", "xlsx", "pdf"].includes((fileType || "").toLowerCase());

    const schemaProps = layoutDefinition?.params_schema?.properties || {};
    const schemaEntries = Object.entries(schemaProps);

    const resolveParamLabel = (key, fallback) => t(`sidebar.layout.param_labels.${key}`, { defaultValue: fallback || key });
    const resolveParamDesc = (key, fallback) => t(`sidebar.layout.param_desc.${key}`, { defaultValue: fallback || "" });
    const resolveEnumLabel = (key, opt) => {
        const token = String(opt);
        return t(`sidebar.layout.param_values.${key}.${token}`, { defaultValue: token });
    };

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

            <div className={`accordion-content accordion-content-step2 ${open ? "is-open" : ""}`}>
                <div className="space-y-5 pt-4 pb-2 px-1">
                    <div className="row-group">
                        <div className="form-group">
                            <label className="field-label">{t("sidebar.mode.label")}</label>
                            <CustomSelect
                                options={[
                                    { value: "bilingual", label: t("sidebar.mode.bilingual") },
                                    { value: "translated", label: t("sidebar.mode.translated") },
                                    { value: "correction", label: t("sidebar.mode.correction") },
                                ]}
                                value={mode}
                                onChange={(e) => setMode(e.target.value)}
                                testId="mode-select"
                            />
                        </div>

                        {mode === "bilingual" && (
                            <div className="form-group">
                                <label className="field-label">{t("sidebar.layout.label")}</label>
                                <CustomSelect
                                    options={resolvedLayoutOptions}
                                    value={bilingualLayout}
                                    onChange={(e) => setBilingualLayout(e.target.value)}
                                    testId="layout-select"
                                />

                            </div>
                        )}
                    </div>

                    <div className="form-group">
                        <label className="field-label">{t("sidebar.lang.label")}</label>
                        <div className="row-group-3">
                            <CustomSelect
                                options={languageOptions || []}
                                value={sourceLang || "auto"}
                                onChange={(e) => {
                                    setSourceLang(e.target.value);
                                    setSourceLocked(true);
                                }}
                                testId="source-lang-select"
                            />
                            <div className="text-center font-bold text-slate-300">→</div>
                            <CustomSelect
                                options={(languageOptions || []).filter((opt) => opt.code !== "auto")}
                                value={targetLang}
                                onChange={(e) => {
                                    setTargetLang(e.target.value);
                                    setTargetLocked(true);
                                }}
                                testId="target-lang-select"
                            />
                        </div>
                    </div>

                    <label className="toggle-check">
                        <input type="checkbox" checked={useTm} onChange={(e) => setUseTm(e.target.checked)} />
                        {t("sidebar.tm")}
                    </label>
                </div>
            </div>
        </div>
    );
}
