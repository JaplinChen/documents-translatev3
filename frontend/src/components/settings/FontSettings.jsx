import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { CustomSelect } from "../common/CustomSelect";
import { DEFAULT_FONT_MAPPING } from "../../constants";


export function FontSettings({ fontMapping, setFontMapping }) {
    const { t } = useTranslation();
    const [newLang, setNewLang] = useState("");
    const [newFont, setNewFont] = useState("");
    const [editingLang, setEditingLang] = useState(null);

    const handleAdd = () => {
        if (!newLang || !newFont) return;
        const normalizedLang = newLang.trim().toLowerCase();
        const fonts = newFont.split(",").map(f => f.trim()).filter(Boolean);

        setFontMapping(prev => ({
            ...prev,
            [normalizedLang]: fonts
        }));

        setNewLang("");
        setNewFont("");
        setEditingLang(null);
    };

    const handleEdit = (lang) => {
        const fonts = fontMapping[lang];
        if (!fonts) return;
        setNewLang(lang);
        setNewFont(fonts.join(", "));
        setEditingLang(lang);
    };

    const handleCancelEdit = () => {
        setNewLang("");
        setNewFont("");
        setEditingLang(null);
    };

    const handleDelete = (lang) => {
        if (confirm(t("settings.fonts.delete_confirm") || "Delete this rule?")) {
            setFontMapping(prev => {
                const next = { ...prev };
                delete next[lang];
                return next;
            });
            if (editingLang === lang) {
                handleCancelEdit();
            }
        }
    };

    const handleReset = () => {
        if (window.confirm(t("settings.fonts.reset_confirm"))) {
            setFontMapping(DEFAULT_FONT_MAPPING);
        }
    };

    const mappingList = Object.entries(fontMapping || {}).sort((a, b) => a[0].localeCompare(b[0]));

    return (
        <div className="font-settings-panel">
            <div className="flex justify-between items-center mb-4">
                <h3 className="section-title text-base font-bold text-slate-700">
                    {t("settings.fonts.title")}
                </h3>
                <button
                    onClick={handleReset}
                    className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                    {t("settings.fonts.reset")}
                </button>
            </div>

            <p className="text-sm text-slate-500 mb-4">
                {t("settings.fonts.description")}
            </p>

            <div className={`add-rule-row flex gap-2 mb-4 p-3 rounded-lg border ${editingLang ? "bg-amber-50 border-amber-200" : "bg-slate-50 border-slate-200"}`}>
                <div className="w-1/4">
                    <label className="text-xs text-slate-500 block mb-1">{t("settings.fonts.lang_code")}</label>
                    <input
                        type="text"
                        value={newLang}
                        onChange={(e) => setNewLang(e.target.value)}
                        placeholder="e.g. vi"
                        className="input-field text-sm w-full"
                        disabled={!!editingLang} // Disable lang code editing in edit mode to prevent duplicates, forcing delete-add for key change
                    />
                </div>
                <div className="flex-1">
                    <label className="text-xs text-slate-500 block mb-1">{t("settings.fonts.font_list")}</label>
                    <input
                        type="text"
                        value={newFont}
                        onChange={(e) => setNewFont(e.target.value)}
                        placeholder="Arial, Calibri"
                        className="input-field text-sm w-full"
                    />
                </div>
                <div className="flex items-end gap-2">
                    {editingLang && (
                        <button
                            onClick={handleCancelEdit}
                            className="btn ghost btn-sm h-[34px] text-slate-500"
                        >
                            ✕
                        </button>
                    )}
                    <button
                        onClick={handleAdd}
                        disabled={!newLang || !newFont}
                        className={`btn btn-sm h-[34px] ${editingLang ? "warning" : "primary"}`}
                    >
                        {editingLang ? t("common.update") || "Update" : t("common.add")}
                    </button>
                </div>
            </div>

            <div className="rules-list max-h-[300px] overflow-y-auto border rounded-lg border-slate-200">
                <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 text-slate-600 font-semibold">
                        <tr>
                            <th className="p-2 border-b w-20">{t("settings.fonts.lang")}</th>
                            <th className="p-2 border-b">{t("settings.fonts.priority")}</th>
                            <th className="p-2 border-b w-24 text-center">{t("common.action")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {mappingList.length === 0 ? (
                            <tr>
                                <td colSpan="3" className="p-4 text-center text-slate-400">
                                    {t("settings.fonts.no_rules")}
                                </td>
                            </tr>
                        ) : (
                            mappingList.map(([lang, fonts]) => (
                                <tr key={lang} className={`border-b last:border-0 hover:bg-slate-50 ${editingLang === lang ? "bg-blue-50" : ""}`}>
                                    <td className="p-2 font-mono text-blue-600 font-bold">{lang}</td>
                                    <td className="p-2 text-slate-700">{fonts.join(", ")}</td>
                                    <td className="p-2 text-center">
                                        <div className="flex justify-center gap-2">
                                            <button
                                                onClick={() => handleEdit(lang)}
                                                className="text-slate-500 hover:text-blue-600 px-2 py-1 rounded hover:bg-blue-100 transition-colors"
                                                title={t("common.edit") || "Edit"}
                                            >
                                                ✎
                                            </button>
                                            <button
                                                onClick={() => handleDelete(lang)}
                                                className="text-red-400 hover:text-red-600 px-2 py-1 rounded hover:bg-red-50 transition-colors"
                                                title={t("common.delete")}
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div className="mt-4 p-3 bg-blue-50 text-blue-800 text-xs rounded border border-blue-100">
                <strong>{t("common.note")}: </strong>
                {t("settings.fonts.hint")}
            </div>
        </div>
    );
}
