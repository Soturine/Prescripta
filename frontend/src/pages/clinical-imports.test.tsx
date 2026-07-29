import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ClinicalImportBatch, ClinicalReconciliation } from "../types/integration";
import ClinicalImports from "./ClinicalImports";

const apiMocks = vi.hoisted(() => ({
  acceptClinicalImport: vi.fn(), acceptClinicalReconciliationItem: vi.fn(), acceptClinicalReconciliationSafeItems: vi.fn(),
  checkCdsPrescription: vi.fn(), downloadReconciliationReport: vi.fn(), exportImportCsv: vi.fn(), exportImportJson: vi.fn(),
  fetchClinicalImports: vi.fn(), fetchClinicalReconciliation: vi.fn(), importClinicalCsv: vi.fn(), importClinicalFhir: vi.fn(),
  importClinicalJson: vi.fn(), rejectClinicalImport: vi.fn(), rejectClinicalReconciliationItem: vi.fn(),
}));
const authMock = vi.hoisted(() => vi.fn());

vi.mock("../services/api", () => apiMocks);
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

const batch: ClinicalImportBatch = {
  id: 12, source_system: "hospital_demo", source_type: "generic_json", imported_by: 2, patient_id: 7,
  consent_id: 5, status: "pending_review", imported_at: "2026-07-29T12:00:00Z", finished_at: null, errors: [],
  educational_notice: "Revisão humana obrigatória.",
  records: [{ id: 101, batch_id: 12, record_type: "condition", source_payload: { value: "renal" }, mapped_payload: { condition: "renal" }, confidence: 0.82, accepted_by_user: false, rejected_reason: null, created_at: "2026-07-29T12:00:00Z" }],
};

const reconciliation: ClinicalReconciliation = {
  batch_id: 12, patient_id: 7, status: "pending_review", summary: { total: 2, conflicts: 1, new: 1 }, badges: ["conflito", "novo"], educational_notice: "Nenhum dado importado é aplicado automaticamente.",
  items: [
    { item_id: "condition:renal", source_record_id: 101, record_type: "condition", field_path: "conditions[0]", current_value: { value: "sem registro" }, imported_value: { value: "condição renal" }, source_system: "hospital_demo", source_type: "generic_json", confidence: 0.82, badge: "conflito", suggestion: "review_manually", conflict: true, decision: null, reviewed_by: null, reviewed_at: null, justification: null },
    { item_id: "medication:new", source_record_id: 102, record_type: "current_medication", field_path: "current_medications[0]", current_value: { value: null }, imported_value: { value: "medicamento demo" }, source_system: "hospital_demo", source_type: "generic_json", confidence: 0.94, badge: "novo", suggestion: "accept_new_data", conflict: false, decision: "accepted", reviewed_by: 2, reviewed_at: "2026-07-29T13:00:00Z", justification: "Revisado" },
  ],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><ClinicalImports /></QueryClientProvider>);
}

beforeEach(() => {
  authMock.mockReturnValue({ can: () => true });
  apiMocks.fetchClinicalImports.mockResolvedValue([batch]);
  apiMocks.fetchClinicalReconciliation.mockResolvedValue(reconciliation);
  apiMocks.importClinicalJson.mockResolvedValue(batch);
  apiMocks.importClinicalFhir.mockResolvedValue(batch);
  apiMocks.importClinicalCsv.mockResolvedValue(batch);
  apiMocks.acceptClinicalImport.mockResolvedValue({ ...batch, status: "accepted" });
  apiMocks.rejectClinicalImport.mockResolvedValue({ ...batch, status: "rejected" });
  apiMocks.acceptClinicalReconciliationItem.mockResolvedValue(reconciliation.items[0]);
  apiMocks.rejectClinicalReconciliationItem.mockResolvedValue(reconciliation.items[0]);
  apiMocks.acceptClinicalReconciliationSafeItems.mockResolvedValue(reconciliation);
  apiMocks.downloadReconciliationReport.mockResolvedValue(undefined);
  apiMocks.exportImportJson.mockResolvedValue(undefined);
  apiMocks.exportImportCsv.mockResolvedValue(undefined);
  apiMocks.checkCdsPrescription.mockResolvedValue({ decision: {}, coverage_status: "covered", status: "liberado", risk_level: "baixo", alerts: [], cards: [{ summary: "Card determinístico", indicator: "info", detail: "Persistência desativada", source: {} }], audit_id: "audit-demo", idempotency_key: "idem-demo", educational_notice: "Demo" });
});

