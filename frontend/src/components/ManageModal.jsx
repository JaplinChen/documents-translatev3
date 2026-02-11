import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import { useDraggableModal } from '../hooks/useDraggableModal';
import { IconButton } from './common/IconButton';
import PreserveTermsTab from './manage/PreserveTermsTab';
import TermsTab from './manage/TermsTab';
import HistoryTab from './manage/HistoryTab';
import TMCategoriesTab from './manage/TMCategoriesTab';
import LearningEventsTab from './manage/LearningEventsTab';
import LearningStatsTab from './manage/LearningStatsTab';
import { useSettingsStore } from '../store/useSettingsStore';
import { GlossaryMemoryPanel } from './manage/GlossaryMemoryPanel';
import { useTmCategories } from './manage/useTmCategories';

export default function ManageModal({
    open,
    onClose,
    tab,
    setTab,
    llmModels,
    llmModel,
    languageOptions,
    defaultSourceLang,
    defaultTargetLang,
    glossaryItems,
    tmItems,
    glossaryTotal,
    tmTotal,
    glossaryPage,
    tmPage,
    glossaryPageSize,
    tmPageSize,
    onGlossaryPageChange,
    onMemoryPageChange,
    onGlossaryPageSizeChange,
    onMemoryPageSizeChange,
    onRefreshGlossary,
    onRefreshMemory,
    onSeed,
    onUpsertGlossary,
    onDeleteGlossary,
    onClearGlossary,
    onUpsertMemory,
    onDeleteMemory,
    onClearMemory,
    onConvertToGlossary,
    onConvertToPreserveTerm,
    onLoadFile,
}) {
    const { t } = useTranslation();
    const supportedTabs = ['glossary', 'preserve', 'tm', 'history', 'learning_events', 'learning_stats', 'tm_categories', 'terms'];
    const { modalRef, position, setPosition, onMouseDown } = useDraggableModal(open, 'manage_modal_state');
    const [modalSize, setModalSize] = useState(null);
    const lastSizeRef = useRef({ width: 0, height: 0 });
    const restoringRef = useRef(false);
    const hasSavedSizeRef = useRef(false);
    const resizingRef = useRef(false);

    const correctionFillColor = useSettingsStore((state) => state.correction.fillColor);
    const { tmCategories, refreshTmCategories } = useTmCategories(open);

    useLayoutEffect(() => {
        if (!open || !modalRef.current) return;
        const el = modalRef.current;
        el.style.top = `${position.top}px`;
        el.style.left = `${position.left}px`;
        if (modalSize?.width) el.style.width = `${modalSize.width}px`;
        else el.style.removeProperty('width');
        if (modalSize?.height) el.style.height = `${modalSize.height}px`;
        else el.style.removeProperty('height');
    }, [open, modalRef, position.top, position.left, modalSize?.width, modalSize?.height]);

    useLayoutEffect(() => {
        if (!open) return;
        restoringRef.current = true;
        try {
            const saved = localStorage.getItem('manage_modal_state');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed?.width && parsed?.height) {
                    setModalSize({ width: parsed.width, height: parsed.height });
                    lastSizeRef.current = { width: parsed.width, height: parsed.height };
                    hasSavedSizeRef.current = true;
                }
                if (typeof parsed?.top === 'number' && typeof parsed?.left === 'number') {
                    setPosition({ top: parsed.top, left: parsed.left });
                }
            }
        } catch {
            setModalSize(null);
        }
        requestAnimationFrame(() => {
            restoringRef.current = false;
        });
    }, [open, setPosition]);

    useEffect(() => {
        if (!open || !modalRef.current) return;
        const target = modalRef.current;
        const observer = new ResizeObserver((entries) => {
            const entry = entries[0];
            if (!entry) return;
            if (restoringRef.current) return;
            if (hasSavedSizeRef.current && !resizingRef.current) return;
            const width = Math.round(entry.contentRect.width);
            const height = Math.round(entry.contentRect.height);
            const last = lastSizeRef.current;
            if (Math.abs(width - last.width) < 2 && Math.abs(height - last.height) < 2) return;
            lastSizeRef.current = { width, height };
            setModalSize({ width, height });
            try {
                const saved = localStorage.getItem('manage_modal_state');
                const parsed = saved ? JSON.parse(saved) : {};
                const nextState = { ...parsed, width, height };
                localStorage.setItem('manage_modal_state', JSON.stringify(nextState));
            } catch {
                // 忽略儲存失敗
            }
        });
        observer.observe(target);
        return () => observer.disconnect();
    }, [open, modalRef]);

    useEffect(() => {
        if (!open) return;
        if (!supportedTabs.includes(tab)) {
            setTab('glossary');
        }
    }, [open, tab, setTab]);

    useEffect(() => {
        if (!open) return;
        const handlePointerUp = () => {
            resizingRef.current = false;
        };
        window.addEventListener('pointerup', handlePointerUp);
        return () => window.removeEventListener('pointerup', handlePointerUp);
    }, [open]);

    if (!open) return null;

    return (
        <div className="modal-backdrop">
            <div
                className="modal is-draggable is-manage"
                ref={modalRef}
                onPointerDown={(event) => {
                    if (!modalRef.current) return;
                    const rect = modalRef.current.getBoundingClientRect();
                    const edge = 16;
                    const nearRight = event.clientX >= rect.right - edge;
                    const nearBottom = event.clientY >= rect.bottom - edge;
                    if (nearRight || nearBottom) {
                        resizingRef.current = true;
                    }
                }}
            >
                <div className="modal-header draggable-handle flex justify-between items-center" onMouseDown={onMouseDown}>
                    <h3>{t('manage.title')}</h3>
                    <IconButton icon={X} onClick={onClose} size="sm" />
                </div>
                <div className="modal-tabs">
                    <button className={`tab-btn ${tab === 'glossary' ? 'is-active' : ''}`} type="button" onClick={() => setTab('glossary')}>{t('manage.tabs.glossary')}</button>
                    <button className={`tab-btn ${tab === 'preserve' ? 'is-active' : ''}`} type="button" onClick={() => setTab('preserve')}>{t('manage.tabs.preserve')}</button>
                    <button className={`tab-btn ${tab === 'tm' ? 'is-active' : ''}`} type="button" onClick={() => setTab('tm')}>{t('manage.tabs.tm')}</button>
                    <button className={`tab-btn ${tab === 'history' ? 'is-active' : ''}`} type="button" onClick={() => setTab('history')}>{t('nav.history', 'History')}</button>
                    <button className={`tab-btn ${tab === 'learning_events' ? 'is-active' : ''}`} type="button" onClick={() => setTab('learning_events')}>{t('manage.tabs.learning_events')}</button>
                    <button className={`tab-btn ${tab === 'learning_stats' ? 'is-active' : ''}`} type="button" onClick={() => setTab('learning_stats')}>{t('manage.tabs.learning_stats')}</button>
                    <button className={`tab-btn ml-4 bg-amber-100 text-amber-900 hover:bg-amber-200 ${tab === 'tm_categories' ? 'is-active !bg-amber-300 !text-amber-950' : ''}`} type="button" onClick={() => setTab('tm_categories')}>{t('manage.tabs.tm_categories')}</button>
                    <button className={`tab-btn bg-amber-100 text-amber-900 hover:bg-amber-200 ${tab === 'terms' ? 'is-active !bg-amber-300 !text-amber-950' : ''}`} type="button" onClick={() => setTab('terms')}>{t('manage.tabs.terms')}</button>
                </div>
                <div className={`modal-body ${tab === 'history' ? '' : 'manage-body'}`}>
                    {tab === 'history' ? (
                        <HistoryTab onLoadFile={onLoadFile} />
                    ) : tab === 'learning_events' ? (
                        <LearningEventsTab />
                    ) : tab === 'learning_stats' ? (
                        <LearningStatsTab />
                    ) : tab === 'terms' ? (
                        <TermsTab />
                    ) : tab === 'preserve' ? (
                        <PreserveTermsTab onClose={onClose} />
                    ) : tab === 'tm_categories' ? (
                        <TMCategoriesTab categories={tmCategories} onRefresh={refreshTmCategories} />
                    ) : (
                        <GlossaryMemoryPanel
                            open={open}
                            tab={tab}
                            glossaryItems={glossaryItems}
                            tmItems={tmItems}
                            glossaryTotal={glossaryTotal}
                            tmTotal={tmTotal}
                            glossaryPage={glossaryPage}
                            tmPage={tmPage}
                            glossaryPageSize={glossaryPageSize}
                            tmPageSize={tmPageSize}
                            onGlossaryPageChange={onGlossaryPageChange}
                            onMemoryPageChange={onMemoryPageChange}
                            onGlossaryPageSizeChange={onGlossaryPageSizeChange}
                            onMemoryPageSizeChange={onMemoryPageSizeChange}
                            defaultSourceLang={defaultSourceLang}
                            defaultTargetLang={defaultTargetLang}
                            tmCategories={tmCategories}
                            onRefreshGlossary={onRefreshGlossary}
                            onRefreshMemory={onRefreshMemory}
                            onSeed={onSeed}
                            onUpsertGlossary={onUpsertGlossary}
                            onDeleteGlossary={onDeleteGlossary}
                            onClearGlossary={onClearGlossary}
                            onUpsertMemory={onUpsertMemory}
                            onDeleteMemory={onDeleteMemory}
                            onClearMemory={onClearMemory}
                            onConvertToGlossary={onConvertToGlossary}
                            onConvertToPreserveTerm={onConvertToPreserveTerm}
                            highlightColor={correctionFillColor}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}
