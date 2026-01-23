import React, { useState } from "react";
import { API_BASE } from "../constants";

/**
 * Export Menu Component
 * Provides multiple export format options with download functionality
 */
export function ExportMenu({ blocks, onClose, disabled = false }) {
    const [exporting, setExporting] = useState(null);
    const [error, setError] = useState(null);

    const formats = [
        { id: "pptx", label: "PowerPoint (.pptx)", icon: "📊", primary: true },
        { id: "docx", label: "Word (.docx)", icon: "📝" },
        { id: "xlsx", label: "Excel (.xlsx)", icon: "📈" },
        { id: "pdf", label: "PDF (.pdf)", icon: "🖨️" },
        { id: "txt", label: "純文字 (.txt)", icon: "📄" },
    ];

    const handleExport = async (formatId) => {
        if (disabled || exporting) return;
        setExporting(formatId);
        setError(null);

        try {
            const response = await fetch(`${API_BASE}/api/export/${formatId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ blocks }),
            });

            if (!response.ok) {
                throw new Error(`匯出失敗 (${response.status})`);
            }

            const blob = await response.blob();
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
        <div className="export-menu" style={{
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            padding: "12px",
            backgroundColor: "#fff",
            borderRadius: "12px",
            boxShadow: "0 4px 20px rgba(0,0,0,0.15)",
            minWidth: "220px",
        }}>
            <div style={{
                fontSize: "13px",
                fontWeight: "600",
                color: "#374151",
                marginBottom: "4px"
            }}>
                選擇匯出格式
            </div>

            {formats.map((format) => (
                <button
                    key={format.id}
                    onClick={() => handleExport(format.id)}
                    disabled={disabled || exporting}
                    className={`export-option ${format.primary ? "primary" : ""}`}
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        padding: "10px 14px",
                        border: format.primary ? "2px solid #3b82f6" : "1px solid #e5e7eb",
                        borderRadius: "8px",
                        backgroundColor: format.primary ? "#eff6ff" : "#fff",
                        cursor: disabled || exporting ? "not-allowed" : "pointer",
                        opacity: disabled ? 0.5 : 1,
                        transition: "all 0.15s ease",
                        textAlign: "left",
                    }}
                >
                    <span style={{ fontSize: "18px" }}>{format.icon}</span>
                    <span style={{
                        flex: 1,
                        fontSize: "13px",
                        fontWeight: format.primary ? "600" : "400",
                        color: "#374151",
                    }}>
                        {format.label}
                    </span>
                    {exporting === format.id && (
                        <span className="spinner" style={{
                            width: "14px",
                            height: "14px",
                            border: "2px solid #e5e7eb",
                            borderTopColor: "#3b82f6",
                            borderRadius: "50%",
                            animation: "spin 0.8s linear infinite",
                        }} />
                    )}
                </button>
            ))}

            {error && (
                <div style={{
                    padding: "8px 12px",
                    backgroundColor: "#fee2e2",
                    color: "#991b1b",
                    borderRadius: "6px",
                    fontSize: "12px",
                }}>
                    {error}
                </div>
            )}

            <style>{`
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                .export-option:hover:not(:disabled) {
                    background-color: #f3f4f6 !important;
                    border-color: #d1d5db !important;
                }
                .export-option.primary:hover:not(:disabled) {
                    background-color: #dbeafe !important;
                    border-color: #2563eb !important;
                }
            `}</style>
        </div>
    );
}

export default ExportMenu;
