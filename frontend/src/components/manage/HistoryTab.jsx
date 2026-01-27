import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../../constants";

export default function HistoryTab({ onLoadFile }) {
    const { t } = useTranslation();
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingFile, setLoadingFile] = useState(null);

    useEffect(() => {
        fetchHistory();
    }, []);

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
            const mimeType = isDocx ?
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document" :
                "application/vnd.openxmlformats-officedocument.presentationml.presentation";
            const file = new File([blob], item.filename, { type: mimeType });

            await onLoadFile(file);
            // We assume the parent modal might close or show a success message if needed, 
            // but for a tab execution, maybe we just load it. 
            // The original closed the modal. We might want to notify the user.
            // For now, just load it.
        } catch (err) {
            console.error("Failed to load file", err);
            alert(t("history.load_error", "Failed to load file"));
        } finally {
            setLoadingFile(null);
        }
    };

    const handleDelete = async (item) => {
        if (!window.confirm(t("history.confirm_delete", "Delete this file?"))) return;
        try {
            const encoded = encodeURIComponent(item.filename);
            const fileType = item.filename.toLowerCase().endsWith(".docx") ? "docx" : "pptx";
            const res = await fetch(`${API_BASE}/api/${fileType}/history/${encoded}`, { method: "DELETE" });
            if (res.ok) fetchHistory();
        } catch (e) {
            console.error(e);
        }
    };

    const handleResetAll = async () => {
        if (!window.confirm(t("history.confirm_reset_all", "警告：這將永久刪除所有翻譯記憶庫 (TM)、用語集快取以及歷史匯出檔案。是否確定執行？"))) return;
        try {
            const res = await fetch(`${API_BASE}/api/admin/reset-cache`, { method: "POST" });
            if (res.ok) {
                const data = await res.json();
                alert(t("history.reset_success", "清理完成，已刪除 {{count}} 個檔案", { count: data.deleted_files }));
                fetchHistory();
            }
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="history-tab-content">
            <div className="flex justify-between items-center mb-4 px-4 py-2 bg-amber-50 border border-amber-100 rounded-lg">
                <div className="text-sm text-amber-800 font-medium flex items-center gap-2">
                    ⚠️ {t("history.reset_warning", "管理提示：若想徹底重新翻譯或清除庫存，請點擊右側按鈕")}
                </div>
                <button
                    className="btn btn-sm danger flex items-center gap-1 py-1 h-8"
                    onClick={handleResetAll}
                >
                    🗑️ {t("history.reset_all", "清理所有快取與檔案")}
                </button>
            </div>
            {loading ? (
                <div className="p-4 text-center text-slate-500">{t("common.loading", "Loading...")}</div>
            ) : items.length === 0 ? (
                <div className="p-4 text-center text-slate-400">{t("history.empty", "No history found")}</div>
            ) : (
                <div className="history-list max-h-[600px] overflow-y-auto">
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
                                    <td className="px-4 py-3 font-medium text-slate-700 truncate max-w-[300px]" title={item.filename}>
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
                                            onClick={() => handleDelete(item)}
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
    );
}
