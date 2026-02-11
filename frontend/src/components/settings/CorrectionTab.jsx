import React, { useLayoutEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Palette, Square, Sliders, Bot } from "lucide-react";

function CorrectionTab({
    fillColor,
    setFillColor,
    textColor,
    setTextColor,
    lineColor,
    setLineColor,
    lineDash,
    setLineDash,
    similarityThreshold,
    setSimilarityThreshold
}) {
    const { t } = useTranslation();
    const previewBoxRef = useRef(null);
    const previewGridRef = useRef(null);
    const thresholdSelectRef = useRef(null);
    const safeThreshold = Number.isFinite(similarityThreshold) ? similarityThreshold : 0.75;
    const padLabel = (text, maxLen) => {
        const len = (text || "").length;
        const pad = Math.max(0, maxLen - len);
        return `${text}${"\u00A0".repeat(pad)}`;
    };
    const steps = [
        { label: t("settings.correction.sensitivity_steps.s1"), value: 0.6, desc: t("settings.correction.sensitivity_desc.s1") },
        { label: t("settings.correction.sensitivity_steps.s2"), value: 0.7, desc: t("settings.correction.sensitivity_desc.s2") },
        { label: t("settings.correction.sensitivity_steps.s3"), value: 0.8, desc: t("settings.correction.sensitivity_desc.s3") },
        { label: t("settings.correction.sensitivity_steps.s4"), value: 0.9, desc: t("settings.correction.sensitivity_desc.s4") },
        { label: t("settings.correction.sensitivity_steps.s5"), value: 0.95, desc: t("settings.correction.sensitivity_desc.s5") },
    ];
    const maxLabelLen = Math.max(...steps.map((step) => (step.label || "").length), 0);

    const getBorderStyle = (dash) => {
        switch (dash) {
            case "dot": return "dotted";
            case "dash": return "dashed";
            case "dashdot": return "dashed";
            case "solid": return "solid";
            default: return "solid";
        }
    };

    useLayoutEffect(() => {
        if (!previewBoxRef.current) return;
        const el = previewBoxRef.current;
        el.style.backgroundColor = fillColor || "#fef9c3";
        el.style.color = textColor || "#b11313";
        el.style.border = `3px ${getBorderStyle(lineDash)} ${lineColor || "#7e22ce"}`;
    }, [fillColor, textColor, lineColor, lineDash]);

    useLayoutEffect(() => {
        if (!previewGridRef.current) return;
        const el = previewGridRef.current;
        el.style.backgroundImage = "conic-gradient(#000 0.25turn, transparent 0.25turn 0.5turn, #000 0.5turn 0.75turn, transparent 0.75turn)";
        el.style.backgroundSize = "20px 20px";
    }, []);

    useLayoutEffect(() => {
        if (!thresholdSelectRef.current) return;
        thresholdSelectRef.current.style.fontFamily = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace";
    }, []);

    return (
        <div className="tab-pane animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                {/* Left: Preview Cabinet */}
                <div className="lg:col-span-5 flex flex-col gap-4">
                    <div className="flex items-center gap-2 mb-1">
                        <Palette size={18} className="text-blue-500" />
                        <label className="text-sm font-bold text-slate-700">{t("settings.correction.preview")}</label>
                    </div>

                    <div className="relative group">
                        <div className="w-full h-48 bg-slate-100/50 border border-slate-200 rounded-3xl flex items-center justify-center overflow-hidden shadow-inner ring-4 ring-slate-50">
                            {/* Grid Backdrop */}
                            <div ref={previewGridRef} className="absolute inset-0 opacity-[0.03] correction-preview-grid"></div>

                            {/* Main Preview Box */}
                            <div
                                ref={previewBoxRef}
                                className="px-6 py-3 text-base font-bold z-10 transition-all duration-500 shadow-xl correction-preview-box"
                            >
                                {t("settings.correction.preview_content")}
                            </div>
                        </div>
                    </div>

                    <div className="p-4 rounded-2xl bg-amber-50 border border-amber-100">
                        <p className="text-[11px] text-amber-700 leading-relaxed font-medium">
                            <Bot size={12} className="inline mr-1 mb-0.5" />
                            {t("settings.correction.hint")}
                        </p>
                    </div>
                </div>

                {/* Right: Master Controls */}
                <div className="lg:col-span-7 flex flex-col gap-6">

                    {/* Logic Control: Similarity */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <Sliders size={18} className="text-indigo-500" />
                                <span className="text-sm font-bold text-slate-700">{t("settings.correction.sensitivity_label")}</span>
                            </div>
                            <span className="text-xs font-black text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                                {Math.round(safeThreshold * 100)}%
                            </span>
                        </div>
                        <div className="flex flex-col gap-2">
                            <select
                                ref={thresholdSelectRef}
                                className="select-input w-full"
                                value={safeThreshold}
                                onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                            >
                                {steps.map((step) => (
                                    <option key={step.value} value={step.value}>
                                        {padLabel(step.label, maxLabelLen)}｜{step.desc}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Style Control: Palette */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                        <div className="flex items-center gap-2 mb-5">
                            <Palette size={18} className="text-pink-500" />
                            <span className="text-sm font-bold text-slate-700">{t("settings.correction.theme_title")}</span>
                        </div>

                        <div className="grid grid-cols-3 gap-4">
                            {[
                                { id: 'fill', label: t("settings.correction.fill_color"), val: fillColor, setter: setFillColor },
                                { id: 'text', label: t("settings.correction.text_color"), val: textColor, setter: setTextColor },
                                { id: 'line', label: t("settings.correction.border_color"), val: lineColor, setter: setLineColor }
                            ].map(item => (
                                <div key={item.id} className="flex flex-col items-center gap-3">
                                    <div className="relative group">
                                        <div
                                            ref={(el) => {
                                                if (el) el.style.backgroundColor = item.val;
                                            }}
                                            className="w-12 h-12 rounded-2xl border-2 border-white shadow-lg cursor-pointer overflow-hidden ring-1 ring-slate-200 transition-transform hover:scale-110 active:scale-95 correction-color-swatch"
                                        >
                                            <input
                                                type="color"
                                                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                                                value={item.val}
                                                onChange={(e) => item.setter(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <span className="text-[10px] font-black text-slate-400 uppercase">{item.label}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Border Style */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm">
                        <div className="flex items-center gap-2 mb-4">
                            <Square size={18} className="text-emerald-500" />
                            <span className="text-sm font-bold text-slate-700">{t("settings.correction.line_style_title")}</span>
                        </div>
                        <div className="flex gap-2">
                            {['solid', 'dash', 'dot', 'dashdot'].map(style => (
                                <button
                                    key={style}
                                    type="button"
                                    onClick={() => setLineDash(style)}
                                    className={`flex-1 py-2.5 rounded-xl border-2 transition-all duration-200 text-[10px] font-black uppercase tracking-tighter
                                        ${lineDash === style
                                            ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                                            : 'bg-white border-slate-50 text-slate-400 hover:border-slate-200'
                                        }`}
                                >
                                    {t(`settings.correction.${style}`)}
                                </button>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}

export default CorrectionTab;
