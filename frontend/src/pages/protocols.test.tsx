import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { EmergencyProtocol, ProtocolRunResult } from "../types/protocol";
import Protocols from "./Protocols";

const apiMocks = vi.hoisted(() => ({
  downloadProtocolRunReportPdf: vi.fn(),
  explainProtocol: vi.fn(),
  exportProtocolRunCsv: vi.fn(),
  exportProtocolRunJson: vi.fn(),
  fetchPatients: vi.fn(),
  fetchProtocolEvidence: vi.fn(),
  fetchProtocolReport: vi.fn(),
  fetchProtocols: vi.fn(),
  runProtocol: vi.fn(),
}));
const authMock = vi.hoisted(() => vi.fn());

vi.mock("../services/api", () => apiMocks);
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

const protocol: EmergencyProtocol = {
  id: "anafilaxia-demo",
  slug: "anafilaxia-demo",
  title: "Anafilaxia demonstrativa",
  category: "Emergência",
  summary: "Fluxo rápido fictício para teste",
  clinical_goal: "Estruturar revisão humana imediata.",
  severity_level: "critical",
  audience: "Equipe clínica",
  jurisdiction: "BR",
  source_name: "Fonte BR demonstrativa",
  source_url: "https://example.test/fonte",
  source_version: "2026.1",
  validation_status: "validado",
  last_reviewed_at: "2026-07-29",
  disclaimer: "Conteúdo demonstrativo",
  red_flags: ["Comprometimento de via aérea"],
  immediate_measures: ["Acionar equipe"],
  medication_references: ["Referência fictícia"],
  cautions: ["Confirmar contexto"],
  referral_criteria: ["Instabilidade"],
  monitoring: ["Sinais vitais"],
  documentation_items: ["Horário"],
  do_not_apply_when: ["Fonte incompatível"],
  human_judgment_points: ["Revisar resposta"],
  safety_notes: ["IA não decide"],
  context_fields: [
    { name: "weight", label: "Peso", field_type: "number", required: true, unit: "kg", helper: "Peso aferido", options: [] },
    { name: "airway", label: "Via aérea comprometida", field_type: "boolean", required: true, options: [] },
    { name: "presentation", label: "Apresentação", field_type: "select", required: false, options: ["cutânea"] },
  ],
  calculators: [{ id: "calc-demo", label: "Cálculo demo", description: "Determinístico", input_fields: ["weight"], source_note: "Fonte demo", requires_human_confirmation: true }],
  steps: [
    { order: 1, title: "Avaliar", action: "Avaliar ABC", explanation: "Confirmação humana", warning_level: "high", requires_human_judgment: true, evidence_ref: "ev-1" },
    { order: 2, title: "Registrar", action: "Registrar resposta", explanation: "Auditar execução", warning_level: "info", requires_human_judgment: true, evidence_ref: "ev-1" },
  ],
};

const runResult: ProtocolRunResult = {
  run_id: 42,
  audit_event_id: 81,
  protocol_id: protocol.id,
  protocol_version: "2026.1",
  title: protocol.title,
  status: "registered",
  warning_level: "critical",
  patient_id: 7,
  patient_context_summary: { age_years: 36, weight_kg: 70, height_cm: 170, bmi: 24.2, reviewed_documents: 2 },
  triage_flags: ["Revisão imediata"],
  calculated_values: [{ label: "Valor demo", value: "0,3", formula: "peso × fator", source_ref: "ev-1", warning: "Confirmar manualmente", requires_human_confirmation: true }],
  timeline: [{ order: 1 }],
  evidence: [],
  audit_notice: "Execução auditada sem decisão automática.",
  educational_notice: "Uso demonstrativo.",
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><Protocols /></QueryClientProvider>);
}

