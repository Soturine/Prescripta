import os
from dataclasses import dataclass, field


def _split_origins(raw_value: str) -> list[str]:
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Prescripta"
    api_prefix: str = "/api"
    database_url: str = os.getenv("PRESCRIPTA_DATABASE_URL", "sqlite:///./prescripta.db")
    cors_origins: list[str] = field(
        default_factory=lambda: _split_origins(
            os.getenv(
                "PRESCRIPTA_CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            )
        )
    )
    auto_seed: bool = os.getenv("PRESCRIPTA_AUTO_SEED", "true").lower() == "true"


settings = Settings()
