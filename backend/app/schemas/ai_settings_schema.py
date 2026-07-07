from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

SUPPORTED_AI_PROVIDERS = {"fallback", "openai", "gemini", "ollama", "openai_compatible"}


class AIProviderInfo(BaseModel):
    provider: str
    label: str
    requires_api_key: bool
    requires_base_url: bool = False
    supports_model_refresh: bool = True
    api_key_url: str | None = None
    docs_url: str | None = None


class AIProviderModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    model_id: str
    display_name: str
    capabilities: list[str] = Field(default_factory=list)
    context_window: int | None = None
    supports_json: bool = False
    supports_structured_output: bool = False
    supports_tools: bool = False
    is_available: bool = True
    is_verified: bool = False
    source: str = "cache"
    refreshed_at: datetime


class AIModelListResponse(BaseModel):
    provider: str
    status: str
    models: list[AIProviderModelRead]
    last_refreshed_at: datetime | None = None
    error: str | None = None
    allows_custom_model: bool = True


class AICredentialSaveRequest(BaseModel):
    provider: str = Field(pattern="^(fallback|openai|gemini|ollama|openai_compatible)$")
    api_key: str | None = Field(default=None, max_length=4096)
    base_url: str | None = Field(default=None, max_length=500)
    persist: bool = True


class AICredentialStatus(BaseModel):
    provider: str
    has_credential: bool
    masked_api_key: str | None = None
    base_url: str | None = None
    is_active: bool = True
    is_persistent: bool = False
    last_verified_at: datetime | None = None
    last_error: str | None = None


class AISettingsRead(BaseModel):
    provider: str
    selected_model: str | None = None
    enable_external_calls: bool = False
    timeout_seconds: int = 30
    temperature: float = 0.2
    max_output_tokens: int = 900
    use_json_mode: bool = True
    credential: AICredentialStatus | None = None
    external_status: str = "fallback"
    fallback_available: bool = True
    updated_at: datetime | None = None


class AIModelSelectRequest(BaseModel):
    provider: str = Field(pattern="^(fallback|openai|gemini|ollama|openai_compatible)$")
    selected_model: str | None = Field(default=None, max_length=180)
    custom_model: str | None = Field(default=None, max_length=180)
    base_url: str | None = Field(default=None, max_length=500)
    enable_external_calls: bool = False
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_output_tokens: int = Field(default=900, ge=64, le=8000)
    use_json_mode: bool = True


class AIConnectionTestRequest(BaseModel):
    provider: str = Field(pattern="^(fallback|openai|gemini|ollama|openai_compatible)$")
    model: str | None = Field(default=None, max_length=180)
    base_url: str | None = Field(default=None, max_length=500)
    enable_external_calls: bool = True
    use_json_mode: bool = True


class AIConnectionTestResponse(BaseModel):
    provider: str
    model: str | None = None
    success: bool
    used_fallback: bool = False
    status: str
    message: str
    last_verified_at: datetime | None = None
    error_summary: str | None = None


class AICompletionRequest(BaseModel):
    system_instructions: str
    payload: dict
    purpose: str


class AICompletionResult(BaseModel):
    provider: str
    model: str | None = None
    content: str
    parsed_json: dict | None = None
    used_fallback: bool = False
    fallback_reason: str | None = None
