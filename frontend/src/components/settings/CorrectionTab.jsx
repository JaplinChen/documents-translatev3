import React from "react";
import { useTranslation } from "react-i18next";
import { Palette, Type, Square, Sliders, CheckCircle2, Bot } from "lucide-react";

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

    const getBorderStyle = (dash) => {
        switch (dash) {
            case "dot": return "dotted";
            case "dash": return "dashed";
            case "dashdot": return "dashed";
            case "solid": return "solid";
            default: return "solid";
        }
    };

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
                            <div className="absolute inset-0 opacity-[0.03]"
                                style={{
                                    backgroundImage: "conic-gradient(#000 0.25turn, transparent 0.25turn 0.5turn, #000 0.5turn 0.75turn, transparent 0.75turn)",
                                    backgroundSize: "20px 20px"
                                }}
                            ></div>

                            {/* Main Preview Box */}
                            <div
                                className="px-6 py-3 text-base font-bold z-10 transition-all duration-500 shadow-xl"
                                style={{
                                    backgroundColor: fillColor,
                                    color: textColor,
                                    border: `3px ${getBorderStyle(lineDash)} ${lineColor}`,
                                    borderRadius: "12px",
                                    transform: "rotate(-1deg)"
                                }}
                            >
                                {t("settings.correction.preview_content")}
                            </div>
                        </div>
                    </div>

                    <div className="p-4 rounded-2xl bg-amber-50 border border-amber-100">
                        <p className="text-[11px] text-amber-700 leading-relaxed font-medium">
                            <Bot size={12} className="inline mr-1 mb-0.5" />
                            {t("settings.correction.hint") || "提示：視覺樣式將套用於 Powerpoint 的校正標記中。調整閾值可控制校正強度。"}
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
                                {Math.round(similarityThreshold * 100)}%
                            </span>
                        </div>
                        <input
                            type="range"
                            min="0" max="1" step="0.05"
                            className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                            value={similarityThreshold}
                            onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                        />
                        <div className="flex justify-between mt-2 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                            <span>{t("settings.correction.sensitivity_loose")}</span>
                            <span>{t("settings.correction.sensitivity_strict")}</span>
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
                                        <div className="w-12 h-12 rounded-2xl border-2 border-white shadow-lg cursor-pointer overflow-hidden ring-1 ring-slate-200 transition-transform hover:scale-110 active:scale-95"
                                            style={{ backgroundColor: item.val }}>
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
                            <span className="text-sm font-bold text-slate-700">線條樣式</span>
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
