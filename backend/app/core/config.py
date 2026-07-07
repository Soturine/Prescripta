import os
from dataclasses import dataclass, field


def _split_origins(raw_value: str) -> list[str]:
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Prescripta"
    api_prefix: str = "/api"
    environment: str = os.getenv("PRESCRIPTA_ENV", "development")
    database_url: str = os.getenv("PRESCRIPTA_DATABASE_URL", "sqlite:///./prescripta.db")
    secret_key: str = os.getenv(
        "PRESCRIPTA_SECRET_KEY",
        "prescripta-local-demo-secret-change-before-production",
    )
    access_token_expire_minutes: int = int(
        os.getenv("PRESCRIPTA_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    jwt_algorithm: str = "HS256"
    config_encryption_key: str = os.getenv("PRESCRIPTA_CONFIG_ENCRYPTION_KEY", "")
    ai_provider: str = os.getenv("PRESCRIPTA_AI_PROVIDER", "fallback")
    ai_api_key: str = os.getenv("PRESCRIPTA_AI_API_KEY", "")
    ai_model: str = os.getenv("PRESCRIPTA_AI_MODEL", "")
    ai_base_url: str = os.getenv("PRESCRIPTA_AI_BASE_URL", "")
    ai_timeout_seconds: int = int(os.getenv("PRESCRIPTA_AI_TIMEOUT_SECONDS", "30"))
    ai_enable_external_calls: bool = (
        os.getenv("PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS", "false").lower() == "true"
    )
    ai_temperature: float = float(os.getenv("PRESCRIPTA_AI_TEMPERATURE", "0.2"))
    ai_max_output_tokens: int = int(os.getenv("PRESCRIPTA_AI_MAX_OUTPUT_TOKENS", "900"))
    ai_use_json_mode: bool = os.getenv("PRESCRIPTA_AI_USE_JSON_MODE", "true").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_api_key: str = os.getenv("OLLAMA_API_KEY", "")
    cors_origins: list[str] = field(
        default_factory=lambda: _split_origins(
            os.getenv(
                "PRESCRIPTA_CORS_ORIGINS",
                (
                    "http://localhost:5173,http://127.0.0.1:5173,"
                    "http://localhost:5174,http://127.0.0.1:5174,"
                    "http://localhost:5175,http://127.0.0.1:5175"
                ),
            )
        )
    )
    auto_seed: bool = os.getenv("PRESCRIPTA_AUTO_SEED", "true").lower() == "true"


settings = Settings()
