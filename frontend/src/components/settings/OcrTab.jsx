import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useSettingsStore } from "../../store/useSettingsStore";

export default function OcrTab() {
  const { t } = useTranslation();
  const { ocr, ocrStatus, setOcrOption, loadOcrSettings } = useSettingsStore();

  useEffect(() => {
    loadOcrSettings();
  }, [loadOcrSettings]);

  const resolveStatus = (status) => {
    if (!status) return "";
    if (typeof status === "string") return t(status);
    if (status.key) return t(status.key, status.params);
    return "";
  };

  return (
    <div className="settings-form">
      <div className="settings-card">
        <h4>{t("settings.ocr.title")}</h4>
        <p className="text-xs text-slate-500 mb-4">{t("settings.ocr.desc")}</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <label className="settings-label mb-0">{t("settings.ocr.dpi")}</label>
              <span className="pill">DPI</span>
            </div>
            <input
              type="number"
              className="text-input mt-2"
              min="50"
              max="600"
              value={ocr.dpi}
              onChange={(e) => setOcrOption("dpi", e.target.value)}
            />
            <div className="text-xs text-slate-400 mt-2">{t("settings.ocr.dpi_hint")}</div>
          </div>
          <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <label className="settings-label mb-0">{t("settings.ocr.conf_min")}</label>
              <span className="pill">0-100</span>
            </div>
            <input
              type="number"
              className="text-input mt-2"
              min="0"
              max="100"
              value={ocr.confMin}
              onChange={(e) => setOcrOption("confMin", e.target.value)}
            />
            <div className="text-xs text-slate-400 mt-2">{t("settings.ocr.conf_min_hint")}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-5">
          <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <label className="settings-label mb-0">{t("settings.ocr.psm")}</label>
              <span className="pill">PSM</span>
            </div>
            <input
              type="number"
              className="text-input mt-2"
              min="3"
              max="13"
              value={ocr.psm}
              onChange={(e) => setOcrOption("psm", e.target.value)}
            />
            <div className="text-xs text-slate-400 mt-2">{t("settings.ocr.psm_hint")}</div>
          </div>
          <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <label className="settings-label mb-0">{t("settings.ocr.engine")}</label>
              <span className="pill">OCR</span>
            </div>
            <select
              className="select-input mt-2"
              value={ocr.engine}
              onChange={(e) => setOcrOption("engine", e.target.value)}
            >
              <option value="paddle">PaddleOCR</option>
              <option value="tesseract">Tesseract</option>
            </select>
            <div className="text-xs text-slate-400 mt-2">{t("settings.ocr.engine_hint")}</div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 mt-6">
          <label className="settings-label">{t("settings.ocr.lang")}</label>
          <input
            type="text"
            className="text-input mt-2"
            placeholder="chi_tra+vie+eng"
            value={ocr.lang}
            onChange={(e) => setOcrOption("lang", e.target.value)}
          />
          <div className="text-xs text-slate-400 mt-2">{t("settings.ocr.lang_hint")}</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 mt-4">
          <label className="settings-label">{t("settings.ocr.poppler_path")}</label>
          <input
            type="text"
            className="text-input mt-2"
            placeholder="C:\\Tools\\poppler\\Library\\bin"
            value={ocr.popplerPath}
            onChange={(e) => setOcrOption("popplerPath", e.target.value)}
          />
          <div className="text-xs text-slate-400 mt-2">{t("settings.ocr.poppler_hint")}</div>
        </div>

        {ocrStatus && (
          <div className="text-xs text-emerald-600 mt-4">
            {resolveStatus(ocrStatus)}
          </div>
        )}
      </div>
    </div>
  );
}
