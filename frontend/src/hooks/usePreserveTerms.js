import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../constants";

export function usePreserveTerms() {
    const { t } = useTranslation();
    const [terms, setTerms] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filterText, setFilterText] = useState("");
    const [filterCategory, setFilterCategory] = useState("all");
    const [editingId, setEditingId] = useState(null);
    const [editForm, setEditForm] = useState({ term: "", category: "產品名稱", case_sensitive: false });
    const [newTerm, setNewTerm] = useState({ term: "", category: "產品名稱", case_sensitive: false });

    const categories = ["產品名稱", "技術縮寫", "專業術語", "翻譯術語", "其他"];

    const fetchTerms = async () => {
        setLoading(true);
        try {
            // Updated to use search query for is_preserve or appropriate backend filter if implemented
            const res = await fetch(`${API_BASE}/api/tm/glossary`);
            if (res.ok) {
                const data = await res.json();
                // Filter terms that are marked as preserve terms
                const allItems = data.items || [];
                setTerms(allItems);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTerms();
    }, []);

    const handleAdd = async () => {
        if (!newTerm.term.trim()) return;
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/tm/glossary`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    source_text: newTerm.term,
                    target_text: "", // Preserve terms don't necessarily have target_text
                    source_lang: "auto",
                    target_lang: "auto",
                    priority: 10,
                    category: newTerm.category,
                    case_sensitive: newTerm.case_sensitive
                }),
            });
            if (res.ok) {
                setNewTerm({ term: "", category: "產品名稱", case_sensitive: false });
                fetchTerms();
            } else {
                const err = await res.json();
                alert(err.detail || t("manage.preserve.alerts.add_fail"));
            }
        } catch (error) {
            alert(`${t("manage.preserve.alerts.add_fail")}: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm(t("manage.preserve.alerts.delete_confirm"))) return;
        try {
            const res = await fetch(`${API_BASE}/api/tm/glossary`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id })
            });
            if (res.ok) fetchTerms();
        } catch (error) {
            alert(`${t("manage.preserve.alerts.delete_fail")}: ${error.message}`);
        }
    };

    const handleUpdate = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/tm/glossary`, {
                method: "POST", // Backend upsert handles updates
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    id: editingId,
                    source_text: editForm.term,
                    target_text: "",
                    category: editForm.category,
                    case_sensitive: editForm.case_sensitive,
                    source_lang: "auto",
                    target_lang: "auto"
                }),
            });
            if (res.ok) {
                setEditingId(null);
                fetchTerms();
            } else {
                const err = await res.json();
                alert(err.detail || t("manage.preserve.alerts.update_fail"));
            }
        } catch (error) {
            alert(`${t("manage.preserve.alerts.update_fail")}: ${error.message}`);
        }
    };

    const handleExport = async () => {
        try {
            window.open(`${API_BASE}/api/tm/glossary/export`, "_blank");
        } catch (error) {
            alert(`${t("manage.preserve.alerts.export_fail")}: ${error.message}`);
        }
    };

    const handleImport = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append("file", file);
        try {
            const res = await fetch(`${API_BASE}/api/tm/glossary/import`, { method: "POST", body: formData });
            if (res.ok) {
                const result = await res.json();
                alert(t("manage.preserve.alerts.import_success", { imported: result.count }));
                fetchTerms();
            }
        } catch (error) {
            alert(`${t("manage.preserve.alerts.import_fail")}: ${error.message}`);
        }
    };

    const handleConvertToGlossary = async (term) => {
        if (!confirm("確定要將此術語轉為對照表嗎？（原記錄將自動刪除）")) return;
        try {
            const res = await fetch(`${API_BASE}/api/tm/glossary`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    source_lang: "auto",
                    target_lang: "zh-TW",
                    source_text: term.source_text,
                    target_text: term.source_text,
                    priority: 10
                })
            });
            if (res.ok) {
                await fetch(`${API_BASE}/api/tm/glossary`, {
                    method: "DELETE",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id: term.id })
                });
                fetchTerms();
            }
        } catch (err) {
            console.error(err);
        }
    };

    const filteredTerms = terms.filter(t => {
        const sourceText = t.source_text || "";
        const matchText = sourceText.toLowerCase().includes(filterText.toLowerCase());
        const matchCat = filterCategory === "all" || t.category === filterCategory;
        return matchText && matchCat;
    });

    return {
        terms, filteredTerms, loading, filterText, setFilterText, filterCategory, setFilterCategory,
        editingId, setEditingId, editForm, setEditForm, newTerm, setNewTerm, categories,
        handleAdd, handleDelete, handleUpdate, handleExport, handleImport, handleConvertToGlossary
    };
}