beforeEach(() => {
  authMock.mockReturnValue({ canAny: () => true });
  apiMocks.fetchProtocols.mockResolvedValue([protocol, { ...protocol, id: "dor-demo", title: "Dor torácica", category: "Cardiologia", severity_level: "attention" }]);
  apiMocks.fetchPatients.mockResolvedValue([{ id: 7, name: "Paciente Demo", age: 36, weight_kg: 70 }]);
  apiMocks.fetchProtocolEvidence.mockResolvedValue([{ evidence_ref: "ev-1", source_name: "Fonte BR demonstrativa", source_url: null, source_version: "2026.1", summary: "Evidência fictícia revisada", validation_status: "validated" }]);
  apiMocks.runProtocol.mockResolvedValue(runResult);
  apiMocks.explainProtocol.mockResolvedValue({ provider: "fallback", model: null, used_fallback: true, protocol_id: protocol.id, simple_explanation: "Explicação simples controlada", professional_summary: "Resumo profissional limitado ao fluxo", safety_note: "A decisão permanece humana", cited_evidence_refs: ["ev-1"], structure_locked: true, educational_notice: "Demo" });
  apiMocks.fetchProtocolReport.mockResolvedValue({ title: "Relatório", protocol_id: protocol.id, protocol_version: "2026.1", run_id: 42, generated_report_id: 9, generated_at: "2026-07-29T12:00:00Z", report_lines: ["Linha auditável", "Sem nova conduta"], report_payload: {}, timeline: [], evidence: [] });
  apiMocks.downloadProtocolRunReportPdf.mockResolvedValue(undefined);
  apiMocks.exportProtocolRunJson.mockResolvedValue(undefined);
  apiMocks.exportProtocolRunCsv.mockResolvedValue(undefined);
});

describe("protocolos rápidos", () => {
  it("normaliza contexto, registra passos e só então habilita artefatos do run", async () => {
    renderPage();
    await screen.findByRole("heading", { name: protocol.title });
    fireEvent.change(screen.getByRole("combobox", { name: /Selecionar paciente/ }), { target: { value: "7" } });
    fireEvent.change(screen.getByRole("spinbutton", { name: /Peso/ }), { target: { value: "70.5" } });
    fireEvent.change(screen.getByRole("combobox", { name: /Via aérea comprometida/ }), { target: { value: "true" } });
    fireEvent.change(screen.getByRole("textbox", { name: "Apresentação" }), { target: { value: "cutânea" } });
    fireEvent.click(screen.getAllByTitle("Marcar passo")[0]);
    fireEvent.click(screen.getByRole("button", { name: "Executar fluxo" }));

    expect(await screen.findByRole("heading", { name: "Execução registrada" })).toBeVisible();
    expect(apiMocks.runProtocol).toHaveBeenCalledWith(protocol.id, expect.objectContaining({
      patient_id: 7,
      context: { weight: 70.5, airway: true, presentation: "cutânea" },
      selected_step_orders: [1],
    }));

    fireEvent.click(screen.getByRole("button", { name: "Preview" }));
    await waitFor(() => expect(apiMocks.fetchProtocolReport).toHaveBeenCalledWith(protocol.id, 42));
    expect(await screen.findByText(/Linha auditável/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "PDF" }));
    fireEvent.click(screen.getByRole("button", { name: "JSON" }));
    fireEvent.click(screen.getByRole("button", { name: "CSV" }));
    expect(apiMocks.downloadProtocolRunReportPdf).toHaveBeenCalledWith(42);
    expect(apiMocks.exportProtocolRunJson).toHaveBeenCalledWith(protocol.id, 42);
    expect(apiMocks.exportProtocolRunCsv).toHaveBeenCalledWith(protocol.id, 42);
  });

  it("filtra catálogo, explica sem alterar o fluxo e respeita consulta sem execução", async () => {
    const { unmount } = renderPage();
    await screen.findByText("Dor torácica");
    fireEvent.change(screen.getByPlaceholderText("Anafilaxia, glicemia, dor..."), { target: { value: "torácica" } });
    expect(screen.queryByRole("button", { name: /Anafilaxia demonstrativa Emergência/ })).not.toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Pergunta contextual" }), { target: { value: "Explique a fonte" } });
    fireEvent.click(screen.getByRole("button", { name: "Explicar protocolo" }));
    expect(await screen.findByText("Explicação simples controlada")).toBeVisible();
    expect(apiMocks.explainProtocol).toHaveBeenCalledWith(protocol.id, expect.objectContaining({ question: "Explique a fonte", run_id: null }));
    unmount();

    authMock.mockReturnValue({ canAny: () => false });
    renderPage();
    expect(await screen.findByText(/pode consultar protocolos/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Executar fluxo" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Explicar protocolo" })).toBeDisabled();
  });

  it("não inventa protocolo quando o catálogo está vazio", async () => {
    apiMocks.fetchProtocols.mockResolvedValue([]);
    renderPage();
    expect(await screen.findByRole("heading", { name: "Nenhum protocolo disponível" })).toBeVisible();
    await waitFor(() => expect(apiMocks.runProtocol).not.toHaveBeenCalled());
  });
});
