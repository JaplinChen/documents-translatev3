import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useDraggableModal } from "../hooks/useDraggableModal";
import { getOptionLabel } from "../utils/appHelpers";
import { API_BASE } from "../constants";
import { X, Save, Edit, Trash2, Plus, Lock, Table, Check, RotateCcw } from "lucide-react";
import { IconButton } from "./common/IconButton";
import PreserveTermsTab from "./manage/PreserveTermsTab";
import TermsTab from "./manage/TermsTab";
import HistoryTab from "./manage/HistoryTab";
import { CategoryPill } from "./manage/CategoryPill";
import { useSettingsStore } from "../store/useSettingsStore";
import { useUIStore } from "../store/useUIStore";

export default function ManageModal({
    open,
    onClose,
    tab,
    setTab,
    llmModels,
    llmModel,
    languageOptions,
    defaultSourceLang,
    defaultTargetLang,
    glossaryItems,
    tmItems,
    glossaryTotal,
    tmTotal,
    onLoadMoreGlossary,
    onLoadMoreMemory,
    onRefreshGlossary,
    onRefreshMemory,
    onSeed,
    onUpsertGlossary,
    onDeleteGlossary,
    onClearGlossary,
    onUpsertMemory,
    onDeleteMemory,
    onClearMemory,
    onConvertToGlossary,
    onConvertToPreserveTerm,
    onLoadFile
}) {
    const { t } = useTranslation();
    const [editingKey, setEditingKey] = useState(null);
    const [editingOriginal, setEditingOriginal] = useState(null);
    const [draft, setDraft] = useState(null);
    const [saving, setSaving] = useState(false);
    const [newEntry, setNewEntry] = useState({
        source_lang: "",
        target_lang: "",
        source_text: "",
        target_text: "",
        priority: 0
    });
    const [selectedIds, setSelectedIds] = useState([]);
    const [tmCategories, setTmCategories] = useState([]);

    const fetchTmCategories = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/tm/categories`);
            const data = await res.json();
            const next = Array.isArray(data.items) ? data.items : [];
            next.sort((a, b) => {
                const ao = Number(a?.sort_order ?? 0);
                const bo = Number(b?.sort_order ?? 0);
                if (ao !== bo) return ao - bo;
                const an = String(a?.name ?? "");
                const bn = String(b?.name ?? "");
                return an.localeCompare(bn, "zh-Hant", { numeric: true, sensitivity: "base" });
            });
            setTmCategories(next);
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        if (open) fetchTmCategories();
    }, [open]);

    useEffect(() => {
        if (!open) return;
        setEditingKey(null);
        setEditingOriginal(null);
        setDraft(null);
        setSaving(false);
        setSelectedIds([]);
        setNewEntry((prev) => ({
            ...prev,
            source_lang: defaultSourceLang || "vi",
            target_lang: defaultTargetLang || "zh-TW",
            category_id: ""
        }));
    }, [open, tab, defaultSourceLang, defaultTargetLang]);

    useEffect(() => {
        if (!open) return;
        if (tab === "glossary" && onRefreshGlossary) onRefreshGlossary();
        if (tab === "tm" && onRefreshMemory) onRefreshMemory();
    }, [open, tab, onRefreshGlossary, onRefreshMemory]);
    useEffect(() => {
        try {
            const saved = localStorage.getItem(compactKey);
            setCompactTable(saved ? JSON.parse(saved) : false);
        } catch {
            setCompactTable(false);
        }
    }, [compactKey]);

    const isGlossary = tab === "glossary";
    const items = isGlossary ? glossaryItems : tmItems;
    const compactKey = isGlossary ? "manage_table_compact_glossary" : "manage_table_compact_tm";
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem(compactKey);
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });
    const makeKey = (item) => `${item.source_lang || ""}|${item.target_lang || ""}|${item.source_text || ""}`;

    const { modalRef, position, setPosition, onMouseDown } = useDraggableModal(open, "manage_modal_state");
    const [modalSize, setModalSize] = useState(null);
    const lastSizeRef = useRef({ width: 0, height: 0 });
    const restoringRef = useRef(false);
    const hasSavedSizeRef = useRef(false);
    const resizingRef = useRef(false);
    const [customModel, setCustomModel] = useState("");
    const correctionFillColor = useSettingsStore((state) => state.correction.fillColor);
    const { setLastGlossaryAt, setLastMemoryAt } = useUIStore();
    const modelOptions = useMemo(() => {
        const options = [...(llmModels || [])];
        if (llmModel && !options.includes(llmModel)) options.unshift(llmModel);
        return options;
    }, [llmModels, llmModel]);

    useEffect(() => {
        if (!open) return;
        setCustomModel(llmModel || "");
    }, [open, llmModel]);

    useLayoutEffect(() => {
        if (!open) return;
        restoringRef.current = true;
        try {
            const saved = localStorage.getItem("manage_modal_state");
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed?.width && parsed?.height) {
                    setModalSize({ width: parsed.width, height: parsed.height });
                    lastSizeRef.current = { width: parsed.width, height: parsed.height };
                    hasSavedSizeRef.current = true;
                }
                if (typeof parsed?.top === "number" && typeof parsed?.left === "number") {
                    setPosition({ top: parsed.top, left: parsed.left });
                }
            }
        } catch {
            setModalSize(null);
        }
        requestAnimationFrame(() => {
            restoringRef.current = false;
        });
    }, [open]);

    useEffect(() => {
        if (!open || !modalRef.current) return;
        const target = modalRef.current;
        const observer = new ResizeObserver((entries) => {
            const entry = entries[0];
            if (!entry) return;
            if (restoringRef.current) return;
            if (hasSavedSizeRef.current && !resizingRef.current) return;
            const width = Math.round(entry.contentRect.width);
            const height = Math.round(entry.contentRect.height);
            const last = lastSizeRef.current;
            if (Math.abs(width - last.width) < 2 && Math.abs(height - last.height) < 2) return;
            lastSizeRef.current = { width, height };
            setModalSize({ width, height });
            try {
                const saved = localStorage.getItem("manage_modal_state");
                const parsed = saved ? JSON.parse(saved) : {};
                const nextState = { ...parsed, width, height };
                localStorage.setItem("manage_modal_state", JSON.stringify(nextState));
            } catch {
                // 忽略儲存失敗
            }
        });
        observer.observe(target);
        return () => observer.disconnect();
    }, [open, modalRef]);

    useEffect(() => {
        if (!open) return;
        const handlePointerUp = () => {
            resizingRef.current = false;
        };
        window.addEventListener("pointerup", handlePointerUp);
        return () => window.removeEventListener("pointerup", handlePointerUp);
    }, [open]);

    if (!open) return null;

    const handleExport = (path) => window.open(path, "_blank");

    const handleImport = (event, path, reload) => {
        const file = event.target.files?.[0];
        if (!file) return;
        if (isGlossary) setLastGlossaryAt(Date.now());
        else setLastMemoryAt(Date.now());
        const formData = new FormData();
        formData.append("file", file);
        fetch(path, { method: "POST", body: formData }).then(() => reload());
        event.target.value = "";
    };

    const handleEdit = (item) => {
        setEditingKey(makeKey(item));
        setEditingOriginal(item);
        setDraft({ ...item, priority: item.priority ?? 0 });
    };

    const handleCancel = () => {
        setEditingKey(null);
        setEditingOriginal(null);
        setDraft(null);
    };

    const handleDelete = async (item) => {
        if (!window.confirm(t("manage.confirm.delete"))) return;
        if (!item.id) return;
        const payload = { id: item.id };
        if (isGlossary) await onDeleteGlossary(payload);
        else await onDeleteMemory(payload);
        if (editingKey === makeKey(item)) handleCancel();
    };

    const handleSave = async () => {
        if (!draft) return;
        setSaving(true);
        const payload = isGlossary
            ? { ...draft, priority: Number.isNaN(Number(draft.priority)) ? 0 : Number(draft.priority) }
            : { ...draft };
        const originalKey = editingOriginal ? makeKey(editingOriginal) : editingKey;
        const nextKey = makeKey(payload);
        if (editingOriginal && originalKey !== nextKey && editingOriginal.id) {
            const deletePayload = { id: editingOriginal.id };
            if (isGlossary) await onDeleteGlossary(deletePayload);
            else await onDeleteMemory(deletePayload);
        }
        if (isGlossary) await onUpsertGlossary(payload);
        else await onUpsertMemory(payload);
        setSaving(false);
        handleCancel();
    };

    const handleCreate = async () => {
        if (!newEntry.source_text || !newEntry.target_text) return;
        if (isGlossary) setLastGlossaryAt(Date.now());
        else setLastMemoryAt(Date.now());
        if (isGlossary) {
            await onUpsertGlossary({
                ...newEntry,
                priority: Number.isNaN(Number(newEntry.priority)) ? 0 : Number(newEntry.priority)
            });
        } else {
            await onUpsertMemory({
                source_lang: newEntry.source_lang,
                target_lang: newEntry.target_lang,
                source_text: newEntry.source_text,
                target_text: newEntry.target_text,
                category_id: newEntry.category_id
            });
        }
        setNewEntry((prev) => ({ ...prev, source_text: "", target_text: "", priority: 0, category_id: "" }));
    };

    const handleBatchDelete = async () => {
        if (!selectedIds.length) return;
        if (!window.confirm(t("manage.batch.confirm_delete", { count: selectedIds.length }))) return;

        try {
            const endpoint = isGlossary ? "glossary" : "memory";
            const res = await fetch(`${API_BASE}/api/tm/${endpoint}/batch`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ids: selectedIds })
            });
            if (res.ok) {
                setSelectedIds([]);
                onSeed(); // Refresh list
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleBatchConvert = async () => {
        if (!selectedIds.length) return;
        const msg = isGlossary ? t("manage.batch.to_preserve") : t("manage.batch.to_glossary");
        if (!window.confirm(t("manage.batch.confirm_convert", { count: selectedIds.length, action: msg }))) return;

        setSaving(true);
        try {
            let successCount = 0;
            let failCount = 0;
            const errors = [];
            for (const id of selectedIds) {
                const item = items.find(i => i.id === id);
                if (item) {
                    if (isGlossary) {
                        const result = await onConvertToPreserveTerm(item, { silent: true });
                        if (result?.ok) successCount += 1;
                        else {
                            failCount += 1;
                            if (result?.error) errors.push(result.error);
                        }
                    } else {
                        await onConvertToGlossary(item);
                        successCount += 1;
                    }
                }
            }
            setSelectedIds([]);
            onSeed();
            if (isGlossary) {
                const baseMsg = t("manage.batch.convert_success", { count: successCount });
                const failMsg = failCount > 0 ? t("manage.batch.convert_failed", { count: failCount }) : "";
                const detail = errors.length > 0 ? `\n${errors[0]}` : "";
                alert(`${baseMsg}${failMsg}${detail}`);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    const handleSelectRow = (id, checked) => {
        if (checked) setSelectedIds(prev => [...prev, id]);
        else setSelectedIds(prev => prev.filter(i => i !== id));
    };

    const handleSelectAll = (checked) => {
        if (checked) setSelectedIds(items.map(i => i.id));
        else setSelectedIds([]);
    };

    return (
        <div className="modal-backdrop">
            <div
                className="modal is-draggable is-manage"
                ref={modalRef}
                onPointerDown={(event) => {
                    if (!modalRef.current) return;
                    const rect = modalRef.current.getBoundingClientRect();
                    const edge = 16;
                    const nearRight = event.clientX >= rect.right - edge;
                    const nearBottom = event.clientY >= rect.bottom - edge;
                    if (nearRight || nearBottom) {
                        resizingRef.current = true;
                    }
                }}
                style={{
                    top: position.top,
                    left: position.left,
                    width: modalSize?.width || undefined,
                    height: modalSize?.height || undefined
                }}
            >
                <div className="modal-header draggable-handle flex justify-between items-center" onMouseDown={onMouseDown}>
                    <h3>{t("manage.title")}</h3>
                    <IconButton icon={X} onClick={onClose} size="sm" />
                </div>
                <div className="modal-tabs">
                    <button className={`tab-btn ${tab === "glossary" ? "is-active" : ""}`} type="button" onClick={() => setTab("glossary")}>{t("manage.tabs.glossary")}</button>
                    <button className={`tab-btn ${tab === "terms" ? "is-active" : ""}`} type="button" onClick={() => setTab("terms")}>術語資料</button>
                    <button className={`tab-btn ${tab === "preserve" ? "is-active" : ""}`} type="button" onClick={() => setTab("preserve")}>{t("manage.tabs.preserve")}</button>
                    <button className={`tab-btn ${tab === "tm" ? "is-active" : ""}`} type="button" onClick={() => setTab("tm")}>{t("manage.tabs.tm")}</button>
                    <button className={`tab-btn ${tab === "history" ? "is-active" : ""}`} type="button" onClick={() => setTab("history")}>{t("nav.history", "History")}</button>
                    <button className={`tab-btn ${tab === "tm_categories" ? "is-active" : ""}`} type="button" onClick={() => setTab("tm_categories")}>分類維護</button>
                </div>
                <div className={`modal-body ${tab === "history" ? "" : "manage-body"}`}>
                    {tab === "history" ? (
                        <HistoryTab onLoadFile={onLoadFile} />
                    ) : tab === "terms" ? (
                        <TermsTab />
                    ) : tab === "preserve" ? (
                        <PreserveTermsTab onClose={onClose} />
                    ) : tab === "tm_categories" ? (
                        <TMCategoriesTab categories={tmCategories} onRefresh={fetchTmCategories} />
                    ) : (
                        <div className="flex flex-col h-full min-h-0">
                            <div className="action-row flex items-center justify-between gap-2">
                                <div className="flex gap-2">
                                    <button className="btn ghost" type="button" onClick={onSeed}>{t("manage.actions.seed")}</button>
                                    <button className="btn ghost" type="button" onClick={() => handleExport(`${API_BASE}/api/tm/${isGlossary ? "glossary" : "memory"}/export`)}>{t("manage.actions.export_csv")}</button>
                                    <label className="btn ghost">
                                        {t("manage.actions.import_csv")}
                                        <input type="file" accept=".csv" className="hidden-input" onChange={(event) => handleImport(event, `${API_BASE}/api/tm/${isGlossary ? "glossary" : "memory"}/import`, onSeed)} />
                                    </label>
                                    <button className="btn danger" type="button" onClick={isGlossary ? onClearGlossary : onClearMemory}>{t("manage.actions.clear_all")}</button>
                                    <span className="text-xs font-bold text-slate-400 self-center">
                                        {t("manage.list_summary", { shown: items.length, total: isGlossary ? glossaryTotal : tmTotal })}
                                    </span>
                                    {(isGlossary ? items.length < glossaryTotal : items.length < tmTotal) && (
                                        <button
                                            className="btn ghost compact"
                                            type="button"
                                            onClick={isGlossary ? onLoadMoreGlossary : onLoadMoreMemory}
                                        >
                                            {t("manage.actions.load_more")}
                                        </button>
                                    )}
                                </div>
                                <div className="flex items-center gap-3">
                                    {selectedIds.length > 0 && (
                                        <div className="batch-actions flex gap-2 animate-in fade-in slide-in-from-right-2">
                                            <span className="text-xs font-bold text-slate-400 self-center mr-2">{t("manage.batch.selected_count", { count: selectedIds.length })}</span>
                                            <button className="btn ghost compact !text-blue-600" onClick={handleBatchConvert}>
                                                {isGlossary ? t("manage.batch.to_preserve") : t("manage.batch.to_glossary")}
                                            </button>
                                            <button className="btn ghost compact !text-red-500" onClick={handleBatchDelete}>{t("manage.batch.delete")}</button>
                                        </div>
                                    )}
                                    <label className="flex items-center gap-2 text-xs text-slate-600">
                                        <input
                                            type="checkbox"
                                            checked={compactTable}
                                            onChange={(e) => {
                                                const checked = e.target.checked;
                                                setCompactTable(checked);
                                                try {
                                                    localStorage.setItem(compactKey, JSON.stringify(checked));
                                                } catch {
                                                    // 忽略儲存失敗
                                                }
                                            }}
                                        />
                                        緊湊模式
                                    </label>
                                </div>
                            </div>
                            <div className="create-row">
                                <div className="manage-create-row">
                                    <select className="select-input manage-field-short" value={newEntry.source_lang} onChange={(e) => setNewEntry((prev) => ({ ...prev, source_lang: e.target.value }))}>
                                        {(languageOptions || []).filter((o) => o.code !== "auto").map((o) => (
                                            <option key={`src-${o.code}`} value={o.code}>{getOptionLabel(t, o)}</option>
                                        ))}
                                    </select>
                                    <select className="select-input manage-field-short" value={newEntry.target_lang} onChange={(e) => setNewEntry((prev) => ({ ...prev, target_lang: e.target.value }))}>
                                        {(languageOptions || []).filter((o) => o.code !== "auto").map((o) => (
                                            <option key={`tgt-${o.code}`} value={o.code}>{getOptionLabel(t, o)}</option>
                                        ))}
                                    </select>
                                    <input className="text-input flex-1 min-w-[160px]" value={newEntry.source_text} placeholder={t("manage.fields.source_text")} onChange={(e) => setNewEntry((prev) => ({ ...prev, source_text: e.target.value }))} />
                                    <input className="text-input flex-1 min-w-[160px]" value={newEntry.target_text} placeholder={t("manage.fields.target_text")} onChange={(e) => setNewEntry((prev) => ({ ...prev, target_text: e.target.value }))} />
                                    {isGlossary && (
                                        <input className="text-input manage-field-number !px-1" type="number" value={newEntry.priority} placeholder="0" onChange={(e) => setNewEntry((prev) => ({ ...prev, priority: e.target.value }))} />
                                    )}
                                    <select
                                        className="select-input manage-field-short !min-w-[100px]"
                                        value={newEntry.category_id || ""}
                                        onChange={(e) => setNewEntry((prev) => ({ ...prev, category_id: e.target.value ? parseInt(e.target.value) : null }))}
                                    >
                                        <option value="">{t("manage.fields.no_category", "無分類")}</option>
                                        {tmCategories.map(c => (
                                            <option key={`cat-new-${c.id}`} value={c.id}>{c.name}</option>
                                        ))}
                                    </select>
                                    <button className="btn primary manage-btn-square" type="button" onClick={handleCreate} title={t("manage.actions.add")}>
                                        <Plus size={18} />
                                    </button>
                                </div>
                            </div>
                            <div className="manage-scroll-area">
                                <DataTable
                                    items={items}
                                    isGlossary={isGlossary}
                                    compact={compactTable}
                                    editingKey={editingKey}
                                    draft={draft}
                                    saving={saving}
                                    selectedIds={selectedIds}
                                    makeKey={makeKey}
                                    setDraft={setDraft}
                                    onEdit={handleEdit}
                                    onSave={handleSave}
                                    onCancel={handleCancel}
                                    onDelete={handleDelete}
                                    onSelectRow={handleSelectRow}
                                    onSelectAll={handleSelectAll}
                                    onConvertToGlossary={onConvertToGlossary}
                                    onConvertToPreserveTerm={onConvertToPreserveTerm}
                                    t={t}
                                    highlightColor={correctionFillColor}
                                    categories={tmCategories}
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function TMCategoriesTab({ categories, onRefresh }) {
    const { t } = useTranslation();
    const [editingId, setEditingId] = useState(null);
    const [draft, setDraft] = useState(null);
    const [newName, setNewName] = useState("");
    const [filterText, setFilterText] = useState("");
    const [saving, setSaving] = useState(false);
    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem("manage_table_compact_categories");
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

    const handleCreate = async () => {
        if (!newName.trim()) return;
        setSaving(true);
        try {
            const res = await fetch(`${API_BASE}/api/tm/categories`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: newName.trim(), sort_order: 0 })
            });
            if (res.ok) {
                setNewName("");
                onRefresh();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    const handleSave = async () => {
        if (!draft?.name?.trim()) return;
        setSaving(true);
        try {
            const res = await fetch(`${API_BASE}/api/tm/categories/${editingId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: draft.name.trim(), sort_order: draft.sort_order })
            });
            if (res.ok) {
                setEditingId(null);
                setDraft(null);
                onRefresh();
            }
        } catch (err) {
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(t("manage.confirm.delete"))) return;
        try {
            const res = await fetch(`${API_BASE}/api/tm/categories/${id}`, {
                method: "DELETE"
            });
            if (res.ok) onRefresh();
        } catch (err) {
            console.error(err);
        }
    };

    const filtered = categories.filter(c =>
        c.name.toLowerCase().includes(filterText.toLowerCase())
    );

    return (
        <div className="flex flex-col h-full">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="flex gap-2 p-2 bg-slate-50 rounded-xl border border-slate-200">
                    <input
                        className="text-input flex-1"
                        value={newName}
                        placeholder="新分類名稱"
                        onChange={(e) => setNewName(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                    />
                    <button className="btn primary" onClick={handleCreate} disabled={saving || !newName.trim()}>
                        <Plus size={18} className="mr-1" />
                        新增
                    </button>
                </div>
                <div className="flex gap-2 p-2 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="flex-1 relative">
                        <input
                            className="text-input w-full pl-8"
                            value={filterText}
                            placeholder="搜尋分類..."
                            onChange={(e) => setFilterText(e.target.value)}
                        />
                        <div className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400">🔍</div>
                    </div>
                </div>
            </div>
            <div className="manage-scroll-area flex-1">
                <div className="flex justify-end mb-2">
                    <label className="flex items-center gap-2 text-xs text-slate-600">
                        <input
                            type="checkbox"
                            checked={compactTable}
                            onChange={(e) => {
                                const checked = e.target.checked;
                                setCompactTable(checked);
                                try {
                                    localStorage.setItem("manage_table_compact_categories", JSON.stringify(checked));
                                } catch {
                                    // 忽略儲存失敗
                                }
                            }}
                        />
                        緊湊模式
                    </label>
                </div>
                <div className={`data-table ${compactTable ? "is-compact text-xs" : "text-sm"}`}>
                    <div className="data-row data-header" style={{ gridTemplateColumns: "1fr 120px 150px 80px 100px" }}>
                        <div className="data-cell">分類名稱</div>
                        <div className="data-cell">預覽</div>
                        <div className="data-cell">使用量 (對照/術語)</div>
                        <div className="data-cell">排序</div>
                        <div className="data-cell data-actions">操作</div>
                    </div>
                    {filtered.map(cat => (
                        <div className="data-row" key={cat.id} style={{ gridTemplateColumns: "1fr 120px 150px 80px 100px" }}>
                            <div className="data-cell">
                                {editingId === cat.id ? (
                                    <input className="data-input" value={draft.name} onChange={(e) => setDraft(prev => ({ ...prev, name: e.target.value }))} />
                                ) : cat.name}
                            </div>
                            <div className="data-cell flex items-center">
                                <CategoryPill name={cat.name} />
                            </div>
                            <div className="data-cell text-xs text-slate-500">
                                <span className="text-blue-600 font-bold">{cat.glossary_count || 0}</span>
                                <span className="mx-1">/</span>
                                <span className="text-emerald-600 font-bold">{cat.tm_count || 0}</span>
                            </div>
                            <div className="data-cell text-center">
                                {editingId === cat.id ? (
                                    <input className="data-input !text-center" type="number" value={draft.sort_order} onChange={(e) => setDraft(prev => ({ ...prev, sort_order: parseInt(e.target.value) || 0 }))} />
                                ) : cat.sort_order}
                            </div>
                            <div className="data-cell data-actions flex justify-end gap-1">
                                {editingId === cat.id ? (
                                    <>
                                        <IconButton icon={Check} variant="action" size="sm" onClick={handleSave} disabled={saving} />
                                        <IconButton icon={RotateCcw} size="sm" onClick={() => { setEditingId(null); setDraft(null); }} />
                                    </>
                                ) : (
                                    <>
                                        <IconButton icon={Edit} size="sm" onClick={() => { setEditingId(cat.id); setDraft({ ...cat }); }} />
                                        <IconButton icon={Trash2} variant="danger" size="sm" onClick={() => handleDelete(cat.id)} />
                                    </>
                                )}
                            </div>
                        </div>
                    ))}
                    {filtered.length === 0 && <div className="data-empty">尚無相符分類</div>}
                </div>
            </div>
        </div>
    );
}

function DataTable({ items, isGlossary, compact, editingKey, draft, saving, selectedIds, makeKey, setDraft, onEdit, onSave, onCancel, onDelete, onSelectRow, onSelectAll, onConvertToGlossary, onConvertToPreserveTerm, t, highlightColor, categories }) {
    const safeItems = Array.isArray(items) ? items : [];
    const [sortKey, setSortKey] = useState(null);
    const [sortDir, setSortDir] = useState("asc");
    const storageKey = isGlossary ? "manage_table_cols_glossary" : "manage_table_cols_tm";
    const [colWidths, setColWidths] = useState(() => {
        try {
            const saved = localStorage.getItem(storageKey);
            return saved ? JSON.parse(saved) : {};
        } catch {
            return {};
        }
    });
    const resizingRef = useRef(null);
    useEffect(() => {
        try {
            const saved = localStorage.getItem(storageKey);
            setColWidths(saved ? JSON.parse(saved) : {});
        } catch {
            setColWidths({});
        }
    }, [storageKey]);

    const allSelected = safeItems.length > 0 && selectedIds.length === safeItems.length;
    const sortedItems = useMemo(() => {
        if (safeItems.length === 0) return [];
        if (!sortKey) return safeItems;
        const withIndex = safeItems.map((item, idx) => ({ item, idx }));
        const dir = sortDir === "asc" ? 1 : -1;
        return withIndex.sort((a, b) => {
            const av = a.item?.[sortKey];
            const bv = b.item?.[sortKey];
            if (sortKey === "priority") {
                const an = Number(av ?? 0);
                const bn = Number(bv ?? 0);
                if (an !== bn) return (an - bn) * dir;
            } else {
                const as = String(av ?? "");
                const bs = String(bv ?? "");
                const cmp = as.localeCompare(bs, "zh-Hant", { numeric: true, sensitivity: "base" });
                if (cmp !== 0) return cmp * dir;
            }
            return (a.idx - b.idx) * dir;
        }).map(({ item }) => item);
    }, [safeItems, sortKey, sortDir]);

    if (safeItems.length === 0) return <div className="data-empty">{t("manage.empty")}</div>;

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
        } else {
            setSortKey(key);
            setSortDir("asc");
        }
    };

    const sortIndicator = (key) => {
        if (sortKey !== key) return "↕";
        return sortDir === "asc" ? "▲" : "▼";
    };

    const columnKeys = [
        "select",
        "source_lang",
        "target_lang",
        "source_text",
        "target_text",
        ...(isGlossary ? ["priority"] : []),
        "category",
        "actions"
    ];
    const baseWidths = {
        select: "40px",
        source_lang: "90px",
        target_lang: "90px",
        source_text: "1fr",
        target_text: "1fr",
        priority: "80px",
        category: "100px",
        actions: "140px"
    };
    const gridTemplateColumns = columnKeys
        .map((key) => (colWidths?.[key] ? `${colWidths[key]}px` : baseWidths[key]))
        .join(" ");

    const startResize = (key, event) => {
        event.preventDefault();
        event.stopPropagation();
        const startX = event.clientX;
        const currentWidth = event.currentTarget.parentElement?.offsetWidth || 120;
        resizingRef.current = { key, startX, startWidth: currentWidth };
        const handleMove = (moveEvent) => {
            if (!resizingRef.current) return;
            const delta = moveEvent.clientX - resizingRef.current.startX;
            const nextWidth = Math.max(60, resizingRef.current.startWidth + delta);
            setColWidths((prev) => {
                const next = { ...(prev || {}), [key]: nextWidth };
                try {
                    localStorage.setItem(storageKey, JSON.stringify(next));
                } catch {
                    // 忽略儲存失敗
                }
                return next;
            });
        };
        const handleUp = () => {
            resizingRef.current = null;
            document.removeEventListener("mousemove", handleMove);
            document.removeEventListener("mouseup", handleUp);
        };
        document.addEventListener("mousemove", handleMove);
        document.addEventListener("mouseup", handleUp);
    };

    return (
        <div className={`data-table ${isGlossary ? "is-glossary" : "is-tm"} ${compact ? "is-compact text-xs" : "text-sm"}`}>
            <div className="data-row data-header" style={{ gridTemplateColumns }}>
                <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                    <input type="checkbox" checked={allSelected} onChange={(e) => onSelectAll(e.target.checked)} />
                    <span className="col-resizer" onMouseDown={(e) => startResize("select", e)} />
                </div>
                <div className="data-cell">
                    <button type="button" className="sort-btn" onClick={() => toggleSort("source_lang")} aria-label={`${t("manage.table.source_lang")} 排序`}>
                        {t("manage.table.source_lang")}
                        <span className="sort-indicator">{sortIndicator("source_lang")}</span>
                    </button>
                    <span className="col-resizer" onMouseDown={(e) => startResize("source_lang", e)} />
                </div>
                <div className="data-cell">
                    <button type="button" className="sort-btn" onClick={() => toggleSort("target_lang")} aria-label={`${t("manage.table.target_lang")} 排序`}>
                        {t("manage.table.target_lang")}
                        <span className="sort-indicator">{sortIndicator("target_lang")}</span>
                    </button>
                    <span className="col-resizer" onMouseDown={(e) => startResize("target_lang", e)} />
                </div>
                <div className="data-cell">
                    <button type="button" className="sort-btn" onClick={() => toggleSort("source_text")} aria-label={`${t("manage.table.source")} 排序`}>
                        {t("manage.table.source")}
                        <span className="sort-indicator">{sortIndicator("source_text")}</span>
                    </button>
                    <span className="col-resizer" onMouseDown={(e) => startResize("source_text", e)} />
                </div>
                <div className="data-cell">
                    <button type="button" className="sort-btn" onClick={() => toggleSort("target_text")} aria-label={`${t("manage.table.target")} 排序`}>
                        {t("manage.table.target")}
                        <span className="sort-indicator">{sortIndicator("target_text")}</span>
                    </button>
                    <span className="col-resizer" onMouseDown={(e) => startResize("target_text", e)} />
                </div>
                {isGlossary && (
                    <div className="data-cell">
                        <button type="button" className="sort-btn" onClick={() => toggleSort("priority")} aria-label={`${t("manage.table.priority")} 排序`}>
                            {t("manage.table.priority")}
                            <span className="sort-indicator">{sortIndicator("priority")}</span>
                        </button>
                        <span className="col-resizer" onMouseDown={(e) => startResize("priority", e)} />
                    </div>
                )}
                <div className="data-cell">
                    分類
                    <span className="col-resizer" onMouseDown={(e) => startResize("category", e)} />
                </div>
                <div className="data-cell data-actions">
                    {t("manage.table.actions")}
                    <span className="col-resizer" onMouseDown={(e) => startResize("actions", e)} />
                </div>
            </div>
            {(sortedItems || []).map((item, idx) => {
                const rowKey = makeKey(item);
                const isEditing = editingKey === rowKey;
                const row = isEditing ? draft || item : item;
                const isSelected = selectedIds.includes(item.id);
                const rowStyle = row?.is_new ? { backgroundColor: highlightColor } : undefined;
                return (
                    <div className={`data-row ${isSelected ? "is-selected" : ""}`} key={`tm-${idx}`} style={{ ...rowStyle, gridTemplateColumns }}>
                        <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                            <input type="checkbox" checked={isSelected} onChange={(e) => onSelectRow(item.id, e.target.checked)} />
                        </div>
                        <div className="data-cell">
                            {isEditing ? <input className="data-input !bg-white !border-blue-200 font-bold" value={row.source_lang || ""} onChange={(e) => setDraft((prev) => ({ ...prev, source_lang: e.target.value }))} /> : row.source_lang}
                        </div>
                        <div className="data-cell">
                            {isEditing ? <input className="data-input !bg-white !border-blue-200 font-bold" value={row.target_lang || ""} onChange={(e) => setDraft((prev) => ({ ...prev, target_lang: e.target.value }))} /> : row.target_lang}
                        </div>
                        <div className="data-cell">
                            {isEditing ? <input className="data-input !bg-white !border-blue-200 font-bold" value={row.source_text || ""} onChange={(e) => setDraft((prev) => ({ ...prev, source_text: e.target.value }))} /> : row.source_text}
                        </div>
                        <div className="data-cell">
                            {isEditing ? <input className="data-input !bg-white !border-blue-200 font-bold" value={row.target_text || ""} onChange={(e) => setDraft((prev) => ({ ...prev, target_text: e.target.value }))} /> : row.target_text}
                        </div>
                        {isGlossary && (
                            <div className="data-cell">
                                {isEditing ? <input className="data-input !bg-white !border-blue-200 font-bold" type="number" value={row.priority ?? 0} onChange={(e) => setDraft((prev) => ({ ...prev, priority: e.target.value }))} /> : row.priority ?? 0}
                            </div>
                        )}
                        <div className="data-cell">
                            {isEditing ? (
                                <select
                                    className="data-input !bg-white !border-blue-200 font-bold !text-[12px]"
                                    value={row.category_id || ""}
                                    onChange={(e) => setDraft((prev) => ({ ...prev, category_id: e.target.value ? parseInt(e.target.value) : null }))}
                                >
                                    <option value="">{t("manage.fields.no_category", "無分類")}</option>
                                    {categories.map(c => (
                                        <option key={`cat-edit-${c.id}`} value={c.id}>{c.name}</option>
                                    ))}
                                </select>
                            ) : (
                                <CategoryPill name={row.category_name} />
                            )}
                        </div>
                        <div className="data-cell data-actions flex justify-end gap-1.5">
                            {isEditing ? (
                                <>
                                    <button
                                        className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                                        onClick={onSave}
                                        disabled={saving}
                                        title={t("manage.actions.save")}
                                    >
                                        <Check size={16} strokeWidth={2.5} />
                                    </button>
                                    <button
                                        className="p-1.5 text-slate-400 hover:bg-slate-50 rounded-lg transition-colors"
                                        onClick={onCancel}
                                        disabled={saving}
                                        title={t("manage.actions.cancel")}
                                    >
                                        <X size={16} strokeWidth={2.5} />
                                    </button>
                                </>
                            ) : (
                                <>
                                    <IconButton icon={Edit} size="sm" onClick={() => onEdit(item)} title={t("manage.actions.edit")} />
                                    <IconButton icon={Lock} size="sm" onClick={() => onConvertToPreserveTerm(item)} title={t("manage.actions.convert_preserve")} />
                                    {!isGlossary && (
                                        <IconButton icon={Table} size="sm" onClick={() => onConvertToGlossary(item)} title={t("manage.actions.convert_glossary")} />
                                    )}
                                    <IconButton icon={Trash2} variant="danger" size="sm" onClick={() => onDelete(item)} title={t("manage.actions.delete")} />
                                </>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
