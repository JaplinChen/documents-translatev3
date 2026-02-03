import React from 'react';

export function TermsImportDialog({
    t,
    show,
    onClose,
    importStep,
    setImportStep,
    importFile,
    setImportFile,
    mappingRows,
    updateMappingRow,
    removeMappingRow,
    addMappingRow,
    setMappingText,
    buildMappingFromRows,
    handlePreview,
    handleImport,
    preview,
    importResult,
}) {
    if (!show) return null;

    return (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/20">
            <div className="w-[720px] max-h-[80vh] overflow-auto bg-white rounded-2xl border border-slate-200 shadow-xl p-5">
                <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-bold text-slate-700">{t('manage.terms_tab.import.title', { step: importStep })}</div>
                    <button className="btn ghost compact" type="button" onClick={onClose}>{t('manage.terms_tab.import.close')}</button>
                </div>
                {importStep === 1 && (
                    <div className="space-y-3">
                        <label className="btn ghost w-fit">
                            {t('manage.terms_tab.import.select_csv')}
                            <input type="file" accept=".csv" className="hidden-input" onChange={(e) => setImportFile(e.target.files?.[0] || null)} />
                        </label>
                        <div className="text-xs text-slate-500">{t('manage.terms_tab.import.select_hint')}</div>
                        <button className="btn primary" type="button" onClick={() => setImportStep(2)} disabled={!importFile}>{t('manage.terms_tab.import.next')}</button>
                    </div>
                )}
                {importStep === 2 && (
                    <div className="space-y-3">
                        <div className="text-xs text-slate-500">{t('manage.terms_tab.import.mapping_hint')}</div>
                        <div className="grid grid-cols-12 gap-2 max-h-48 overflow-auto pr-1">
                            {mappingRows.map((row, idx) => (
                                <React.Fragment key={`${row.to}-${idx}`}>
                                    <input
                                        className="text-input col-span-5"
                                        placeholder={t('manage.terms_tab.import.csv_column')}
                                        value={row.from}
                                        onChange={(e) => updateMappingRow(idx, 'from', e.target.value)}
                                    />
                                    <input
                                        className="text-input col-span-5"
                                        placeholder={t('manage.terms_tab.import.system_column')}
                                        value={row.to}
                                        onChange={(e) => updateMappingRow(idx, 'to', e.target.value)}
                                    />
                                    <button
                                        className="btn ghost compact col-span-2"
                                        type="button"
                                        onClick={() => removeMappingRow(idx)}
                                    >
                                        {t('manage.actions.delete')}
                                    </button>
                                </React.Fragment>
                            ))}
                        </div>
                        <div className="flex gap-2">
                            <button className="btn ghost compact" type="button" onClick={addMappingRow}>{t('manage.terms_tab.import.add_mapping')}</button>
                            <button className="btn ghost compact" type="button" onClick={() => setMappingText(JSON.stringify(buildMappingFromRows()))}>{t('manage.terms_tab.import.apply_json')}</button>
                            <button className="btn ghost compact" type="button" onClick={() => setMappingRows([])}>{t('manage.terms_tab.import.clear_mapping')}</button>
                        </div>
                        <div className="flex gap-2">
                            <button className="btn ghost" type="button" onClick={() => setImportStep(1)}>{t('manage.terms_tab.import.prev')}</button>
                            <button className="btn primary" type="button" onClick={async () => {
                                await handlePreview();
                                setImportStep(3);
                            }}>{t('manage.terms_tab.import.next')}</button>
                        </div>
                    </div>
                )}
                {importStep === 3 && (
                    <div className="space-y-3">
                        <div className="text-xs text-slate-500">{t('manage.terms_tab.import.preview_result')}</div>
                        {preview?.summary && (
                            <div className="text-xs text-slate-600">
                                {t('manage.terms_tab.import.summary', { total: preview.summary.total, valid: preview.summary.valid, invalid: preview.summary.invalid })}
                            </div>
                        )}
                        <div className="flex gap-2">
                            <button className="btn ghost" type="button" onClick={() => setImportStep(2)}>{t('manage.terms_tab.import.prev')}</button>
                            <button className="btn primary" type="button" onClick={handleImport}>{t('manage.terms_tab.import.confirm_import')}</button>
                        </div>
                        {importResult && (
                            <div className="text-xs text-slate-600">
                                {t('manage.terms_tab.import.import_complete', { imported: importResult.imported, failed: importResult.failed?.length || 0 })}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
