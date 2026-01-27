import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useDraggableModal } from "../hooks/useDraggableModal";
import { API_BASE } from "../constants";
import { X, Save, Edit, Trash2, Plus, Lock, Table, Check, RotateCcw } from "lucide-react";
import { IconButton } from "./common/IconButton";
import PreserveTermsTab from "./manage/PreserveTermsTab";
import HistoryTab from "./manage/HistoryTab";

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
            target_lang: defaultTargetLang || "zh-TW"
        }));
    }, [open, tab, defaultSourceLang, defaultTargetLang]);

    const isGlossary = tab === "glossary";
    const items = isGlossary ? glossaryItems : tmItems;
    const makeKey = (item) => `${item.source_lang || ""}|${item.target_lang || ""}|${item.source_text || ""}`;

    const { modalRef, position, onMouseDown } = useDraggableModal(open);
    const [customModel, setCustomModel] = useState("");
    const modelOptions = useMemo(() => {
        const options = [...(llmModels || [])];
        if (llmModel && !options.includes(llmModel)) options.unshift(llmModel);
        return options;
    }, [llmModels, llmModel]);

    useEffect(() => {
        if (!open) return;
        setCustomModel(llmModel || "");
    }, [open, llmModel]);

    if (!open) return null;

    const handleExport = (path) => window.open(path, "_blank");

    const handleImport = (event, path, reload) => {
        const file = event.target.files?.[0];
        if (!file) return;
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
                target_text: newEntry.target_text
            });
        }
        setNewEntry((prev) => ({ ...prev, source_text: "", target_text: "", priority: 0 }));
    };

    const handleBatchDelete = async () => {
        if (!selectedIds.length) return;
        if (!window.confirm(`確定要刪除選取的 ${selectedIds.length} 筆資料嗎？`)) return;

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
        const msg = isGlossary ? "轉為術語" : "轉為對照表";
        if (!window.confirm(`確定要將選取的 ${selectedIds.length} 筆資料${msg}嗎？（原記錄將自動刪除）`)) return;

        setSaving(true);
        try {
            for (const id of selectedIds) {
                const item = items.find(i => i.id === id);
                if (item) {
                    if (isGlossary) await onConvertToPreserveTerm(item);
                    else await onConvertToGlossary(item);
                }
            }
            setSelectedIds([]);
            onSeed();
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
            <div className="modal is-draggable" ref={modalRef} style={{ top: position.top, left: position.left }}>
                <div className="modal-header draggable-handle flex justify-between items-center" onMouseDown={onMouseDown}>
                    <h3>{t("manage.title")}</h3>
                    <IconButton icon={X} onClick={onClose} size="sm" />
                </div>
                <div className="modal-tabs">
                    <button className={`tab-btn ${tab === "glossary" ? "is-active" : ""}`} type="button" onClick={() => setTab("glossary")}>{t("manage.tabs.glossary")}</button>
                    <button className={`tab-btn ${tab === "preserve" ? "is-active" : ""}`} type="button" onClick={() => setTab("preserve")}>{t("manage.tabs.preserve")}</button>
                    <button className={`tab-btn ${tab === "tm" ? "is-active" : ""}`} type="button" onClick={() => setTab("tm")}>{t("manage.tabs.tm")}</button>
                    <button className={`tab-btn ${tab === "history" ? "is-active" : ""}`} type="button" onClick={() => setTab("history")}>{t("nav.history", "History")}</button>
                </div>
                <div className="modal-body">
                    {tab === "history" ? (
                        <HistoryTab onLoadFile={onLoadFile} />
                    ) : tab === "preserve" ? (
                        <PreserveTermsTab onClose={onClose} />
                    ) : (
                        <>
                            <div className="action-row flex items-center justify-between gap-2">
                                <div className="flex gap-2">
                                    <button className="btn ghost" type="button" onClick={onSeed}>{t("manage.actions.seed")}</button>
                                    <button className="btn ghost" type="button" onClick={() => handleExport(`${API_BASE}/api/tm/${isGlossary ? "glossary" : "memory"}/export`)}>{t("manage.actions.export_csv")}</button>
                                    <label className="btn ghost">
                                        {t("manage.actions.import_csv")}
                                        <input type="file" accept=".csv" className="hidden-input" onChange={(event) => handleImport(event, `${API_BASE}/api/tm/${isGlossary ? "glossary" : "memory"}/import`, onSeed)} />
                                    </label>
                                    <button className="btn danger" type="button" onClick={isGlossary ? onClearGlossary : onClearMemory}>{t("manage.actions.clear_all")}</button>
                                </div>
                                {selectedIds.length > 0 && (
                                    <div className="batch-actions flex gap-2 animate-in fade-in slide-in-from-right-2">
                                        <span className="text-xs font-bold text-slate-400 self-center mr-2">已選取 {selectedIds.length} 筆</span>
                                        <button className="btn ghost compact !text-blue-600" onClick={handleBatchConvert}>
                                            {isGlossary ? "轉術語" : "轉為對照表"}
                                        </button>
                                        <button className="btn ghost compact !text-red-500" onClick={handleBatchDelete}>批次刪除</button>
                                    </div>
                                )}
                            </div>
                            <div className="create-row">
                                <div className="create-fields grid grid-cols-12 gap-2 w-full items-center">
                                    <select className="select-input col-span-2" value={newEntry.source_lang} onChange={(e) => setNewEntry((prev) => ({ ...prev, source_lang: e.target.value }))}>
                                        {(languageOptions || []).filter((o) => o.code !== "auto").map((o) => <option key={`src-${o.code}`} value={o.code}>{o.label}</option>)}
                                    </select>
                                    <select className="select-input col-span-2" value={newEntry.target_lang} onChange={(e) => setNewEntry((prev) => ({ ...prev, target_lang: e.target.value }))}>
                                        {(languageOptions || []).filter((o) => o.code !== "auto").map((o) => <option key={`tgt-${o.code}`} value={o.code}>{o.label}</option>)}
                                    </select>
                                    <input className="text-input col-span-3" value={newEntry.source_text} placeholder={t("manage.fields.source_text")} onChange={(e) => setNewEntry((prev) => ({ ...prev, source_text: e.target.value }))} />
                                    <input className="text-input col-span-3" value={newEntry.target_text} placeholder={t("manage.fields.target_text")} onChange={(e) => setNewEntry((prev) => ({ ...prev, target_text: e.target.value }))} />
                                    <div className="col-span-2 flex gap-1">
                                        {isGlossary && (
                                            <input className="text-input w-12 text-center !px-1" type="number" value={newEntry.priority} placeholder="0" onChange={(e) => setNewEntry((prev) => ({ ...prev, priority: e.target.value }))} />
                                        )}
                                        <button className={`btn primary flex-1 h-9 min-h-[2.25rem] flex items-center justify-center p-0`} type="button" onClick={handleCreate} title={t("manage.actions.add")}>
                                            <Plus size={18} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <DataTable
                                items={items}
                                isGlossary={isGlossary}
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
                            />

                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

function DataTable({ items, isGlossary, editingKey, draft, saving, selectedIds, makeKey, setDraft, onEdit, onSave, onCancel, onDelete, onSelectRow, onSelectAll, onConvertToGlossary, onConvertToPreserveTerm, t }) {

    if (items.length === 0) return <div className="data-empty">{t("manage.empty")}</div>;

    const allSelected = items.length > 0 && selectedIds.length === items.length;

    return (
        <div className={`data-table ${isGlossary ? "is-glossary" : "is-tm"}`}>
            <div className="data-row data-header">
                <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                    <input type="checkbox" checked={allSelected} onChange={(e) => onSelectAll(e.target.checked)} />
                </div>
                <div className="data-cell">{t("manage.table.source_lang")}</div>
                <div className="data-cell">{t("manage.table.target_lang")}</div>
                <div className="data-cell">{t("manage.table.source")}</div>
                <div className="data-cell">{t("manage.table.target")}</div>
                {isGlossary && <div className="data-cell">{t("manage.table.priority")}</div>}
                <div className="data-cell data-actions">{t("manage.table.actions")}</div>
            </div>
            {(items || []).map((item, idx) => {
                const rowKey = makeKey(item);
                const isEditing = editingKey === rowKey;
                const row = isEditing ? draft || item : item;
                const isSelected = selectedIds.includes(item.id);
                return (
                    <div className={`data-row ${isSelected ? "is-selected" : ""}`} key={`tm-${idx}`}>
                        <div className="data-cell w-10 shrink-0 flex items-center justify-center">
                            <input type="checkbox" checked={isSelected} onChange={(e) => onSelectRow(item.id, e.target.checked)} />
                        </div>
                        <div className="data-cell">
                            {isEditing ? <input className="data-input" value={row.source_lang || ""} onChange={(e) => setDraft((prev) => ({ ...prev, source_lang: e.target.value }))} /> : row.source_lang}
                        </div>
                        <div className="data-cell">
                            {isEditing ? <input className="data-input" value={row.target_lang || ""} onChange={(e) => setDraft((prev) => ({ ...prev, target_lang: e.target.value }))} /> : row.target_lang}
                        </div>
                        <div className="data-cell">
                            {isEditing ? <input className="data-input" value={row.source_text || ""} onChange={(e) => setDraft((prev) => ({ ...prev, source_text: e.target.value }))} /> : row.source_text}
                        </div>
                        <div className="data-cell">
                            {isEditing ? <input className="data-input" value={row.target_text || ""} onChange={(e) => setDraft((prev) => ({ ...prev, target_text: e.target.value }))} /> : row.target_text}
                        </div>
                        {isGlossary && (
                            <div className="data-cell">
                                {isEditing ? <input className="data-input" type="number" value={row.priority ?? 0} onChange={(e) => setDraft((prev) => ({ ...prev, priority: e.target.value }))} /> : row.priority ?? 0}
                            </div>
                        )}
                        <div className="data-cell data-actions flex justify-end gap-1">
                            {isEditing ? (
                                <>
                                    <IconButton icon={Check} variant="action" size="sm" onClick={onSave} disabled={saving} title={t("manage.actions.save")} />
                                    <IconButton icon={RotateCcw} size="sm" onClick={onCancel} disabled={saving} title={t("manage.actions.cancel")} />
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
