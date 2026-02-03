import React from 'react';
import { CategoryPill } from './CategoryPill';
import { Plus } from 'lucide-react';
import { getCategoryLabel } from './preserveTabHelpers';

export const buildPreserveColumns = ({
    t,
    editingId,
    editForm,
    setEditForm,
    setEditingId,
    handleKeyDown,
    handleUpdate,
    handleAdd,
    handleConvertToGlossary,
    handleDelete,
    categories,
}) => [
    {
        key: 'term',
        label: t('manage.preserve.table.term'),
        width: '1.5fr',
        sortable: true,
        cellClass: 'font-bold text-slate-700',
        render: (value, item) => editingId === item.id ? (
            <input
                className="data-input !bg-white !border-blue-200 w-full"
                value={editForm.term}
                onChange={(e) => setEditForm({ ...editForm, term: e.target.value })}
                onKeyDown={(e) => handleKeyDown(e, handleUpdate, () => setEditingId(null))}
                autoFocus
                onClick={(e) => e.stopPropagation()}
            />
        ) : value
    },
    {
        key: 'category',
        label: t('manage.preserve.table.category'),
        width: '100px',
        sortable: true,
        cellClass: 'text-center',
        render: (value, item) => editingId === item.id ? (
            <select
                className="data-input !text-[11px] !py-1 !px-2 w-full !bg-white border-blue-200 font-bold"
                value={editForm.category}
                onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                onKeyDown={(e) => handleKeyDown(e, handleUpdate, () => setEditingId(null))}
                onClick={(e) => e.stopPropagation()}
            >
                {categories.map((cat) => (
                    <option key={cat} value={cat}>{getCategoryLabel(cat, t)}</option>
                ))}
            </select>
        ) : (
            <CategoryPill name={getCategoryLabel(value, t)} />
        )
    },
    {
        key: 'case_sensitive',
        label: t('manage.preserve.table.case'),
        width: '80px',
        sortable: true,
        cellClass: 'text-center',
        render: (value, item) => editingId === item.id ? (
            <input
                type="checkbox"
                className="w-4 h-4 rounded border-slate-300 text-blue-600"
                checked={editForm.case_sensitive}
                onChange={(e) => setEditForm({ ...editForm, case_sensitive: e.target.checked })}
                onKeyDown={(e) => handleKeyDown(e, handleUpdate, () => setEditingId(null))}
                onClick={(e) => e.stopPropagation()}
            />
        ) : (
            <span className={`text-[10px] font-black uppercase tracking-wider ${value ? 'text-blue-600' : 'text-slate-300'}`}>
                {value ? t('manage.preserve.table.yes') : t('manage.preserve.table.no')}
            </span>
        )
    },
    {
        key: 'created_at',
        label: t('manage.preserve.table.date'),
        width: '100px',
        sortable: true,
        cellClass: 'text-center text-[10px] font-medium text-slate-400',
        render: (value) => new Date(value || Date.now()).toLocaleDateString()
    },
    {
        key: 'actions',
        label: t('manage.preserve.table.actions'),
        width: '120px',
        render: (_, item) => (
            <div className="flex justify-end gap-1.5">
                {editingId === item.id ? (
                    <>
                        <button className="action-btn-sm success" onClick={(e) => { e.stopPropagation(); handleUpdate(); }} title={t('manage.actions.save')}>
                            <img src="https://emojicdn.elk.sh/✅?style=apple" className="w-5 h-5 object-contain" alt="Save" />
                        </button>
                        <button className="action-btn-sm" onClick={(e) => { e.stopPropagation(); setEditingId(null); }} title={t('manage.actions.cancel')}>
                            <img src="https://emojicdn.elk.sh/❌?style=apple" className="w-5 h-5 object-contain" alt="Cancel" />
                        </button>
                    </>
                ) : (
                    <>
                        <button className="action-btn-sm success" onClick={(e) => { e.stopPropagation(); handleAdd(item); }} title={t('manage.actions.add')}>
                            <Plus size={18} className="text-emerald-600" />
                        </button>
                        <button
                            className="action-btn-sm"
                            onClick={(e) => {
                                e.stopPropagation();
                                setEditingId(item.id);
                                setEditForm({ term: item.term, category: item.category, case_sensitive: item.case_sensitive });
                            }}
                            title={t('manage.actions.edit')}
                        >
                            <img src="https://emojicdn.elk.sh/✏️?style=apple" className="w-5 h-5 object-contain" alt="Edit" />
                        </button>
                        <button className="action-btn-sm primary" onClick={(e) => { e.stopPropagation(); handleConvertToGlossary(item); }} title={t('manage.actions.convert_glossary')}>
                            <img src="https://emojicdn.elk.sh/📑?style=apple" className="w-5 h-5 object-contain" alt="To Glossary" />
                        </button>
                        <button className="action-btn-sm danger" onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }} title={t('common.delete')}>
                            <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                        </button>
                    </>
                )}
            </div>
        )
    }
];
