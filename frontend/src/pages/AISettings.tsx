import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ExternalLink,
  Eye,
  EyeOff,
  KeyRound,
  RefreshCw,
  Save,
  TestTube2,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import LoadingState from "../components/LoadingState";
import { useAuth } from "../context/AuthContext";
import {
  deleteAICredential,
  fetchAIModels,
  fetchAIProviders,
  fetchCurrentAISettings,
  saveAICredential,
  selectAIModel,
  testAIConnection,
} from "../services/api";
import type { AICredentialStatus, AIProviderId, AIProviderInfo } from "../types/aiSettings";
import { formatDateTime } from "../utils/formatters";

const providerOrder: AIProviderId[] = [
  "fallback",
  "openai",
  "gemini",
  "ollama",
  "openai_compatible",
];

export default function AISettings() {
  const queryClient = useQueryClient();
  const { canAccess } = useAuth();
  const canManage = canAccess(["admin"]);
  const [provider, setProvider] = useState<AIProviderId>("fallback");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [selectedModel, setSelectedModel] = useState("");
  const [customModel, setCustomModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [externalCalls, setExternalCalls] = useState(false);
  const [useJsonMode, setUseJsonMode] = useState(true);
  const [timeoutSeconds, setTimeoutSeconds] = useState(30);
  const [temperature, setTemperature] = useState(0.2);
  const [maxOutputTokens, setMaxOutputTokens] = useState(900);
  const [credentialStatus, setCredentialStatus] = useState<AICredentialStatus | null>(null);

  const { data: providers = [] } = useQuery({
    queryKey: ["ai-providers"],
    queryFn: fetchAIProviders,
  });
  const { data: current, isLoading: isLoadingCurrent } = useQuery({
    queryKey: ["ai-settings-current"],
    queryFn: fetchCurrentAISettings,
  });
  const { data: modelList, isFetching: isFetchingModels } = useQuery({
    queryKey: ["ai-models", provider],
    queryFn: () => fetchAIModels(provider, false),
  });

  useEffect(() => {
    if (!current) {
      return;
    }
    setProvider(current.provider);
    setSelectedModel(current.selected_model ?? "");
    setBaseUrl(current.credential?.base_url ?? "");
    setExternalCalls(current.enable_external_calls);
    setUseJsonMode(current.use_json_mode);
    setTimeoutSeconds(current.timeout_seconds);
    setTemperature(current.temperature);
    setMaxOutputTokens(current.max_output_tokens);
    setCredentialStatus(current.credential);
  }, [current]);

  const activeProvider = useMemo(
    () => providers.find((item) => item.provider === provider),
    [provider, providers],
  );
  const models = modelList?.models ?? [];
  const activeModel = customModel.trim() || selectedModel || null;
  const displayedCredential =
    credentialStatus?.provider === provider
      ? credentialStatus
      : current?.provider === provider
        ? current.credential
        : null;

  const saveCredentialMutation = useMutation({
    mutationFn: () =>
      saveAICredential({
        provider,
        api_key: apiKey.trim() || null,
        base_url: baseUrl.trim() || null,
        persist: true,
      }),
    onSuccess: async (status) => {
      setCredentialStatus(status);
      setApiKey("");
      await queryClient.invalidateQueries({ queryKey: ["ai-settings-current"] });
    },
  });
  const deleteCredentialMutation = useMutation({
    mutationFn: () => deleteAICredential(provider),
    onSuccess: async (status) => {
      setCredentialStatus(status);
      setApiKey("");
      await queryClient.invalidateQueries({ queryKey: ["ai-settings-current"] });
    },
  });
  const refreshModelsMutation = useMutation({
    mutationFn: () => fetchAIModels(provider, true),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["ai-models", provider] });
    },
  });
  const testMutation = useMutation({
    mutationFn: () =>
      testAIConnection({
        provider,
        model: activeModel,
        base_url: baseUrl.trim() || null,
        enable_external_calls: externalCalls,
        use_json_mode: useJsonMode,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["ai-settings-current"] });
      await queryClient.invalidateQueries({ queryKey: ["ai-models", provider] });
    },
  });
  const selectMutation = useMutation({
    mutationFn: () =>
      selectAIModel({
        provider,
        selected_model: selectedModel || null,
        custom_model: customModel.trim() || null,
        base_url: baseUrl.trim() || null,
        enable_external_calls: externalCalls,
        timeout_seconds: timeoutSeconds,
        temperature,
        max_output_tokens: maxOutputTokens,
        use_json_mode: useJsonMode,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["ai-settings-current"] });
    },
  });

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Configurações de IA</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Configure provider, chave, modelo e chamadas externas. O frontend nunca chama o
          provider diretamente e a API Key não é retornada pela API.
        </p>
      </header>

      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-medium leading-6 text-amber-900">
        A IA do Prescripta é explicativa e extratora/classificadora com fonte. Ela não decide
        prescrição, risco, bloqueio, dose ou recomendação final.
      </section>

      {isLoadingCurrent ? <LoadingState label="Carregando configuração de IA" /> : null}

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <KeyRound aria-hidden="true" className="h-5 w-5 text-ocean" />
            <h2 className="text-lg font-bold text-ink">Provider e credencial</h2>
          </div>

          <div className="mt-4 grid gap-4">
            <label className="grid gap-1.5">
              <span className="label">Provider</span>
              <select
                className="field"
                disabled={!canManage}
                value={provider}
                onChange={(event) => {
                  setProvider(event.target.value as AIProviderId);
                  setSelectedModel("");
                  setCustomModel("");
                }}
              >
                {providerOrder.map((item) => {
                  const info = providers.find((providerItem) => providerItem.provider === item);
                  return (
                    <option key={item} value={item}>
                      {info?.label ?? item}
                    </option>
                  );
                })}
              </select>
            </label>

            <div className="grid gap-2 rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm">
              <StatusLine label="Provider ativo" value={current?.provider ?? "-"} />
              <StatusLine label="Modelo ativo" value={current?.selected_model ?? "fallback"} />
              <StatusLine label="Chamadas externas" value={current?.enable_external_calls ? "habilitadas" : "desabilitadas"} />
              <StatusLine label="Chave salva" value={displayedCredential?.masked_api_key ?? "não configurada"} />
              <StatusLine label="Persistência" value={displayedCredential?.is_persistent ? "criptografada" : "memória/env/local"} />
              <StatusLine label="Última verificação" value={displayedCredential?.last_verified_at ? formatDateTime(displayedCredential.last_verified_at) : "-"} />
            </div>

            {activeProvider?.requires_base_url ? (
              <label className="grid gap-1.5">
                <span className="label">Base URL</span>
                <input
                  className="field"
                  disabled={!canManage}
                  placeholder={provider === "ollama" ? "http://localhost:11434" : "https://provider.example/v1"}
                  value={baseUrl}
                  onChange={(event) => setBaseUrl(event.target.value)}
                />
              </label>
            ) : null}

            {activeProvider?.requires_api_key ? (
              <label className="grid gap-1.5">
                <span className="label">API Key</span>
                <div className="flex gap-2">
                  <input
                    autoComplete="off"
                    className="field"
                    disabled={!canManage}
                    placeholder={displayedCredential?.masked_api_key ?? "Cole a chave aqui"}
                    type={showKey ? "text" : "password"}
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                  />
                  <button
                    className="btn-secondary aspect-square px-3"
                    onClick={() => setShowKey((value) => !value)}
                    title={showKey ? "Ocultar chave" : "Mostrar chave"}
                    type="button"
                  >
                    {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </label>
            ) : null}

            <div className="flex flex-wrap gap-2">
              <button
                className="btn-primary"
                disabled={!canManage || saveCredentialMutation.isPending || provider === "fallback"}
                onClick={() => saveCredentialMutation.mutate()}
                type="button"
              >
                <Save aria-hidden="true" className="h-4 w-4" />
                Salvar chave
              </button>
              <button
                className="btn-secondary"
                disabled={!canManage || deleteCredentialMutation.isPending || provider === "fallback"}
                onClick={() => deleteCredentialMutation.mutate()}
                type="button"
              >
                <Trash2 aria-hidden="true" className="h-4 w-4" />
                Apagar chave
              </button>
            </div>

            <ProviderLinks provider={activeProvider} />
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <RefreshCw aria-hidden="true" className="h-5 w-5 text-ocean" />
            <h2 className="text-lg font-bold text-ink">Modelo e chamada</h2>
          </div>

          <div className="mt-4 grid gap-4">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3">
              <div>
                <p className="text-sm font-bold text-ink">Lista de modelos</p>
                <p className="text-xs text-slate-500">
                  Status: {modelList?.status ?? "manual"} · atualizado em{" "}
                  {modelList?.last_refreshed_at ? formatDateTime(modelList.last_refreshed_at) : "-"}
                </p>
              </div>
              <button
                className="btn-secondary"
                disabled={!canManage || refreshModelsMutation.isPending || isFetchingModels}
                onClick={() => refreshModelsMutation.mutate()}
                type="button"
              >
                <RefreshCw aria-hidden="true" className="h-4 w-4" />
                Atualizar modelos
              </button>
            </div>

            {modelList?.error ? (
              <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-900">
                {modelList.error}
              </p>
            ) : null}

            <label className="grid gap-1.5">
              <span className="label">Modelo disponível</span>
              <select
                className="field"
                disabled={!canManage || Boolean(customModel)}
                value={selectedModel}
                onChange={(event) => setSelectedModel(event.target.value)}
              >
                <option value="">Selecionar modelo</option>
                {models.map((model) => (
                  <option key={model.model_id} value={model.model_id}>
                    {model.display_name}
                    {model.is_verified ? " · verificado" : ""}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-1.5">
              <span className="label">Modelo customizado</span>
              <input
                className="field"
                disabled={!canManage}
                placeholder="Use apenas quando o modelo não aparecer na lista"
                value={customModel}
                onChange={(event) => setCustomModel(event.target.value)}
              />
            </label>

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 text-sm font-semibold text-slate-700">
                <input
                  checked={externalCalls}
                  className="h-4 w-4 accent-ocean"
                  disabled={!canManage || provider === "fallback"}
                  onChange={(event) => setExternalCalls(event.target.checked)}
                  type="checkbox"
                />
                Permitir chamadas externas de IA
              </label>
              <label className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 text-sm font-semibold text-slate-700">
                <input
                  checked={useJsonMode}
                  className="h-4 w-4 accent-ocean"
                  disabled={!canManage}
                  onChange={(event) => setUseJsonMode(event.target.checked)}
                  type="checkbox"
                />
                Usar modo JSON quando suportado
              </label>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <label className="grid gap-1.5">
                <span className="label">Timeout</span>
                <input
                  className="field"
                  disabled={!canManage}
                  min={1}
                  max={120}
                  type="number"
                  value={timeoutSeconds}
                  onChange={(event) => setTimeoutSeconds(Number(event.target.value))}
                />
              </label>
              <label className="grid gap-1.5">
                <span className="label">Temperatura</span>
                <input
                  className="field"
                  disabled={!canManage}
                  max={2}
                  min={0}
                  step={0.1}
                  type="number"
                  value={temperature}
                  onChange={(event) => setTemperature(Number(event.target.value))}
                />
              </label>
              <label className="grid gap-1.5">
                <span className="label">Máx. tokens</span>
                <input
                  className="field"
                  disabled={!canManage}
                  min={64}
                  max={8000}
                  type="number"
                  value={maxOutputTokens}
                  onChange={(event) => setMaxOutputTokens(Number(event.target.value))}
                />
              </label>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                className="btn-secondary"
                disabled={!canManage || testMutation.isPending}
                onClick={() => testMutation.mutate()}
                type="button"
              >
                <TestTube2 aria-hidden="true" className="h-4 w-4" />
                Testar conexão
              </button>
              <button
                className="btn-primary"
                disabled={!canManage || selectMutation.isPending}
                onClick={() => selectMutation.mutate()}
                type="button"
              >
                <Save aria-hidden="true" className="h-4 w-4" />
                Ativar modelo
              </button>
            </div>

            {testMutation.data ? (
              <p
                className={[
                  "rounded-lg border p-3 text-sm font-semibold",
                  testMutation.data.success
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border-amber-200 bg-amber-50 text-amber-900",
                ].join(" ")}
              >
                {testMutation.data.message}
              </p>
            ) : null}
            {selectMutation.isError || saveCredentialMutation.isError || testMutation.isError ? (
              <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700">
                A operação não foi concluída. Revise provider, chave, base URL e modelo.
              </p>
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}

function StatusLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-slate-500">{label}</span>
      <span className="text-right font-bold text-ink">{value}</span>
    </div>
  );
}

function ProviderLinks({
  provider,
}: {
  provider: AIProviderInfo | undefined;
}) {
  if (!provider?.api_key_url && !provider?.docs_url) {
    return null;
  }
  return (
    <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-3">
      {provider.api_key_url ? (
        <a className="btn-secondary" href={provider.api_key_url} rel="noreferrer" target="_blank">
          <ExternalLink aria-hidden="true" className="h-4 w-4" />
          Obter chave
        </a>
      ) : null}
      {provider.docs_url ? (
        <a className="btn-secondary" href={provider.docs_url} rel="noreferrer" target="_blank">
          <ExternalLink aria-hidden="true" className="h-4 w-4" />
          Abrir documentação
        </a>
      ) : null}
    </div>
  );
}
