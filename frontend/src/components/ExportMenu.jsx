import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { exportApi } from "../services/api/export";

/**
 * Export Menu Component
 * Provides multiple export format options with download functionality
 */
export function ExportMenu({ blocks, onClose, disabled = false }) {
    const { t } = useTranslation();
    const [exporting, setExporting] = useState(null);
    const [error, setError] = useState(null);

    const formats = [
        { id: "pptx", label: t("export.formats.pptx"), icon: "📊", primary: true },
        { id: "docx", label: t("export.formats.docx"), icon: "📝" },
        { id: "xlsx", label: t("export.formats.xlsx"), icon: "📈" },
        { id: "txt", label: t("export.formats.txt"), icon: "📄" },
        { id: "md", label: t("export.formats.md"), icon: "🧾" },
    ];

    const handleExport = async (formatId) => {
        if (disabled || exporting) return;
        setExporting(formatId);
        setError(null);

        try {
            const blob = await exportApi.exportByFormat(formatId, { blocks });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `translation.${formatId}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            if (onClose) onClose();
        } catch (err) {
            setError(err.message);
        } finally {
            setExporting(null);
        }
    };

    return (
        <div className="export-menu">
            <div className="export-menu-title">
                {t("export.title")}
            </div>

            {formats.map((format) => (
                <button
                    key={format.id}
                    onClick={() => handleExport(format.id)}
                    disabled={disabled || exporting}
                    className={`export-option ${format.primary ? "primary" : ""}`}
                >
                    <span className="export-option-icon">{format.icon}</span>
                    <span className={`export-option-label ${format.primary ? "is-primary" : ""}`}>
                        {format.label}
                    </span>
                    {exporting === format.id && (
                        <span className="spinner" />
                    )}
                </button>
            ))}

            {error && (
                <div className="export-menu-error">
                    {error}
                </div>
            )}
        </div>
    );
}

export default ExportMenu;
