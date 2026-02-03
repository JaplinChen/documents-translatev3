export const buildMappingFromRows = (mappingRows) => {
    const mapping = {};
    mappingRows.forEach((row) => {
        const from = (row.from || '').trim();
        const to = (row.to || '').trim();
        if (from && to) mapping[from] = to;
    });
    return mapping;
};

export const formatLanguages = (langs) => (langs || [])
    .map((l) => `${l.lang_code}:${l.value}`)
    .join(' / ');

export const parseLanguages = (text) => (text || '')
    .split('/')
    .map((raw) => raw.trim())
    .filter(Boolean)
    .map((chunk) => {
        const [code, ...rest] = chunk.split(':');
        const value = rest.join(':').trim();
        if (!code) return null;
        return { lang_code: code.trim(), value };
    })
    .filter(Boolean);

export const detectConflict = ({ form, terms, editingId, t }) => {
    const normalize = (text) => (text || '').trim().toLowerCase();
    const termValue = normalize(form.term);
    if (!termValue) return t('manage.terms_tab.validation.term_required');
    const existing = terms.filter((item) => item.id !== editingId);
    const termSet = new Set(existing.map((item) => normalize(item.term)));
    if (termSet.has(termValue)) {
        return t('manage.terms_tab.validation.term_exists');
    }
    return '';
};

export const renderDiff = (diff, t) => {
    if (!diff || !diff.before || !diff.after) {
        return <div className="text-xs text-slate-400">{t('manage.terms_tab.no_diff')}</div>;
    }
    const before = diff.before || {};
    const after = diff.after || {};
    const fields = ['term', 'category_name', 'source_lang', 'target_lang', 'priority', 'source', 'case_rule', 'filename'];
    return (
        <div className="space-y-1">
            {fields.map((field) => {
                const b = before[field];
                const a = after[field];
                if (JSON.stringify(b) === JSON.stringify(a)) return null;
                return (
                    <div key={field} className="flex gap-2">
                        <span className="w-24 text-slate-400 font-mono text-[10px]">{field}</span>
                        <span className="line-through text-rose-500">{String(b ?? '')}</span>
                        <span className="text-emerald-600">{String(a ?? '')}</span>
                    </div>
                );
            })}
        </div>
    );
};
