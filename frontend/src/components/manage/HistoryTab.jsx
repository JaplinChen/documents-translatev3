import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../../constants";

export default function HistoryTab({ onLoadFile }) {
    const { t } = useTranslation();
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingFile, setLoadingFile] = useState(null);
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem("manage_table_compact_history");
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

    useEffect(() => {
        fetchHistory();
    }, []);

    const getFileExt = (filename) => {
        const lower = filename.toLowerCase();
        if (lower.endsWith(".json")) return "json";
        if (lower.endsWith(".docx")) return "docx";
        if (lower.endsWith(".pptx")) return "pptx";
        return "unknown";
    };

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
        const fileExt = getFileExt(filename);
        if (fileExt === "json") {
            window.open(`${API_BASE}/api/pptx/download/${encoded}`, "_blank");
            return;
        }
        const fileType = fileExt === "docx" ? "docx" : "pptx";
        window.open(`${API_BASE}/api/${fileType}/download/${encoded}`, "_blank");
    };

    const handleLoad = async (item) => {
        if (!onLoadFile) return;
        if (getFileExt(item.filename) === "json") {
            alert(t("history.load_json_blocked"));
            return;
        }
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
        if (!window.confirm(t("history.confirm_delete"))) return;
        try {
            const encoded = encodeURIComponent(item.filename);
            const fileExt = getFileExt(item.filename);
            const fileType = fileExt === "docx" ? "docx" : "pptx";
            const res = await fetch(`${API_BASE}/api/${fileType}/history/${encoded}`, { method: "DELETE" });
            if (res.ok) fetchHistory();
        } catch (e) {
            console.error(e);
        }
    };

    const handleResetAll = async () => {
        if (!window.confirm(t("history.confirm_reset_all"))) return;
        try {
            const res = await fetch(`${API_BASE}/api/admin/reset-cache`, { method: "POST" });
            if (res.ok) {
                const data = await res.json();
                alert(t("history.reset_success", { count: data.deleted_files }));
                fetchHistory();
            }
        } catch (e) {
            console.error(e);
        }
    };

    const gridTemplateColumns = "1fr 130px 80px 140px";

    return (
        <div className="history-tab-content">
            <div className="flex justify-between items-center mb-4 px-4 py-3 bg-amber-50/50 border border-amber-100 rounded-2xl">
                <div className="text-sm text-amber-800 font-medium flex items-center gap-2">
                    <span className="text-lg">⚠️</span> {t("history.reset_warning")}
                </div>
                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 text-xs text-amber-800 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={compactTable}
                            onChange={(e) => {
                                const checked = e.target.checked;
                                setCompactTable(checked);
                                try {
                                    localStorage.setItem("manage_table_compact_history", JSON.stringify(checked));
                                } catch {
                                    // 忽略儲存失敗
                                }
                            }}
                        />
                        緊湊模式
                    </label>
                    <button
                        className="btn ghost compact danger ml-4"
                        onClick={handleResetAll}
                    >
                        <span className="text-sm">🗑️</span> {t("history.reset_all")}
                    </button>
                </div>
            </div>
            {loading ? (
                <div className="p-8 text-center text-slate-400 italic">{t("common.loading")}</div>
            ) : items.length === 0 ? (
                <div className="p-12 text-center text-slate-300 flex flex-col items-center gap-2">
                    <span className="text-4xl opacity-50">📂</span>
                    <div>{t("history.empty")}</div>
                </div>
            ) : (
                <div className={`data-table is-history mt-2 ${compactTable ? "is-compact text-xs" : "text-sm"}`}>
                    <div className="data-row data-header" style={{ gridTemplateColumns }}>
                        <div className="data-cell">{t("history.filename")}</div>
                        <div className="data-cell">{t("history.date")}</div>
                        <div className="data-cell">{t("history.size")}</div>
                        <div className="data-cell data-actions justify-center">{t("history.actions")}</div>
                    </div>
                    <div className="max-h-[500px] overflow-y-auto custom-scrollbar">
                        {items.map((item, idx) => (
                            <div key={idx} className="data-row" style={{ gridTemplateColumns }}>
                                <div className="data-cell font-medium text-slate-700 truncate" title={item.filename}>
                                    {item.filename}
                                </div>
                                <div className="data-cell text-slate-500 text-xs">
                                    {item.date_str}
                                </div>
                                <div className="data-cell text-slate-500 text-xs text-right pr-8">
                                    {(item.size / 1024 / 1024).toFixed(2)} MB
                                </div>
                                <div className="data-cell data-actions flex gap-2 justify-center">
                                    <button
                                        className="action-btn-sm success"
                                        onClick={() => handleDownload(item.filename)}
                                        title={t("common.download")}
                                    >
                                        <img src="https://emojicdn.elk.sh/⬇️?style=apple" className="w-5 h-5 object-contain" alt="Download" />
                                    </button>
                                    <button
                                        className="action-btn-sm primary"
                                        onClick={() => handleLoad(item)}
                                        disabled={!!loadingFile || getFileExt(item.filename) === "json"}
                                        title={t("history.load")}
                                    >
                                        {loadingFile === item.filename ? (
                                            <span className="animate-spin text-sm">⌛</span>
                                        ) : (
                                            <img src="https://emojicdn.elk.sh/📂?style=apple" className="w-5 h-5 object-contain" alt="Load" />
                                        )}
                                    </button>
                                    <button
                                        className="action-btn-sm danger"
                                        onClick={() => handleDelete(item)}
                                        title={t("common.delete")}
                                    >
                                        <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
