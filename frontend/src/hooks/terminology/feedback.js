import { tmApi } from '../../services/api/tm';

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
            await tmApi.feedback({
                source,
                target,
                source_lang: sourceLang,
                target_lang: targetLang,
            });
        } catch (error) {
            console.error('Failed to record feedback:', error);
        }
    }, 2000);
};
