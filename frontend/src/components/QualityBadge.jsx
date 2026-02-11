import { useTranslation } from "react-i18next";
import "../css/quality-badge.css";

/**
 * Quality Badge Component
 */
export function QualityBadge({ score, issues = [], compact = false }) {
    const { t } = useTranslation();
    if (!score && score !== 0) return null;

    const getStatusClass = (s) => {
        if (s >= 8) return "excellent";
        if (s >= 5) return "fair";
        return "poor";
    };

    const getLabel = (s) => {
        if (s >= 9) return t("components.quality_badge.excellent");
        if (s >= 8) return t("components.quality_badge.good");
        if (s >= 6) return t("components.quality_badge.fair");
        if (s >= 4) return t("components.quality_badge.poor");
        return t("components.quality_badge.review");
    };

    const statusClass = getStatusClass(score);

    if (compact) {
        return (
            <span
                className={`quality-badge-compact ${statusClass} ${issues.length > 0 ? "is-help" : ""}`}
                title={`${t("components.quality_badge.score_label")}: ${score}/10\n${issues.join("\n")}`}
            >
                {score}
            </span>
        );
    }

    return (
        <div className={`quality-badge ${statusClass}`}>
            <span className="quality-score">{score}</span>
            <span>{getLabel(score)}</span>
            {issues.length > 0 && (
                <span title={issues.join("\n")} className="quality-help">
                    ⚠️
                </span>
            )}
        </div>
    );
}

export default QualityBadge;