describe("importações clínicas", () => {
  it("exige consentimento no payload e suporta JSON, FHIR e CSV separadamente", async () => {
    renderPage();
    await screen.findByRole("heading", { name: "Detalhes da importação #12" });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Importar" }));
    await waitFor(() => expect(apiMocks.importClinicalJson).toHaveBeenCalledWith(expect.objectContaining({ consent_confirmed: true, source_system: "hospital_teste" }), expect.objectContaining({ patient: expect.any(Object) })));

    fireEvent.click(screen.getByRole("button", { name: "FHIR" }));
    fireEvent.change(screen.getByRole("combobox", { name: "Exemplo FHIR de teste" }), { target: { value: "renalConflict" } });
    fireEvent.click(screen.getByRole("button", { name: "Importar" }));
    await waitFor(() => expect(apiMocks.importClinicalFhir).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ resourceType: "Bundle" })));

    fireEvent.click(screen.getByRole("button", { name: "CSV" }));
    fireEvent.click(screen.getByRole("button", { name: "Editar payload" }));
    const csvEditor = screen.getByRole("textbox", { name: "CSV" });
    fireEvent.change(csvEditor, { target: { value: "record_type,value\nallergy,demo" } });
    fireEvent.click(screen.getByRole("button", { name: "Importar" }));
    await waitFor(() => expect(apiMocks.importClinicalCsv).toHaveBeenCalledWith(expect.anything(), "record_type,value\nallergy,demo"));
  });

  it("mantém conflito granular sob decisão humana e audita exportações", async () => {
    renderPage();
    const detail = await screen.findByRole("heading", { name: "Detalhes da importação #12" });
    const section = detail.closest("section") as HTMLElement;
    expect(await within(section).findByRole("button", { name: "Conflitos exigem revisão" })).toBeDisabled();
    fireEvent.change(within(section).getByRole("textbox", { name: "Justificativa para decisão granular" }), { target: { value: "Conferido com fonte demo" } });
    const row = within(section).getByText("conditions[0]").closest("tr") as HTMLElement;
    fireEvent.click(within(row).getByRole("button", { name: "Aceitar" }));
    fireEvent.click(within(row).getByRole("button", { name: "Rejeitar" }));
    fireEvent.click(within(section).getByTitle("Aceitar importação"));
    fireEvent.change(within(section).getAllByRole("textbox").at(-1) as HTMLElement, { target: { value: "Fonte externa inconsistente" } });
    fireEvent.click(within(section).getByTitle("Rejeitar importação"));
    fireEvent.click(within(section).getByRole("button", { name: "Baixar relatório de reconciliação" }));
    fireEvent.click(within(section).getByRole("button", { name: "Exportar JSON" }));
    fireEvent.click(within(section).getByRole("button", { name: "Exportar CSV" }));

    await waitFor(() => expect(apiMocks.acceptClinicalReconciliationItem).toHaveBeenCalledWith(12, "condition:renal", "Conferido com fonte demo"));
    expect(apiMocks.rejectClinicalReconciliationItem).toHaveBeenCalledWith(12, "condition:renal", "Conferido com fonte demo");
    expect(apiMocks.rejectClinicalImport).toHaveBeenCalledWith(12, "Fonte externa inconsistente");
    expect(apiMocks.downloadReconciliationReport).toHaveBeenCalledWith(12);
    expect(apiMocks.exportImportJson).toHaveBeenCalledWith(12);
    expect(apiMocks.exportImportCsv).toHaveBeenCalledWith(12);
  });

  it("mostra CDS não persistente, falha explícita e menor privilégio", async () => {
    const { unmount } = renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Testar CDS demo" }));
    expect(await screen.findByText("Card determinístico")).toBeVisible();
    expect(apiMocks.checkCdsPrescription).toHaveBeenCalledWith(expect.objectContaining({ persist: false }));
    unmount();

    authMock.mockReturnValue({ can: () => false });
    apiMocks.importClinicalJson.mockRejectedValue(new Error("consentimento ausente"));
    renderPage();
    await screen.findByText(/hospital_demo/);
    expect(screen.queryByRole("button", { name: "Exportar JSON" })).not.toBeInTheDocument();
    expect(screen.queryByTitle("Aceitar importação")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Importar" }));
    expect(await screen.findByText(/Não foi possível importar/)).toBeVisible();
  });

  it("renderiza estado vazio sem fabricar lote", async () => {
    apiMocks.fetchClinicalImports.mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText("Nenhuma importação registrada.")).toBeVisible();
    expect(screen.queryByText(/Detalhes da importação/)).not.toBeInTheDocument();
  });
});
