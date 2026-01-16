import { useEffect, useMemo, useState } from "react";

const PROMPT_LABELS = {
  translate_json: "翻譯 JSON 提示",
  system_message: "System 提示",
  ollama_batch: "Ollama 批次提示"
};

const PROVIDERS = [
  { id: "chatgpt", name: "ChatGPT (OpenAI)", sub: "標準 API", icon: "🤖" },
  { id: "gemini", name: "Gemini", sub: "Google AI Studio", icon: "✨" },
  { id: "ollama", name: "Ollama", sub: "本機模型", icon: "💻" }
];

function SettingsModal({
  open,
  onClose,
  tab,
  setTab,
  llmProvider,
  setLlmProvider,
  llmApiKey,
  setLlmApiKey,
  llmBaseUrl,
  setLlmBaseUrl,
  llmModel,
  setLlmModel,
  llmFastMode,
  setLlmFastMode,
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
  setLineDash,
  apiBase
}) {
  const [showKey, setShowKey] = useState(false);
  const [promptList, setPromptList] = useState([]);
  const [selectedPrompt, setSelectedPrompt] = useState("");
  const [promptContent, setPromptContent] = useState("");
  const [promptStatus, setPromptStatus] = useState("");
  const [promptLoading, setPromptLoading] = useState(false);

  const currentProvider = useMemo(
    () => PROVIDERS.find((item) => item.id === llmProvider) || PROVIDERS[0],
    [llmProvider]
  );

  const displayedModels = useMemo(() => {
    const models = [...(llmModels || [])];
    if (llmModel && !models.includes(llmModel)) {
      models.unshift(llmModel);
    }
    return models;
  }, [llmModels, llmModel]);

  useEffect(() => {
    if (!open || tab !== "prompt") {
      return;
    }
    let active = true;
    const loadList = async () => {
      try {
        const response = await fetch(`${apiBase}/api/prompts`);
        const data = await response.json();
        if (!active) {
          return;
        }
        setPromptList(data || []);
        if (data && data.length) {
          setSelectedPrompt((prev) => prev || data[0]);
        }
      } catch (error) {
        if (active) {
          setPromptList([]);
        }
      }
    };
    loadList();
    return () => {
      active = false;
    };
  }, [open, tab, apiBase]);

  useEffect(() => {
    if (!open || tab !== "prompt" || !selectedPrompt) {
      return;
    }
    let active = true;
    const loadPrompt = async () => {
      setPromptLoading(true);
      try {
        const response = await fetch(`${apiBase}/api/prompts/${selectedPrompt}`);
        const data = await response.json();
        if (active) {
          setPromptContent(data.content || "");
        }
      } catch (error) {
        if (active) {
          setPromptContent("");
        }
      } finally {
        if (active) {
          setPromptLoading(false);
        }
      }
    };
    loadPrompt();
    return () => {
      active = false;
    };
  }, [open, tab, selectedPrompt, apiBase]);

  if (!open) {
    return null;
  }

  const handleSavePrompt = async () => {
    if (!selectedPrompt) {
      return;
    }
    setPromptStatus("儲存中...");
    try {
      await fetch(`${apiBase}/api/prompts/${selectedPrompt}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: promptContent })
      });
      setPromptStatus("已儲存");
      setTimeout(() => setPromptStatus(""), 2000);
      onClose();
    } catch (error) {
      setPromptStatus("儲存失敗");
    }
  };

  const handleResetPrompt = async () => {
    if (!selectedPrompt) {
      return;
    }
    setPromptLoading(true);
    try {
      const response = await fetch(`${apiBase}/api/prompts/${selectedPrompt}`);
      const data = await response.json();
      setPromptContent(data.content || "");
    } finally {
      setPromptLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-wide" onClick={(event) => event.stopPropagation()}>
        <div className="settings-shell">
          <aside className="settings-sidebar">
            <h4 className="sidebar-title">設定</h4>
            <div className="sidebar-tabs">
              <button
                className={`sidebar-tab ${tab === "llm" ? "active" : ""}`}
                type="button"
                onClick={() => setTab("llm")}
              >
                LLM
              </button>
              <button
                className={`sidebar-tab ${tab === "correction" ? "active" : ""}`}
                type="button"
                onClick={() => setTab("correction")}
              >
                校正
              </button>
              <button
                className={`sidebar-tab ${tab === "prompt" ? "active" : ""}`}
                type="button"
                onClick={() => setTab("prompt")}
              >
                Prompt
              </button>
            </div>
            {tab === "llm" ? (
              <div className="sidebar-list">
                {PROVIDERS.map((item) => (
                  <button
                    key={item.id}
                    className={`sidebar-item ${llmProvider === item.id ? "active" : ""}`}
                    type="button"
                    onClick={() => setLlmProvider(item.id)}
                  >
                    <span className="sidebar-icon" aria-hidden="true">
                      {item.icon}
                    </span>
                    <div className="sidebar-text">
                      <div className="sidebar-name">{item.name}</div>
                      <div className="sidebar-sub">{item.sub}</div>
                    </div>
                  </button>
                ))}
              </div>
            ) : null}
            {tab === "prompt" ? (
              <div className="sidebar-list">
                {promptList.length === 0 ? (
                  <div className="sidebar-empty">尚無 Prompt</div>
                ) : (
                  promptList.map((name) => (
                    <button
                      key={name}
                      className={`sidebar-item ${selectedPrompt === name ? "active" : ""}`}
                      type="button"
                      onClick={() => setSelectedPrompt(name)}
                    >
                      <span className="sidebar-icon" aria-hidden="true">
                        🧩
                      </span>
                      <div className="sidebar-text">
                        <div className="sidebar-name">{PROMPT_LABELS[name] || name}</div>
                        <div className="sidebar-sub">{name}</div>
                      </div>
                    </button>
                  ))
                )}
              </div>
            ) : null}
          </aside>

          <div className="settings-main">
            <div className="modal-header fancy">
              <div className="header-title">
                {tab === "llm" && (
                  <h3>
                    {currentProvider.name} 設定
                  </h3>
                )}
                {tab === "correction" && <h3>校正設定</h3>}
                {tab === "prompt" && <h3>Prompt 設定</h3>}
              </div>
              <div className="header-actions">
                {tab === "prompt" ? (
                  <>
                    <span className="text-xs text-green-600">{promptStatus}</span>
                    <button className="ghost-btn" type="button" onClick={handleResetPrompt}>
                      ↺
                    </button>
                    <button className="btn-icon-action" type="button" onClick={onClose}>
                      ✕
                    </button>
                    <button
                      className="btn-icon-action text-primary border-primary"
                      type="button"
                      onClick={handleSavePrompt}
                    >
                      ✔
                    </button>
                  </>
                ) : (
                  <>
                    <button className="btn-icon-action" type="button" onClick={onClose}>
                      ✕
                    </button>
                    <button
                      className="btn-icon-action text-primary border-primary"
                      type="button"
                      onClick={tab === "llm" ? onSave : onSaveCorrection}
                    >
                      ✔
                    </button>
                  </>
                )}
              </div>
            </div>

              <div className="settings-content">
                {tab === "llm" ? (
                <form onSubmit={(event) => event.preventDefault()}>
                  {llmProvider !== "ollama" ? (
                    <div className="config-field compact">
                      <label>API Key</label>
                      <div className="inline-row">
                        <input
                          name="llmApiKey"
                          type={showKey ? "text" : "password"}
                          value={llmApiKey}
                          onChange={(event) => setLlmApiKey(event.target.value)}
                          autoComplete="new-password"
                          placeholder="輸入 API Key"
                        />
                        <button
                          className="btn-icon-action"
                          type="button"
                          onClick={() => setShowKey((prev) => !prev)}
                        >
                          {showKey ? "🙈" : "👁️"}
                        </button>
                      </div>
                      <p className="hint">請輸入對應供應商的 API Key。</p>
                    </div>
                  ) : (
                    <div className="config-field compact">
                      <label>Base URL</label>
                      <input
                        type="text"
                        value={llmBaseUrl}
                        onChange={(event) => setLlmBaseUrl(event.target.value)}
                        placeholder={defaultBaseUrl}
                      />
                      <p className="hint">本機端預設為 {defaultBaseUrl}</p>
                    </div>
                  )}

                  {llmProvider === "ollama" ? (
                    <div className="config-field compact">
                      <label>Ollama 快速模式</label>
                      <label className="toggle-row">
                        <input
                          type="checkbox"
                          checked={llmFastMode}
                          onChange={(event) => setLlmFastMode(event.target.checked)}
                        />
                        <span>小批次、關閉單次請求</span>
                      </label>
                    </div>
                  ) : null}

                  <div className="config-field compact">
                    <div className="inline-row between">
                      <label>模型</label>
                      <button className="text-btn" type="button" onClick={onDetect}>
                        重新整理
                      </button>
                    </div>
                    <select
                      className="model-select"
                      value={llmModel}
                      onChange={(event) => setLlmModel(event.target.value)}
                    >
                      {displayedModels.length === 0 ? (
                        <option value="">請選擇模型</option>
                      ) : (
                        displayedModels.map((model) => (
                          <option key={model} value={model}>
                            {model}
                          </option>
                        ))
                      )}
                    </select>
                    <div className="inline-row">
                      <input
                        type="text"
                        value={llmModel}
                        onChange={(event) => setLlmModel(event.target.value)}
                        placeholder="輸入自訂模型"
                      />
                      <button className="btn ghost" type="button" onClick={() => setLlmModel(llmModel)}>
                        加入
                      </button>
                    </div>
                    <p className="hint">{llmStatus || "請先偵測模型"}</p>
                  </div>
                </form>
              ) : null}

              {tab === "correction" ? (
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
                  <div className="config-field compact">
                    <label>外框線條</label>
                    <select
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
              ) : null}

              {tab === "prompt" ? (
                <div className="prompt-editor-container">
                  <div className="prompt-selector-row">
                    <label className="prompt-selector-label">選擇 Prompt</label>
                    <select
                      className="prompt-template-select"
                      value={selectedPrompt}
                      onChange={(event) => setSelectedPrompt(event.target.value)}
                    >
                      {promptList.map((name) => (
                        <option key={name} value={name}>
                          {PROMPT_LABELS[name] || name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <textarea
                    className="prompt-textarea"
                    value={promptContent}
                    onChange={(event) => setPromptContent(event.target.value)}
                    placeholder={promptLoading ? "載入中..." : "請輸入 Prompt 內容"}
                    rows={16}
                    spellCheck="false"
                    disabled={promptLoading}
                  />
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
