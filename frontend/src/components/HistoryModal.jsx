import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useDraggableModal } from "../hooks/useDraggableModal";
import { API_BASE } from "../constants";

export default function HistoryModal({
    open,
    onClose,
    onLoadFile // callback to load file into editor
}) {
    const { t } = useTranslation();
    const { modalRef, position, onMouseDown } = useDraggableModal(open);
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingFile, setLoadingFile] = useState(null); // filename being loaded

    useEffect(() => {
        if (open) {
            fetchHistory();
        }
    }, [open]);

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/pptx/history`);
            if (res.ok) {
                const data = await res.json();
                setItems(data.items || []);
            }
        } catch (err) {
            console.error("Failed to fetch history", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = (filename) => {
        // Encoding logic similar to backend to ensure safe URL
        // But backend returns full download URL, or constructed here?
        // pptx.py returns download_url in /apply, but /history just gives filename.
        // /download endpoint expects path param.

        // Simple window.open or anchor click
        // Need to handle special chars if any, though backend sends clean filenames usually.
        // The backend `pptx_download` handles URL decoding.

        const encoded = encodeURIComponent(filename);
        const fileType = filename.toLowerCase().endsWith(".docx") ? "docx" : "pptx";
        window.open(`${API_BASE}/api/${fileType}/download/${encoded}`, "_blank");
    };

    const handleLoad = async (item) => {
        if (!onLoadFile) return;
        setLoadingFile(item.filename);
        try {
            const encoded = encodeURIComponent(item.filename);
            const isDocx = item.filename.toLowerCase().endsWith(".docx");
            const fileType = isDocx ? "docx" : "pptx";
            const res = await fetch(`${API_BASE}/api/${fileType}/download/${encoded}`);
            if (!res.ok) throw new Error("Download failed");

            const blob = await res.blob();
            // Create a File object
            const mimeType = isDocx ?
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document" :
                "application/vnd.openxmlformats-officedocument.presentationml.presentation";
            const file = new File([blob], item.filename, { type: mimeType });

            await onLoadFile(file);
            onClose();
        } catch (err) {
            console.error("Failed to load file", err);
            alert(t("history.load_error", "Failed to load file"));
        } finally {
            setLoadingFile(null);
        }
    };

    if (!open) return null;

    return (
        <div className="modal-backdrop">
            <div className="modal is-draggable" ref={modalRef} style={{ top: position.top, left: position.left, width: "600px" }}>
                <div className="modal-header draggable-handle" onMouseDown={onMouseDown}>
                    <h3>{t("history.title", "History")}</h3>
                    <button className="icon-btn ghost !rounded-md" type="button" onClick={onClose}>×</button>
                </div>
                <div className="modal-body">
                    {loading ? (
                        <div className="p-4 text-center text-slate-500">{t("common.loading", "Loading...")}</div>
                    ) : items.length === 0 ? (
                        <div className="p-4 text-center text-slate-400">{t("history.empty", "No history found")}</div>
                    ) : (
                        <div className="history-list max-h-[400px] overflow-y-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-slate-500 uppercase bg-slate-50 sticky top-0">
                                    <tr>
                                        <th className="px-4 py-2">{t("history.filename", "File Name")}</th>
                                        <th className="px-4 py-2 w-32">{t("history.date", "Date")}</th>
                                        <th className="px-4 py-2 w-20">{t("history.size", "Size")}</th>
                                        <th className="px-4 py-2 w-32 text-center">{t("history.actions", "Actions")}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {items.map((item, idx) => (
                                        <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                                            <td className="px-4 py-3 font-medium text-slate-700 truncate max-w-[200px]" title={item.filename}>
                                                {item.filename}
                                            </td>
                                            <td className="px-4 py-3 text-slate-500 text-xs">
                                                {item.date_str}
                                            </td>
                                            <td className="px-4 py-3 text-slate-500 text-xs">
                                                {(item.size / 1024 / 1024).toFixed(2)} MB
                                            </td>
                                            <td className="px-4 py-3 flex gap-2 justify-center">
                                                <button
                                                    className="action-btn-sm primary"
                                                    onClick={() => handleDownload(item.filename)}
                                                    title={t("common.download", "Download")}
                                                >
                                                    ⬇
                                                </button>
                                                <button
                                                    className="action-btn-sm secondary"
                                                    onClick={() => handleLoad(item)}
                                                    disabled={!!loadingFile}
                                                    title={t("history.load", "Load into Editor")}
                                                >
                                                    {loadingFile === item.filename ? "..." : "📂"}
                                                </button>
                                                <button
                                                    className="action-btn-sm danger hover:bg-red-100 text-red-600"
                                                    onClick={async () => {
                                                        if (!window.confirm(t("history.confirm_delete", "Delete this file?"))) return;
                                                        try {
                                                            const encoded = encodeURIComponent(item.filename);
                                                            const fileType = item.filename.toLowerCase().endsWith(".docx") ? "docx" : "pptx";
                                                            const res = await fetch(`${API_BASE}/api/${fileType}/history/${encoded}`, { method: "DELETE" });
                                                            if (res.ok) fetchHistory();
                                                        } catch (e) {
                                                            console.error(e);
                                                        }
                                                    }}
                                                    title={t("common.delete", "Delete")}
                                                >
                                                    🗑️
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
