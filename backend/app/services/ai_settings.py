from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.database.models import (
    AIConfigurationAuditLogModel,
    AIProviderCredentialModel,
    AIProviderModelCacheModel,
    AIProviderSettingsModel,
    AuditEventModel,
    UserModel,
)
from app.schemas.ai_settings_schema import (
    AIConnectionTestRequest,
    AIConnectionTestResponse,
    AICredentialSaveRequest,
    AICredentialStatus,
    AIModelListResponse,
    AIModelSelectRequest,
    AIProviderInfo,
    AIProviderModelRead,
    AISettingsRead,
)

MODEL_CACHE_TTL = timedelta(hours=24)

PROVIDER_CATALOG = {
    "fallback": AIProviderInfo(
        provider="fallback",
        label="Fallback local",
        requires_api_key=False,
        supports_model_refresh=False,
        docs_url=None,
    ),
    "openai": AIProviderInfo(
        provider="openai",
        label="OpenAI",
        requires_api_key=True,
        api_key_url="https://platform.openai.com/api-keys",
        docs_url="https://platform.openai.com/docs/models",
    ),
    "gemini": AIProviderInfo(
        provider="gemini",
        label="Gemini",
        requires_api_key=True,
        api_key_url="https://aistudio.google.com/app/apikey",
        docs_url="https://ai.google.dev/gemini-api/docs/models",
    ),
    "ollama": AIProviderInfo(
        provider="ollama",
        label="Ollama",
        requires_api_key=False,
        requires_base_url=True,
        api_key_url=None,
        docs_url="https://ollama.com",
    ),
    "openai_compatible": AIProviderInfo(
        provider="openai_compatible",
        label="OpenAI-compatible",
        requires_api_key=True,
        requires_base_url=True,
        api_key_url=None,
        docs_url="https://platform.openai.com/docs/models",
    ),
}

_MEMORY_CREDENTIALS: dict[str, dict[str, str | None]] = {}


class AIConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class ActiveAIConfig:
    provider: str
    model: str | None
    api_key: str | None
    base_url: str | None
    enable_external_calls: bool
    timeout_seconds: int
    temperature: float
    max_output_tokens: int
    use_json_mode: bool


