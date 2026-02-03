import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { APP_STATUS } from "../constants";
import { ExportButton } from "./sidebar/ExportButton";
import { SidebarStep2 } from "./sidebar/SidebarStep2";
import { Stepper } from "./Stepper";

export function Sidebar({
    file, setFile, mode, setMode, bilingualLayout, setBilingualLayout,
    sourceLang, setSourceLang, setSourceLocked, secondaryLang, setSecondaryLang, setSecondaryLocked,
    targetLang, setTargetLang, setTargetLocked, useTm, setUseTm, languageOptions,
    busy, onExtract, onExtractGlossary, onTranslate, onApply, canApply, blockCount,
    selectedCount, status, appStatus, sidebarRef, modeDescription, llmTone, setLlmTone,
    useVisionContext, setUseVisionContext, useSmartLayout, setUseSmartLayout, blocks
}) {
    const { t } = useTranslation();
    const isFileSelected = !!file;
    const isExtracted = blockCount > 0;
    const hasTranslation = blocks && blocks.some(b => b.translated_text);
    const isTranslating = appStatus === APP_STATUS.TRANSLATING;
    const isFinished = appStatus === APP_STATUS.EXPORT_COMPLETED;
    const fileExt = file?.name?.split(".")?.pop()?.toUpperCase();

    const [openSections, setOpenSections] = useState({ step1: true, step2: false, step3: false, step4: false });

    useEffect(() => {
        if (isFinished || hasTranslation) setOpenSections({ step1: false, step2: false, step3: false, step4: true });
        else if (isExtracted) setOpenSections({ step1: false, step2: true, step3: true, step4: false });
        else if (isFileSelected) setOpenSections({ step1: false, step2: true, step3: false, step4: false });
        else setOpenSections({ step1: true, step2: false, step3: false, step4: false });
    }, [isFileSelected, isExtracted, hasTranslation, isFinished]);

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
                    <div className="accordion-content" style={{ maxHeight: openSections.step1 ? "500px" : "0", opacity: openSections.step1 ? 1 : 0 }}>
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
                    languageOptions={languageOptions} sourceLang={sourceLang} setSourceLang={setSourceLang}
                    setSourceLocked={setSourceLocked} targetLang={targetLang} setTargetLang={setTargetLang}
                    setTargetLocked={setTargetLocked} useTm={useTm} setUseTm={setUseTm} blockCount={blockCount}
                    onExtract={onExtract}
                />

                <div className={`accordion-section ${openSections.step3 ? "is-open" : ""} ${hasTranslation ? "is-done" : ""}`}>
                    <div className="accordion-header" onClick={() => toggleSection("step3")}>
                        <div className="flex items-center gap-2">
                            <span className={`step-number ${openSections.step3 ? "is-active" : ""} ${hasTranslation ? "is-done" : ""}`}>{hasTranslation ? "✓" : "3"}</span>
                            <span className="step-label">{t("nav.step3")}</span>
                        </div>
                        <span className="accordion-indicator">▼</span>
                    </div>
                    <div className="accordion-content" style={{ maxHeight: openSections.step3 ? "400px" : "0", opacity: openSections.step3 ? 1 : 0 }}>
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
                    <div className="accordion-content" style={{ maxHeight: openSections.step4 ? "400px" : "0", opacity: openSections.step4 ? 1 : 0 }}>
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
