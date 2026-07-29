import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AuditRecord } from "../types/audit";
import type { GeneratedReport } from "../types/report";
import Audit from "./Audit";
import Reports from "./Reports";

const apiMocks = vi.hoisted(() => ({
  downloadAuditReport: vi.fn(),
  downloadPatientGuidanceReport: vi.fn(),
  downloadPrescriptionTechnicalReport: vi.fn(),
  downloadProtocolRunReportPdf: vi.fn(),
  downloadReconciliationReport: vi.fn(),
  exportAuditCsv: vi.fn(),
  exportAuditJson: vi.fn(),
  exportReportJson: vi.fn(),
  fetchAudit: vi.fn(),
  fetchAuditEvidence: vi.fn(),
  fetchAuditTimeline: vi.fn(),
  fetchPrescriptionEvidence: vi.fn(),
  fetchPrescriptionReportPreview: vi.fn(),
  fetchPrescriptionTimeline: vi.fn(),
  fetchReports: vi.fn(),
}));

vi.mock("../services/api", () => apiMocks);

const auditRecord: AuditRecord = {
  id: 42,
  user_id: 2,
  user_name: "Médica Demo",
  user_email: "medica@prescripta.local",
  user_role: "medico",
  action: "prescription.check",
  resource_type: "prescription_audit",
  resource_id: "21",
  created_at: "2026-07-29T12:00:00Z",
  status: "bloqueado",
  risk_level: "critico",
  details: { ai_provider: "fallback", ai_model: "deterministic", source: "Anvisa", jurisdiction: "BR", validation_status: "validated" },
};

function report(id: number, report_type: string, target_type: string): GeneratedReport {
  return {
    id,
    report_type,
    target_type,
    target_id: String(id + 10),
    generated_by_user_id: 1,
    generated_at: "2026-07-29T12:00:00Z",
    template_version: "v0.8.7",
    prescripta_version: "0.8.7",
    evidence_bundle_hash: `hash-${id}`,
    ai_provider: "fallback",
    ai_model: null,
    ai_prompt_version: null,
    ai_used: false,
    fallback_used: true,
    anonymized: id % 2 === 0,
    file_hash: `file-${id}`,
    status: "generated",
    metadata_json: { demo: true },
  };
}

function renderPage(node: React.ReactNode, entry = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[entry]}>{node}</MemoryRouter></QueryClientProvider>);
}

beforeEach(() => {
  apiMocks.fetchAudit.mockResolvedValue({ items: [auditRecord], page: 1, page_size: 20, total: 1, total_pages: 1, has_next: false, has_previous: false });
  apiMocks.fetchAuditTimeline.mockResolvedValue([{ title: "Checagem persistida", status: "completed" }]);
  apiMocks.fetchAuditEvidence.mockResolvedValue([{ source_id: "anvisa-demo", source_name: "Anvisa" }]);
  apiMocks.fetchReports.mockResolvedValue([
    report(1, "prescription_technical", "prescription_audit"),
    report(2, "patient_guidance", "prescription_audit"),
    report(3, "reconciliation", "clinical_import"),
    report(4, "protocol_run_report", "protocol_run"),
    report(5, "audit", "audit_events"),
  ]);
  apiMocks.fetchPrescriptionReportPreview.mockResolvedValue({ title: "Decisão clínica demonstrativa" });
  apiMocks.fetchPrescriptionTimeline.mockResolvedValue([{ order: 1, title: "Contexto", status: "completed" }]);
  apiMocks.fetchPrescriptionEvidence.mockResolvedValue([{ source_id: "rule-demo", evidence_summary: "Regra determinística" }]);
  for (const mock of Object.values(apiMocks)) {
    if (mock.getMockImplementation() === undefined) mock.mockResolvedValue(undefined);
  }
});

describe("auditoria", () => {
  it("filtra, exporta e abre evidências de uma decisão", async () => {
    renderPage(<Audit />, "/audit?patient=Paciente%20Demo");
    expect(await screen.findByText("Médica Demo")).toBeVisible();
    expect(screen.getByText(/Paciente: Paciente Demo/)).toBeVisible();
    fireEvent.change(screen.getByLabelText("Risco"), { target: { value: "critico" } });
    fireEvent.click(screen.getByRole("button", { name: "Filtrar" }));
    expect(await screen.findByText(/Risco: critico/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Exportar JSON" }));
    fireEvent.click(screen.getByRole("button", { name: "Exportar CSV" }));
    fireEvent.click(screen.getByRole("button", { name: "Gerar PDF" }));
    await waitFor(() => expect(apiMocks.exportAuditJson).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Ver" }));
    expect(await screen.findByRole("heading", { name: "Detalhe do evento #42" })).toBeVisible();
    expect((await screen.findAllByText(/Anvisa/)).length).toBeGreaterThan(0);
    fireEvent.click(screen.getAllByRole("button", { name: /Limpar/ })[0]);
  });

  it("mostra vazio sem sugerir sucesso", async () => {
    apiMocks.fetchAudit.mockResolvedValue({ items: [], page: 1, total: 0, total_pages: 0 });
    renderPage(<Audit />);
    expect(await screen.findByRole("heading", { name: "Nenhum evento registrado" })).toBeVisible();
  });
});

describe("relatórios auditáveis", () => {
  it("exibe bundle, timeline, evidência e exportação", async () => {
    renderPage(<Reports />);
    expect(await screen.findByText("Decisão clínica demonstrativa")).toBeVisible();
    expect(screen.getByText(/Regra determinística/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "JSON" }));
    fireEvent.click(screen.getByRole("button", { name: "Regenerar PDF" }));
    await waitFor(() => expect(apiMocks.exportReportJson.mock.calls[0][0]).toBe(1));
    expect(apiMocks.downloadPrescriptionTechnicalReport).toHaveBeenCalledWith(11, false);
  });

  it("regenera cada tipo pelo endpoint correto", async () => {
    renderPage(<Reports />);
    await screen.findByText("Decisão clínica demonstrativa");
    const labels = ["Orientações ao Paciente", "Relatório de Reconciliação Clínica", "Relatório de Protocolo", "Relatório de Auditoria"];
    for (const label of labels) {
      fireEvent.click(screen.getByRole("button", { name: new RegExp(label) }));
      fireEvent.click(screen.getByRole("button", { name: "Regenerar PDF" }));
      await waitFor(() => expect(screen.getByRole("heading", { name: label })).toBeVisible());
    }
    expect(apiMocks.downloadPatientGuidanceReport).toHaveBeenCalled();
    expect(apiMocks.downloadReconciliationReport).toHaveBeenCalled();
    expect(apiMocks.downloadProtocolRunReportPdf).toHaveBeenCalled();
    expect(apiMocks.downloadAuditReport).toHaveBeenCalled();
  });

  it("distingue ausência de histórico", async () => {
    apiMocks.fetchReports.mockResolvedValue([]);
    renderPage(<Reports />);
    expect(await screen.findByRole("heading", { name: "Nenhum relatório gerado" })).toBeVisible();
  });
});
