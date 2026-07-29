import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AISettings from "./AISettings";

const apiMocks = vi.hoisted(() => ({
  deleteAICredential: vi.fn(),
  fetchAIHealth: vi.fn(),
  fetchAIModels: vi.fn(),
  fetchAIProviders: vi.fn(),
  fetchCurrentAISettings: vi.fn(),
  saveAICredential: vi.fn(),
  selectAIModel: vi.fn(),
  testAIConnection: vi.fn(),
}));
const authMock = vi.hoisted(() => vi.fn());
vi.mock("../services/api", () => apiMocks);
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><AISettings /></QueryClientProvider>);
}

beforeEach(() => {
  authMock.mockReturnValue({ can: () => true });
  apiMocks.fetchAIProviders.mockResolvedValue([
    { provider: "fallback", label: "Fallback", requires_api_key: false, requires_base_url: false },
    { provider: "openai", label: "OpenAI", requires_api_key: true, requires_base_url: false, api_key_url: "https://platform.openai.com/api-keys", docs_url: "https://platform.openai.com/docs" },
    { provider: "ollama", label: "Ollama", requires_api_key: false, requires_base_url: true },
  ]);
  apiMocks.fetchCurrentAISettings.mockResolvedValue({
    provider: "openai",
    selected_model: "gpt-demo",
    enable_external_calls: false,
    use_json_mode: true,
    timeout_seconds: 30,
    temperature: 0.2,
    max_output_tokens: 900,
    credential: { provider: "openai", masked_api_key: "sk-••••demo", is_persistent: true, last_verified_at: "2026-07-29T12:00:00Z" },
  });
  apiMocks.fetchAIHealth.mockResolvedValue({
    provider: "openai", selected_model: "gpt-demo", external_calls_enabled: false,
    credential_status: "configured", cache_status: "fresh", json_mode_enabled: true,
    failure_count: 0, circuit_breaker_state: "closed", last_verified_at: "2026-07-29T12:00:00Z",
    last_error: null, recent_events: [{ action: "test", provider: "openai", model: "gpt-demo", result: "success", created_at: "2026-07-29T12:00:00Z" }],
  });
  apiMocks.fetchAIModels.mockResolvedValue({ status: "fresh", last_refreshed_at: "2026-07-29T12:00:00Z", error: null, models: [{ model_id: "gpt-demo", display_name: "GPT Demo", is_verified: true }] });
  apiMocks.saveAICredential.mockResolvedValue({ provider: "openai", masked_api_key: "sk-••••nova", is_persistent: true });
  apiMocks.deleteAICredential.mockResolvedValue({ provider: "openai", masked_api_key: null, is_persistent: false });
  apiMocks.testAIConnection.mockResolvedValue({ success: true, message: "Conexão validada" });
  apiMocks.selectAIModel.mockResolvedValue({ provider: "openai" });
});

describe("configuração segura de IA", () => {
  it("exibe saúde, credencial mascarada e links oficiais", async () => {
    renderPage();
    expect(await screen.findByText("sk-••••demo")).toBeVisible();
    expect(screen.getByText("Operacional")).toBeVisible();
    expect(screen.getByText(/test · openai/)).toBeVisible();
    expect(screen.getByRole("link", { name: "Obter chave" })).toHaveAttribute("target", "_blank");
  });

  it("salva, apaga, atualiza, testa e ativa somente pelo backend", async () => {
    renderPage();
    await screen.findByText("sk-••••demo");
    fireEvent.change(screen.getByLabelText("API Key"), { target: { value: "sk-chave-ficticia" } });
    fireEvent.click(screen.getByTitle("Mostrar chave"));
    expect(screen.getByLabelText("API Key")).toHaveAttribute("type", "text");
    fireEvent.click(screen.getByRole("button", { name: "Salvar chave" }));
    fireEvent.click(screen.getByRole("button", { name: "Apagar chave" }));
    fireEvent.click(screen.getByRole("button", { name: "Atualizar modelos" }));
    fireEvent.change(screen.getByLabelText("Modelo disponível"), { target: { value: "gpt-demo" } });
    fireEvent.click(screen.getByLabelText("Permitir chamadas externas de IA"));
    fireEvent.change(screen.getByLabelText("Timeout"), { target: { value: "45" } });
    fireEvent.change(screen.getByLabelText("Temperatura"), { target: { value: "0.1" } });
    fireEvent.change(screen.getByLabelText("Máx. tokens"), { target: { value: "700" } });
    fireEvent.click(screen.getByRole("button", { name: "Testar conexão" }));
    fireEvent.click(screen.getByRole("button", { name: "Ativar modelo" }));
    await waitFor(() => expect(apiMocks.saveAICredential).toHaveBeenCalled());
    expect(apiMocks.testAIConnection).toHaveBeenCalled();
    expect(apiMocks.selectAIModel).toHaveBeenCalled();
    expect(await screen.findByText("Conexão validada")).toBeVisible();
  });

  it("mostra base URL para provider local e bloqueia escrita sem capacidade", async () => {
    authMock.mockReturnValue({ can: () => false });
    apiMocks.fetchCurrentAISettings.mockResolvedValue({
      provider: "ollama", selected_model: null, enable_external_calls: false, use_json_mode: true,
      timeout_seconds: 30, temperature: 0.2, max_output_tokens: 900, credential: null,
    });
    apiMocks.fetchAIHealth.mockResolvedValue({ circuit_breaker_state: "open", credential_status: "missing", cache_status: "empty", recent_events: [], failure_count: 3, last_error: "Provider indisponível" });
    renderPage();
    expect(await screen.findByLabelText("Base URL")).toBeDisabled();
    expect(screen.getByText("Breaker aberto")).toBeVisible();
    expect(screen.getByText(/Último erro/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Ativar modelo" })).toBeDisabled();
  });
});
