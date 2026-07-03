import os
from dataclasses import dataclass, field


def _split_origins(raw_value: str) -> list[str]:
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Prescripta"
    api_prefix: str = "/api"
    database_url: str = os.getenv("PRESCRIPTA_DATABASE_URL", "sqlite:///./prescripta.db")
    secret_key: str = os.getenv(
        "PRESCRIPTA_SECRET_KEY",
        "prescripta-local-demo-secret-change-before-production",
    )
    access_token_expire_minutes: int = int(
        os.getenv("PRESCRIPTA_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    jwt_algorithm: str = "HS256"
    ai_provider: str = os.getenv("PRESCRIPTA_AI_PROVIDER", "fallback")
    ai_api_key: str = os.getenv("PRESCRIPTA_AI_API_KEY", "")
    ai_model: str = os.getenv("PRESCRIPTA_AI_MODEL", "gpt-5.5")
    ai_base_url: str = os.getenv("PRESCRIPTA_AI_BASE_URL", "")
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
