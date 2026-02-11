import { useState } from 'react';

export function useGlossaryMemoryEditing({
    isGlossary,
    glossaryItems,
    tmItems,
    defaultSourceLang,
    defaultTargetLang,
    onUpsertGlossary,
    onDeleteGlossary,
    onUpsertMemory,
    onDeleteMemory,
    setLastGlossaryAt,
    setLastMemoryAt,
    t,
}) {
    const [editingKey, setEditingKey] = useState(null);
    const [editingOriginal, setEditingOriginal] = useState(null);
    const [draft, setDraft] = useState(null);
    const [editingField, setEditingField] = useState(null);
    const [saving, setSaving] = useState(false);
    const [newEntry, setNewEntry] = useState({
        source_lang: '',
        target_lang: '',
        source_text: '',
        target_text: '',
        priority: 0,
        category_id: '',
    });

    const makeKey = (item) => `${item.source_lang || ''}|${item.target_lang || ''}|${item.source_text || ''}`;

    const handleEdit = (item, fieldKey = 'source_text') => {
        setEditingKey(makeKey(item));
        setEditingOriginal(item);
        setDraft({ ...item, priority: item.priority ?? 0 });
        setEditingField(fieldKey);
    };

    const handleCancel = () => {
        setEditingKey(null);
        setEditingOriginal(null);
        setDraft(null);
        setEditingField(null);
    };

    const handleDelete = async (item) => {
        if (!window.confirm(t('manage.confirm.delete'))) return;
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
            : { ...draft, category_id: draft.category_id || '' };
        const originalKey = editingOriginal ? makeKey(editingOriginal) : editingKey;
        const nextKey = makeKey(payload);

        if (!editingOriginal && editingKey?.startsWith('__clone__')) {
            const list = isGlossary ? glossaryItems : tmItems;
            const exists = list.some((item) => makeKey(item) === nextKey);
            if (exists) {
                const confirmed = window.confirm(
                    t('manage.confirm.duplicate_source') ||
                    'A record with the same source text already exists. Saving will overwrite it. Continue?'
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

        // 如果點選 + 按鈕 (proto 為 null) 或者是從現有項隆隆 (proto 有值)
        // 則進入行內編輯模式
        const entryToEdit = proto ? {
            source_lang: proto.source_lang,
            target_lang: proto.target_lang,
            source_text: proto.source_text,
            target_text: proto.target_text,
            priority: proto.priority ?? 10,
            category_id: proto.category_id || '',
        } : {
            source_lang: defaultSourceLang || 'vi',
            target_lang: defaultTargetLang || 'zh-TW',
            source_text: '',
            target_text: '',
            priority: 10,
            category_id: '',
        };

        const cloneKey = `__clone__${Date.now()}`;
        setEditingKey(cloneKey);
        setEditingOriginal(null);
        setDraft(entryToEdit);
        setEditingField('source_text'); // 預設聚焦原文欄位
    };

    const handleKeyDown = (e, saveFn, cancelFn) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveFn();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelFn();
        }
    };

    return {
        editingKey,
        editingOriginal,
        draft,
        editingField,
        saving,
        newEntry,
        setNewEntry,
        setDraft,
        setEditingKey,
        setEditingOriginal,
        setEditingField,
        handleEdit,
        handleCancel,
        handleDelete,
        handleSave,
        handleCreate,
        handleKeyDown,
        makeKey,
    };
}
