from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'soapflow.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "SOAPFlow"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = DEFAULT_DATABASE_URL

    # API Keys (optional — falls back to demo mode)
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Model selection
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-opus-4-6"
    ollama_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout_s: float = 600.0

    # Groq (free-tier hosted Llama / Mixtral)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_timeout_s: float = 120.0

    # MLX (local Apple-Silicon LoRA fine-tuned models)
    mlx_model: str = "mlx-community/Qwen2.5-3B-Instruct-4bit"
    mlx_adapter_path: str = ""
    mlx_max_tokens: int = 2048
    mlx_max_transcript_chars: int = 6000

    # Generation mode: "openai" | "anthropic" | "ollama" | "groq" | "mlx" | "demo"
    generation_mode: Literal["openai", "anthropic", "ollama", "groq", "mlx", "demo"] = "demo"

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # Limits
    max_transcript_length: int = 20_000
    min_transcript_length: int = 50

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug_flag(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return value


settings = Settings()
