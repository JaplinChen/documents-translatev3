import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { exportApi } from "../services/api/export";

/**
 * Term Suggestions Panel Component
 * Displays AI-suggested terms that can be added to glossary
 */
export function TermSuggestionsPanel({ blocks, onAddTerm, onClose }) {
    const { t } = useTranslation();
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [addedTerms, setAddedTerms] = useState(new Set());

    useEffect(() => {
        if (!blocks || blocks.length === 0) {
            setLoading(false);
            return;
        }
        fetchSuggestions();
    }, [blocks]);

    const fetchSuggestions = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await exportApi.suggestTerms(blocks);
            setSuggestions(data.suggestions || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAddTerm = (suggestion) => {
        if (onAddTerm) {
            onAddTerm({
                source_text: suggestion.term,
                target_text: "",
                source_lang: "auto",
                target_lang: "zh-TW",
                priority: 5,
            });
        }
        setAddedTerms(prev => new Set([...prev, suggestion.term.toLowerCase()]));
    };

    const getCategoryIcon = (category) => {
        switch (category) {
            case "product": return "🏷️";
            case "acronym": return "🔤";
            case "technical": return "⚙️";
            case "proper_noun": return "📌";
            default: return "📝";
        }
    };

    const getConfidenceClass = (confidence) => {
        if (confidence >= 0.9) return "confidence-high";
        if (confidence >= 0.7) return "confidence-medium";
        return "confidence-low";
    };

    return (
        <div className="term-suggestions-panel">
            {/* Header */}
            <div className="term-suggestions-header">
                <div>
                    <h3 className="term-suggestions-title">
                        {t("term_suggestions.title")}
                    </h3>
                    <p className="term-suggestions-count">
                        {t("term_suggestions.count", { count: suggestions.length })}
                    </p>
                </div>
                {onClose && (
                    <button onClick={onClose} className="term-suggestions-close-btn">
                        ×
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="term-suggestions-content">
                {loading && (
                    <div className="term-suggestions-state">
                        {t("term_suggestions.loading")}
                    </div>
                )}

                {error && (
                    <div className="term-suggestions-error">
                        {error}
                    </div>
                )}

                {!loading && !error && suggestions.length === 0 && (
                    <div className="term-suggestions-state">
                        {t("term_suggestions.empty")}
                    </div>
                )}

                {!loading && suggestions.map((suggestion, idx) => {
                    const isAdded = addedTerms.has(suggestion.term.toLowerCase());
                    return (
                        <div
                            key={idx}
                            className={`term-suggestion-item ${isAdded ? "is-added" : ""}`}
                        >
                            <div className="term-suggestion-head">
                                <span className="term-suggestion-term">
                                    {getCategoryIcon(suggestion.category)} {suggestion.term}
                                </span>
                                <span className={`term-suggestion-confidence ${getConfidenceClass(suggestion.confidence)}`}>
                                    {Math.round(suggestion.confidence * 100)}%
                                </span>
                            </div>
                            <div className="term-suggestion-context">
                                {suggestion.context}
                            </div>
                            <button
                                onClick={() => handleAddTerm(suggestion)}
                                disabled={isAdded}
                                className={`term-suggestion-add-btn ${isAdded ? "is-added" : ""}`}
                            >
                                {isAdded ? t("term_suggestions.added") : t("term_suggestions.add")}
                            </button>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default TermSuggestionsPanel;
