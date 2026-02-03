import React from 'react';
import { renderDiff } from './termsTabHelpers.jsx';

export function TermsVersionsPanel({ t, versions, onClose }) {
    if (!versions) return null;

    return (
        <div className="mt-3 p-3 border border-slate-200 rounded-lg bg-slate-50/50">
            <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-bold">{t('manage.terms_tab.version.title')}</div>
                <button className="btn ghost compact" onClick={onClose}>{t('manage.terms_tab.import.close')}</button>
            </div>
            <div className="space-y-2 text-xs text-slate-600">
                {versions.items.length === 0 && <div>{t('manage.terms_tab.version.empty')}</div>}
                {versions.items.map((v) => (
                    <div key={v.id} className="p-2 rounded bg-white border border-slate-200 shadow-sm">
                        <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                            <span>{t('manage.terms_tab.version.time')}：{v.created_at}</span>
                            <span>{t('manage.terms_tab.version.operator')}：{v.created_by || '-'}</span>
                        </div>
                        <div className="mt-1">
                            {renderDiff(v.diff, t)}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
