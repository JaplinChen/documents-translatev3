import { API_BASE } from '../../constants';

export function useGlossaryMemoryBatch({
    isGlossary,
    items,
    selectedIds,
    setSelectedIds,
    onSeed,
    onConvertToGlossary,
    onConvertToPreserveTerm,
    t,
}) {
    const handleBatchDelete = async () => {
        if (!selectedIds.length) return;
        if (!window.confirm(t('manage.batch.confirm_delete', { count: selectedIds.length }))) return;

        try {
            const endpoint = isGlossary ? 'glossary' : 'memory';
            const res = await fetch(`${API_BASE}/api/tm/${endpoint}/batch`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: selectedIds }),
            });
            if (res.ok) {
                setSelectedIds([]);
                onSeed();
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleBatchConvert = async () => {
        if (!selectedIds.length) return;
        const msg = isGlossary ? t('manage.batch.to_preserve') : t('manage.batch.to_glossary');
        if (!window.confirm(t('manage.batch.confirm_convert', { count: selectedIds.length, action: msg }))) return;

        try {
            let successCount = 0;
            let failCount = 0;
            const errors = [];
            for (const id of selectedIds) {
                const item = items.find((i) => i.id === id);
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
                const baseMsg = t('manage.batch.convert_success', { count: successCount });
                const failMsg = failCount > 0 ? t('manage.batch.convert_failed', { count: failCount }) : '';
                const detail = errors.length > 0 ? `
${errors[0]}` : '';
                alert(`${baseMsg}${failMsg}${detail}`);
            }
        } catch (err) {
            console.error(err);
        }
    };

    return { handleBatchDelete, handleBatchConvert };
}