class AISecretService:
    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings

    @property
    def can_persist(self) -> bool:
        return bool(self.settings.config_encryption_key.strip())

    @property
    def requires_persistence_key(self) -> bool:
        return self.settings.environment.lower() in {"prod", "production"}

    def encrypt(self, value: str) -> str:
        return self._fernet().encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, encrypted_value: str) -> str:
        try:
            return self._fernet().decrypt(encrypted_value.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise AIConfigurationError("Credencial de IA não pôde ser descriptografada.") from exc

    def mask(self, value: str | None) -> str | None:
        if not value:
            return None
        if len(value) <= 8:
            return "..." + value[-2:]
        return f"{value[:4]}...{value[-4:]}"

    def _fernet(self) -> Fernet:
        if not self.can_persist:
            raise AIConfigurationError(
                "PRESCRIPTA_CONFIG_ENCRYPTION_KEY ausente; use armazenamento em memória."
            )
        digest = hashlib.sha256(self.settings.config_encryption_key.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)


class AISettingsService:
    def __init__(self, db: Session, app_settings: Settings = settings) -> None:
        self.db = db
        self.settings = app_settings
        self.secrets = AISecretService(app_settings)

    def providers(self) -> list[AIProviderInfo]:
        return list(PROVIDER_CATALOG.values())

    def current(self) -> AISettingsRead:
        config = self.runtime_config()
        credential = self.credential_status(config.provider)
        row = self._settings_row()
        external_status = "fallback"
        if config.provider != "fallback" and config.enable_external_calls:
            external_status = "enabled" if self._provider_ready(config) else "needs_configuration"
        return AISettingsRead(
            provider=config.provider,
            selected_model=config.model,
            enable_external_calls=config.enable_external_calls,
            timeout_seconds=config.timeout_seconds,
            temperature=config.temperature,
            max_output_tokens=config.max_output_tokens,
            use_json_mode=config.use_json_mode,
            credential=credential,
            external_status=external_status,
            updated_at=row.updated_at if row else None,
        )

    def credential_status(self, provider: str) -> AICredentialStatus:
        provider = self._normalize_provider(provider)
        memory = _MEMORY_CREDENTIALS.get(provider)
        row = self._credential(provider)
        masked = row.masked_api_key if row else None
        base_url = row.base_url if row else None
        persistent = bool(row and row.is_persistent)
        if memory:
            masked = str(memory.get("masked_api_key") or masked or "")
            base_url = str(memory.get("base_url") or base_url or "") or None
            persistent = False
        has_credential = bool(masked or self._env_api_key(provider))
        if not masked and self._env_api_key(provider):
            masked = self.secrets.mask(self._env_api_key(provider))
        if not base_url:
            base_url = self._env_base_url(provider)
        return AICredentialStatus(
            provider=provider,
            has_credential=has_credential,
            masked_api_key=masked,
            base_url=base_url,
            is_active=bool(row.is_active) if row else True,
            is_persistent=persistent,
            last_verified_at=row.last_verified_at if row else None,
            last_error=row.last_error if row else None,
        )

    def save_credential(
        self,
        payload: AICredentialSaveRequest,
        user: UserModel,
    ) -> AICredentialStatus:
        provider = self._normalize_provider(payload.provider)
        api_key = (payload.api_key or "").strip() or None
        base_url = (payload.base_url or "").strip() or None
        if provider in {"openai", "gemini", "openai_compatible"} and not api_key:
            raise AIConfigurationError("Informe uma API Key para este provider.")

        if payload.persist and not self.secrets.can_persist:
            if self.secrets.requires_persistence_key:
                raise AIConfigurationError(
                    "PRESCRIPTA_CONFIG_ENCRYPTION_KEY é obrigatória em produção."
                )
            _MEMORY_CREDENTIALS[provider] = {
                "api_key": api_key,
                "masked_api_key": self.secrets.mask(api_key),
                "base_url": base_url,
            }
            self._audit(user, "credential_saved", provider, None, "not_persistent", None)
            self.db.commit()
            return self.credential_status(provider)

        row = self._credential(provider)
        if row is None:
            row = AIProviderCredentialModel(
                provider=provider,
                created_by=user.id,
                updated_by=user.id,
            )
            self.db.add(row)
        if api_key:
            row.encrypted_api_key = self.secrets.encrypt(api_key)
            row.masked_api_key = self.secrets.mask(api_key)
        row.base_url = base_url
        row.updated_by = user.id
        row.is_active = True
        row.is_persistent = bool(api_key and payload.persist)
        row.last_error = None
        _MEMORY_CREDENTIALS.pop(provider, None)
        self._audit(user, "credential_saved", provider, None, "success", None)
        self.db.commit()
        return self.credential_status(provider)

    def delete_credential(self, provider: str, user: UserModel) -> AICredentialStatus:
        provider = self._normalize_provider(provider)
        row = self._credential(provider)
        if row:
            row.encrypted_api_key = None
            row.masked_api_key = None
            row.is_active = False
            row.updated_by = user.id
        _MEMORY_CREDENTIALS.pop(provider, None)
        self._audit(user, "credential_deleted", provider, None, "success", None)
        self.db.commit()
        return self.credential_status(provider)

    def select_model(
        self,
        payload: AIModelSelectRequest,
        user: UserModel,
    ) -> AISettingsRead:
        provider = self._normalize_provider(payload.provider)
        model = (payload.custom_model or payload.selected_model or "").strip() or None
        if provider != "fallback" and payload.custom_model:
            cached = self._model_cache(provider, payload.custom_model)
            if cached is None or not cached.is_verified:
                raise AIConfigurationError(
                    "Modelo customizado precisa ser testado antes de ativar."
                )
        row = self._ensure_settings_row()
        row.provider = provider
        row.selected_model = model
        row.enable_external_calls = payload.enable_external_calls and provider != "fallback"
        row.timeout_seconds = payload.timeout_seconds
        row.temperature = payload.temperature
        row.max_output_tokens = payload.max_output_tokens
        row.use_json_mode = payload.use_json_mode
        row.updated_by = user.id
        if payload.base_url:
            self._upsert_base_url(provider, payload.base_url, user)
        self._audit(
            user,
            "model_selected",
            provider,
            model,
            "success",
            None,
            external_calls_enabled=row.enable_external_calls,
        )
        self.db.commit()
        return self.current()

    def list_models(
        self,
        provider: str,
        *,
        refresh: bool,
        user: UserModel | None,
    ) -> AIModelListResponse:
        provider = self._normalize_provider(provider)
        cached = self._cached_models(provider)
        if provider == "fallback":
            models = [
                self._upsert_model(
                    provider="fallback",
                    model_id="fallback_deterministic",
                    display_name="Fallback determinístico",
                    capabilities=["local", "deterministic"],
                    supports_json=True,
                    supports_structured_output=True,
                    source="manual",
                )
            ]
            self.db.commit()
            return self._model_response(provider, "manual", models)
        if cached and not refresh and self._cache_is_fresh(cached):
            return self._model_response(provider, "cache", cached)
        try:
            config = self.runtime_config(provider_override=provider, enable_external_calls=True)
            models = self._refresh_provider_models(config)
            if user:
                self._audit(user, "model_list_refreshed", provider, None, "success", None)
            self.db.commit()
            return self._model_response(provider, "updated", models)
        except Exception as exc:  # pragma: no cover - provider/network defensive path
            error = self._safe_error(exc)
            if user:
                self._audit(user, "model_list_refreshed", provider, None, "error", error)
            self.db.commit()
            if cached:
                return self._model_response(provider, "error_cache", cached, error=error)
            return AIModelListResponse(provider=provider, status="manual", models=[], error=error)

    def test_connection(
        self,
        payload: AIConnectionTestRequest,
        user: UserModel,
    ) -> AIConnectionTestResponse:
        provider = self._normalize_provider(payload.provider)
        model = (payload.model or "").strip() or None
        if provider == "fallback":
            checked_at = datetime.now(UTC)
            self._mark_verified(provider, model or "fallback_deterministic", checked_at)
            self._audit(user, "connection_tested", provider, model, "success", None)
            self.db.commit()
            return AIConnectionTestResponse(
                provider=provider,
                model=model,
                success=True,
                used_fallback=True,
                status="fallback",
                message="Fallback local disponível.",
                last_verified_at=checked_at,
            )
        config = self.runtime_config(
            provider_override=provider,
            model_override=model,
            base_url_override=payload.base_url,
            enable_external_calls=payload.enable_external_calls,
            use_json_mode_override=payload.use_json_mode,
        )
        if not config.enable_external_calls:
            message = "Chamadas externas de IA estão desabilitadas."
            self._audit(user, "connection_tested", provider, model, "blocked", message)
            self.db.commit()
            return AIConnectionTestResponse(
                provider=provider,
                model=model,
                success=False,
                used_fallback=True,
                status="external_calls_disabled",
                message=message,
                error_summary=message,
            )
        try:
            result = self.complete_json(
                system_instructions=(
                    "Responda apenas JSON válido com a chave ok=true. "
                    "Não use dados clínicos reais."
                ),
                payload={"test": "prescripta_ai_settings"},
                purpose="connection_test",
                config=config,
            )
            if result.get("ok") is not True:
                raise AIConfigurationError("Provider respondeu, mas sem JSON esperado.")
            checked_at = datetime.now(UTC)
            self._mark_verified(provider, config.model or model or "custom", checked_at)
            self._mark_credential_verified(provider, checked_at, None)
            self._audit(user, "connection_tested", provider, config.model, "success", None)
            self.db.commit()
            return AIConnectionTestResponse(
                provider=provider,
                model=config.model,
                success=True,
                status="verified",
                message="Conexão testada com sucesso.",
                last_verified_at=checked_at,
            )
        except Exception as exc:  # pragma: no cover - provider/network defensive path
            error = self._safe_error(exc)
            self._mark_credential_verified(provider, None, error)
            self._audit(user, "connection_tested", provider, config.model, "error", error)
            self.db.commit()
            return AIConnectionTestResponse(
                provider=provider,
                model=config.model,
                success=False,
                used_fallback=True,
                status="error",
                message="IA externa indisponível; fallback local será usado.",
                error_summary=error,
            )

    def runtime_config(
        self,
        *,
        provider_override: str | None = None,
        model_override: str | None = None,
        base_url_override: str | None = None,
        enable_external_calls: bool | None = None,
        use_json_mode_override: bool | None = None,
    ) -> ActiveAIConfig:
        row = self._settings_row()
        provider = self._normalize_provider(
            provider_override or (row.provider if row else self.settings.ai_provider)
        )
        model = model_override or (row.selected_model if row else self.settings.ai_model) or None
        credential = self._credential(provider)
        base_url = base_url_override or (credential.base_url if credential else None)
        base_url = base_url or self._env_base_url(provider)
        if enable_external_calls is not None:
            external_calls = bool(enable_external_calls)
        elif row:
            external_calls = bool(row.enable_external_calls)
        else:
            external_calls = self.settings.ai_enable_external_calls
        return ActiveAIConfig(
            provider=provider,
            model=model,
            api_key=self._api_key(provider),
            base_url=base_url,
            enable_external_calls=external_calls and provider != "fallback",
            timeout_seconds=row.timeout_seconds if row else self.settings.ai_timeout_seconds,
            temperature=row.temperature if row else self.settings.ai_temperature,
            max_output_tokens=row.max_output_tokens if row else self.settings.ai_max_output_tokens,
            use_json_mode=(
                use_json_mode_override
                if use_json_mode_override is not None
                else row.use_json_mode if row else self.settings.ai_use_json_mode
            ),
        )

    def complete_json(
        self,
        *,
        system_instructions: str,
        payload: dict,
        purpose: str,
        config: ActiveAIConfig | None = None,
    ) -> dict:
        config = config or self.runtime_config()
        if not self._provider_ready(config):
            raise AIConfigurationError("Provider externo não configurado; usando fallback local.")
        content = self._external_completion(config, system_instructions, payload, purpose)
        return self._parse_json(content)

    def _provider_ready(self, config: ActiveAIConfig) -> bool:
        if config.provider == "fallback" or not config.enable_external_calls:
            return False
        if not config.model:
            return False
        if config.provider in {"openai", "gemini", "openai_compatible"} and not config.api_key:
            return False
        if config.provider in {"ollama", "openai_compatible"} and not config.base_url:
            return False
        return True

    def _refresh_provider_models(self, config: ActiveAIConfig) -> list[AIProviderModelCacheModel]:
        if config.provider in {"openai", "openai_compatible"}:
            return self._refresh_openai_compatible_models(config)
        if config.provider == "gemini":
            return self._refresh_gemini_models(config)
        if config.provider == "ollama":
            return self._refresh_ollama_models(config)
        return []

    def _refresh_openai_compatible_models(
        self, config: ActiveAIConfig
    ) -> list[AIProviderModelCacheModel]:
        if not config.api_key:
            raise AIConfigurationError("API Key ausente para listar modelos.")
        base = self._openai_base_url(config)
        response = httpx.get(
            f"{base}/models",
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        models = []
        for item in response.json().get("data", []):
            model_id = str(item.get("id") or "").strip()
            if not model_id:
                continue
            models.append(
                self._upsert_model(
                    provider=config.provider,
                    model_id=model_id,
                    display_name=model_id,
                    capabilities=["text", "json"],
                    supports_json=True,
                    supports_structured_output=True,
                    source="provider",
                )
            )
        return models

    def _refresh_gemini_models(self, config: ActiveAIConfig) -> list[AIProviderModelCacheModel]:
        if not config.api_key:
            raise AIConfigurationError("API Key ausente para listar modelos.")
        response = httpx.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": config.api_key},
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        models = []
        for item in response.json().get("models", []):
            model_id = str(item.get("name") or "").replace("models/", "")
            if not model_id:
                continue
            methods = item.get("supportedGenerationMethods") or []
            models.append(
                self._upsert_model(
                    provider="gemini",
                    model_id=model_id,
                    display_name=str(item.get("displayName") or model_id),
                    capabilities=list(methods),
                    supports_json=True,
                    supports_structured_output=False,
                    source="provider",
                )
            )
        return models

    def _refresh_ollama_models(self, config: ActiveAIConfig) -> list[AIProviderModelCacheModel]:
        base_url = (config.base_url or self.settings.ollama_base_url).rstrip("/")
        response = httpx.get(f"{base_url}/api/tags", timeout=config.timeout_seconds)
        response.raise_for_status()
        models = []
        for item in response.json().get("models", []):
            model_id = str(item.get("name") or "").strip()
            if not model_id:
                continue
            models.append(
                self._upsert_model(
                    provider="ollama",
                    model_id=model_id,
                    display_name=model_id,
                    capabilities=["local", "text"],
                    supports_json=True,
                    supports_structured_output=False,
                    source="provider",
                )
            )
        return models

    def _external_completion(
        self,
        config: ActiveAIConfig,
        system_instructions: str,
        payload: dict,
        purpose: str,
    ) -> str:
        if config.provider in {"openai", "openai_compatible"}:
            return self._openai_compatible_completion(config, system_instructions, payload)
        if config.provider == "gemini":
            return self._gemini_completion(config, system_instructions, payload)
        if config.provider == "ollama":
            return self._ollama_completion(config, system_instructions, payload)
        raise AIConfigurationError(f"Provider não suportado para {purpose}.")

    def _openai_compatible_completion(
        self,
        config: ActiveAIConfig,
        system_instructions: str,
        payload: dict,
    ) -> str:
        base = self._openai_base_url(config)
        body: dict[str, Any] = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_output_tokens,
        }
        if config.use_json_mode:
            body["response_format"] = {"type": "json_object"}
        response = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {config.api_key}"},
            json=body,
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"])

    def _gemini_completion(
        self,
        config: ActiveAIConfig,
        system_instructions: str,
        payload: dict,
    ) -> str:
        model = str(config.model or "").replace("models/", "")
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system_instructions}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": json.dumps(payload, ensure_ascii=False)}],
                }
            ],
            "generationConfig": {
                "temperature": config.temperature,
                "maxOutputTokens": config.max_output_tokens,
            },
        }
        if config.use_json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": config.api_key},
            json=body,
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        parts = response.json()["candidates"][0]["content"]["parts"]
        return str(parts[0].get("text") or "")

    def _ollama_completion(
        self,
        config: ActiveAIConfig,
        system_instructions: str,
        payload: dict,
    ) -> str:
        base_url = (config.base_url or self.settings.ollama_base_url).rstrip("/")
        headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
        body: dict[str, Any] = {
            "model": config.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_output_tokens,
            },
        }
        if config.use_json_mode:
            body["format"] = "json"
        response = httpx.post(
            f"{base_url}/api/chat",
            headers=headers,
            json=body,
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        return str(response.json()["message"]["content"])

    def _parse_json(self, content: str) -> dict:
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.removeprefix("json").strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end >= start:
            raw = raw[start : end + 1]
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise AIConfigurationError("Provider retornou JSON fora do formato esperado.")
        return parsed

    def _openai_base_url(self, config: ActiveAIConfig) -> str:
        if config.provider == "openai":
            return (config.base_url or "https://api.openai.com/v1").rstrip("/")
        if not config.base_url:
            raise AIConfigurationError("Base URL é obrigatória para provider OpenAI-compatible.")
        base = config.base_url.rstrip("/")
        return base if base.endswith("/v1") else f"{base}/v1"

    def _settings_row(self) -> AIProviderSettingsModel | None:
        return self.db.scalar(select(AIProviderSettingsModel).order_by(AIProviderSettingsModel.id))

    def _ensure_settings_row(self) -> AIProviderSettingsModel:
        row = self._settings_row()
        if row is None:
            row = AIProviderSettingsModel(
                provider=self._normalize_provider(self.settings.ai_provider),
                selected_model=self.settings.ai_model or None,
                enable_external_calls=self.settings.ai_enable_external_calls,
                timeout_seconds=self.settings.ai_timeout_seconds,
                temperature=self.settings.ai_temperature,
                max_output_tokens=self.settings.ai_max_output_tokens,
                use_json_mode=self.settings.ai_use_json_mode,
            )
            self.db.add(row)
            self.db.flush()
        return row

    def _credential(self, provider: str) -> AIProviderCredentialModel | None:
        return self.db.scalar(
            select(AIProviderCredentialModel).where(AIProviderCredentialModel.provider == provider)
        )

    def _api_key(self, provider: str) -> str | None:
        memory = _MEMORY_CREDENTIALS.get(provider)
        if memory and memory.get("api_key"):
            return str(memory["api_key"])
        row = self._credential(provider)
        if row and row.encrypted_api_key and row.is_active:
            return self.secrets.decrypt(row.encrypted_api_key)
        return self._env_api_key(provider) or None

    def _env_api_key(self, provider: str) -> str:
        if provider == "openai":
            return self.settings.openai_api_key or self.settings.ai_api_key
        if provider == "gemini":
            return self.settings.gemini_api_key or self.settings.google_api_key
        if provider == "ollama":
            return self.settings.ollama_api_key
        if provider == "openai_compatible":
            return self.settings.ai_api_key or self.settings.openai_api_key
        return ""

    def _env_base_url(self, provider: str) -> str | None:
        if provider == "ollama":
            return self.settings.ai_base_url or self.settings.ollama_base_url
        if provider == "openai_compatible":
            return self.settings.ai_base_url or None
        if provider == "openai":
            return self.settings.ai_base_url or None
        return None

    def _upsert_base_url(self, provider: str, base_url: str, user: UserModel) -> None:
        row = self._credential(provider)
        if row is None:
            row = AIProviderCredentialModel(
                provider=provider,
                created_by=user.id,
                updated_by=user.id,
                is_persistent=False,
            )
            self.db.add(row)
        row.base_url = base_url
        row.updated_by = user.id

    def _cached_models(self, provider: str) -> list[AIProviderModelCacheModel]:
        return list(
            self.db.scalars(
                select(AIProviderModelCacheModel)
                .where(AIProviderModelCacheModel.provider == provider)
                .order_by(AIProviderModelCacheModel.model_id)
            )
        )

    def _model_cache(self, provider: str, model_id: str) -> AIProviderModelCacheModel | None:
        return self.db.scalar(
            select(AIProviderModelCacheModel).where(
                AIProviderModelCacheModel.provider == provider,
                AIProviderModelCacheModel.model_id == model_id,
            )
        )

    def _cache_is_fresh(self, models: list[AIProviderModelCacheModel]) -> bool:
        latest = max(model.refreshed_at for model in models)
        return datetime.now(UTC) - latest <= MODEL_CACHE_TTL

    def _upsert_model(
        self,
        *,
        provider: str,
        model_id: str,
        display_name: str,
        capabilities: list[str],
        supports_json: bool,
        supports_structured_output: bool,
        source: str,
        supports_tools: bool = False,
        context_window: int | None = None,
    ) -> AIProviderModelCacheModel:
        row = self._model_cache(provider, model_id)
        if row is None:
            row = AIProviderModelCacheModel(provider=provider, model_id=model_id)
            self.db.add(row)
        row.display_name = display_name
        row.capabilities = capabilities
        row.context_window = context_window
        row.supports_json = supports_json
        row.supports_structured_output = supports_structured_output
        row.supports_tools = supports_tools
        row.is_available = True
        row.source = source
        row.refreshed_at = datetime.now(UTC)
        return row

    def _mark_verified(self, provider: str, model_id: str, verified_at: datetime) -> None:
        row = self._model_cache(provider, model_id)
        if row is None:
            row = self._upsert_model(
                provider=provider,
                model_id=model_id,
                display_name=model_id,
                capabilities=["verified"],
                supports_json=True,
                supports_structured_output=True,
                source="verified",
            )
        row.is_verified = True
        row.refreshed_at = verified_at

    def _mark_credential_verified(
        self,
        provider: str,
        verified_at: datetime | None,
        error: str | None,
    ) -> None:
        row = self._credential(provider)
        if row:
            row.last_verified_at = verified_at
            row.last_error = error

    def _model_response(
        self,
        provider: str,
        status: str,
        models: list[AIProviderModelCacheModel],
        *,
        error: str | None = None,
    ) -> AIModelListResponse:
        latest = max((model.refreshed_at for model in models), default=None)
        return AIModelListResponse(
            provider=provider,
            status=status,
            models=[AIProviderModelRead.model_validate(model) for model in models],
            last_refreshed_at=latest,
            error=error,
        )

    def _audit(
        self,
        user: UserModel,
        action: str,
        provider: str,
        model: str | None,
        result: str,
        error_summary: str | None,
        *,
        external_calls_enabled: bool | None = None,
    ) -> None:
        row = self._settings_row()
        self.db.add(
            AIConfigurationAuditLogModel(
                user_id=user.id,
                action=action,
                provider=provider,
                model=model,
                external_calls_enabled=(
                    bool(external_calls_enabled)
                    if external_calls_enabled is not None
                    else bool(row.enable_external_calls) if row else False
                ),
                result=result,
                error_summary=error_summary,
            )
        )
        self.db.add(
            AuditEventModel(
                user_id=user.id,
                user_name=user.name,
                user_email=user.email,
                user_role=user.role,
                action=f"ai_configuration.{action}",
                resource_type="ai_settings",
                resource_id=provider,
                status=result,
                details={
                    "provider": provider,
                    "model": model,
                    "external_calls_enabled": (
                        bool(external_calls_enabled)
                        if external_calls_enabled is not None
                        else bool(row.enable_external_calls) if row else False
                    ),
                    "error_summary": error_summary,
                    "secret_logged": False,
                },
            )
        )

    def _safe_error(self, exc: Exception) -> str:
        text = str(exc) or type(exc).__name__
        for provider in PROVIDER_CATALOG:
            api_key = self._env_api_key(provider)
            if api_key:
                text = text.replace(api_key, "[secret]")
        for memory in _MEMORY_CREDENTIALS.values():
            secret = memory.get("api_key")
            if secret:
                text = text.replace(str(secret), "[secret]")
        return text[:300]

    def _normalize_provider(self, provider: str | None) -> str:
        normalized = (provider or "fallback").strip().lower()
        if normalized in {"gpt", "openai"}:
            normalized = "openai"
        if normalized in {"llama", "local"}:
            normalized = "ollama"
        if normalized not in PROVIDER_CATALOG:
            raise AIConfigurationError("Provider de IA não suportado.")
        return normalized
