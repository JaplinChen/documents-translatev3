import React from "react";
import { useTranslation } from "react-i18next";
import { layoutsApi } from "../../services/api/layouts";
import { useUIStore } from "../../store/useUIStore";

const FILE_TYPES = ["pptx", "docx", "xlsx", "pdf"];

function slugifyName(name) {
    return String(name || "")
        .toLowerCase()
        .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "_")
        .replace(/^_+|_+$/g, "")
        .slice(0, 40) || "layout";
}

export default function LayoutsTab() {
    const { t } = useTranslation();
    const {
        bilingualLayout, layoutDefs, setLayoutDefs,
        layoutParams, setLayoutParams
    } = useUIStore();
    const [fileType, setFileType] = React.useState("xlsx");
    const [mode, setMode] = React.useState("bilingual");
    const [layouts, setLayouts] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [message, setMessage] = React.useState("");
    const [messageType, setMessageType] = React.useState("info");
    const [nameInput, setNameInput] = React.useState("");
    const [selectedBase, setSelectedBase] = React.useState("inline");
    const [searchQuery, setSearchQuery] = React.useState("");

    const load = React.useCallback(async () => {
        setLoading(true);
        setMessage("");
        try {
            const res = await layoutsApi.list(fileType, mode, true);
            const items = res.layouts || [];
            setLayouts(items);
            // 同步更新全域 Store，確保其他組件也能取得最新版面定義
            setLayoutDefs(items);
            if (!items.some((x) => x.id === selectedBase)) {
                setSelectedBase(items[0]?.id || "inline");
            }
        } catch (err) {
            setMessageType("error");
            setMessage(err?.message || t("manage.layouts.load_failed"));
            setLayouts([]);
        } finally {
            setLoading(false);
        }
    }, [fileType, mode, selectedBase, t, setLayoutDefs]);

    React.useEffect(() => {
        load();
    }, [load]);

    const [activeDefinition, setActiveDefinition] = React.useState(null);

    // 優先使用本地 layouts（LayoutsTab 自己載入，保證有資料），全域 layoutDefs 作為備援
    React.useEffect(() => {
        const source = layouts.length > 0 ? layouts : layoutDefs;
        // 先嘗試匹配 bilingualLayout，若不在目前清單中則 fallback 到第一個已啟用的佈局
        let def = source.find(x => x.id === bilingualLayout)
            || source.find(x => x.enabled && !x.is_custom)
            || source[0]
            || null;
        if (def && def.is_custom) {
            // Find base layout to merge missing params
            const base = source.find(x => !x.is_custom && x.apply_value === def.apply_value && x.file_type === def.file_type);
            if (base) {
                def = {
                    ...def,
                    params_schema: {
                        ...def.params_schema,
                        properties: {
                            ...(base.params_schema?.properties || {}),
                            ...(def.params_schema?.properties || {})
                        }
                    }
                };
            }
        }
        setActiveDefinition(def || null);
    }, [layouts, layoutDefs, bilingualLayout]);

    const builtinOrAll = layouts.filter((x) => x.enabled || x.is_custom);
    const customLayouts = layouts.filter((x) => x.is_custom);
    const enabledCustomCount = customLayouts.filter((x) => x.enabled).length;
    const filteredCustomLayouts = customLayouts.filter((item) => {
        const q = searchQuery.trim().toLowerCase();
        if (!q) return true;
        return item.name?.toLowerCase().includes(q) || item.id?.toLowerCase().includes(q);
    });

    const handleCreate = async () => {
        const name = nameInput.trim();
        if (!name) return;
        const base = layouts.find((x) => x.id === selectedBase);
        const id = `custom_${fileType}_${slugifyName(name)}`;
        try {
            await layoutsApi.upsertCustom({
                id,
                name,
                file_type: fileType,
                modes: [mode],
                apply_value: base?.apply_value || selectedBase || "inline",
                enabled: true,
                params_schema: base?.params_schema || { type: "object", properties: {}, additionalProperties: true },
            });
            setNameInput("");
            setMessageType("success");
            setMessage(t("manage.layouts.created"));
            await load();
        } catch (err) {
            setMessageType("error");
            setMessage(err?.message || t("manage.layouts.create_failed"));
        }
    };

    const handleRename = async (item) => {
        const next = window.prompt(
            t("manage.layouts.rename_prompt"),
            item.name
        );
        if (!next || !next.trim() || next.trim() === item.name) return;
        try {
            await layoutsApi.patchCustom(fileType, item.id, { name: next.trim() });
            setMessageType("success");
            await load();
        } catch (err) {
            setMessageType("error");
            setMessage(err?.message || t("manage.layouts.rename_failed"));
        }
    };

    const handleToggle = async (item) => {
        try {
            await layoutsApi.patchCustom(fileType, item.id, { enabled: !item.enabled });
            setMessageType("success");
            await load();
        } catch (err) {
            setMessageType("error");
            setMessage(err?.message || t("manage.layouts.toggle_failed"));
        }
    };

    const handleDelete = async (item) => {
        if (!window.confirm(t("manage.layouts.delete_confirm"))) return;
        try {
            await layoutsApi.removeCustom(fileType, item.id);
            setMessageType("success");
            await load();
        } catch (err) {
            setMessageType("error");
            setMessage(err?.message || t("manage.layouts.delete_failed"));
        }
    };

    const handleExport = async () => {
        try {
            const res = await layoutsApi.exportCustom(fileType);
            const payload = {
                version: 1,
                exported_at: new Date().toISOString(),
                file_type: fileType,
                layouts: res.layouts || [],
            };
            const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `custom-layouts-${fileType}-${new Date().toISOString().slice(0, 10)}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            setMessageType("success");
            setMessage(t("manage.layouts.exported"));
        } catch (err) {
            setMessageType("error");
            setMessage(err?.message || t("manage.layouts.export_failed"));
        }
    };

    const handleImportFile = async (file) => {
        if (!file) return;
        try {
            const raw = await file.text();
            const parsed = JSON.parse(raw);
            const fromPayload = Array.isArray(parsed?.layouts) ? parsed.layouts : [];
            const fromArray = Array.isArray(parsed) ? parsed : [];
            const importLayouts = fromPayload.length > 0 ? fromPayload : fromArray;
            if (!importLayouts.length) {
                setMessageType("error");
                setMessage(t("manage.layouts.import_empty"));
                return;
            }
            await layoutsApi.importCustom({
                layouts: importLayouts,
                mode: "merge",
                file_type: fileType,
            });
            setMessageType("success");
            setMessage(t("manage.layouts.imported"));
            await load();
        } catch (err) {
            setMessageType("error");
            setMessage(err?.message || t("manage.layouts.import_failed"));
        }
    };

    return (
        <section className="layouts-tab">
            <header className="layouts-overview">
                <div>
                    <h4 className="layouts-overview-title">{t("manage.layouts.title")}</h4>
                    <p className="layouts-overview-subtitle">{t("manage.layouts.subtitle")}</p>
                </div>
                <div className="layouts-overview-stats">
                    <div className="layouts-stat-chip">
                        <span className="layouts-stat-label">{t("manage.layouts.custom_count")}</span>
                        <span className="layouts-stat-value">{customLayouts.length}</span>
                    </div>
                    <div className="layouts-stat-chip">
                        <span className="layouts-stat-label">{t("manage.layouts.enabled_count")}</span>
                        <span className="layouts-stat-value">{enabledCustomCount}</span>
                    </div>
                </div>
            </header>

            <section className="layouts-toolbar-card">
                <div className="layouts-toolbar-grid">
                    <div className="form-group">
                        <label className="field-label">{t("manage.layouts.file_type")}</label>
                        <select className="select-input" value={fileType} onChange={(e) => setFileType(e.target.value)}>
                            {FILE_TYPES.map((ft) => <option key={ft} value={ft}>{ft.toUpperCase()}</option>)}
                        </select>
                    </div>
                    <div className="form-group">
                        <label className="field-label">{t("manage.layouts.mode")}</label>
                        <select className="select-input" value={mode} onChange={(e) => setMode(e.target.value)}>
                            <option value="bilingual">{t("sidebar.mode.bilingual")}</option>
                            <option value="translated">{t("sidebar.mode.translated")}</option>
                            <option value="correction">{t("sidebar.mode.correction")}</option>
                        </select>
                    </div>
                    <button type="button" className="btn secondary layouts-action-btn" onClick={load} disabled={loading}>
                        {loading ? "..." : t("manage.layouts.reload")}
                    </button>
                    <button type="button" className="btn secondary layouts-action-btn" onClick={handleExport}>
                        {t("manage.layouts.export")}
                    </button>
                    <label className="btn secondary cursor-pointer layouts-action-btn">
                        {t("manage.layouts.import")}
                        <input
                            type="file"
                            accept=".json"
                            className="hidden-input"
                            onChange={(e) => {
                                const f = e.target.files?.[0];
                                e.target.value = "";
                                handleImportFile(f);
                            }}
                        />
                    </label>
                </div>
                <p className="field-hint">{t("manage.layouts.current_scope", { type: fileType.toUpperCase() })}</p>
            </section>

            <div className="layouts-main-grid">
                <section className="layouts-panel-card">
                    <h5 className="layouts-panel-title">{t("manage.layouts.create_title")}</h5>
                    <p className="field-hint">{t("manage.layouts.create_hint")}</p>
                    <div className="layouts-form-stack">
                        <div className="form-group">
                            <label className="field-label">{t("manage.layouts.base_layout")}</label>
                            <select className="select-input" value={selectedBase} onChange={(e) => setSelectedBase(e.target.value)}>
                                {builtinOrAll.map((item) => (
                                    <option key={item.id} value={item.id}>{item.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label className="field-label">{t("manage.layouts.layout_name")}</label>
                            <input
                                className="text-input"
                                value={nameInput}
                                onChange={(e) => setNameInput(e.target.value)}
                                placeholder={t("manage.layouts.name_placeholder")}
                            />
                        </div>
                        <button type="button" className="btn primary layouts-create-btn" onClick={handleCreate} disabled={!nameInput.trim()}>
                            {t("manage.layouts.create")}
                        </button>
                    </div>
                </section>

                <section className="layouts-panel-card">
                    <div className="layouts-list-header">
                        <h5 className="layouts-panel-title">{t("manage.layouts.custom_list")}</h5>
                        <input
                            className="text-input layouts-search-input"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder={t("manage.layouts.search_placeholder")}
                        />
                    </div>
                    {filteredCustomLayouts.length === 0 && (
                        <p className="field-hint">{t("manage.layouts.empty")}</p>
                    )}
                    <div className="layouts-list">
                        {filteredCustomLayouts.map((item) => (
                            <article key={`${item.file_type}-${item.id}`} className="layouts-item-card">
                                <div className="min-w-0">
                                    <div className="layouts-item-title-row">
                                        <p className="layouts-item-title">{item.name}</p>
                                        <span className={`layouts-item-state ${item.enabled ? "is-on" : "is-off"}`}>
                                            {item.enabled ? t("manage.layouts.state_enabled") : t("manage.layouts.state_disabled")}
                                        </span>
                                    </div>
                                    <p className="layouts-item-id">{item.id}</p>
                                </div>
                                <div className="layouts-item-actions">
                                    <button type="button" className="btn secondary btn-sm" onClick={() => handleRename(item)}>
                                        {t("manage.layouts.rename")}
                                    </button>
                                    <button type="button" className="btn secondary btn-sm" onClick={() => handleToggle(item)}>
                                        {item.enabled
                                            ? t("manage.layouts.disable")
                                            : t("manage.layouts.enable")}
                                    </button>
                                    <button type="button" className="btn secondary btn-sm" onClick={() => handleDelete(item)}>
                                        {t("manage.layouts.delete")}
                                    </button>
                                </div>
                            </article>
                        ))}
                    </div>
                </section>
            </div>

            <section className="layouts-panel-card mt-6">
                <h5 className="layouts-panel-title">{t("sidebar.layout.label")} {t("settings.tabs.params", { defaultValue: "參數設定" })}</h5>

                {activeDefinition?.params_schema?.properties ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(activeDefinition.params_schema.properties).map(([key, cfg]) => {
                            const fieldType = cfg?.type || "string";
                            const label = t(`sidebar.layout.param_labels.${key}`, { defaultValue: cfg?.title || key });
                            const val = layoutParams?.[key];
                            const help = t(`sidebar.layout.param_desc.${key}`, { defaultValue: cfg?.description || "" });
                            const enumOptions = Array.isArray(cfg?.enum) ? cfg.enum : null;

                            if (fieldType === "boolean") {
                                return (
                                    <label key={key} className="layout-param-toggle">
                                        <input
                                            type="checkbox"
                                            checked={!!val}
                                            onChange={(e) => {
                                                const checked = e.target.checked;
                                                setLayoutParams(prev => ({ ...(prev || {}), [key]: checked }));
                                            }}
                                        />
                                        <span className="layout-param-toggle-body">
                                            <span className="layout-param-toggle-title">{label}</span>
                                            {help ? <span className="layout-param-toggle-desc">{help}</span> : null}
                                        </span>
                                    </label>
                                );
                            }

                            if (enumOptions && enumOptions.length > 0) {
                                return (
                                    <div key={key} className="flex flex-col gap-1">
                                        <label className="field-label">{label}</label>
                                        <select
                                            className="select-input"
                                            value={val ?? enumOptions[0]}
                                            onChange={(e) => setLayoutParams(prev => ({ ...(prev || {}), [key]: e.target.value }))}
                                        >
                                            {enumOptions.map((opt) => (
                                                <option key={`${key}-${opt}`} value={opt}>
                                                    {t(`sidebar.layout.param_values.${key}.${opt}`, { defaultValue: String(opt) })}
                                                </option>
                                            ))}
                                        </select>
                                        {help ? <p className="field-hint">{help}</p> : null}
                                    </div>
                                );
                            }

                            return (
                                <div key={key} className="flex flex-col gap-1">
                                    <label className="field-label">{label}</label>
                                    <input
                                        className="text-input"
                                        type={fieldType === "number" || fieldType === "integer" ? "number" : "text"}
                                        value={val ?? ""}
                                        onChange={(e) => {
                                            const v = e.target.value;
                                            const finalVal = (fieldType === "number" || fieldType === "integer") ? (Number(v) || 0) : v;
                                            setLayoutParams(prev => ({ ...(prev || {}), [key]: finalVal }));
                                        }}
                                    />
                                    {help ? <p className="field-hint">{help}</p> : null}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <p className="field-hint text-center py-8 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                        {t("manage.layouts.no_params", { defaultValue: "此版面無可調整參數" })}
                    </p>
                )}
            </section>

            {message && (
                <p className={`layouts-message ${messageType === "error" ? "is-error" : "is-success"}`}>
                    {message}
                </p>
            )}
        </section>
    );
}
