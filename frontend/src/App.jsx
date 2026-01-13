import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function useDraggableModal(open) {
  const modalRef = useRef(null);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const dragState = useRef(null);

  useLayoutEffect(() => {
    if (!open) {
      return;
    }
    const modal = modalRef.current;
    if (!modal) {
      return;
    }
    const rect = modal.getBoundingClientRect();
    const top = Math.max(24, (window.innerHeight - rect.height) / 2);
    const left = Math.max(24, (window.innerWidth - rect.width) / 2);
    setPosition({ top, left });
  }, [open]);

  const onMouseDown = (event) => {
    if (event.button !== 0) {
      return;
    }
    if (event.target.closest("button")) {
      return;
    }
    const modal = modalRef.current;
    if (!modal) {
      return;
    }
    const rect = modal.getBoundingClientRect();
    dragState.current = {
      offsetX: event.clientX - rect.left,
      offsetY: event.clientY - rect.top
    };

    const handleMove = (moveEvent) => {
      if (!dragState.current) {
        return;
      }
      const bounds = modal.getBoundingClientRect();
      const maxLeft = window.innerWidth - bounds.width - 12;
      const maxTop = window.innerHeight - bounds.height - 12;
      let nextLeft = moveEvent.clientX - dragState.current.offsetX;
      let nextTop = moveEvent.clientY - dragState.current.offsetY;
      nextLeft = Math.min(Math.max(12, nextLeft), Math.max(12, maxLeft));
      nextTop = Math.min(Math.max(12, nextTop), Math.max(12, maxTop));
      setPosition({ top: nextTop, left: nextLeft });
    };

    const handleUp = () => {
      dragState.current = null;
      document.removeEventListener("mousemove", handleMove);
      document.removeEventListener("mouseup", handleUp);
    };

    document.addEventListener("mousemove", handleMove);
    document.addEventListener("mouseup", handleUp);
  };

  return { modalRef, position, onMouseDown };
}

