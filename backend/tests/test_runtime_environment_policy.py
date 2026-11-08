"""PRE-12 (config): uma única definição de ambiente local e segredo JWT mínimo fora dele.

Antes, quatro pontos decidiam "ambiente local" com regras diferentes (com/sem strip, com/sem
"testing", ou só {"prod","production"}) e produção aceitava qualquer segredo diferente do demo.
"""

from __future__ import annotations

import pytest

from app.core.config import (
    Settings,
    UnsafeRuntimeConfiguration,
    is_local_environment,
    validate_runtime_settings,
)
from app.services.ai_settings import AISecretService

SAFE = {
    "database_url": "postgresql+psycopg://prescripta@db/prescripta",
    "auto_seed": False,
    "cors_origins": ["https://prescripta.example"],
    "config_encryption_key": "configured-by-secret-manager",
}


@pytest.mark.parametrize(
    ("environment", "local"),
    [
        ("development", True),
        (" Local ", True),
        ("TESTING", True),
        ("test", True),
        ("staging", False),
        ("prod", False),
        ("production ", False),
        ("", False),
    ],
)
def test_single_local_environment_definition(environment: str, local: bool) -> None:
    assert is_local_environment(environment) is local
    # Credenciais de IA só em memória quando local; fora disso exige chave de persistência.
    secrets = AISecretService(Settings(environment=environment))
    assert secrets.requires_persistence_key is (not local)


@pytest.mark.parametrize("weak", ["changeme", "x" * 31, "segredo-curto-de-producao"])
def test_non_local_rejects_short_jwt_secret(weak: str) -> None:
    with pytest.raises(UnsafeRuntimeConfiguration, match="32 bytes"):
        validate_runtime_settings(Settings(environment="staging", secret_key=weak, **SAFE))


def test_non_local_accepts_strong_secret() -> None:
    validate_runtime_settings(
        Settings(environment="staging", secret_key="s" * 32, **SAFE)
    )


def test_non_local_rejects_published_placeholder_secret() -> None:
    with pytest.raises(UnsafeRuntimeConfiguration, match="demonstrativo"):
        validate_runtime_settings(
            Settings(
                environment="production",
                secret_key="change-this-demo-secret-before-production",
                **SAFE,
            )
        )
