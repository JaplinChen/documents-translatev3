import React, { useState } from "react";
import { exportApi } from "../../services/api/export";

export function ExportButton({ format, label, blocks, originalFilename, mode, layout, disabled }) {
    const [exporting, setExporting] = useState(false);
    const handleExport = async () => {
        if (disabled || exporting || !blocks?.length) return;
        setExporting(true);
        try {
            const response = await exportApi.exportByFormatWithHeaders(format, {
                blocks,
                original_filename: originalFilename,
                mode: mode,
                layout: layout
            });

            // Try to get filename from header
            const disposition = response.headers.get('Content-Disposition');
            let filename = `translation.${format}`;
            if (disposition && disposition.includes('filename*=')) {
                filename = decodeURIComponent(disposition.split("filename*=UTF-8''")[1]);
            } else if (disposition && disposition.includes('filename=')) {
                filename = disposition.split('filename=')[1].replace(/["']/g, '');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Export error:", err);
        } finally { setExporting(false); }
    };
    return (
        <button
            className="btn secondary btn-sm export-mini-btn"
            onClick={handleExport}
            disabled={disabled || exporting}
        >
            {exporting ? "..." : label}
        </button>
    );
}
