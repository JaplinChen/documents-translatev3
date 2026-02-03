import { useTranslation } from 'react-i18next';
import { Plus } from 'lucide-react';
import { API_BASE } from '../../constants';
import { DataTable } from '../common/DataTable';
import { useGlossaryMemoryState } from './useGlossaryMemoryState';

export function GlossaryMemoryPanel(props) {
    const { t } = useTranslation();
    const state = useGlossaryMemoryState({ ...props, t });

    return (
        <div className="flex flex-col h-full min-h-0">
            <div className="action-row flex items-center justify-between gap-2">
                <div className="flex gap-2">
                    <button className="btn ghost compact" type="button" onClick={state.onSeed}>{t('manage.actions.seed')}</button>
                    <button
                        className="btn ghost compact"
                        type="button"
                        onClick={() => state.handleExport(`${API_BASE}/api/tm/${state.isGlossary ? 'glossary' : 'memory'}/export`)}
                    >
                        {t('manage.actions.export_csv')}
                    </button>
                    <label className="btn ghost compact">
                        {t('manage.actions.import_csv')}
                        <input
                            type="file"
                            accept=".csv"
                            className="hidden-input"
                            onChange={(event) => state.handleImport(
                                event,
                                `${API_BASE}/api/tm/${state.isGlossary ? 'glossary' : 'memory'}/import`,
                                state.onSeed
                            )}
                        />
                    </label>
                    <button
                        className="btn ghost compact"
                        type="button"
                        onClick={state.isGlossary ? state.onClearGlossary : state.onClearMemory}
                    >
                        {t('manage.actions.clear_all')}
                    </button>
                    <button
                        className="btn primary compact !px-3"
                        type="button"
                        onClick={() => state.handleCreate()}
                        title={t('manage.actions.add')}
                    >
                        <Plus size={16} />
                    </button>
                </div>
                <div className="flex items-center gap-3">
                    {state.selectedIds.length > 0 && (
                        <div className="batch-actions flex gap-2 animate-in fade-in slide-in-from-right-2">
                            <span className="text-xs font-bold text-slate-400 self-center mr-2">
                                {t('manage.batch.selected_count', { count: state.selectedIds.length })}
                            </span>
                            <button className="btn ghost compact !text-blue-600" onClick={state.handleBatchConvert}>
                                {state.isGlossary ? t('manage.batch.to_preserve') : t('manage.batch.to_glossary')}
                            </button>
                            <button className="btn ghost compact !text-red-500" onClick={state.handleBatchDelete}>
                                {t('manage.batch.delete')}
                            </button>
                        </div>
                    )}
                </div>
            </div>
            <div className="manage-scroll-area flex-1 pr-1 flex flex-col min-h-0">
                <DataTable
                    columns={state.columns}
                    data={state.sortedItems}
                    rowKey={(item) => `${item.source_lang || ''}|${item.target_lang || ''}|${item.source_text || ''}`}
                    selectedIds={state.selectedIds}
                    onSelectionChange={(ids) => state.setSelectedIds(ids)}
                    sortKey={state.sortKey}
                    sortDir={state.sortDir}
                    onSort={state.toggleSort}
                    storageKey={state.isGlossary ? 'manage_table_cols_glossary_v2' : 'manage_table_cols_tm_v2'}
                    compact={state.compactTable}
                    onCompactChange={(checked) => {
                        state.setCompactTable(checked);
                        try {
                            localStorage.setItem(state.compactKey, JSON.stringify(checked));
                        } catch { }
                    }}
                    className={state.isGlossary ? 'is-glossary' : 'is-tm'}
                    highlightColor={props.highlightColor}
                    canLoadMore={state.isGlossary ? state.items.length < state.glossaryTotal : state.items.length < state.tmTotal}
                    totalCount={state.isGlossary ? state.glossaryTotal : state.tmTotal}
                    onLoadMore={state.isGlossary ? state.onLoadMoreGlossary : state.onLoadMoreMemory}
                />
            </div>
        </div>
    );
}
