import { API_BASE } from '../../constants';

export const recordFeedbackWithDebounce = ({
    feedbackTimerRef,
    source,
    target,
    sourceLang,
    targetLang,
}) => {
    if (!source || !target) return;
    if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current);
    feedbackTimerRef.current = setTimeout(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/tm/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source,
                    target,
                    source_lang: sourceLang,
                    target_lang: targetLang,
                }),
            });
            if (!response.ok) {
                console.warn('Feedback recording skipped or failed:', response.status);
            }
        } catch (error) {
            console.error('Failed to record feedback:', error);
        }
    }, 2000);
};
