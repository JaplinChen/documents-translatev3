import React from 'react';
import { Plus } from 'lucide-react';
import { CategoryPill } from './CategoryPill';

export const buildGlossaryMemoryColumns = ({
    t,
    isGlossary,
    editingKey,
    makeKey,
    draft,
    setDraft,
    handleKeyDown,
    handleSave,
    handleCancel,
    handleCreate,
    handleEdit,
    handleDelete,
    onConvertToPreserveTerm,
    onConvertToGlossary,
    tmCategories,
    saving,
}) => [
    {
        key: 'source_lang',
        label: t('manage.table.source_lang'),
        width: '90px',
        sortable: true,
        render: (val, row) => editingKey === makeKey(row) ? (
            <input
                className="data-input !bg-white !border-blue-200 font-bold"
                value={draft?.source_lang || ''}
                onChange={(e) => setDraft((p) => ({ ...p, source_lang: e.target.value }))}
                onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)}
                autoFocus
            />
        ) : val
    },
    {
        key: 'target_lang',
        label: t('manage.table.target_lang'),
        width: '90px',
        sortable: true,
        render: (val, row) => editingKey === makeKey(row) ? (
            <input
                className="data-input !bg-white !border-blue-200 font-bold"
                value={draft?.target_lang || ''}
                onChange={(e) => setDraft((p) => ({ ...p, target_lang: e.target.value }))}
                onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)}
            />
        ) : val
    },
    {
        key: 'source_text',
        label: t('manage.table.source'),
        width: '1fr',
        sortable: true,
        render: (val, row) => editingKey === makeKey(row) ? (
            <input
                className="data-input !bg-white !border-blue-200 font-bold"
                value={draft?.source_text || ''}
                onChange={(e) => setDraft((p) => ({ ...p, source_text: e.target.value }))}
                onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)}
            />
        ) : val
    },
    {
        key: 'target_text',
        label: t('manage.table.target'),
        width: '1fr',
        sortable: true,
        render: (val, row) => editingKey === makeKey(row) ? (
            <input
                className="data-input !bg-white !border-blue-200 font-bold"
                value={draft?.target_text || ''}
                onChange={(e) => setDraft((p) => ({ ...p, target_text: e.target.value }))}
                onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)}
            />
        ) : val
    },
    ...(isGlossary ? [{
        key: 'priority',
        label: t('manage.table.priority'),
        width: '80px',
        sortable: true,
        render: (val, row) => editingKey === makeKey(row) ? (
            <input
                type="number"
                className="data-input !bg-white !border-blue-200 font-bold"
                value={draft?.priority ?? 0}
                onChange={(e) => setDraft((p) => ({ ...p, priority: e.target.value }))}
                onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)}
            />
        ) : (val ?? 0)
    }] : []),
    {
        key: 'category',
        label: t('manage.fields.category', '分類'),
        width: '100px',
        render: (val, row) => editingKey === makeKey(row) ? (
            <select
                className="data-input !bg-white !border-blue-200 font-bold !text-[12px]"
                value={draft?.category_id || ''}
                onChange={(e) => setDraft((p) => ({
                    ...p,
                    category_id: e.target.value ? parseInt(e.target.value) : null,
                }))}
                onKeyDown={(e) => handleKeyDown(e, handleSave, handleCancel)}
            >
                <option value="">{t('manage.fields.no_category', '無分類')}</option>
                {tmCategories.map((c) => (
                    <option key={`cat-edit-${c.id}`} value={c.id}>{c.name}</option>
                ))}
            </select>
        ) : (
            <CategoryPill name={row.category_name} />
        )
    },
    {
        key: 'actions',
        label: t('manage.table.actions'),
        width: '140px',
        render: (_, row) => (
            <div className="flex justify-end gap-1.5">
                {editingKey === makeKey(row) ? (
                    <>
                        <button className="action-btn-sm success" onClick={handleSave} disabled={saving} title={t('manage.actions.save')}>
                            <img src="https://emojicdn.elk.sh/✅?style=apple" className="w-5 h-5 object-contain" alt="Save" />
                        </button>
                        <button className="action-btn-sm" onClick={handleCancel} disabled={saving} title={t('manage.actions.cancel')}>
                            <img src="https://emojicdn.elk.sh/❌?style=apple" className="w-5 h-5 object-contain" alt="Cancel" />
                        </button>
                    </>
                ) : (
                    <>
                        <button className="action-btn-sm success" onClick={() => handleCreate(row)} title={t('manage.actions.add')}>
                            <Plus size={18} className="text-emerald-600" />
                        </button>
                        <button className="action-btn-sm" onClick={() => handleEdit(row)} title={t('manage.actions.edit')}>
                            <img src="https://emojicdn.elk.sh/✏️?style=apple" className="w-5 h-5 object-contain" alt="Edit" />
                        </button>
                        <button className="action-btn-sm primary" onClick={() => onConvertToPreserveTerm(row)} title={t('manage.actions.convert_preserve')}>
                            <img src="https://emojicdn.elk.sh/🔒?style=apple" className="w-5 h-5 object-contain" alt="Preserve" />
                        </button>
                        {!isGlossary && (
                            <button className="action-btn-sm primary" onClick={() => onConvertToGlossary(row)} title={t('manage.actions.convert_glossary')}>
                                <img src="https://emojicdn.elk.sh/📑?style=apple" className="w-5 h-5 object-contain" alt="To Glossary" />
                            </button>
                        )}
                        <button className="action-btn-sm danger" onClick={() => handleDelete(row)} title={t('manage.actions.delete')}>
                            <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                        </button>
                    </>
                )}
            </div>
        )
    }
];
