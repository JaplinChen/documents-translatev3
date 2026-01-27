import React from "react";
import { useTranslation } from "react-i18next";

export function Header({ status, onOpenSettings, onOpenManage }) {
    const { t } = useTranslation();
    return (
        <header className="hero">
            <div className="hero-content">
                <p className="kicker">Document Translation Console</p>
                <h1>{t("app.title")}</h1>
                <p className="subtitle">
                    {t("nav.subtitle")}
                </p>
            </div>

            <div className="header-actions-group">
                <div className="status">
                    <span className="status-label">{t("nav.status") || "Status"}</span>
                    <span className="status-value">{status}</span>
                </div>

                <div className="btn-group">
                    <button
                        className="btn-icon-action text-primary border-primary"
                        type="button"
                        onClick={onOpenSettings}
                        title={t("nav.settings")}
                    >
                        ⚙
                    </button>
                    <button
                        className="btn-icon-action"
                        type="button"
                        onClick={onOpenManage}
                        title={t("manage.title")}
                    >
                        📚
                    </button>
                </div>
            </div>
        </header>
    );
}
