import { buildApiUrl } from '../../services/api/core';
import { useFileStore } from '../../store/useFileStore';
import { preserveTermsApi } from '../../services/api/preserve_terms';
import { termsApi } from '../../services/api/terms';

const CATEGORY_MAP = {
    product: '產品',
    brand: '品牌',
    person: '人名',
    place: '地名',
    technical: '技術',
    abbreviation: '縮寫',
    other: '其他',
};

const dedupeTerms = (rawTerms, sourceLang, targetLang) => {
    const uniqueTermsMap = new Map();
    rawTerms.forEach((term) => {
        if (!term.source) return;
        const key = term.source.toLowerCase().trim();
        if (!uniqueTermsMap.has(key)) {
            const categoryName = CATEGORY_MAP[term.category] || CATEGORY_MAP.other;
            uniqueTermsMap.set(key, {
                source_lang: sourceLang || 'auto',
                target_lang: targetLang,
                source_text: term.source,
                target_text: term.target || '',
                category_name: categoryName,
                confidence: term.confidence || 5,
                priority: term.confidence || 5,
                reason: term.reason || '',
            });
        }
    });
    const termsToUpsert = Array.from(uniqueTermsMap.values());
    termsToUpsert.sort((a, b) => (b.confidence || 0) - (a.confidence || 0));
    return termsToUpsert;
};

export const extractGlossaryFromBlocks = async ({
    blocks,
    sourceLang,
    targetLang,
    llmProvider,
    llmApiKey,
    llmBaseUrl,
    llmModel,
    t,
    setStatus,
    setBusy,
    setLastPreserveAt,
    setManageOpen,
    setManageTab,
}) => {
    if (!blocks || blocks.length === 0) {
        setStatus(t('status.no_blocks'));
        return;
    }

    setBusy(true);
    setLastPreserveAt(Date.now());
    setStatus(t('manage.glossary_extract.processing'));

    try {
        const payload = {
            blocks,
            target_language: targetLang,
            provider: llmProvider,
            model: llmModel,
            api_key: llmApiKey,
            base_url: llmBaseUrl,
        };

        const response = await fetch(buildApiUrl(`/api/tm/extract-glossary-stream`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || t('manage.glossary_extract.failed'));
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let rawTerms = [];

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            let currentEvent = null;
            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    currentEvent = line.replace('event: ', '').trim();
                } else if (line.startsWith('data: ')) {
                    const dataStr = line.replace('data: ', '').trim();
                    try {
                        const data = JSON.parse(dataStr);
                        if (currentEvent === 'progress') {
                            setStatus(`${data.message} (${data.percent}%)`);
                        } else if (currentEvent === 'complete') {
                            rawTerms = data.terms || [];
                            window._lastExtractionDomain = data.domain || 'general';
                        } else if (currentEvent === 'error') {
                            throw new Error(data.detail || t('manage.glossary_extract.failed'));
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE data:', dataStr, e);
                    }
                }
            }
        }

        if (rawTerms.length === 0) {
            setStatus(t('manage.glossary_extract.empty'));
            return;
        }

        const termsToUpsert = dedupeTerms(rawTerms, sourceLang, targetLang);

        setStatus(t('status.saving'));
        const currentFilename = useFileStore.getState().file?.name || '';

        let finalMsg = t('manage.glossary_extract.success', { count: termsToUpsert.length }) + ' ' +
            t('manage.glossary_extract.learning_hint', { domain: window._lastExtractionDomain || 'general' });
        setStatus(finalMsg);

        const preservePayload = {
            terms: termsToUpsert.map((term) => ({
                term: term.source_text,
                category: term.category_name || '翻譯',
                case_sensitive: true,
            })),
        };

        await preserveTermsApi.batch(preservePayload);

        for (const term of termsToUpsert) {
            await termsApi.upsert({
                term: term.source_text,
                category_name: term.category_name || '翻譯',
                source: 'terminology',
                filename: currentFilename,
                priority: term.priority,
                note: term.reason,
                languages: [{ lang_code: term.target_lang, value: term.target_text }],
            });
        }

        finalMsg = t('manage.glossary_extract.success', { count: termsToUpsert.length }) + ' ' +
            t('manage.glossary_extract.learning_hint', { domain: rawTerms[0]?.domain || 'general' });
        setStatus(finalMsg);
        setManageOpen(true);
        setManageTab('terms');
    } catch (error) {
        console.error('Failed to extract glossary:', error);
        setStatus(t('manage.glossary_extract.failed_detail', { message: error.message }));
    } finally {
        setBusy(false);
    }
};
