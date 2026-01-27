import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../constants";

/**
 * Token Usage Statistics Display Component
 * Shows real-time token usage and cost estimation
 */
export default function TokenStats({ className = "" }) {
    const { t } = useTranslation();
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(false);

    const fetchStats = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/token-stats`);
            if (!res.ok) throw new Error("API error");
            const data = await res.json();
            setStats(data);
        } catch (error) {
            // Silently fail to not disrupt UX
            setStats(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
        // Refresh every 60 seconds
        const interval = setInterval(fetchStats, 60000);
        return () => clearInterval(interval);
    }, []);

    if (loading || !stats) return null;

    const { session, all_time } = stats;
    const hasUsage = session.total_tokens > 0;

    const formatNumber = (num) => {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
        if (num >= 1000) return (num / 1000).toFixed(1) + "K";
        return num.toString();
    };

    const formatCost = (cost) => {
        if (cost < 0.01 && cost > 0) return t("components.token_stats.cost_tiny");
        return `$${cost.toFixed(2)}`;
    };

    return (
        <div className={`token-stats ${className}`}>
            <button
                className="token-stats-toggle"
                onClick={() => setExpanded(!expanded)}
                title={t("components.token_stats.title")}
            >
                <span className="token-icon">🔢</span>
                <span className="token-count">{formatNumber(session.total_tokens)}</span>
                {hasUsage && <span className="token-cost">{formatCost(session.estimated_cost_usd)}</span>}
            </button>

            {expanded && (
                <div className="token-stats-dropdown animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="token-stats-header">
                        <h4>{t("components.token_stats.title")}</h4>
                        <button className="close-btn" onClick={() => setExpanded(false)}>×</button>
                    </div>

                    <div className="token-stats-section">
                        <h5>📊 {t("components.token_stats.session_title")}</h5>
                        <div className="stats-grid">
                            <div className="stat-item">
                                <span className="stat-label">{t("components.token_stats.input_tokens")}</span>
                                <span className="stat-value">{formatNumber(session.prompt_tokens)}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">{t("components.token_stats.output_tokens")}</span>
                                <span className="stat-value">{formatNumber(session.completion_tokens)}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">{t("components.token_stats.total_tokens")}</span>
                                <span className="stat-value highlight">{formatNumber(session.total_tokens)}</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-label">{t("components.token_stats.estimated_cost")}</span>
                                <span className="stat-value cost">{formatCost(session.estimated_cost_usd)}</span>
                            </div>
                        </div>
                        <p className="stat-hint">{t("components.token_stats.request_count")}：{session.request_count}</p>
                    </div>

                    <div className="token-stats-section">
                        <h5>📈 {t("components.token_stats.all_time_title")}</h5>
                        <div className="stats-row">
                            <span>{formatNumber(all_time.total_tokens)} Tokens</span>
                            <span>{formatCost(all_time.estimated_cost_usd)}</span>
                            <span>{all_time.request_count} {t("components.token_stats.request_count")}</span>
                        </div>
                    </div>

                    {session.models_used && session.models_used.length > 0 && (
                        <div className="token-stats-section">
                            <h5>🤖 {t("components.token_stats.models_used")}</h5>
                            <div className="model-tags">
                                {session.models_used.map((model, i) => (
                                    <span key={i} className="model-tag">{model}</span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
