const categoryKeyMap = {
    '產品名稱': 'product', '產品': 'product',
    '技術縮寫': 'abbr', '技術': 'abbr',
    '專業術語': 'special', '專業': 'special',
    '翻譯術語': 'trans', '翻譯': 'trans',
    '公司名稱': 'company', '公司': 'company',
    '網絡術語': 'network', '網絡': 'network',
    '其他': 'other',
};

export const getCategoryLabel = (cat, t) => {
    const key = categoryKeyMap[cat];
    if (key) return t(`manage.preserve.categories.${key}`);
    return cat || t('manage.preserve.categories.other');
};

export const sortPreserveTerms = ({ terms, sortKey, sortDir }) => {
    if (!terms) return [];
    const list = [...terms];
    if (!sortKey) return list;

    const dir = sortDir === 'asc' ? 1 : -1;
    list.sort((a, b) => {
        const av = a[sortKey];
        const bv = b[sortKey];

        if (sortKey === 'case_sensitive') {
            const an = av ? 1 : 0;
            const bn = bv ? 1 : 0;
            return (an - bn) * dir;
        }
        if (sortKey === 'created_at') {
            const ad = new Date(av || 0).getTime();
            const bd = new Date(bv || 0).getTime();
            return (ad - bd) * dir;
        }
        return String(av || '').localeCompare(String(bv || ''), 'zh-Hant') * dir;
    });

    return list;
};
