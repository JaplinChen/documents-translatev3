import React from "react";
import { useTranslation } from "react-i18next";
import { usePreserveTerms } from "../../hooks/usePreserveTerms";
import { API_BASE } from "../../constants";
import { useUIStore } from "../../store/useUIStore";
import { useSettingsStore } from "../../store/useSettingsStore";
import { PreserveTermsHeader } from "./PreserveTerms/PreserveTermsHeader";
import { PreserveTermsAddForm } from "./PreserveTerms/PreserveTermsAddForm";
import { PreserveTermsList } from "./PreserveTerms/PreserveTermsList";

export default function PreserveTermsTab({ onClose }) {
    const { t } = useTranslation();
    const targetLang = useUIStore((state) => state.targetLang);
    const setLastGlossaryAt = useUIStore((state) => state.setLastGlossaryAt);
    const correctionFillColor = useSettingsStore((state) => state.correction.fillColor);
    const {
        filteredTerms, loading, filterText, setFilterText, filterCategory, setFilterCategory,
        editingId, setEditingId, editForm, setEditForm, newTerm, setNewTerm, categories,
        handleAdd, handleDelete, handleUpdate, handleExport, handleImport, handleConvertToGlossary,
        refreshTerms
    } = usePreserveTerms();

    const [selectedIds, setSelectedIds] = React.useState([]);
    const [visibleCount, setVisibleCount] = React.useState(200);
    const [compactTable, setCompactTable] = React.useState(() => {
        try {
            const saved = localStorage.getItem("manage_table_compact_preserve");
            return saved ? JSON.parse(saved) : false;
        } catch {
            return false;
        }
    });

    React.useEffect(() => {
        setVisibleCount(200);
    }, [filterText, filterCategory]);

    const categoryKeyMap = {
        "產品名稱": "product", "產品": "product",
        "技術縮寫": "abbr", "技術": "abbr",
        "專業術語": "special", "專業": "special",
        "翻譯術語": "trans", "翻譯": "trans",
        "公司名稱": "company", "公司": "company",
        "網絡術語": "network", "網絡": "network",
        "其他": "other"
    };
    const getCategoryLabel = (cat) => {
        const key = categoryKeyMap[cat];
        if (key) return t(`manage.preserve.categories.${key}`);
        return cat || t("manage.preserve.categories.other");
    };


    const handleBatchDelete = async () => {
        if (!selectedIds.length) return;
        if (!window.confirm(t("manage.preserve.alerts.delete_confirm"))) return;
        try {
            await Promise.all(
                selectedIds.map((id) =>
                    fetch(`${API_BASE}/api/preserve-terms/${id}`, {
                        method: "DELETE",
                    })
                )
            );
            setSelectedIds([]);
            refreshTerms();
        } catch (err) {
            console.error(err);
        }
    };

    const handleBatchConvertToGlossary = async () => {
        if (!selectedIds.length) return;
        if (!window.confirm(t("manage.preserve.alerts.batch_convert_confirm"))) return;

        try {
            setLastGlossaryAt(Date.now());
            await Promise.all(
                selectedIds.map(async (id) => {
                    const term = filteredTerms.find((item) => item.id === id);
                    if (!term) return;
                    await fetch(`${API_BASE}/api/preserve-terms/convert-to-glossary`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            id: term.id,
                            target_lang: targetLang || "zh-TW",
                            priority: 10,
                        }),
                    });
                })
            );
            setSelectedIds([]);
            refreshTerms();
        } catch (err) {
            console.error(err);
        }
    };

    const visibleTerms = filteredTerms.slice(0, visibleCount);
    const totalCount = filteredTerms.length;
    const shownCount = visibleTerms.length;

    return (
        <div className="flex flex-col flex-1 min-h-0 overflow-hidden px-1">
            <div className="action-row flex items-center justify-between gap-2">
                <PreserveTermsHeader
                    filterText={filterText} setFilterText={setFilterText}
                    filterCategory={filterCategory} setFilterCategory={setFilterCategory}
                    categories={categories} getCategoryLabel={getCategoryLabel}
                    handleExport={handleExport} handleImport={handleImport}
                    shownCount={shownCount}
                    totalCount={totalCount}
                    canLoadMore={shownCount < totalCount}
                    onLoadMore={() => setVisibleCount((prev) => prev + 200)}
                />
            </div>

            <div className="create-row flex items-center gap-2">
                <div className="flex-1 min-w-0">
                    <PreserveTermsAddForm
                        newTerm={newTerm} setNewTerm={setNewTerm}
                        categories={categories} getCategoryLabel={getCategoryLabel}
                        handleAdd={handleAdd} loading={loading}
                    />
                </div>
                {selectedIds.length > 0 && (
                    <div className="ml-auto flex items-center gap-2 animate-in fade-in slide-in-from-right-2">
                        <button className="btn ghost compact !text-blue-600 text-xs font-bold" onClick={handleBatchConvertToGlossary}>{t("manage.batch.to_glossary")}</button>
                        <button className="btn ghost compact !text-red-500 text-xs font-bold" onClick={handleBatchDelete}>{t("manage.batch.delete")}</button>
                    </div>
                )}
            </div>

            <div className="manage-scroll-area">
                <div className="flex justify-end mb-2">
                    <label className="flex items-center gap-2 text-xs text-slate-600">
                        <input
                            type="checkbox"
                            checked={compactTable}
                            onChange={(e) => {
                                const checked = e.target.checked;
                                setCompactTable(checked);
                                try {
                                    localStorage.setItem("manage_table_compact_preserve", JSON.stringify(checked));
                                } catch {
                                    // 忽略儲存失敗
                                }
                            }}
                        />
                        緊湊模式
                    </label>
                </div>
                <PreserveTermsList
                    filteredTerms={visibleTerms} filterText={filterText} filterCategory={filterCategory}
                    editingId={editingId} setEditingId={setEditingId}
                    editForm={editForm} setEditForm={setEditForm}
                    selectedIds={selectedIds} setSelectedIds={setSelectedIds}
                    categories={categories} getCategoryLabel={getCategoryLabel}
                    handleUpdate={handleUpdate} handleDelete={handleDelete} onConvertToGlossary={handleConvertToGlossary}
                    highlightColor={correctionFillColor}
                    t={t}
                    compact={compactTable}
                />
            </div>
        </div>
    );
}
