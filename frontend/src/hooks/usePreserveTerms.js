import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../constants";
import { useUIStore } from "../store/useUIStore";

export function usePreserveTerms() {
    const { t } = useTranslation();
    const targetLang = useUIStore((state) => state.targetLang);
    const { setLastPreserveAt, setLastGlossaryAt } = useUIStore();
    const [terms, setTerms] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filterText, setFilterText] = useState("");
    const [filterCategory, setFilterCategory] = useState("all");
    const [editingId, setEditingId] = useState(null);
    const [editForm, setEditForm] = useState({ term: "", category: "產品名稱", case_sensitive: false });
    const [newTerm, setNewTerm] = useState({ term: "", category: "產品名稱", case_sensitive: false });

    const fetchCategories = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/tm/categories`);
            if (res.ok) {
                const data = await res.json();
                const items = Array.isArray(data.items) ? data.items : [];
                items.sort((a, b) => {
                    const ao = Number(a?.sort_order ?? 0);
                    const bo = Number(b?.sort_order ?? 0);
                    if (ao !== bo) return ao - bo;
                    const an = String(a?.name ?? "");
                    const bn = String(b?.name ?? "");
                    return an.localeCompare(bn, "zh-Hant", { numeric: true, sensitivity: "base" });
                });
                const cats = items.map(c => c.name);
                setCategories(cats);
                if (cats.length > 0) {
                    setNewTerm(prev => ({ ...prev, category: cats[0] }));
                    setEditForm(prev => ({ ...prev, category: cats[0] }));
                }
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchTerms = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/preserve-terms`);
            if (res.ok) {
                const data = await res.json();
                const { lastPreserveAt: latestPreserveAt } = useUIStore.getState();
                const parsed = (data.terms || []).map((term) => {
                    if (!term?.created_at || !latestPreserveAt) return { ...term, is_new: false };
                    const createdTs = Date.parse(term.created_at);
                    return { ...term, is_new: !Number.isNaN(createdTs) && createdTs >= latestPreserveAt };
                });
                setTerms(parsed);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCategories();
        fetchTerms();
    }, []);

    const handleAdd = async () => {
        if (!newTerm.term.trim()) return;
        setLoading(true);
        try {
            setLastPreserveAt(Date.now());
            const res = await fetch(`${API_BASE}/api/preserve-terms`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    term: newTerm.term,
                    category: newTerm.category,
                    case_sensitive: newTerm.case_sensitive,
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
            const res = await fetch(`${API_BASE}/api/preserve-terms/${id}`, {
                method: "DELETE",
            });
            if (res.ok) fetchTerms();
        } catch (error) {
            alert(`${t("manage.preserve.alerts.delete_fail")}: ${error.message}`);
        }
    };

    const handleUpdate = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/preserve-terms/${editingId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    category: editForm.category,
                    case_sensitive: editForm.case_sensitive,
                    term: editForm.term,
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
            window.open(`${API_BASE}/api/preserve-terms/export`, "_blank");
        } catch (error) {
            alert(`${t("manage.preserve.alerts.export_fail")}: ${error.message}`);
        }
    };

    const handleImport = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        try {
            setLastPreserveAt(Date.now());
            const csvText = await file.text();
            if (!csvText.trim()) {
                alert(t("manage.preserve.alerts.import_fail"));
                return;
            }
            const res = await fetch(`${API_BASE}/api/preserve-terms/import`, {
                method: "POST",
                headers: { "Content-Type": "text/plain" },
                body: csvText,
            });
            if (res.ok) {
                const result = await res.json();
                alert(
                    t("manage.preserve.alerts.import_success", {
                        imported: result.imported || 0,
                        skipped: result.skipped || 0,
                    })
                );
                fetchTerms();
            }
        } catch (error) {
            alert(`${t("manage.preserve.alerts.import_fail")}: ${error.message}`);
        }
        e.target.value = "";
    };

    const handleConvertToGlossary = async (term) => {
        if (!confirm(t("manage.preserve.alerts.convert_confirm"))) return;
        try {
            setLastGlossaryAt(Date.now());
            const res = await fetch(`${API_BASE}/api/preserve-terms/convert-to-glossary`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    id: term.id,
                    target_lang: targetLang || "zh-TW",
                    priority: 10,
                })
            });
            if (res.ok) {
                fetchTerms();
            }
        } catch (err) {
            console.error(err);
        }
    };

    const filteredTerms = terms.filter(t => {
        const sourceText = t.term || "";
        const matchText = sourceText.toLowerCase().includes(filterText.toLowerCase());
        const matchCat = filterCategory === "all" || t.category === filterCategory;
        return matchText && matchCat;
    });

    return {
        terms, filteredTerms, loading, filterText, setFilterText, filterCategory, setFilterCategory,
        editingId, setEditingId, editForm, setEditForm, newTerm, setNewTerm, categories,
        handleAdd, handleDelete, handleUpdate, handleExport, handleImport, handleConvertToGlossary,
        refreshTerms: fetchTerms,
    };
}