function App() {
  const [file, setFile] = useState(null);
  const [blocks, setBlocks] = useState([]);
  const [mode, setMode] = useState("bilingual");
  const [bilingualLayout, setBilingualLayout] = useState("inline");
  const [sourceLang, setSourceLang] = useState("");
  const [secondaryLang, setSecondaryLang] = useState("");
  const [targetLang, setTargetLang] = useState("zh-TW");
  const [sourceLocked, setSourceLocked] = useState(false);
  const [secondaryLocked, setSecondaryLocked] = useState(false);
  const [targetLocked, setTargetLocked] = useState(false);
  const [llmOpen, setLlmOpen] = useState(false);
  const [llmProvider, setLlmProvider] = useState("chatgpt");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [llmBaseUrl, setLlmBaseUrl] = useState("");
  const [llmModel, setLlmModel] = useState("");
  const [llmModels, setLlmModels] = useState([]);
  const [llmStatus, setLlmStatus] = useState("");
  const [llmTab, setLlmTab] = useState("llm");
  const [manageTab, setManageTab] = useState("glossary");
  const [manageOpen, setManageOpen] = useState(false);
  const [glossaryItems, setGlossaryItems] = useState([]);
  const [tmItems, setTmItems] = useState([]);
  const [useTm, setUseTm] = useState(false);
  const glossaryFileRef = useRef(null);
  const tmFileRef = useRef(null);
  const [fillColor, setFillColor] = useState("#FFF16A");
  const [textColor, setTextColor] = useState("#D90000");
  const [lineColor, setLineColor] = useState("#7B2CB9");
  const [lineDash, setLineDash] = useState("dash");
  const [filterText, setFilterText] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterSlide, setFilterSlide] = useState("");
  const [status, setStatus] = useState("待命中");
  const [busy, setBusy] = useState(false);
  const leftPanelRef = useRef(null);
  const editorRefs = useRef({});

  const blockCount = blocks.length;
  const selectedCount = blocks.filter((block) => block.selected !== false).length;
  const canApply = file && blockCount > 0 && !busy;

  const modeDescription = useMemo(() => {
    if (mode === "correction") {
      return "中文校正會套用黃色底、紅字與紫色虛線框。";
    }
    if (mode === "translated") {
      return "翻譯檔案會以譯文覆蓋原文，不保留原文內容。";
    }
    return "雙語模式會用原文與譯文合併輸出。";
  }, [mode]);

  const languageOptions = useMemo(
    () => [
      { code: "auto", label: "自動" },
      { code: "vi", label: "越南語" },
      { code: "zh-TW", label: "繁體中文" },
      { code: "zh-CN", label: "簡體中文" },
      { code: "en", label: "英文" },
      { code: "ja", label: "日文" },
      { code: "ko", label: "韓文" }
    ],
    []
  );

  const providerOptions = useMemo(
    () => [
      { code: "chatgpt", label: "ChatGPT (OpenAI)" },
      { code: "gpt-4o", label: "GPT-4o (支援圖片)" },
      { code: "gemini", label: "Gemini" },
      { code: "ollama", label: "Ollama" }
    ],
    []
  );

  const cjkRegex = /[\u4e00-\u9fff\u3400-\u4dbf]/;
  const viRegex =
    /[\u00C0-\u00C3\u00C8-\u00CA\u00CC-\u00CD\u00D2-\u00D5\u00D9-\u00DA\u00DD\u00E0-\u00E3\u00E8-\u00EA\u00EC-\u00ED\u00F2-\u00F5\u00F9-\u00FA\u00FD\u0102\u0103\u0110\u0111\u0128\u0129\u0168\u0169\u01A0\u01A1\u01AF\u01B0\u1EA0-\u1EF9]/i;

  const extractLanguageLines = (text, lang) => {
    const lines = (text || "").split("\n").map((line) => line.trim()).filter(Boolean);
    if (!lang || lang === "auto") {
      return lines;
    }
    if (lang.startsWith("zh")) {
      return lines.filter((line) => cjkRegex.test(line));
    }
    if (lang === "vi") {
      return lines.filter((line) => viRegex.test(line));
    }
    return lines;
  };

  const normalizeText = (text) => (text || "").replace(/\s+/g, "").trim();
  const buildBlockKey = (block) =>
    [block.slide_index ?? "", block.shape_id ?? "", block.block_type ?? ""].join("|");
  const buildBlockUid = (block, fallbackIndex) =>
    block._uid ||
    block.client_id ||
    `${block.slide_index ?? "x"}-${block.shape_id ?? "x"}-${block.block_type ?? "x"}-${fallbackIndex}`;
  const resolveOutputMode = (block) => {
    if (block.output_mode) {
      return block.output_mode;
    }
    const translatedText = (block.translated_text || "").trim();
    return translatedText ? "translated" : "source";
  };

  const defaultBaseUrl = useMemo(() => {
    if (llmProvider === "gemini") {
      return "https://generativelanguage.googleapis.com/v1beta";
    }
    if (llmProvider === "ollama") {
      return "http://localhost:11434";
    }
    return "https://api.openai.com/v1";
  }, [llmProvider]);

  const readLlmSettings = () => {
    const empty = {
      provider: "chatgpt",
      providers: {
        chatgpt: { apiKey: "", baseUrl: "", model: "" },
        gemini: { apiKey: "", baseUrl: "", model: "" },
        ollama: { apiKey: "", baseUrl: "", model: "" }
      }
    };
    const saved = window.localStorage.getItem("llmSettings");
    if (!saved) {
      return empty;
    }
    try {
      const parsed = JSON.parse(saved);
      if (parsed && parsed.providers) {
        return {
          ...empty,
          ...parsed,
          providers: {
            ...empty.providers,
            ...parsed.providers
          }
        };
      }
      const provider = parsed?.provider || "chatgpt";
      return {
        provider,
        providers: {
          ...empty.providers,
          [provider]: {
            apiKey: parsed?.apiKey || "",
            baseUrl: parsed?.baseUrl || "",
            model: parsed?.model || ""
          }
        }
      };
    } catch (error) {
      return empty;
    }
  };

  useEffect(() => {
    const settings = readLlmSettings();
    const provider = settings.provider || "chatgpt";
    const providerSettings = settings.providers?.[provider] || {};
    setLlmProvider(provider);
    setLlmApiKey(providerSettings.apiKey || "");
    setLlmBaseUrl(providerSettings.baseUrl || "");
    setLlmModel(providerSettings.model || "");
  }, []);

  useEffect(() => {
    const saved = window.localStorage.getItem("correctionSettings");
    if (!saved) {
      return;
    }
    try {
      const parsed = JSON.parse(saved);
      setFillColor(parsed.fillColor || "#FFF16A");
      setTextColor(parsed.textColor || "#D90000");
      setLineColor(parsed.lineColor || "#7B2CB9");
      setLineDash(parsed.lineDash || "dash");
    } catch (error) {
      setStatus("校正設定讀取失敗");
    }
  }, []);

  useEffect(() => {
    if (!llmOpen) {
      return;
    }
    if (llmProvider === "ollama" || llmApiKey) {
      handleDetectModels();
    }
  }, [llmOpen, llmProvider, llmApiKey]);

  useEffect(() => {
    const settings = readLlmSettings();
    const providerSettings = settings.providers?.[llmProvider] || {};
    setLlmApiKey(providerSettings.apiKey || "");
    setLlmBaseUrl(providerSettings.baseUrl || "");
    setLlmModel(providerSettings.model || "");
    setLlmModels([]);
    setLlmStatus("");
  }, [llmProvider]);

  useEffect(() => {
    document.documentElement.style.setProperty("--correction-fill", fillColor);
    document.documentElement.style.setProperty("--correction-text", textColor);
    document.documentElement.style.setProperty("--correction-line", lineColor);
  }, [fillColor, textColor, lineColor]);

  useEffect(() => {
    if (!file) {
      return;
    }
    handleDetectLanguages(file);
  }, [file]);

  useEffect(() => {
    if (mode !== "bilingual" || targetLocked) {
      return;
    }
    const desired =
      secondaryLang && secondaryLang !== "auto" ? secondaryLang : "zh-TW";
    if (desired && desired !== targetLang) {
      setTargetLang(desired);
    }
  }, [mode, secondaryLang, targetLang, targetLocked]);

  useEffect(() => {
    if (mode !== "correction") {
      return;
    }
    blocks.forEach((block, index) => {
      const editor = editorRefs.current[index];
      if (!editor) {
        return;
      }
      if (document.activeElement === editor) {
        return;
      }
      const nextText = block.translated_text || "";
      if (editor.innerText !== nextText) {
        editor.innerText = nextText;
      }
    });
  }, [blocks, mode]);

  const updatePanelHeight = () => {
    const panel = leftPanelRef.current;
    if (!panel) {
      return;
    }
    const height = Math.ceil(panel.getBoundingClientRect().height);
    document.documentElement.style.setProperty("--panel-height", `${height}px`);
  };

  useLayoutEffect(() => {
    updatePanelHeight();
  }, [mode, blocks.length]);

  useEffect(() => {
    const panel = leftPanelRef.current;
    if (!panel || typeof ResizeObserver === "undefined") {
      return undefined;
    }
    const observer = new ResizeObserver(() => updatePanelHeight());
    observer.observe(panel);
    window.addEventListener("resize", updatePanelHeight);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", updatePanelHeight);
    };
  }, []);

  const filteredBlocks = useMemo(() => {
    return blocks.filter((block) => {
      if (filterType !== "all" && block.block_type !== filterType) {
        return false;
      }
      if (filterSlide.trim() !== "") {
        const slideValue = Number(filterSlide);
        if (!Number.isNaN(slideValue) && block.slide_index !== slideValue) {
          return false;
        }
      }
      if (filterText.trim() !== "") {
        const needle = filterText.toLowerCase();
        const source = (block.source_text || "").toLowerCase();
        const translated = (block.translated_text || "").toLowerCase();
        if (!source.includes(needle) && !translated.includes(needle)) {
          return false;
        }
      }
      return true;
    });
  }, [blocks, filterText, filterSlide, filterType]);

  const handleExtract = async () => {
    if (!file) {
      setStatus("請先選擇 PPTX 檔案");
      return;
    }
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith(".pptx")) {
      setStatus("只支援 .pptx 檔案，請重新選擇");
      return;
    }
    setBusy(true);
    setStatus("抽取中...");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${API_BASE}/api/pptx/extract`, {
        method: "POST",
        body: formData
      });
      if (!response.ok) {
        const errorText = await response.text();
        let errorMsg = "抽取失敗";
        try {
          const errorData = JSON.parse(errorText);
          errorMsg = errorData.detail || errorMsg;
        } catch {
          errorMsg = errorText || errorMsg;
        }
        throw new Error(errorMsg);
      }
      const data = await response.json();
      const nextBlocks = (data.blocks || []).map((block, idx) => {
        const translatedText = (block.translated_text || "").trim();
        const outputMode = block.output_mode || (translatedText ? "translated" : "source");
        const uid = buildBlockUid(block, idx);
        return {
          ...block,
          _uid: uid,
          client_id: block.client_id || uid,
          selected: block.selected !== false,
          output_mode: outputMode
        };
      });
      setBlocks(nextBlocks);
      if (data.language_summary) {
        applyDetectedLanguages(data.language_summary);
      }
      setStatus(`完成抽取，共 ${data.blocks?.length || 0} 筆`);
    } catch (error) {
      setStatus("抽取失敗，請確認檔案格式");
    } finally {
      setBusy(false);
    }
  };

  const applyDetectedLanguages = (summary) => {
    const primary = summary?.primary || "";
    const secondary = summary?.secondary || "";
    const fallbackSecondary = targetLang || "zh-TW";

    if (!sourceLocked && primary) {
      setSourceLang(primary);
    }
    if (!secondaryLocked) {
      if (secondary) {
        setSecondaryLang(secondary);
      } else if (!secondaryLang) {
        setSecondaryLang(fallbackSecondary);
      }
    }
    if (!targetLocked && !targetLang) {
      if (mode === "correction" && secondary) {
        setTargetLang(secondary);
      } else if (primary) {
        if (secondary) {
          setTargetLang(secondary);
        } else if (primary.startsWith("zh")) {
          setTargetLang("vi");
        } else {
          setTargetLang("zh-TW");
        }
      }
    }
  };

  const handleDetectLanguages = async (fileToDetect) => {
    setStatus("語言偵測中...");
    try {
      const formData = new FormData();
      formData.append("file", fileToDetect);
      const response = await fetch(`${API_BASE}/api/pptx/languages`, {
        method: "POST",
        body: formData
      });
      if (!response.ok) {
        throw new Error("偵測失敗");
      }
      const data = await response.json();
      applyDetectedLanguages(data.language_summary);
      setStatus("已完成語言偵測");
    } catch (error) {
      setStatus("語言偵測失敗");
    }
  };

  const handleTranslate = async () => {
    if (blocks.length === 0) {
      setStatus("請先抽取區塊");
      return;
    }
    if (!targetLang) {
      setStatus("請選擇翻譯/校正語言");
      return;
    }
    if (llmProvider !== "ollama" && !llmApiKey) {
      setStatus("請先在 LLM 設定中填入 API Key");
      return;
    }
    if (!llmModel) {
      setStatus("請先在 LLM 設定中選擇模型");
      return;
    }
    setBusy(true);
    const providerLabel =
      providerOptions.find((option) => option.code === llmProvider)?.label || llmProvider;
    setStatus(`翻譯中...（${providerLabel} / ${llmModel || "未選擇"}）`);
    try {
      const formData = new FormData();
      formData.append("blocks", JSON.stringify(blocks));
      formData.append("source_language", sourceLang || "auto");
      formData.append("secondary_language", secondaryLang || "auto");
      formData.append("target_language", targetLang);
      formData.append("mode", mode);
      formData.append("use_tm", useTm ? "true" : "false");
      formData.append("provider", llmProvider);
      if (llmModel) {
        formData.append("model", llmModel);
      }
      if (llmApiKey) {
        formData.append("api_key", llmApiKey);
      }
      if (llmBaseUrl) {
        formData.append("base_url", llmBaseUrl);
      }
      const response = await fetch(`${API_BASE}/api/pptx/translate`, {
        method: "POST",
        body: formData
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "翻譯失敗");
      }
      const data = await response.json();
      const translated = data.blocks || [];
      if (!translated.length) {
        setStatus("翻譯回傳空結果，請檢查 LLM 設定或 API 配額");
        return;
      }
      const translatedMap = new Map();
      translated.forEach((item) => {
        const key = item.client_id || buildBlockKey(item);
        if (!translatedMap.has(key)) {
          translatedMap.set(key, []);
        }
        translatedMap.get(key).push(item);
      });
      const merged = blocks.map((block, index) => {
        const key = block.client_id || buildBlockKey(block);
        const bucket = translatedMap.get(key);
        const matched = bucket && bucket.length ? bucket.shift() : translated[index];
        const translatedText = matched?.translated_text || block.translated_text || "";
        const sourceText = (block.source_text || "").trim();
        const normalizedTranslated = translatedText.trim();
        const outputMode =
          block.output_mode ||
          (!normalizedTranslated || normalizedTranslated === sourceText ? "source" : "translated");
        return {
          ...block,
          client_id: block.client_id || matched?.client_id || buildBlockUid(block, index),
          translated_text: translatedText,
          output_mode: outputMode
        };
      });
      setBlocks(merged);
      const changed = merged.some(
        (block, idx) => block.translated_text !== blocks[idx]?.translated_text
      );
      setStatus(changed ? "翻譯完成" : "翻譯回傳無變更，請確認語言與模型");
    } catch (error) {
      setStatus(error?.message ? `翻譯失敗：${error.message}` : "翻譯失敗，請稍後再試");
    } finally {
      setBusy(false);
    }
  };

  const handleDetectModels = async () => {
    setLlmStatus("模型偵測中...");
    try {
      const formData = new FormData();
      formData.append("provider", llmProvider);
      if (llmApiKey) {
        formData.append("api_key", llmApiKey);
      }
      if (llmBaseUrl || defaultBaseUrl) {
        formData.append("base_url", llmBaseUrl || defaultBaseUrl);
      }
      const response = await fetch(`${API_BASE}/api/llm/models`, {
        method: "POST",
        body: formData
      });
      if (!response.ok) {
        throw new Error("偵測失敗");
      }
      const data = await response.json();
      const models = data.models || [];
      setLlmModels(models);
      if (models.length && (!llmModel || !models.includes(llmModel))) {
        setLlmModel(models[0]);
      }
      setLlmStatus(models.length ? `已偵測 ${models.length} 個模型` : "未偵測到模型");
    } catch (error) {
      setLlmStatus("模型偵測失敗");
    }
  };

  const handleSaveLlm = () => {
    const stored = readLlmSettings();
    const next = {
      ...stored,
      provider: llmProvider,
      providers: {
        ...stored.providers,
        [llmProvider]: {
          apiKey: llmApiKey,
          baseUrl: llmBaseUrl,
          model: llmModel
        }
      }
    };
    window.localStorage.setItem("llmSettings", JSON.stringify(next));
    setLlmStatus("?????");
    setLlmOpen(false);
  };

  const handleSaveCorrection = () => {
    const payload = {
      fillColor,
      textColor,
      lineColor,
      lineDash
    };
    window.localStorage.setItem("correctionSettings", JSON.stringify(payload));
    setStatus("已保存校正設定");
    setLlmOpen(false);
  };

  const loadGlossary = async () => {
    const response = await fetch(`${API_BASE}/api/tm/glossary`);
    const data = await response.json();
    setGlossaryItems(data.items || []);
  };

  const loadMemory = async () => {
    const response = await fetch(`${API_BASE}/api/tm/memory`);
    const data = await response.json();
    setTmItems(data.items || []);
  };

  const upsertGlossary = async (entry) => {
    await fetch(`${API_BASE}/api/tm/glossary`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry)
    });
    await loadGlossary();
  };

  const deleteGlossary = async (entry) => {
    await fetch(`${API_BASE}/api/tm/glossary`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry)
    });
    await loadGlossary();
  };

  const upsertMemory = async (entry) => {
    await fetch(`${API_BASE}/api/tm/memory`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry)
    });
    await loadMemory();
  };

  const deleteMemory = async (entry) => {
    await fetch(`${API_BASE}/api/tm/memory`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry)
    });
    await loadMemory();
  };

  const convertMemoryToGlossary = async (item) => {
    if (!item?.source_text || !item?.target_text) {
      return;
    }
    await upsertGlossary({
      source_lang: item.source_lang,
      target_lang: item.target_lang,
      source_text: item.source_text,
      target_text: item.target_text,
      priority: 0
    });
    if (item.id) {
      await deleteMemory({ id: item.id });
    }
  };

  const handleSeedTm = async () => {
    await fetch(`${API_BASE}/api/tm/seed`, { method: "POST" });
    await loadGlossary();
    await loadMemory();
  };

  const handleApply = async () => {
    if (!canApply) {
      setStatus("請先上傳與抽取區塊");
      return;
    }
    setBusy(true);
    setStatus("套用中...");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const applyBlocks =
        mode === "correction"
          ? blocks.map((block) =>
              resolveOutputMode(block) === "source"
                ? { ...block, apply: false }
                : block
            )
          : mode === "translated"
            ? blocks.map((block) => ({
                ...block,
                translated_text: block.translated_text || block.source_text || ""
              }))
            : blocks;
      formData.append("blocks", JSON.stringify(applyBlocks));
      formData.append("mode", mode);
        if (mode === "correction") {
          formData.append("fill_color", fillColor);
          formData.append("text_color", textColor);
          formData.append("line_color", lineColor);
          formData.append("line_dash", lineDash);
        }
        if (mode === "bilingual") {
          formData.append("bilingual_layout", bilingualLayout);
        }
      const response = await fetch(`${API_BASE}/api/pptx/apply`, {
        method: "POST",
        body: formData
      });
      if (!response.ok) {
        throw new Error("套用失敗");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = mode === "correction" ? "pptx_corrected.pptx" : "pptx_bilingual.pptx";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setStatus("已輸出 PPTX 檔案");
    } catch (error) {
      setStatus("套用失敗，請稍後再試");
    } finally {
      setBusy(false);
    }
  };

  const handleBlockChange = (index, value) => {
    setBlocks((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], translated_text: value };
      return next;
    });
  };

  const handleBlockSelect = (index, checked) => {
    setBlocks((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], selected: checked };
      return next;
    });
  };

  const handleOutputModeChange = (index, value) => {
    setBlocks((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], output_mode: value };
      return next;
    });
  };

  const extractBlockSource = (block) => {
    const lines = extractLanguageLines(block.source_text, sourceLang || "auto");
    return lines.join("\n").trim();
  };

  const handleAddGlossaryFromBlock = async (block) => {
    const sourceText = extractBlockSource(block);
    const targetText = (block.translated_text || "").trim();
    if (!sourceText || !targetText) {
      setStatus("缺少原文或翻譯內容，無法新增術語");
      return;
    }
    await upsertGlossary({
      source_lang: sourceLang || "auto",
      target_lang: targetLang || "auto",
      source_text: sourceText,
      target_text: targetText,
      priority: 5
    });
    setStatus("已加入術語");
  };

  const handleAddMemoryFromBlock = async (block) => {
    const sourceText = extractBlockSource(block);
    const targetText = (block.translated_text || "").trim();
    if (!sourceText || !targetText) {
      setStatus("缺少原文或翻譯內容，無法新增翻譯記憶");
      return;
    }
    await upsertMemory({
      source_lang: sourceLang || "auto",
      target_lang: targetLang || "auto",
      source_text: sourceText,
      target_text: targetText
    });
    setStatus("已加入翻譯記憶");
  };

  const handleEditorInput = (index, event) => {
    const value = event.currentTarget.innerText;
    handleBlockChange(index, value);
  };

  const handleSelectAll = () => {
    setBlocks((prev) => prev.map((block) => ({ ...block, selected: true })));
  };

  const handleClearSelection = () => {
    setBlocks((prev) => prev.map((block) => ({ ...block, selected: false })));
  };

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="kicker">Documents Translate Console</p>
          <h1>企業級 PPTX 翻譯與校正控制台</h1>
          <p className="subtitle">
            上傳簡報、抽取文字、調整翻譯，再輸出具有校正樣式的 PPTX。
          </p>
        </div>
        <div className="status">
          <span className="status-label">狀態</span>
          <span className="status-value">{status}</span>
        </div>
      </header>

      <main className="grid">
        <section className="panel panel-left" ref={leftPanelRef}>
          <div className="panel-header panel-header-row">
            <div>
              <h2>操作設定</h2>
              <p>檔案上傳與處理流程</p>
            </div>
            <button
              className="icon-btn"
              type="button"
              onClick={() => {
                setLlmTab("llm");
                setLlmOpen(true);
              }}
              aria-label="設定"
              title="設定"
            >
              ⚙
            </button>
            <button
              className="icon-btn"
              type="button"
              onClick={() => {
                setManageTab("glossary");
                setManageOpen(true);
                loadGlossary();
                loadMemory();
              }}
              aria-label="術語與翻譯記憶"
              title="術語與翻譯記憶"
            >
              📚
            </button>
          </div>

          <div className="form-group">
            <label className="field-label" htmlFor="pptx-file">
              PPTX 檔案
            </label>
            <input
              id="pptx-file"
              className="file-input"
              type="file"
              accept=".pptx"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </div>

          <div className="form-group">
            <label className="field-label" htmlFor="mode">
              處理模式
            </label>
            <select
              id="mode"
              className="select-input"
              value={mode}
              onChange={(event) => setMode(event.target.value)}
            >
              <option value="bilingual">雙語輸出</option>
              <option value="translated">翻譯檔案</option>
              <option value="correction">校正</option>
            </select>
            <p className="field-hint">{modeDescription}</p>
          </div>
          {mode === "bilingual" ? (
            <div className="form-group">
              <label className="field-label" htmlFor="bilingual-layout">
                雙語輸出方式
              </label>
              <select
                id="bilingual-layout"
                className="select-input"
                value={bilingualLayout}
                onChange={(event) => setBilingualLayout(event.target.value)}
              >
                <option value="inline">原文 + 譯文同框</option>
                <option value="auto">自動排版</option>
                <option value="new_slide">新增譯文的 slide</option>
              </select>
              <p className="field-hint">
                自動排版會嘗試縮字與分段，必要時拆成多個文字框。
              </p>
            </div>
          ) : null}

          <div className="form-group">
            <label className="field-label">語言設定</label>
            <div className="language-grid">
              <div className="language-item">
                <span>來源語言</span>
                <select
                  className="select-input"
                  value={sourceLang || "auto"}
                  onChange={(event) => {
                    setSourceLang(event.target.value);
                    setSourceLocked(true);
                  }}
                >
                  {languageOptions.map((option) => (
                    <option key={option.code} value={option.code}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="language-item">
                <span>第二語言</span>
                <select
                  className="select-input"
                  value={secondaryLang || "auto"}
                  onChange={(event) => {
                    setSecondaryLang(event.target.value);
                    setSecondaryLocked(true);
                  }}
                >
                  {languageOptions.map((option) => (
                    <option key={option.code} value={option.code}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="language-item">
                <span>{mode === "correction" ? "校正語言" : "翻譯語言"}</span>
                <select
                  className="select-input"
                  value={targetLang}
                  onChange={(event) => {
                    setTargetLang(event.target.value);
                    setTargetLocked(true);
                  }}
                >
                  {languageOptions
                    .filter((option) => option.code !== "auto")
                    .map((option) => (
                      <option key={option.code} value={option.code}>
                        {option.label}
                      </option>
                    ))}
                </select>
              </div>
            </div>
            <label className="toggle-check">
              <input
                type="checkbox"
                checked={useTm}
                onChange={(event) => setUseTm(event.target.checked)}
              />
              使用翻譯記憶（TM）
            </label>
            <p className="field-hint">
              已選擇檔案會自動偵測來源與第二語言，可手動覆寫。
            </p>
          </div>

          <div className="action-row">
            <button className="btn" type="button" onClick={handleExtract} disabled={busy}>
              抽取區塊
            </button>
            <button
              className="btn ghost"
              type="button"
              onClick={handleTranslate}
              disabled={busy || blocks.length === 0}
            >
              自動翻譯
            </button>
            <button
              className="btn primary"
              type="button"
              onClick={handleApply}
              disabled={!canApply}
            >
              套用並輸出
            </button>
          </div>

          <div className="flow-panel">
            <div className="flow-item">
              <span className={`flow-dot ${file ? "is-active" : ""}`} />
              <div>
                <strong>1. 上傳 PPTX</strong>
                <p>{file ? "已選擇檔案" : "尚未選擇"}</p>
              </div>
            </div>
            <div className="flow-item">
              <span className={`flow-dot ${blockCount > 0 ? "is-active" : ""}`} />
              <div>
                <strong>2. 抽取文字</strong>
                <p>{blockCount > 0 ? `已抽取 ${blockCount} 筆` : "等待抽取"}</p>
              </div>
            </div>
            <div className="flow-item">
              <span className={`flow-dot ${selectedCount > 0 ? "is-active" : ""}`} />
              <div>
                <strong>3. 編輯翻譯</strong>
                <p>{selectedCount > 0 ? `已選取 ${selectedCount} 筆` : "尚未選取"}</p>
              </div>
            </div>
            <div className="flow-item">
              <span className={`flow-dot ${status.includes("輸出") ? "is-active" : ""}`} />
              <div>
                <strong>4. 輸出 PPTX</strong>
                <p>{status.includes("輸出") ? "已完成" : "等待套用"}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="panel panel-right">
          <div className="panel-header">
            <h2>文字區塊</h2>
            <p>
              共 {blockCount} 筆，顯示 {filteredBlocks.length} 筆，可直接修改
              translated_text
            </p>
          </div>

          {blockCount === 0 ? (
            <div className="empty-state">
              <p>尚未抽取任何文字區塊</p>
              <span>請先上傳 PPTX 並按下「抽取區塊」</span>
            </div>
          ) : (
            <>
              <div className="filter-row">
                <div className="filter-item">
                  <label className="field-label" htmlFor="filter-text">
                    搜尋
                  </label>
                  <input
                    id="filter-text"
                    className="select-input"
                    type="text"
                    value={filterText}
                    placeholder="搜尋原文/翻譯"
                    onChange={(event) => setFilterText(event.target.value)}
                  />
                </div>
                <div className="filter-item">
                  <label className="field-label" htmlFor="filter-type">
                    類型
                  </label>
                  <select
                    id="filter-type"
                    className="select-input"
                    value={filterType}
                    onChange={(event) => setFilterType(event.target.value)}
                  >
                    <option value="all">全部</option>
                    <option value="textbox">textbox</option>
                    <option value="table_cell">table_cell</option>
                    <option value="notes">notes</option>
                  </select>
                </div>
                <div className="filter-item">
                  <label className="field-label" htmlFor="filter-slide">
                    Slide
                  </label>
                  <input
                    id="filter-slide"
                    className="select-input"
                    type="number"
                    value={filterSlide}
                    placeholder="0"
                    onChange={(event) => setFilterSlide(event.target.value)}
                  />
                </div>
                <div className="filter-actions">
                  <button className="btn ghost" type="button" onClick={handleSelectAll}>
                    全選
                  </button>
                  <button className="btn ghost" type="button" onClick={handleClearSelection}>
                    清除
                  </button>
                </div>
              </div>

              <div className="block-list">
                {filteredBlocks.map((block, filteredIndex) => {
                  const index = blocks.findIndex((item) => item._uid === block._uid);
                  return (
                    <div
                      className={`block-card ${block.selected === false ? "is-muted" : ""}`}
                      key={block._uid || `${block.slide_index}-${block.shape_id}-${filteredIndex}`}
                    >
                      <div className="block-meta">
                        <label className="select-box">
                          <input
                            type="checkbox"
                            checked={block.selected !== false}
                            onChange={(event) =>
                              handleBlockSelect(index, event.target.checked)
                            }
                          />
                          <span>套用</span>
                        </label>
                        <span>Slide {block.slide_index}</span>
                        <span>Shape {block.shape_id}</span>
                        <span className="pill">{block.block_type}</span>
                      </div>
                      <div className="block-body">
                        <div>
                          <div className="field-label-row">
                            <span className="field-label">原文</span>
                            {mode === "correction" ? (
                              <label className="toggle-check">
                                <input
                                  type="checkbox"
                                  checked={resolveOutputMode(block) === "source"}
                                  onChange={() => handleOutputModeChange(index, "source")}
                                />
                                <span>輸出</span>
                              </label>
                            ) : null}
                          </div>
                          <div className="readonly-box">{block.source_text}</div>
                        </div>
                        <div>
                          <div className="field-label-row">
                            <span className="field-label">翻譯 / 校正</span>
                            {mode === "correction" ? (
                              <label className="toggle-check">
                                <input
                                  type="checkbox"
                                  checked={resolveOutputMode(block) === "translated"}
                                  onChange={() => handleOutputModeChange(index, "translated")}
                                />
                                <span>輸出</span>
                              </label>
                            ) : null}
                          </div>
                      {mode === "correction" ? (
                        <div className="correction-stack">
                          <div className="correction-preview">
                            {(() => {
                              const sourceLines = extractLanguageLines(
                                block.source_text,
                                sourceLang || "auto"
                              );
                              const secondaryLines = extractLanguageLines(
                                block.source_text,
                                secondaryLang || "auto"
                              );
                              const sourceText = sourceLines.join("\n");
                              const secondaryText = secondaryLines.join("\n");
                              const translatedText = block.translated_text || "";
                              const showTranslation =
                                normalizeText(translatedText) &&
                                normalizeText(translatedText) !== normalizeText(secondaryText);

                              if (!showTranslation) {
                                return null;
                              }
                              return (
                                <>
                                  <div className="correction-source">{sourceText}</div>
                                  <div
                                    className="correction-editor"
                                    contentEditable
                                    role="textbox"
                                    aria-multiline="true"
                                    suppressContentEditableWarning
                                    ref={(node) => {
                                      editorRefs.current[index] = node;
                                    }}
                                    onInput={(event) => handleEditorInput(index, event)}
                                  >
                                    {translatedText}
                                  </div>
                                </>
                              );
                            })()}
                          </div>
                        </div>
                      ) : (
                            <textarea
                              className="textarea"
                              rows={3}
                              value={block.translated_text || ""}
                              onChange={(event) =>
                                handleBlockChange(index, event.target.value)
                              }
                            />
                          )}
                        </div>
                      </div>
                      <div className="block-actions">
                        <button
                          className="action-btn"
                          type="button"
                          onClick={() => handleAddGlossaryFromBlock(block)}
                          disabled={!block.translated_text}
                        >
                          加入術語
                        </button>
                        <button
                          className="action-btn"
                          type="button"
                          onClick={() => handleAddMemoryFromBlock(block)}
                          disabled={!block.translated_text}
                        >
                          加入翻譯記憶
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </section>
      </main>
      <LlmModal
        open={llmOpen}
        onClose={() => setLlmOpen(false)}
        tab={llmTab}
        setTab={setLlmTab}
        providerOptions={providerOptions}
        llmProvider={llmProvider}
        setLlmProvider={setLlmProvider}
        llmApiKey={llmApiKey}
        setLlmApiKey={setLlmApiKey}
        llmBaseUrl={llmBaseUrl}
        setLlmBaseUrl={setLlmBaseUrl}
        llmModel={llmModel}
        setLlmModel={setLlmModel}
        llmModels={llmModels}
        llmStatus={llmStatus}
        onDetect={handleDetectModels}
        onSave={handleSaveLlm}
        onSaveCorrection={handleSaveCorrection}
        defaultBaseUrl={defaultBaseUrl}
        fillColor={fillColor}
        setFillColor={setFillColor}
        textColor={textColor}
        setTextColor={setTextColor}
        lineColor={lineColor}
        setLineColor={setLineColor}
        lineDash={lineDash}
        setLineDash={setLineDash}
      />
      <ManageModal
        open={manageOpen}
        onClose={() => setManageOpen(false)}
        tab={manageTab}
        setTab={setManageTab}
        languageOptions={languageOptions}
        defaultSourceLang={sourceLang || "vi"}
        defaultTargetLang={targetLang || "zh-TW"}
        glossaryItems={glossaryItems}
        tmItems={tmItems}
        onSeed={handleSeedTm}
        onUpsertGlossary={upsertGlossary}
        onDeleteGlossary={deleteGlossary}
        onUpsertMemory={upsertMemory}
        onDeleteMemory={deleteMemory}
        onConvertToGlossary={convertMemoryToGlossary}
      />
    </div>
  );
}

function LlmModal({
  open,
  onClose,
  tab,
  setTab,
  providerOptions,
  llmProvider,
  setLlmProvider,
  llmApiKey,
  setLlmApiKey,
  llmBaseUrl,
  setLlmBaseUrl,
  llmModel,
  setLlmModel,
  llmModels,
  llmStatus,
  onDetect,
  onSave,
  onSaveCorrection,
  defaultBaseUrl,
  fillColor,
  setFillColor,
  textColor,
  setTextColor,
  lineColor,
  setLineColor,
  lineDash,
  setLineDash
}) {
  const { modalRef, position, onMouseDown } = useDraggableModal(open);
  const [customModel, setCustomModel] = useState("");
  const modelOptions = useMemo(() => {
    const options = [...llmModels];
    if (llmModel && !options.includes(llmModel)) {
      options.unshift(llmModel);
    }
    return options;
  }, [llmModels, llmModel]);

  useEffect(() => {
    if (!open) {
      return;
    }
    setCustomModel(llmModel || "");
  }, [open, llmModel]);
  if (!open) {
    return null;
  }

  return (
    <div className="modal-backdrop">
      <div
        className="modal modal-wide is-draggable"
        ref={modalRef}
        style={{ top: position.top, left: position.left }}
      >
        <div className="modal-header draggable-handle" onMouseDown={onMouseDown}>
          <h3>設定</h3>
          <button
            className="icon-btn ghost"
            type="button"
            onClick={onClose}
            aria-label="關閉"
            title="關閉"
          >
            ×
          </button>
        </div>
        <div className="modal-tabs">
          <button
            className={`tab-btn ${tab === "llm" ? "is-active" : ""}`}
            type="button"
            onClick={() => setTab("llm")}
          >
            LLM
          </button>
          <button
            className={`tab-btn ${tab === "correction" ? "is-active" : ""}`}
            type="button"
            onClick={() => setTab("correction")}
          >
            校正
          </button>
        </div>
        <div className="modal-body">
          {tab === "llm" ? (
            <form
              className="form-stack"
              onSubmit={(event) => event.preventDefault()}
              autoComplete="on"
            >
              <input
                className="visually-hidden"
                type="text"
                name="username"
                autoComplete="username"
                tabIndex={-1}
                aria-hidden="true"
              />
              <div className="form-group">
                <label className="field-label">供應商</label>
                <select
                  className="select-input"
                  value={llmProvider}
                  onChange={(event) => setLlmProvider(event.target.value)}
                >
                  {providerOptions.map((option) => (
                    <option key={option.code} value={option.code}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {llmProvider !== "ollama" && (
                <div className="form-group">
                  <label className="field-label">API Key</label>
                  <input
                    className="select-input"
                    type="text"
                    value={llmApiKey}
                    onChange={(event) => setLlmApiKey(event.target.value)}
                    placeholder="輸入 API Key"
                    autoComplete="off"
                    name="llm-api-key"
                  />
                </div>
              )}

              <div className="form-group">
                <label className="field-label">Base URL</label>
                <input
                  className="select-input"
                  type="text"
                  value={llmBaseUrl}
                  onChange={(event) => setLlmBaseUrl(event.target.value)}
                  placeholder={defaultBaseUrl}
                />
              </div>

              <div className="form-group">
                <label className="field-label">??</label>
                <div className="inline-row">
                  <select
                    className="select-input"
                    value={llmModel}
                    onChange={(event) => setLlmModel(event.target.value)}
                  >
                    {modelOptions.length === 0 ? (
                      <option value="">????</option>
                    ) : (
                      modelOptions.map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))
                    )}
                  </select>
                  <button className="btn ghost" type="button" onClick={onDetect}>
                    ????
                  </button>
                </div>
                <div className="inline-row">
                  <input
                    className="select-input"
                    type="text"
                    value={customModel}
                    onChange={(event) => setCustomModel(event.target.value)}
                    placeholder="????????"
                  />
                  <button
                    className="btn ghost"
                    type="button"
                    onClick={() => {
                      const value = customModel.trim();
                      if (value) {
                        setLlmModel(value);
                      }
                    }}
                  >
                    ??
                  </button>
                </div>
                <p className="field-hint">{llmStatus || "????????????"}</p>
              </div>
            </form>
          ) : (
            <>
              <div className="color-grid">
                <div className="color-item">
                  <span>底色</span>
                  <input
                    className="color-input"
                    type="color"
                    value={fillColor}
                    onChange={(event) => setFillColor(event.target.value)}
                  />
                </div>
                <div className="color-item">
                  <span>文字</span>
                  <input
                    className="color-input"
                    type="color"
                    value={textColor}
                    onChange={(event) => setTextColor(event.target.value)}
                  />
                </div>
                <div className="color-item">
                  <span>外框</span>
                  <input
                    className="color-input"
                    type="color"
                    value={lineColor}
                    onChange={(event) => setLineColor(event.target.value)}
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="field-label" htmlFor="line-dash-modal">
                  外框線型
                </label>
                <select
                  id="line-dash-modal"
                  className="select-input"
                  value={lineDash}
                  onChange={(event) => setLineDash(event.target.value)}
                >
                  <option value="dash">虛線</option>
                  <option value="dot">點線</option>
                  <option value="dashdot">點虛線</option>
                  <option value="solid">實線</option>
                </select>
              </div>
            </>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn ghost" type="button" onClick={onClose}>
            取消
          </button>
          <button
            className="btn primary"
            type="button"
            onClick={tab === "llm" ? onSave : onSaveCorrection}
          >
            保存
          </button>
        </div>
      </div>
    </div>
  );
}

function ManageModal({
  open,
  onClose,
  tab,
  setTab,
  languageOptions,
  defaultSourceLang,
  defaultTargetLang,
  glossaryItems,
  tmItems,
  onSeed,
  onUpsertGlossary,
  onDeleteGlossary,
  onUpsertMemory,
  onDeleteMemory,
  onConvertToGlossary
}) {
  const [editingKey, setEditingKey] = useState(null);
  const [editingOriginal, setEditingOriginal] = useState(null);
  const [draft, setDraft] = useState(null);
  const [saving, setSaving] = useState(false);
  const [newEntry, setNewEntry] = useState({
    source_lang: "",
    target_lang: "",
    source_text: "",
    target_text: "",
    priority: 0
  });

  useEffect(() => {
    if (!open) {
      return;
    }
    setEditingKey(null);
    setEditingOriginal(null);
    setDraft(null);
    setSaving(false);
    setNewEntry((prev) => ({
      ...prev,
      source_lang: defaultSourceLang || "vi",
      target_lang: defaultTargetLang || "zh-TW"
    }));
  }, [open, tab, defaultSourceLang, defaultTargetLang]);

  const isGlossary = tab === "glossary";
  const items = isGlossary ? glossaryItems : tmItems;
  const makeKey = (item) =>
    `${item.source_lang || ""}|${item.target_lang || ""}|${item.source_text || ""}`;

  const { modalRef, position, onMouseDown } = useDraggableModal(open);
  const [customModel, setCustomModel] = useState("");
  const modelOptions = useMemo(() => {
    const options = [...llmModels];
    if (llmModel && !options.includes(llmModel)) {
      options.unshift(llmModel);
    }
    return options;
  }, [llmModels, llmModel]);

  useEffect(() => {
    if (!open) {
      return;
    }
    setCustomModel(llmModel || "");
  }, [open, llmModel]);
  if (!open) {
    return null;
  }

  const handleExport = (path) => {
    window.open(path, "_blank");
  };

  const handleImport = (event, path, reload) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const formData = new FormData();
    formData.append("file", file);
    fetch(path, { method: "POST", body: formData }).then(() => reload());
    event.target.value = "";
  };

  const handleEdit = (item) => {
    setEditingKey(makeKey(item));
    setEditingOriginal(item);
    setDraft({
      ...item,
      priority: item.priority ?? 0
    });
  };

  const handleCancel = () => {
    setEditingKey(null);
    setEditingOriginal(null);
    setDraft(null);
  };

  const handleDelete = async (item) => {
    const ok = window.confirm("確定要刪除這筆資料嗎？");
    if (!ok) {
      return;
    }
    if (!item.id) {
      return;
    }
    const payload = { id: item.id };
    if (isGlossary) {
      await onDeleteGlossary(payload);
    } else {
      await onDeleteMemory(payload);
    }
    if (editingKey === makeKey(item)) {
      handleCancel();
    }
  };

  const handleSave = async () => {
    if (!draft) {
      return;
    }
    setSaving(true);
    const payload = isGlossary
      ? {
          ...draft,
          priority: Number.isNaN(Number(draft.priority)) ? 0 : Number(draft.priority)
        }
      : { ...draft };
    const originalKey = editingOriginal ? makeKey(editingOriginal) : editingKey;
    const nextKey = makeKey(payload);
    if (editingOriginal && originalKey !== nextKey && editingOriginal.id) {
      const deletePayload = { id: editingOriginal.id };
      if (isGlossary) {
        await onDeleteGlossary(deletePayload);
      } else {
        await onDeleteMemory(deletePayload);
      }
    }
    if (isGlossary) {
      await onUpsertGlossary(payload);
    } else {
      await onUpsertMemory(payload);
    }
    setSaving(false);
    handleCancel();
  };

  const handleCreate = async () => {
    if (!newEntry.source_text || !newEntry.target_text) {
      return;
    }
    if (isGlossary) {
      await onUpsertGlossary({
        ...newEntry,
        priority: Number.isNaN(Number(newEntry.priority)) ? 0 : Number(newEntry.priority)
      });
    } else {
      await onUpsertMemory({
        source_lang: newEntry.source_lang,
        target_lang: newEntry.target_lang,
        source_text: newEntry.source_text,
        target_text: newEntry.target_text
      });
    }
    setNewEntry((prev) => ({
      ...prev,
      source_text: "",
      target_text: "",
      priority: 0
    }));
  };

  return (
    <div className="modal-backdrop">
      <div
        className="modal is-draggable"
        ref={modalRef}
        style={{ top: position.top, left: position.left }}
      >
        <div className="modal-header draggable-handle" onMouseDown={onMouseDown}>
          <h3>術語與翻譯記憶</h3>
          <button className="icon-btn ghost" type="button" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="modal-tabs">
          <button
            className={`tab-btn ${tab === "glossary" ? "is-active" : ""}`}
            type="button"
            onClick={() => setTab("glossary")}
          >
            術語
          </button>
          <button
            className={`tab-btn ${tab === "tm" ? "is-active" : ""}`}
            type="button"
            onClick={() => setTab("tm")}
          >
            翻譯記憶
          </button>
        </div>
        <div className="modal-body">
          <div className="action-row">
            <button className="btn ghost" type="button" onClick={onSeed}>
              匯入示範資料
            </button>
            {tab === "glossary" ? (
              <>
                <button
                  className="btn ghost"
                  type="button"
                  onClick={() => handleExport(`${API_BASE}/api/tm/glossary/export`)}
                >
                  匯出 CSV
                </button>
                <label className="btn ghost">
                  匯入 CSV
                  <input
                    type="file"
                    accept=".csv"
                    className="hidden-input"
                    onChange={(event) =>
                      handleImport(event, `${API_BASE}/api/tm/glossary/import`, onSeed)
                    }
                  />
                </label>
              </>
            ) : (
              <>
                <button
                  className="btn ghost"
                  type="button"
                  onClick={() => handleExport(`${API_BASE}/api/tm/memory/export`)}
                >
                  匯出 CSV
                </button>
                <label className="btn ghost">
                  匯入 CSV
                  <input
                    type="file"
                    accept=".csv"
                    className="hidden-input"
                    onChange={(event) =>
                      handleImport(event, `${API_BASE}/api/tm/memory/import`, onSeed)
                    }
                  />
                </label>
              </>
            )}
          </div>
          <div className="create-row">
            <div className="create-fields">
              <select
                className="select-input"
                value={newEntry.source_lang}
                onChange={(event) =>
                  setNewEntry((prev) => ({ ...prev, source_lang: event.target.value }))
                }
              >
                {languageOptions
                  .filter((option) => option.code !== "auto")
                  .map((option) => (
                    <option key={`src-${option.code}`} value={option.code}>
                      {option.label}
                    </option>
                  ))}
              </select>
              <select
                className="select-input"
                value={newEntry.target_lang}
                onChange={(event) =>
                  setNewEntry((prev) => ({ ...prev, target_lang: event.target.value }))
                }
              >
                {languageOptions
                  .filter((option) => option.code !== "auto")
                  .map((option) => (
                    <option key={`tgt-${option.code}`} value={option.code}>
                      {option.label}
                    </option>
                  ))}
              </select>
              <input
                className="select-input"
                value={newEntry.source_text}
                placeholder="來源文字"
                onChange={(event) =>
                  setNewEntry((prev) => ({ ...prev, source_text: event.target.value }))
                }
              />
              <input
                className="select-input"
                value={newEntry.target_text}
                placeholder="目標文字"
                onChange={(event) =>
                  setNewEntry((prev) => ({ ...prev, target_text: event.target.value }))
                }
              />
              {isGlossary ? (
                <input
                  className="select-input"
                  type="number"
                  value={newEntry.priority}
                  placeholder="權重"
                  onChange={(event) =>
                    setNewEntry((prev) => ({ ...prev, priority: event.target.value }))
                  }
                />
              ) : null}
            </div>
            <button className="btn primary" type="button" onClick={handleCreate}>
              手動新增
            </button>
          </div>
          <div className={`data-table ${isGlossary ? "is-glossary" : "is-tm"}`}>
            <div className="data-row data-header">
              <div className="data-cell">來源語言</div>
              <div className="data-cell">目標語言</div>
              <div className="data-cell">來源</div>
              <div className="data-cell">對應</div>
              {isGlossary ? <div className="data-cell">權重</div> : null}
              <div className="data-cell data-actions">操作</div>
            </div>
            {items.length === 0 ? (
              <div className="data-empty">尚無資料</div>
            ) : (
              items.map((item, idx) => {
                const rowKey = makeKey(item);
                const isEditing = editingKey === rowKey;
                const row = isEditing ? draft || item : item;
                return (
                  <div className="data-row" key={`tm-${idx}`}>
                    <div className="data-cell">
                      {isEditing ? (
                        <input
                          className="data-input"
                          value={row.source_lang || ""}
                          onChange={(event) =>
                            setDraft((prev) => ({ ...prev, source_lang: event.target.value }))
                          }
                        />
                      ) : (
                        row.source_lang
                      )}
                    </div>
                    <div className="data-cell">
                      {isEditing ? (
                        <input
                          className="data-input"
                          value={row.target_lang || ""}
                          onChange={(event) =>
                            setDraft((prev) => ({ ...prev, target_lang: event.target.value }))
                          }
                        />
                      ) : (
                        row.target_lang
                      )}
                    </div>
                    <div className="data-cell">
                      {isEditing ? (
                        <input
                          className="data-input"
                          value={row.source_text || ""}
                          onChange={(event) =>
                            setDraft((prev) => ({ ...prev, source_text: event.target.value }))
                          }
                        />
                      ) : (
                        row.source_text
                      )}
                    </div>
                    <div className="data-cell">
                      {isEditing ? (
                        <input
                          className="data-input"
                          value={row.target_text || ""}
                          onChange={(event) =>
                            setDraft((prev) => ({ ...prev, target_text: event.target.value }))
                          }
                        />
                      ) : (
                        row.target_text
                      )}
                    </div>
                    {isGlossary ? (
                      <div className="data-cell">
                        {isEditing ? (
                          <input
                            className="data-input"
                            type="number"
                            value={row.priority ?? 0}
                            onChange={(event) =>
                              setDraft((prev) => ({ ...prev, priority: event.target.value }))
                            }
                          />
                        ) : (
                          row.priority ?? 0
                        )}
                      </div>
                    ) : null}
                    <div className="data-cell data-actions">
                      {isEditing ? (
                        <>
                          <button
                            className="action-btn primary"
                            type="button"
                            onClick={handleSave}
                            disabled={saving}
                          >
                            保存
                          </button>
                          <button
                            className="action-btn ghost"
                            type="button"
                            onClick={handleCancel}
                            disabled={saving}
                          >
                            取消
                          </button>
                        </>
                      ) : (
                        <>
                          <button className="action-btn" type="button" onClick={() => handleEdit(item)}>
                            編輯
                          </button>
                          {!isGlossary ? (
                            <button
                              className="action-btn"
                              type="button"
                              onClick={() => onConvertToGlossary(item)}
                            >
                              轉為術語
                            </button>
                          ) : null}
                          <button
                            className="action-btn danger"
                            type="button"
                            onClick={() => handleDelete(item)}
                          >
                            刪除
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
