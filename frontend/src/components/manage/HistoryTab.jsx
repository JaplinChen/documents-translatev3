import React, { useEffect, useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { buildApiUrl, deleteJson, postJson } from "../../services/api/core";
import { DataTable } from "../common/DataTable";
import { fetchHistoryFile, fetchHistoryItems } from "../../services/api/history";

export default function HistoryTab({ onLoadFile }) {
    const { t } = useTranslation();
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingFile, setLoadingFile] = useState(null);
    const [selectedIds, setSelectedIds] = useState([]);
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem("manage_table_compact_history");
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

    // Sorting state
    const [sortKey, setSortKey] = useState(null);
    const [sortDir, setSortDir] = useState("asc");

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
            const data = await fetchHistoryItems();
            setItems(data.items || []);
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
            window.open(buildApiUrl(`/api/pptx/download/${encoded}`), "_blank");
            return;
        }
        const fileType = fileExt === "docx" ? "docx" : "pptx";
        window.open(buildApiUrl(`/api/${fileType}/download/${encoded}`), "_blank");
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
            const file = await fetchHistoryFile(item.filename, fileType);

            await onLoadFile(file);
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
            await deleteJson(`/api/${fileType}/history/${encoded}`);
            fetchHistory();
        } catch (e) {
            console.error(e);
        }
    };

    const handleResetAll = async () => {
        if (!window.confirm(t("history.extra_confirm_msg") || "確定要清理所有歷史快取檔案嗎？\n⚠️ 此操作僅會清除匯出的暫存檔，您的「對照表」與「術語」資料將會被妥善保留。")) return;
        try {
            const data = await postJson(`/api/admin/reset-cache`);
            alert(t("history.reset_success", { count: data.deleted_files }));
            fetchHistory();
        } catch (e) {
            console.error(e);
        }
    };

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
        } else {
            setSortKey(key);
            setSortDir("asc");
        }
    };

    const sortedItems = useMemo(() => {
        if (!sortKey) return items;
        const dir = sortDir === "asc" ? 1 : -1;
        return [...items].sort((a, b) => {
            const av = a[sortKey];
            const bv = b[sortKey];
            if (typeof av === "string" && typeof bv === "string") {
                return av.localeCompare(bv) * dir;
            }
            if (av < bv) return -1 * dir;
            if (av > bv) return 1 * dir;
            return 0;
        });
    }, [items, sortKey, sortDir]);

    const columns = [
        {
            key: "filename",
            label: t("history.filename"),
            width: "1fr",
            sortable: true,
            cellClass: "font-medium text-slate-700 truncate",
            render: (value) => <span title={value}>{value}</span>
        },
        {
            key: "date_str",
            label: t("history.date"),
            width: "130px",
            sortable: true,
            cellClass: "text-slate-500 text-xs"
        },
        {
            key: "size",
            label: t("history.size"),
            width: "80px",
            sortable: true,
            cellClass: "text-slate-500 text-xs text-right pr-4",
            render: (value) => (value / 1024 / 1024).toFixed(2) + " MB"
        },
        {
            key: "actions",
            label: t("history.actions"),
            width: "140px",
            render: (_, item) => (
                <div className="flex gap-2 justify-center">
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
            )
        }
    ];

    return (
        <div className="history-tab-content flex flex-col h-full min-h-0 overflow-hidden px-1">
            <div className="flex justify-between items-center mb-4 px-4 py-3 bg-amber-50/50 border border-amber-100 rounded-2xl shrink-0">
                <div className="text-sm text-amber-800 font-medium flex items-center gap-2">
                    <span className="text-lg">⚠️</span> {t("history.reset_warning")}
                </div>
                <div>
                    <button
                        className="btn ghost compact danger"
                        onClick={handleResetAll}
                    >
                        <span className="text-sm">🗑️</span> {t("history.reset_all")}
                    </button>
                </div>
            </div>

            <DataTable
                columns={columns}
                data={sortedItems}
                rowKey="filename" // Using filename as unique key
                selectedIds={selectedIds}
                onSelectionChange={setSelectedIds}
                loading={loading}
                sortKey={sortKey}
                sortDir={sortDir}
                onSort={toggleSort}
                compact={compactTable}
                onCompactChange={(checked) => {
                    setCompactTable(checked);
                    try {
                        localStorage.setItem("manage_table_compact_history", JSON.stringify(checked));
                    } catch { }
                }}
                emptyState={
                    <div className="flex flex-col items-center gap-2">
                        <span className="text-4xl opacity-50">📂</span>
                        <div>{t("history.empty")}</div>
                    </div>
                }
                className="is-history w-full"
            />
        </div>
    );
}
