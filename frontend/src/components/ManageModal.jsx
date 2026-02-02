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
import TMCategoriesTab from "./manage/TMCategoriesTab";
import { useSettingsStore } from "../store/useSettingsStore";
import { useUIStore } from "../store/useUIStore";
import { DataTable } from "./common/DataTable";

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
    const isGlossary = tab === "glossary";
    const items = isGlossary ? glossaryItems : tmItems;
    const compactKey = isGlossary ? "manage_table_compact_glossary" : "manage_table_compact_tm";

    const [editingKey, setEditingKey] = useState(null);
    const [editingOriginal, setEditingOriginal] = useState(null);
    const [draft, setDraft] = useState(null);
    const [saving, setSaving] = useState(false);
    const [newEntry, setNewEntry] = useState({
        source_lang: "",
        target_lang: "",
        source_text: "",
        target_text: "",
        priority: 0,
        category_id: ""
    });
    const [selectedIds, setSelectedIds] = useState([]);
    const [tmCategories, setTmCategories] = useState([]);

    const [compactTable, setCompactTable] = useState(() => {
        try {
            const saved = localStorage.getItem(compactKey);
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

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

    // Sort state
    const [sortKey, setSortKey] = useState(isGlossary ? "priority" : null);
    const [sortDir, setSortDir] = useState("asc");

    const toggleSort = (key) => {
        if (sortKey === key) {
            setSortDir(p => p === "asc" ? "desc" : "asc");
        } else {
            setSortKey(key);
            setSortDir("asc");
        }
    };

    const sortedItems = useMemo(() => {
        if (!items) return [];
        const list = [...items];
        if (!sortKey) return list;

        list.sort((a, b) => {
            const valA = a[sortKey];
            const valB = b[sortKey];
            const dir = sortDir === "asc" ? 1 : -1;

            if (sortKey === "priority" || sortKey === "category_id") {
                return (Number(valA || 0) - Number(valB || 0)) * dir;
            }
            return String(valA || "").localeCompare(String(valB || ""), "zh-Hant") * dir;
        });
        return list;
    }, [items, sortKey, sortDir]);

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
            : { ...draft, category_id: draft.category_id || "" };
        const originalKey = editingOriginal ? makeKey(editingOriginal) : editingKey;
        const nextKey = makeKey(payload);

        // If this is a NEW entry (cloned, no editingOriginal), check for duplicates
        if (!editingOriginal && editingKey?.startsWith("__clone__")) {
            const items = isGlossary ? glossary : memory;
            const exists = items.some(item => makeKey(item) === nextKey);
            if (exists) {
                const confirmed = window.confirm(
                    t("manage.confirm.duplicate_source") ||
                    "A record with the same source text already exists. Saving will overwrite it. Continue?"
                );
                if (!confirmed) {
                    setSaving(false);
                    return;
                }
            }
        }

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

    const handleCreate = async (proto = null) => {
        if (isGlossary) setLastGlossaryAt(Date.now());
        else setLastMemoryAt(Date.now());

        // If proto is provided (cloning from existing row), enter EDIT MODE
        // with all data copied. By not setting editingOriginal, save will create new record.
        if (proto) {
            const clonedEntry = {
                // No id - this is a NEW record
                source_lang: proto.source_lang,
                target_lang: proto.target_lang,
                source_text: proto.source_text,  // Keep source_text
                target_text: proto.target_text,
                priority: proto.priority ?? 10,
                category_id: proto.category_id || ""
            };
            // Enter edit mode for this cloned entry (use a special key to identify as new)
            const cloneKey = `__clone__${Date.now()}`;
            setEditingKey(cloneKey);
            setEditingOriginal(null);  // No original = will create new, not update
            setDraft(clonedEntry);
            return;
        }

        // Direct creation with newEntry values
        const payload = {
            source_lang: newEntry.source_lang || defaultSourceLang || "vi",
            target_lang: newEntry.target_lang || defaultTargetLang || "zh-TW",
            source_text: newEntry.source_text || "",
            target_text: newEntry.target_text || "",
            priority: newEntry.priority ?? 10,
            category_id: newEntry.category_id || ""
        };

        if (!payload.source_text.trim()) {
            alert(t("manage.alerts.source_text_required") || "Please enter source text");
            return;
        }

        if (isGlossary) {
            await onUpsertGlossary(payload);
        } else {
            await onUpsertMemory(payload);
        }
        // Reset the new entry form after successful creation
        setNewEntry({
            source_lang: defaultSourceLang || "vi",
            target_lang: defaultTargetLang || "zh-TW",
            source_text: "",
            target_text: "",
            priority: 10,
            category_id: ""
        });
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
        else setSelectedIds(prev => prev.filter(x => x !== id));
    };

    const handleSelectAll = (checked) => {
        if (checked) setSelectedIds(items.map(i => i.id));
        else setSelectedIds([]);
    };



    const handleKeyDown = (e, saveFn, cancelFn) => {
        if (e.key === "Enter") {
            e.preventDefault();
            saveFn();
        } else if (e.key === "Escape") {
            e.preventDefault();
            cancelFn();
        }
    };

    const columns = [
        {
            key: "source_lang",
            label: t("manage.table.source_lang"),
            width: "90px",
            sortable: true,
            render: (val, row) => editingKey === makeKey(row) ? (
                <input className="data-input !bg-white !border-blue-200 font-bold" value={draft?.source_lang || ""} onChange={(e) => setDraft(p => ({ ...p, source_lang: e.target.value }))} onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)} autoFocus />
            ) : val
        },
        {
            key: "target_lang",
            label: t("manage.table.target_lang"),
            width: "90px",
            sortable: true,
            render: (val, row) => editingKey === makeKey(row) ? (
                <input className="data-input !bg-white !border-blue-200 font-bold" value={draft?.target_lang || ""} onChange={(e) => setDraft(p => ({ ...p, target_lang: e.target.value }))} onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)} />
            ) : val
        },
        {
            key: "source_text",
            label: t("manage.table.source"),
            width: "1fr",
            sortable: true,
            render: (val, row) => editingKey === makeKey(row) ? (
                <input className="data-input !bg-white !border-blue-200 font-bold" value={draft?.source_text || ""} onChange={(e) => setDraft(p => ({ ...p, source_text: e.target.value }))} onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)} />
            ) : val
        },
        {
            key: "target_text",
            label: t("manage.table.target"),
            width: "1fr",
            sortable: true,
            render: (val, row) => editingKey === makeKey(row) ? (
                <input className="data-input !bg-white !border-blue-200 font-bold" value={draft?.target_text || ""} onChange={(e) => setDraft(p => ({ ...p, target_text: e.target.value }))} onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)} />
            ) : val
        },
        ...(isGlossary ? [{
            key: "priority",
            label: t("manage.table.priority"),
            width: "80px",
            sortable: true,
            render: (val, row) => editingKey === makeKey(row) ? (
                <input type="number" className="data-input !bg-white !border-blue-200 font-bold" value={draft?.priority ?? 0} onChange={(e) => setDraft(p => ({ ...p, priority: e.target.value }))} onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)} />
            ) : (val ?? 0)
        }] : []),
        {
            key: "category",
            label: t("manage.fields.category", "分類"),
            width: "100px",
            render: (val, row) => editingKey === makeKey(row) ? (
                <select
                    className="data-input !bg-white !border-blue-200 font-bold !text-[12px]"
                    value={draft?.category_id || ""}
                    onChange={(e) => setDraft(p => ({ ...p, category_id: e.target.value ? parseInt(e.target.value) : null }))}
                    onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)}
                >
                    <option value="">{t("manage.fields.no_category", "無分類")}</option>
                    {tmCategories.map(c => <option key={`cat-edit-${c.id}`} value={c.id}>{c.name}</option>)}
                </select>
            ) : (
                <CategoryPill name={row.category_name} />
            )
        },
        {
            key: "actions",
            label: t("manage.table.actions"),
            width: "140px",
            render: (_, row) => (
                <div className="flex justify-end gap-1.5">
                    {editingKey === makeKey(row) ? (
                        <>
                            <button className="action-btn-sm success" onClick={handleSave} disabled={saving} title={t("manage.actions.save")}>
                                <img src="https://emojicdn.elk.sh/✅?style=apple" className="w-5 h-5 object-contain" alt="Save" />
                            </button>
                            <button className="action-btn-sm" onClick={handleCancel} disabled={saving} title={t("manage.actions.cancel")}>
                                <img src="https://emojicdn.elk.sh/❌?style=apple" className="w-5 h-5 object-contain" alt="Cancel" />
                            </button>
                        </>
                    ) : (
                        <>
                            <button className="action-btn-sm success" onClick={() => handleCreate(row)} title={t("manage.actions.add")}>
                                <Plus size={18} className="text-emerald-600" />
                            </button>
                            <button className="action-btn-sm" onClick={() => handleEdit(row)} title={t("manage.actions.edit")}>
                                <img src="https://emojicdn.elk.sh/✏️?style=apple" className="w-5 h-5 object-contain" alt="Edit" />
                            </button>
                            <button className="action-btn-sm primary" onClick={() => onConvertToPreserveTerm(row)} title={t("manage.actions.convert_preserve")}>
                                <img src="https://emojicdn.elk.sh/🔒?style=apple" className="w-5 h-5 object-contain" alt="Preserve" />
                            </button>
                            {!isGlossary && (
                                <button className="action-btn-sm primary" onClick={() => onConvertToGlossary(row)} title={t("manage.actions.convert_glossary")}>
                                    <img src="https://emojicdn.elk.sh/📑?style=apple" className="w-5 h-5 object-contain" alt="To Glossary" />
                                </button>
                            )}
                            <button className="action-btn-sm danger" onClick={() => handleDelete(row)} title={t("manage.actions.delete")}>
                                <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                            </button>
                        </>
                    )}
                </div>
            )
        }
    ];

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
                    <button className={`tab-btn ${tab === "preserve" ? "is-active" : ""}`} type="button" onClick={() => setTab("preserve")}>{t("manage.tabs.preserve")}</button>
                    <button className={`tab-btn ${tab === "tm" ? "is-active" : ""}`} type="button" onClick={() => setTab("tm")}>{t("manage.tabs.tm")}</button>
                    <button className={`tab-btn ${tab === "history" ? "is-active" : ""}`} type="button" onClick={() => setTab("history")}>{t("nav.history", "History")}</button>
                    <button className={`tab-btn ml-4 bg-amber-100 text-amber-900 hover:bg-amber-200 ${tab === "tm_categories" ? "is-active !bg-amber-300 !text-amber-950" : ""}`} type="button" onClick={() => setTab("tm_categories")}>{t("manage.tabs.tm_categories")}</button>
                    <button className={`tab-btn bg-amber-100 text-amber-900 hover:bg-amber-200 ${tab === "terms" ? "is-active !bg-amber-300 !text-amber-950" : ""}`} type="button" onClick={() => setTab("terms")}>{t("manage.tabs.terms")}</button>
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
                                    <button className="btn ghost compact" type="button" onClick={onSeed}>{t("manage.actions.seed")}</button>
                                    <button className="btn ghost compact" type="button" onClick={() => handleExport(`${API_BASE}/api/tm/${isGlossary ? "glossary" : "memory"}/export`)}>{t("manage.actions.export_csv")}</button>
                                    <label className="btn ghost compact">
                                        {t("manage.actions.import_csv")}
                                        <input type="file" accept=".csv" className="hidden-input" onChange={(event) => handleImport(event, `${API_BASE}/api/tm/${isGlossary ? "glossary" : "memory"}/import`, onSeed)} />
                                    </label>
                                    <button className="btn ghost compact" type="button" onClick={isGlossary ? onClearGlossary : onClearMemory}>{t("manage.actions.clear_all")}</button>
                                    <button className="btn primary compact !px-3" type="button" onClick={() => handleCreate()} title={t("manage.actions.add")}>
                                        <Plus size={16} />
                                    </button>
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

                                </div>
                            </div>
                            <div className="manage-scroll-area flex-1 pr-1 flex flex-col min-h-0">
                                <DataTable
                                    columns={columns}
                                    data={sortedItems}
                                    rowKey={(item) => makeKey(item)}
                                    selectedIds={selectedIds}
                                    onSelectionChange={(ids) => setSelectedIds(ids)}
                                    sortKey={sortKey}
                                    sortDir={sortDir}
                                    onSort={toggleSort}
                                    storageKey={isGlossary ? "manage_table_cols_glossary_v2" : "manage_table_cols_tm_v2"}
                                    compact={compactTable}
                                    onCompactChange={(checked) => {
                                        setCompactTable(checked);
                                        try {
                                            localStorage.setItem(compactKey, JSON.stringify(checked));
                                        } catch { }
                                    }}
                                    className={isGlossary ? "is-glossary" : "is-tm"}
                                    highlightColor={correctionFillColor}
                                    canLoadMore={isGlossary ? items.length < glossaryTotal : items.length < tmTotal}
                                    totalCount={isGlossary ? glossaryTotal : tmTotal}
                                    onLoadMore={isGlossary ? onLoadMoreGlossary : onLoadMoreMemory}
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
}


