import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { buildApiUrl } from "../../services/api/core";
import { tmApi } from "../../services/api/tm";
import { DataTable } from "../common/DataTable";

export default function LearningEventsTab() {
    const { t } = useTranslation();
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [limit, setLimit] = useState(200);
    const [eventType, setEventType] = useState("");
    const [entityType, setEntityType] = useState("");
    const [scopeType, setScopeType] = useState("");
    const [scopeId, setScopeId] = useState("");
    const [sourceLang, setSourceLang] = useState("");
    const [targetLang, setTargetLang] = useState("");
    const [query, setQuery] = useState("");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");
    const [sortBy, setSortBy] = useState("id");
    const [sortDir, setSortDir] = useState("desc");
    const [offset, setOffset] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem("manage_table_compact_learning_events");
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

    const fetchData = async () => {
        setLoading(true);
        setError("");
        try {
            const params = new URLSearchParams();
            params.set("limit", String(limit));
            params.set("offset", String(offset));
            if (eventType) params.set("event_type", eventType);
            if (entityType) params.set("entity_type", entityType);
            if (scopeType) params.set("scope_type", scopeType);
            if (scopeId) params.set("scope_id", scopeId);
            if (sourceLang) params.set("source_lang", sourceLang);
            if (targetLang) params.set("target_lang", targetLang);
            if (query) params.set("q", query);
            if (dateFrom) params.set("date_from", dateFrom);
            if (dateTo) params.set("date_to", dateTo);
            if (sortBy) params.set("sort_by", sortBy);
            if (sortDir) params.set("sort_dir", sortDir);
            const data = await tmApi.getLearningEvents({
                limit,
                offset,
                event_type: eventType,
                entity_type: entityType,
                scope_type: scopeType,
                scope_id: scopeId,
                source_lang: sourceLang,
                target_lang: targetLang,
                q: query,
                date_from: dateFrom,
                date_to: dateTo,
                sort_by: sortBy,
                sort_dir: sortDir,
            });
            setItems(Array.isArray(data.items) ? data.items : []);
            setTotal(Number(data.total || 0));
            setOffset(Number(data.offset || offset));
        } catch (err) {
            setError(err?.message || "load_failed");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        fetchData();
    }, [limit, offset]);

    const maxPage = Math.max(1, Math.ceil(total / Math.max(1, limit)));
    const currentPage = Math.floor(offset / Math.max(1, limit)) + 1;

    const handlePrev = () => {
        const nextOffset = Math.max(0, offset - limit);
        setOffset(nextOffset);
    };

    const handleNext = () => {
        const nextOffset = offset + limit;
        if (nextOffset >= total) return;
        setOffset(nextOffset);
    };

    const handleExport = () => {
        const params = new URLSearchParams();
        if (eventType) params.set("event_type", eventType);
        if (entityType) params.set("entity_type", entityType);
        if (scopeType) params.set("scope_type", scopeType);
        if (scopeId) params.set("scope_id", scopeId);
        if (sourceLang) params.set("source_lang", sourceLang);
        if (targetLang) params.set("target_lang", targetLang);
        if (query) params.set("q", query);
        if (dateFrom) params.set("date_from", dateFrom);
        if (dateTo) params.set("date_to", dateTo);
        if (sortBy) params.set("sort_by", sortBy);
        if (sortDir) params.set("sort_dir", sortDir);
        window.open(buildApiUrl(`/api/tm/learning-events/export?${params.toString()}`), "_blank");
    };

    const columns = useMemo(() => ([
        { key: "id", label: t("manage.learning.id"), width: "80px" },
        { key: "created_at", label: t("manage.learning.created_at"), width: "160px" },
        { key: "event_type", label: t("manage.learning.event_type"), width: "160px" },
        { key: "entity_type", label: t("manage.learning.entity_type"), width: "120px" },
        { key: "entity_id", label: t("manage.learning.entity_id"), width: "120px" },
        { key: "source_lang", label: t("manage.table.source_lang"), width: "90px" },
        { key: "target_lang", label: t("manage.table.target_lang"), width: "90px" },
        { key: "source_text", label: t("manage.table.source"), width: "1fr" },
        { key: "target_text", label: t("manage.table.target"), width: "1fr" },
        { key: "scope_type", label: t("manage.learning.scope_type"), width: "120px" },
        { key: "scope_id", label: t("manage.learning.scope_id"), width: "140px" }
    ]), [t]);

    return (
        <div className="flex flex-col h-full min-h-0">
            <div className="action-row flex items-center justify-between gap-2">
                <div className="flex gap-2 flex-wrap">
                    <input
                        className="data-input !w-[140px]"
                        placeholder={t("manage.learning.query")}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <input
                        className="data-input !w-[140px]"
                        placeholder={t("manage.learning.event_type")}
                        value={eventType}
                        onChange={(e) => setEventType(e.target.value)}
                    />
                    <input
                        className="data-input !w-[140px]"
                        placeholder={t("manage.learning.entity_type")}
                        value={entityType}
                        onChange={(e) => setEntityType(e.target.value)}
                    />
                    <input
                        className="data-input !w-[90px]"
                        placeholder={t("manage.table.source_lang")}
                        value={sourceLang}
                        onChange={(e) => setSourceLang(e.target.value)}
                    />
                    <input
                        className="data-input !w-[90px]"
                        placeholder={t("manage.table.target_lang")}
                        value={targetLang}
                        onChange={(e) => setTargetLang(e.target.value)}
                    />
                    <input
                        className="data-input !w-[120px]"
                        placeholder={t("manage.learning.scope_type")}
                        value={scopeType}
                        onChange={(e) => setScopeType(e.target.value)}
                    />
                    <input
                        className="data-input !w-[140px]"
                        placeholder={t("manage.learning.scope_id")}
                        value={scopeId}
                        onChange={(e) => setScopeId(e.target.value)}
                    />
                    <input
                        className="data-input !w-[140px]"
                        type="date"
                        placeholder={t("manage.learning.date_from")}
                        value={dateFrom}
                        onChange={(e) => setDateFrom(e.target.value)}
                    />
                    <input
                        className="data-input !w-[140px]"
                        type="date"
                        placeholder={t("manage.learning.date_to")}
                        value={dateTo}
                        onChange={(e) => setDateTo(e.target.value)}
                    />
                    <select
                        className="data-input !w-[140px]"
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                    >
                        <option value="id">{t("manage.learning.sort_by_id")}</option>
                        <option value="created_at">{t("manage.learning.sort_by_created_at")}</option>
                    </select>
                    <select
                        className="data-input !w-[120px]"
                        value={sortDir}
                        onChange={(e) => setSortDir(e.target.value)}
                    >
                        <option value="desc">{t("manage.learning.sort_desc")}</option>
                        <option value="asc">{t("manage.learning.sort_asc")}</option>
                    </select>
                    <input
                        className="data-input !w-[110px]"
                        type="number"
                        min="1"
                        max="1000"
                        placeholder={t("manage.learning.limit")}
                        value={limit}
                        onChange={(e) => setLimit(Number(e.target.value || 1))}
                    />
                    <button className="btn ghost compact" type="button" onClick={fetchData} disabled={loading}>
                        {loading ? t("common.loading") : t("common.refresh")}
                    </button>
                    <button className="btn ghost compact" type="button" onClick={handleExport}>
                        {t("manage.learning.export")}
                    </button>
                </div>
                <div className="text-xs text-slate-500">
                    {t("manage.learning.total", { count: total })} · {t("manage.learning.page", { page: currentPage, total: maxPage })}
                </div>
            </div>
            {error && (
                <div className="text-xs text-red-500 px-1 py-2">{t("common.error")}: {error}</div>
            )}
            <div className="manage-scroll-area flex-1 pr-1 flex flex-col min-h-0">
                <DataTable
                    columns={columns}
                    data={items}
                    rowKey={(item) => `${item.id || item.created_at}-${item.event_type}`}
                    storageKey="manage_table_cols_learning_events_v1"
                    compact={compactTable}
                    onCompactChange={(checked) => {
                        setCompactTable(checked);
                        try {
                            localStorage.setItem("manage_table_compact_learning_events", JSON.stringify(checked));
                        } catch { }
                    }}
                    className="is-tm"
                    canLoadMore={false}
                    totalCount={total}
                />
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
                <button className="btn ghost compact" type="button" onClick={handlePrev} disabled={offset <= 0}>
                    {t("manage.learning.prev_page")}
                </button>
                <button className="btn ghost compact" type="button" onClick={handleNext} disabled={offset + limit >= total}>
                    {t("manage.learning.next_page")}
                </button>
            </div>
        </div>
    );
}
