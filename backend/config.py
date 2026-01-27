from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = "ollama"
    translate_llm_mode: str = "real"

    # Server Configuration
    port: int = 5002
    host: str = "0.0.0.0"

    # Ollama Configuration
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_timeout: int = 180
    ollama_num_gpu: int | None = None
    ollama_num_gpu_layers: int | None = None
    ollama_num_ctx: int | None = None
    ollama_num_thread: int | None = None
    ollama_force_gpu: bool = False

    # Gemini Configuration
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_timeout: int = 180

    # OpenAI Configuration
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout: int = 60

    # Translation Settings
    source_language: str = "auto"
    llm_context_strategy: str = "none"
    llm_glossary_path: str | None = None
    llm_fallback_on_error: bool = False

    # Performance / Rate Limiting
    llm_single_request: bool = True
    llm_chunk_size: int = 40
    llm_max_retries: int = 2
    llm_retry_backoff: float = 0.8
    llm_retry_max_backoff: float = 8.0
    llm_chunk_delay: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
