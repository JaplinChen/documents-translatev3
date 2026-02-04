import React from 'react';
import { CategoryPill } from './CategoryPill';
import { formatLanguages, parseLanguages } from './termsTabHelpers.jsx';

export const buildTermsColumns = ({
    t,
    categories,
    editingId,
    editingField,
    form,
    setForm,
    handleKeyDown,
    handleUpsert,
    resetForm,
    startEdit,
    loadVersions,
    remove,
    langListId,
    commonLangs,
    recentLangs,
    langOptions,
    rememberLang,
    onSourceLangChange,
    onTargetLangChange,
}) => [
    {
        key: 'source_lang',
        label: t('manage.table.source_lang'),
        width: '80px',
        sortable: true,
        cellClass: 'text-slate-500 font-mono text-[11px]',
        render: (value, item) => editingId === item.id ? (
            <select
                className="data-input !bg-white !border-blue-200 font-bold w-full"
                value={form.source_lang || ''}
                onChange={(e) => {
                    const next = e.target.value;
                    if (onSourceLangChange) {
                        onSourceLangChange(next);
                    } else {
                        setForm((p) => ({ ...p, source_lang: next }));
                    }
                    rememberLang && rememberLang(next);
                }}
                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                autoFocus={editingField === 'source_lang'}
                onClick={(e) => e.stopPropagation()}
            >
                <option value="">{t('manage.table.source_lang')}</option>
                {commonLangs?.length ? (
                    <optgroup label="常用">
                        {commonLangs.map((lang) => (
                            <option key={`src-common-${lang}`} value={lang}>{lang}</option>
                        ))}
                    </optgroup>
                ) : null}
                {recentLangs?.length ? (
                    <optgroup label="最近使用">
                        {recentLangs.map((lang) => (
                            <option key={`src-recent-${lang}`} value={lang}>{lang}</option>
                        ))}
                    </optgroup>
                ) : null}
                <optgroup label="其他">
                    {(langOptions || []).filter((lang) => !commonLangs?.includes(lang) && !recentLangs?.includes(lang))
                        .map((lang) => (
                            <option key={`src-other-${lang}`} value={lang}>{lang}</option>
                        ))}
                </optgroup>
            </select>
        ) : (value || '')
    },
    {
        key: 'target_lang',
        label: t('manage.table.target_lang'),
        width: '80px',
        sortable: true,
        cellClass: 'text-slate-500 font-mono text-[11px]',
        render: (value, item) => editingId === item.id ? (
            <select
                className="data-input !bg-white !border-blue-200 font-bold w-full"
                value={form.target_lang || ''}
                onChange={(e) => {
                    const next = e.target.value;
                    if (onTargetLangChange) {
                        onTargetLangChange(next);
                    } else {
                        setForm((p) => {
                            const nextLangs = (p.languages || []).map((lang) => ({
                                ...lang,
                                lang_code: next,
                            }));
                            return {
                                ...p,
                                target_lang: next,
                                languages: nextLangs.length ? nextLangs : [{ lang_code: next, value: '' }],
                            };
                        });
                    }
                    rememberLang && rememberLang(next);
                }}
                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                autoFocus={editingField === 'target_lang'}
                onClick={(e) => e.stopPropagation()}
            >
                <option value="">{t('manage.table.target_lang')}</option>
                {commonLangs?.length ? (
                    <optgroup label="常用">
                        {commonLangs.map((lang) => (
                            <option key={`tgt-common-${lang}`} value={lang}>{lang}</option>
                        ))}
                    </optgroup>
                ) : null}
                {recentLangs?.length ? (
                    <optgroup label="最近使用">
                        {recentLangs.map((lang) => (
                            <option key={`tgt-recent-${lang}`} value={lang}>{lang}</option>
                        ))}
                    </optgroup>
                ) : null}
                <optgroup label="其他">
                    {(langOptions || []).filter((lang) => !commonLangs?.includes(lang) && !recentLangs?.includes(lang))
                        .map((lang) => (
                            <option key={`tgt-other-${lang}`} value={lang}>{lang}</option>
                        ))}
                </optgroup>
            </select>
        ) : (value || '')
    },
    {
        key: 'term',
        label: t('manage.terms_tab.columns.term'),
        width: '1.2fr',
        sortable: true,
        render: (value, item) => editingId === item.id ? (
            <input
                className="data-input !bg-white !border-blue-200 font-bold w-full"
                value={form.term || ''}
                onChange={(e) => setForm((p) => ({ ...p, term: e.target.value }))}
                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                autoFocus={editingField === 'term'}
                onClick={(e) => e.stopPropagation()}
            />
        ) : value
    },
    {
        key: 'languages',
        label: t('manage.terms_tab.columns.languages'),
        width: '1.2fr',
        render: (value, item) => editingId === item.id ? (
            <div className="space-y-1" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                    <span>語言碼</span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                        {form.target_lang || '-'}
                    </span>
                    {!form.target_lang && (
                        <span className="text-rose-500">請先選目標語言</span>
                    )}
                </div>
                <input
                    className="data-input !bg-white !border-blue-200 font-bold w-full"
                    value={(form.languages || [])[0]?.value || ''}
                    onChange={(e) => setForm((p) => ({
                        ...p,
                        languages: [{
                            lang_code: p.target_lang || '',
                            value: e.target.value,
                        }],
                    }))}
                    onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                    autoFocus={editingField === 'languages'}
                    placeholder="請輸入對應內容"
                />
            </div>
        ) : ((value || []).map((l) => l.value).join(' / '))
    },
    {
        key: 'priority',
        label: t('manage.table.priority'),
        width: '60px',
        sortable: true,
        cellClass: 'text-center',
        render: (value, item) => editingId === item.id ? (
            <input
                type="number"
                className="data-input !bg-white !border-blue-200 font-bold !text-center w-full"
                value={form.priority || 0}
                onChange={(e) => setForm((p) => ({ ...p, priority: parseInt(e.target.value) || 0 }))}
                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                autoFocus={editingField === 'priority'}
                onClick={(e) => e.stopPropagation()}
            />
        ) : (
            <span className="text-slate-400 font-mono text-[11px]">{value ?? 0}</span>
        )
    },
    {
        key: 'source',
        label: t('manage.terms_tab.columns.source'),
        width: '80px',
        sortable: true,
        render: (value, item) => editingId === item.id ? (
            <select
                className="data-input !bg-white !border-blue-200 font-bold !text-[12px] w-full"
                value={form.source || ''}
                onChange={(e) => setForm((p) => ({ ...p, source: e.target.value }))}
                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                autoFocus={editingField === 'source'}
                onClick={(e) => e.stopPropagation()}
            >
                <option value="">{t('manage.terms_tab.columns.source')}</option>
                <option value="reference">{t('manage.terms_tab.filter_source_reference')}</option>
                <option value="terminology">{t('manage.terms_tab.filter_source_terminology')}</option>
                <option value="manual">{t('manage.terms_tab.filter_source_manual')}</option>
            </select>
        ) : (
            value && (
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${value === 'reference' ? 'bg-blue-50 text-blue-600 border border-blue-100' :
                    value === 'terminology' ? 'bg-purple-50 text-purple-600 border border-purple-100' :
                        'bg-slate-50 text-slate-500 border border-slate-100'
                    }`}
                >
                    {value === 'reference' ? t('manage.terms_tab.source_labels.reference') :
                        value === 'terminology' ? t('manage.terms_tab.source_labels.terminology') : t('manage.terms_tab.source_labels.manual')}
                </span>
            )
        )
    },
    {
        key: 'case_rule',
        label: t('manage.table.case'),
        width: '80px',
        sortable: true,
        render: (value, item) => editingId === item.id ? (
            <select
                className="data-input !bg-white !border-blue-200 font-bold !text-[12px] w-full"
                value={form.case_rule || 'preserve'}
                onChange={(e) => setForm((p) => ({ ...p, case_rule: e.target.value }))}
                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                autoFocus={editingField === 'case_rule'}
                onClick={(e) => e.stopPropagation()}
            >
                <option value="preserve">{t('manage.terms_tab.case_rules.preserve')}</option>
                <option value="lowercase">{t('manage.terms_tab.case_rules.lowercase')}</option>
                <option value="uppercase">{t('manage.terms_tab.case_rules.uppercase')}</option>
            </select>
        ) : (
            <span className="text-[10px] text-slate-500">{t(`manage.terms_tab.case_rules.${value || 'preserve'}`)}</span>
        )
    },
    {
        key: 'category',
        label: t('manage.terms_tab.columns.category'),
        width: '100px',
        sortable: true,
        sortKey: 'category_name',
        render: (value, item) => editingId === item.id ? (
            <select
                className="data-input !bg-white !border-blue-200 font-bold !text-[12px] w-full"
                value={form.category_id || ''}
                onChange={(e) => setForm((p) => ({ ...p, category_id: e.target.value ? parseInt(e.target.value) : null }))}
                onKeyDown={(e) => handleKeyDown(e, handleUpsert, resetForm)}
                autoFocus={editingField === 'category'}
                onClick={(e) => e.stopPropagation()}
            >
                <option value="">{t('manage.terms_tab.columns.category')}</option>
                {categories.map((c) => (
                    <option key={`cat-edit-${c.id}`} value={c.id}>{c.name}</option>
                ))}
            </select>
        ) : (
            <CategoryPill name={item.category_name} />
        )
    },
    {
        key: 'filename',
        label: t('manage.terms_tab.columns.filename'),
        width: '120px',
        sortable: true,
        cellClass: 'text-slate-500 font-mono text-[11px] truncate',
        render: (value) => <span title={value}>{value || ''}</span>
    },
    {
        key: 'created_by',
        label: t('manage.terms_tab.columns.created_by'),
        width: '90px',
        sortable: true,
        cellClass: 'text-slate-400 text-[11px]',
        render: (value) => value || ''
    },
    {
        key: 'actions',
        label: t('manage.terms_tab.columns.actions'),
        width: '140px',
        render: (_, item) => (
            <div className="flex justify-end gap-1">
                {editingId === item.id ? (
                    <>
                        <button className="action-btn-sm success" onClick={(e) => { e.stopPropagation(); handleUpsert(); }} title={t('manage.actions.save')}>
                            <img src="https://emojicdn.elk.sh/✅?style=apple" className="w-5 h-5 object-contain" alt="Save" />
                        </button>
                        <button className="action-btn-sm" onClick={(e) => { e.stopPropagation(); resetForm(); }} title={t('manage.actions.cancel')}>
                            <img src="https://emojicdn.elk.sh/❌?style=apple" className="w-5 h-5 object-contain" alt="Cancel" />
                        </button>
                    </>
                ) : (
                    <>
                        <button className="action-btn-sm" onClick={(e) => { e.stopPropagation(); loadVersions(item.id); }} title={t('manage.terms_tab.version_btn')}>
                            <img src="https://emojicdn.elk.sh/📜?style=apple" className="w-5 h-5 object-contain" alt="Version" />
                        </button>
                        <button className="action-btn-sm danger" onClick={(e) => { e.stopPropagation(); remove(item.id); }} title={t('manage.actions.delete')}>
                            <img src="https://emojicdn.elk.sh/🗑️?style=apple" className="w-5 h-5 object-contain" alt="Delete" />
                        </button>
                    </>
                )}
            </div>
        )
    }
];
