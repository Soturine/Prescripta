export type AIProviderId = "fallback" | "openai" | "gemini" | "ollama" | "openai_compatible";

export type AIProviderInfo = {
  provider: AIProviderId;
  label: string;
  requires_api_key: boolean;
  requires_base_url: boolean;
  supports_model_refresh: boolean;
  api_key_url: string | null;
  docs_url: string | null;
};

export type AIProviderModel = {
  provider: AIProviderId;
  model_id: string;
  display_name: string;
  capabilities: string[];
  context_window: number | null;
  supports_json: boolean;
  supports_structured_output: boolean;
  supports_tools: boolean;
  is_available: boolean;
  is_verified: boolean;
  source: string;
  refreshed_at: string;
};

export type AIModelListResponse = {
  provider: AIProviderId;
  status: "updated" | "cache" | "error_cache" | "manual" | string;
  models: AIProviderModel[];
  last_refreshed_at: string | null;
  error: string | null;
  allows_custom_model: boolean;
};

export type AICredentialStatus = {
  provider: AIProviderId;
  has_credential: boolean;
  masked_api_key: string | null;
  base_url: string | null;
  is_active: boolean;
  is_persistent: boolean;
  last_verified_at: string | null;
  last_error: string | null;
};

export type AISettings = {
  provider: AIProviderId;
  selected_model: string | null;
  enable_external_calls: boolean;
  timeout_seconds: number;
  temperature: number;
  max_output_tokens: number;
  use_json_mode: boolean;
  credential: AICredentialStatus | null;
  external_status: string;
  fallback_available: boolean;
  updated_at: string | null;
};

export type AIHealthEvent = {
  action: string;
  provider: AIProviderId | string;
  model: string | null;
  result: string;
  error_summary: string | null;
  created_at: string;
};

export type AIHealth = {
  provider: AIProviderId;
  selected_model: string | null;
  external_calls_enabled: boolean;
  external_status: string;
  credential_status: string;
  cache_status: string;
  json_mode_enabled: boolean;
  fallback_available: boolean;
  circuit_breaker_state: string;
  failure_count: number;
  degraded_until: string | null;
  last_verified_at: string | null;
  last_error: string | null;
  recent_events: AIHealthEvent[];
};

export type AICredentialPayload = {
  provider: AIProviderId;
  api_key: string | null;
  base_url: string | null;
  persist: boolean;
};

export type AIModelSelectPayload = {
  provider: AIProviderId;
  selected_model: string | null;
  custom_model: string | null;
  base_url: string | null;
  enable_external_calls: boolean;
  timeout_seconds: number;
  temperature: number;
  max_output_tokens: number;
  use_json_mode: boolean;
};

export type AIConnectionTestPayload = {
  provider: AIProviderId;
  model: string | null;
  base_url: string | null;
  enable_external_calls: boolean;
  use_json_mode: boolean;
};

export type AIConnectionTestResult = {
  provider: AIProviderId;
  model: string | null;
  success: boolean;
  used_fallback: boolean;
  status: string;
  message: string;
  last_verified_at: string | null;
  error_summary: string | null;
};
