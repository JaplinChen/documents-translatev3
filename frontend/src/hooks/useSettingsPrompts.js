import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { promptsApi } from "../services/api/prompts";

export function useSettingsPrompts(open, tab) {
    const { t } = useTranslation();
    const [promptList, setPromptList] = useState([]);
    const [selectedPrompt, setSelectedPrompt] = useState("");
    const [promptContent, setPromptContent] = useState("");
    const [promptStatus, setPromptStatus] = useState("");
    const [promptLoading, setPromptLoading] = useState(false);

    const PROMPT_LABELS = {
        translate_json: t("settings.prompt_labels.translate_json"),
        system_message: t("settings.prompt_labels.system_message"),
        ollama_batch: t("settings.prompt_labels.ollama_batch")
    };

    useEffect(() => {
        if (!open || tab !== "prompt") return;
        let active = true;
        promptsApi.list()
            .then((data) => {
                if (!active) return;
                setPromptList(data || []);
                if (data?.length) setSelectedPrompt(prev => prev || data[0]);
            })
            .catch(() => active && setPromptList([]));
        return () => { active = false; };
    }, [open, tab]);

    useEffect(() => {
        if (!open || tab !== "prompt" || !selectedPrompt) return;
        let active = true;
        setPromptLoading(true);
        promptsApi.get(selectedPrompt)
            .then((data) => active && setPromptContent(data.content || ""))
            .catch(() => active && setPromptContent(""))
            .finally(() => active && setPromptLoading(false));
        return () => { active = false; };
    }, [open, tab, selectedPrompt]);

    const handleSavePrompt = async (onClose) => {
        if (!selectedPrompt) return;
        setPromptStatus(t("settings.status.saving"));
        try {
            await promptsApi.save(selectedPrompt, promptContent);
            setPromptStatus(t("settings.status.saved"));
            setTimeout(() => setPromptStatus(""), 2000);
            onClose();
        } catch (error) {
            setPromptStatus(t("settings.status.failed"));
        }
    };

    const handleResetPrompt = async () => {
        if (!selectedPrompt) return;
        setPromptLoading(true);
        try {
            const data = await promptsApi.get(selectedPrompt);
            setPromptContent(data.content || "");
        } finally {
            setPromptLoading(false);
        }
    };

    return {
        promptList, selectedPrompt, setSelectedPrompt,
        promptContent, setPromptContent, promptStatus, promptLoading,
        handleSavePrompt, handleResetPrompt, PROMPT_LABELS
    };
}
