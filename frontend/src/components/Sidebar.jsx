import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { APP_STATUS } from "../constants";
import { layoutsApi } from "../services/api/layouts";
import { ExportButton } from "./sidebar/ExportButton";
import { SidebarStep2 } from "./sidebar/SidebarStep2";
import { Stepper } from "./Stepper";
import { useUIStore } from "../store/useUIStore";

export function Sidebar({
    file, setFile, mode, setMode, bilingualLayout, setBilingualLayout,
    layoutParams, setLayoutParams,
    sourceLang, setSourceLang, setSourceLocked,
    targetLang, setTargetLang, setTargetLocked, useTm, setUseTm, languageOptions,
    busy, onExtract, onExtractGlossary, onTranslate, onApply, canApply, blockCount,
    selectedCount, status, appStatus, sidebarRef, blocks,
}) {
    const { t } = useTranslation();
    const { layoutDefs, setLayoutDefs } = useUIStore();
    const isFileSelected = !!file;
    const isExtracted = blockCount > 0;
    const hasTranslation = blocks && blocks.some(b => b.translated_text);
    const isTranslating = appStatus === APP_STATUS.TRANSLATING;
    const isFinished = appStatus === APP_STATUS.EXPORT_COMPLETED;
    const fileExt = file?.name?.split(".")?.pop()?.toUpperCase();
    const fileType = file?.name?.split(".")?.pop()?.toLowerCase();

    const [openSections, setOpenSections] = useState({ step1: true, step2: false, step3: false, step4: false });
    const [layoutOptions, setLayoutOptions] = useState([]);

    const getDefaultLayoutParams = (schema) => {
        const props = schema?.properties || {};
        const out = {};
        Object.entries(props).forEach(([key, cfg]) => {
            if (Object.prototype.hasOwnProperty.call(cfg || {}, "default")) {
                out[key] = cfg.default;
                return;
            }
            if (cfg?.type === "boolean") out[key] = false;
            else if (cfg?.type === "number" || cfg?.type === "integer") out[key] = 0;
            else out[key] = "";
        });
        return out;
    };

    useEffect(() => {
        if (isFinished || hasTranslation) setOpenSections({ step1: false, step2: false, step3: false, step4: true });
        else if (isExtracted) setOpenSections({ step1: false, step2: true, step3: true, step4: false });
        else if (isFileSelected) setOpenSections({ step1: false, step2: true, step3: false, step4: false });
        else setOpenSections({ step1: true, step2: false, step3: false, step4: false });
    }, [isFileSelected, isExtracted, hasTranslation, isFinished]);

    useEffect(() => {
        if (mode !== "bilingual") return;
        const supported = ["pptx", "docx", "xlsx", "pdf"];
        if (!supported.includes(fileType || "")) {
            setLayoutOptions([]);
            setLayoutDefs([]);
            return;
        }

        let cancelled = false;
        layoutsApi.list(fileType, mode, true)
            .then((res) => {
                if (cancelled) return;
                const defs = res.layouts || [];
                setLayoutDefs(defs);
                const options = (res.layouts || [])
                    .filter((layout) => layout.enabled || layout.id === bilingualLayout)
                    .map((layout) => ({
                        value: layout.id,
                        label: layout.name,
                    }));
                setLayoutOptions(options);
                if (options.length > 0 && !options.some((opt) => opt.value === bilingualLayout)) {
                    setBilingualLayout(options[0].value);
                }
            })
            .catch(() => {
                if (!cancelled) setLayoutOptions([]);
            });

        return () => {
            cancelled = true;
        };
    }, [fileType, mode, bilingualLayout, setBilingualLayout]);

    useEffect(() => {
        const activeDef = layoutDefs.find((item) => item.id === bilingualLayout);
        if (!activeDef) return;
        const defaults = getDefaultLayoutParams(activeDef.params_schema);
        const props = activeDef?.params_schema?.properties || {};
        const current = layoutParams || {};

        // Only trigger update if there are NEW keys from defaults that aren't in current
        let changed = false;
        const merged = { ...current };

        Object.keys(props).forEach((key) => {
            if (!Object.prototype.hasOwnProperty.call(current, key)) {
                merged[key] = defaults[key];
                changed = true;
            }
        });

        // Ensure we remove keys that are no longer in the schema? 
        // No, keep them for now to avoid data loss during layout switching, 
        // but the core issue of "forgetting" checks is the priority.

        if (changed) {
            setLayoutParams(merged);
        }
    }, [bilingualLayout, layoutDefs]); // Removed layoutParams from dependencies to avoid loop, though it's already absent

    const toggleSection = (s) => setOpenSections(prev => ({ ...prev, [s]: !prev[s] }));

    return (
        <section className="panel panel-left" ref={sidebarRef}>
            <div className="panel-header">
                <h2>{t("nav.title")}</h2>
                <Stepper file={file} blockCount={blockCount} selectedCount={selectedCount} status={typeof status === 'string' ? status : (status?.key || "")} appStatus={appStatus} />
            </div>
            <div className="sidebar-scrollable-content">
                <div className={`accordion-section ${openSections.step1 ? "is-open" : ""} ${isFileSelected ? "is-done" : ""}`}>
                    <div className="accordion-header" onClick={() => toggleSection("step1")}>
                        <div className="flex items-center gap-2">
                            <span className={`step-number ${openSections.step1 ? "is-active" : ""} ${isFileSelected ? "is-done" : ""}`}>{isFileSelected ? "✓" : "1"}</span>
                            <span className="step-label">{t("nav.step1")}</span>
                        </div>
                        <span className="accordion-indicator">▼</span>
                    </div>
                    <div className={`accordion-content accordion-content-step1 ${openSections.step1 ? "is-open" : ""}`}>
                        <div className="form-group py-1"><div className="file-input-container">
                            <label className={`file-input-label ${isFileSelected ? "is-selected" : ""}`}>
                                <span className="icon">{isFileSelected ? "📄" : "📁"}</span>
                                <div className="flex flex-col items-center">
                                    <span className="text-main">{isFileSelected ? file.name : t("sidebar.upload.placeholder")}</span>
                                    {!isFileSelected && (
                                        <>
                                            <span className="text-sub">{t("sidebar.upload.limit")}</span>
                                            <div className="file-type-chips">
                                                {["PPTX", "DOCX", "XLSX", "PDF"].map(type => (
                                                    <span key={type} className="file-type-chip">{type}</span>
                                                ))}
                                            </div>
                                        </>
                                    )}
                                    {isFileSelected && <span className="text-sub text-blue-600">{t("sidebar.upload.ready")}</span>}
                                    {isFileSelected && fileExt && <span className="file-type-chip is-selected">{fileExt}</span>}
                                </div>
                                <input className="file-input-hidden" type="file" accept=".pptx,.docx,.xlsx,.pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} data-testid="file-input" />
                            </label>
                        </div></div>
                    </div>
                </div>

                <SidebarStep2
                    open={openSections.step2} toggle={() => toggleSection("step2")} isExtracted={isExtracted}
                    mode={mode} setMode={setMode} bilingualLayout={bilingualLayout} setBilingualLayout={setBilingualLayout}
                    layoutOptions={layoutOptions}
                    layoutDefinition={layoutDefs.find((item) => item.id === bilingualLayout) || null}
                    layoutParams={layoutParams}
                    setLayoutParams={setLayoutParams}
                    fileType={fileType}
                    languageOptions={languageOptions} sourceLang={sourceLang} setSourceLang={setSourceLang}
                    setSourceLocked={setSourceLocked} targetLang={targetLang} setTargetLang={setTargetLang}
                    setTargetLocked={setTargetLocked} useTm={useTm} setUseTm={setUseTm}
                />

                <div className={`accordion-section ${openSections.step3 ? "is-open" : ""} ${hasTranslation ? "is-done" : ""}`}>
                    <div className="accordion-header" onClick={() => toggleSection("step3")}>
                        <div className="flex items-center gap-2">
                            <span className={`step-number ${openSections.step3 ? "is-active" : ""} ${hasTranslation ? "is-done" : ""}`}>{hasTranslation ? "✓" : "3"}</span>
                            <span className="step-label">{t("nav.step3")}</span>
                        </div>
                        <span className="accordion-indicator">▼</span>
                    </div>
                    <div className={`accordion-content accordion-content-step3 ${openSections.step3 ? "is-open" : ""}`}>
                        <div className="py-2 flex flex-col gap-3">
                            <div className="smart-extract-section">
                                <p className="field-label mb-2">{t("sidebar.preprocess")}</p>
                                <button className="btn secondary w-full" onClick={onExtractGlossary} disabled={busy || !isExtracted}>{t("sidebar.extract.button")}</button>
                                <p className="field-hint mt-1">{t("sidebar.extract.hint")}</p>
                            </div>
                            <hr className="border-slate-200" />
                            <div className="flex gap-2 items-stretch h-10">
                                <button className={`btn primary flex-1 h-full truncate ${isExtracted && !isTranslating ? "pulse-shadow" : ""}`} onClick={() => onTranslate(false)} disabled={busy || !isExtracted} data-testid="translate-button">
                                    {isTranslating ? (typeof status === 'string' ? status : (status?.key ? t(status.key, status.params) : "")) : <span className="flex items-center justify-center gap-1">{t("sidebar.translate.button")}</span>}
                                </button>
                                <button className={`btn secondary px-3 h-full flex items-center justify-center transition-all ${isExtracted && !isTranslating ? "opacity-100" : "opacity-0 pointer-events-none w-0 px-0 ml--2"}`} title={t("sidebar.translate.refresh_button")} onClick={() => onTranslate(true)} disabled={busy || !isExtracted}>🔄</button>
                            </div>
                            {!isExtracted && <p className="field-hint text-center">{t("sidebar.hint.step12")}</p>}
                        </div>
                    </div>
                </div>

                <div className={`accordion-section ${openSections.step4 ? "is-open" : ""} ${isFinished ? "is-done" : ""}`}>
                    <div className="accordion-header" onClick={() => toggleSection("step4")}>
                        <div className="flex items-center gap-2">
                            <span className={`step-number ${openSections.step4 ? "is-active" : ""} ${isFinished ? "is-done" : ""}`}>{isFinished ? "✓" : "4"}</span>
                            <span className="step-label">{t("nav.step4")}</span>
                        </div>
                        <span className="accordion-indicator">▼</span>
                    </div>
                    <div className={`accordion-content accordion-content-step4 ${openSections.step4 ? "is-open" : ""}`}>
                        <div className="py-2 flex flex-col gap-3">
                            <button className="btn success w-full" onClick={onApply} disabled={!canApply} data-testid="apply-button">{t("sidebar.apply.button")}</button>
                            {canApply && (
                                <div className="export-alternatives">
                                    <p className="field-label mb-2">{t("sidebar.export.others")}</p>
                                    <div className="flex gap-2 flex-wrap">
                                        <ExportButton format="docx" label="DOCX" blocks={blocks} originalFilename={file?.name} mode={mode} layout={bilingualLayout} disabled={!canApply} />
                                        <ExportButton format="xlsx" label="XLSX" blocks={blocks} originalFilename={file?.name} mode={mode} layout={bilingualLayout} disabled={!canApply} />
                                        <ExportButton format="txt" label="TXT" blocks={blocks} originalFilename={file?.name} mode={mode} layout={bilingualLayout} disabled={!canApply} />
                                        <ExportButton format="md" label="Markdown" blocks={blocks} originalFilename={file?.name} mode={mode} layout={bilingualLayout} disabled={!canApply} />
                                    </div>
                                </div>
                            )}
                            {!canApply && <p className="field-hint text-center">{t("sidebar.hint.step3")}</p>}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
