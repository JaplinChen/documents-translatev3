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
                className={`quality-badge-compact ${statusClass}`}
                title={`${t("components.quality_badge.score_label")}: ${score}/10\n${issues.join("\n")}`}
                style={{ cursor: issues.length > 0 ? "help" : "default" }}
            >
                {score}
            </span>
        );
    }

    return (
        <div className={`quality-badge ${statusClass}`}>
            <span style={{ fontWeight: "700" }}>{score}</span>
            <span>{getLabel(score)}</span>
            {issues.length > 0 && (
                <span title={issues.join("\n")} style={{ cursor: "help", opacity: 0.7 }}>
                    ⚠️
                </span>
            )}
        </div>
    );
}

export default QualityBadge;
