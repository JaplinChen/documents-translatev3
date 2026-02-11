import { useEffect, useRef, useState } from "react";
import { useUIStore } from "../store/useUIStore";
import { termsApi } from "../services/api/terms";
import { buildApiUrl } from "../services/api/core";

const DEFAULT_FORM = {
    term: "",
    category_id: null,
    category_name: "",
    languages: [{ lang_code: "zh-TW", value: "" }],
    source: "",
    source_lang: "",
    target_lang: "",
    case_rule: "preserve",
    priority: 5,
    filename: "",
    created_by: ""
};

export function useTerms() {
    const { lastGlossaryAt, setLastGlossaryAt } = useUIStore();
    const skipNextSyncRef = useRef(false);
    const formRef = useRef(DEFAULT_FORM);
    const [terms, setTerms] = useState([]);
    const [categories, setCategories] = useState([]);
    const [filters, setFilters] = useState({
        q: "",
        category_id: "",
        missing_lang: "",
        has_alias: "",
        source: "",
        filename: ""
    });
    const [selectedIds, setSelectedIds] = useState([]);
    const [loading, setLoading] = useState(false);
    const [form, setFormState] = useState(DEFAULT_FORM);
    const [editingId, setEditingId] = useState(null);
    const [preview, setPreview] = useState(null);
    const [pagination, setPagination] = useState({ limit: 200, offset: 0 });
    const [totalCount, setTotalCount] = useState(0);
    const setForm = (updater) => {
        setFormState((prev) => {
            const next = typeof updater === "function" ? updater(prev) : updater;
            formRef.current = next;
            return next;
        });
    };

    const loadCategories = async () => {
        try {
            const data = await termsApi.getCategories();
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
        } catch (err) {
            console.error('[useTerms] loadCategories failed:', err);
        }
    };

    const loadTerms = async (options = {}) => {
        const { silent = false } = options;
        const limit = options.limit ?? pagination.limit;
        const offset = options.offset ?? pagination.offset;
        if (!silent) setLoading(true);
        try {
            const params = {};
            Object.entries(filters).forEach(([k, v]) => {
                if (v !== "" && v != null) params[k] = v;
            });
            params.limit = limit;
            params.offset = offset;
            const data = await termsApi.list(params);
            setTerms(data.items || []);
            setTotalCount(data.total ?? (data.items || []).length);
        } catch (err) {
            console.error('[useTerms] loadTerms failed:', err);
            setTerms([]);
            setTotalCount(0);
        } finally {
            if (!silent) setLoading(false);
        }
    };

    useEffect(() => {
        loadCategories();
    }, []);

    useEffect(() => {
        loadTerms();
    }, [filters, pagination.limit, pagination.offset]);

    useEffect(() => {
        if (!lastGlossaryAt) return;
        if (skipNextSyncRef.current) {
            skipNextSyncRef.current = false;
            return;
        }
        loadCategories();
        loadTerms({ silent: true });
    }, [lastGlossaryAt]);

    const resetForm = () => {
        setForm(DEFAULT_FORM);
        setEditingId(null);
    };

    const upsert = async () => {
        const currentForm = formRef.current || form;
        const payload = {
            ...currentForm,
            // Fix: Convert empty string to null for category_id
            category_id: currentForm.category_id === "" || currentForm.category_id === null ? null : Number(currentForm.category_id),
            source_lang: currentForm.source_lang ? String(currentForm.source_lang).trim() : null,
            target_lang: currentForm.target_lang ? String(currentForm.target_lang).trim() : null,
            aliases: (currentForm.aliases || "")
                .split("|")
                .map((a) => a.trim())
                .filter(Boolean),
        };
        try {
            if (editingId) {
                await termsApi.update(editingId, payload);
            } else {
                await termsApi.create(payload);
            }
        } catch (err) {
            alert(err?.detail || err?.message || "儲存失敗");
            return;
        }
        resetForm();
        await loadTerms({ silent: true });
        skipNextSyncRef.current = true;
        setLastGlossaryAt(Date.now());
    };

    const remove = async (id) => {
        await termsApi.delete(id);
        await loadTerms({ silent: true });
        skipNextSyncRef.current = true;
        setLastGlossaryAt(Date.now());
    };

    const batchUpdate = async (payload) => {
        await termsApi.batchUpdate({ ids: selectedIds, ...payload });
        setSelectedIds([]);
        await loadTerms({ silent: true });
        skipNextSyncRef.current = true;
        setLastGlossaryAt(Date.now());
    };

    const batchDelete = async () => {
        await termsApi.batchDelete({ ids: selectedIds });
        setSelectedIds([]);
        await loadTerms({ silent: true });
        skipNextSyncRef.current = true;
        setLastGlossaryAt(Date.now());
    };

    const exportCsv = () => {
        window.open(buildApiUrl("/api/terms/export"), "_blank");
    };

    const previewImport = async (file, mapping) => {
        const data = await termsApi.importPreview(file, mapping);
        setPreview(data);
    };

    const importCsv = async (file, mapping) => {
        const data = await termsApi.import(file, mapping);
        if (data.error_report_url) {
            window.open(buildApiUrl(data.error_report_url), "_blank");
        }
        await loadTerms();
        return data;
    };

    return {
        terms,
        totalCount,
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
        pagination,
        setPagination,
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
