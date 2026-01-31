import { useEffect, useState } from "react";
import { API_BASE } from "../constants";

const DEFAULT_FORM = {
    term: "",
    category_id: null,
    category_name: "",
    status: "active",
    case_rule: "",
    note: "",
    aliases: "",
    languages: [{ lang_code: "zh-TW", value: "" }],
    source: "",
    created_by: ""
};

export function useTerms() {
    const [terms, setTerms] = useState([]);
    const [categories, setCategories] = useState([]);
    const [filters, setFilters] = useState({
        q: "",
        category_id: "",
        status: "",
        missing_lang: "",
        has_alias: "",
        source: ""
    });
    const [selectedIds, setSelectedIds] = useState([]);
    const [loading, setLoading] = useState(false);
    const [form, setForm] = useState(DEFAULT_FORM);
    const [editingId, setEditingId] = useState(null);
    const [preview, setPreview] = useState(null);

    const loadCategories = async () => {
        const res = await fetch(`${API_BASE}/api/terms/categories`);
        const data = await res.json();
        const next = Array.isArray(data.items) ? data.items : [];
        next.sort((a, b) => {
            const ao = Number(a?.sort_order ?? 0);
            const bo = Number(b?.sort_order ?? 0);
            if (ao !== bo) return ao - bo;
            const an = String(a?.name ?? "");
            const bn = String(b?.name ?? "");
            return an.localeCompare(bn, "zh-Hant", { numeric: true, sensitivity: "base" });
        });
        setCategories(next);
    };

    const loadTerms = async () => {
        setLoading(true);
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([k, v]) => {
            if (v !== "" && v != null) params.append(k, v);
        });
        const res = await fetch(`${API_BASE}/api/terms?${params.toString()}`);
        const data = await res.json();
        setTerms(data.items || []);
        setLoading(false);
    };

    useEffect(() => {
        loadCategories();
    }, []);

    useEffect(() => {
        loadTerms();
    }, [filters]);

    const resetForm = () => {
        setForm(DEFAULT_FORM);
        setEditingId(null);
    };

    const upsert = async () => {
        const payload = {
            ...form,
            aliases: form.aliases
                .split("|")
                .map((a) => a.trim())
                .filter(Boolean),
        };
        const url = editingId
            ? `${API_BASE}/api/terms/${editingId}`
            : `${API_BASE}/api/terms`;
        const method = editingId ? "PUT" : "POST";
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!res.ok) {
            const err = await res.text();
            alert(err);
            return;
        }
        resetForm();
        await loadTerms();
    };

    const remove = async (id) => {
        await fetch(`${API_BASE}/api/terms/${id}`, { method: "DELETE" });
        await loadTerms();
    };

    const batchUpdate = async (payload) => {
        await fetch(`${API_BASE}/api/terms/batch`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ids: selectedIds, ...payload }),
        });
        setSelectedIds([]);
        await loadTerms();
    };

    const batchDelete = async () => {
        await fetch(`${API_BASE}/api/terms/batch`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ids: selectedIds }),
        });
        setSelectedIds([]);
        await loadTerms();
    };

    const exportCsv = () => {
        window.open(`${API_BASE}/api/terms/export`, "_blank");
    };

    const previewImport = async (file, mapping) => {
        const formData = new FormData();
        formData.append("file", file);
        if (mapping) formData.append("mapping", JSON.stringify(mapping));
        const res = await fetch(`${API_BASE}/api/terms/import/preview`, {
            method: "POST",
            body: formData,
        });
        const data = await res.json();
        setPreview(data);
    };

    const importCsv = async (file, mapping) => {
        const formData = new FormData();
        formData.append("file", file);
        if (mapping) formData.append("mapping", JSON.stringify(mapping));
        const res = await fetch(`${API_BASE}/api/terms/import`, {
            method: "POST",
            body: formData,
        });
        const data = await res.json();
        if (data.error_report_url) {
            window.open(`${API_BASE}${data.error_report_url}`, "_blank");
        }
        await loadTerms();
        return data;
    };

    return {
        terms,
        categories,
        filters,
        setFilters,
        selectedIds,
        setSelectedIds,
        loading,
        form,
        setForm,
        editingId,
        setEditingId,
        preview,
        setPreview,
        loadTerms,
        resetForm,
        upsert,
        remove,
        batchUpdate,
        batchDelete,
        exportCsv,
        previewImport,
        importCsv,
    };
}
