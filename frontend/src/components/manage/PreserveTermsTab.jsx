import React from "react";
import { useTranslation } from "react-i18next";
import { usePreserveTerms } from "../../hooks/usePreserveTerms";
import { API_BASE } from "../../constants";
import { PreserveTermsHeader } from "./PreserveTerms/PreserveTermsHeader";
import { PreserveTermsAddForm } from "./PreserveTerms/PreserveTermsAddForm";
import { PreserveTermsList } from "./PreserveTerms/PreserveTermsList";

export default function PreserveTermsTab({ onClose }) {
    const { t } = useTranslation();
    const {
        filteredTerms, loading, filterText, setFilterText, filterCategory, setFilterCategory,
        editingId, setEditingId, editForm, setEditForm, newTerm, setNewTerm, categories,
        handleAdd, handleDelete, handleUpdate, handleExport, handleImport, handleConvertToGlossary,
        refreshTerms
    } = usePreserveTerms();

    const [selectedIds, setSelectedIds] = React.useState([]);

    const categoryKeyMap = { "產品名稱": "product", "技術縮寫": "abbr", "專業術語": "special", "其他": "other", "翻譯術語": "trans" };
    const getCategoryLabel = (cat) => t(`manage.preserve.categories.${categoryKeyMap[cat] || "other"}`);

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
        if (!window.confirm("確定要將選取的術語轉為對照表嗎？（原記錄將自動刪除）")) return;

        try {
            await Promise.all(
                selectedIds.map(async (id) => {
                    const term = filteredTerms.find((item) => item.id === id);
                    if (!term) return;
                    await fetch(`${API_BASE}/api/tm/glossary`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            source_lang: "auto",
                            target_lang: "zh-TW",
                            source_text: term.term,
                            target_text: term.term,
                            priority: 10,
                        }),
                    });
                    await fetch(`${API_BASE}/api/preserve-terms/${term.id}`, {
                        method: "DELETE",
                    });
                })
            );
            setSelectedIds([]);
            refreshTerms();
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="modal-body !p-0 flex flex-col h-full overflow-hidden bg-white">
            <div className="sticky-header bg-white p-4 pb-3 space-y-3 sticky top-0 z-20 border-b border-slate-100 shadow-sm !mb-0">
                <PreserveTermsHeader
                    filterText={filterText} setFilterText={setFilterText}
                    filterCategory={filterCategory} setFilterCategory={setFilterCategory}
                    categories={categories} getCategoryLabel={getCategoryLabel}
                    handleExport={handleExport} handleImport={handleImport}
                />

                <div className="flex items-center justify-between gap-4">
                    <PreserveTermsAddForm
                        newTerm={newTerm} setNewTerm={setNewTerm}
                        categories={categories} getCategoryLabel={getCategoryLabel}
                        handleAdd={handleAdd} loading={loading}
                    />
                    {selectedIds.length > 0 && (
                        <div className="flex gap-2 animate-in fade-in slide-in-from-right-2">
                            <button className="btn ghost compact !text-blue-600 text-xs font-bold" onClick={handleBatchConvertToGlossary}>轉為對照表</button>
                            <button className="btn ghost compact !text-red-500 text-xs font-bold" onClick={handleBatchDelete}>批次刪除</button>
                        </div>
                    )}
                </div>
            </div>

            <PreserveTermsList
                filteredTerms={filteredTerms} filterText={filterText} filterCategory={filterCategory}
                editingId={editingId} setEditingId={setEditingId}
                editForm={editForm} setEditForm={setEditForm}
                selectedIds={selectedIds} setSelectedIds={setSelectedIds}
                categories={categories} getCategoryLabel={getCategoryLabel}
                handleUpdate={handleUpdate} handleDelete={handleDelete} onConvertToGlossary={handleConvertToGlossary} t={t}
            />
        </div>
    );
}
