import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Medication, MedicationCounselingSummary } from "../types/medication";
import Medications from "./Medications";

const apiMocks = vi.hoisted(() => ({
  bulkImportMedicationKnowledge: vi.fn(), createMedication: vi.fn(), fetchActiveIngredients: vi.fn(),
  fetchAdverseEffectTaxonomy: vi.fn(), fetchMedicationCounselingSummary: vi.fn(),
  fetchMedicationCurationQueue: vi.fn(), fetchMedications: vi.fn(), generateMedicationCounselingSummary: vi.fn(),
  lookupAnvisaSource: vi.fn(), lookupMedicationKnowledge: vi.fn(), reviewMedicationCounselingSummary: vi.fn(),
  reviewMedicationKnowledge: vi.fn(), searchMedicationCatalog: vi.fn(), updateMedication: vi.fn(),
}));
const authMock = vi.hoisted(() => vi.fn());
vi.mock("../services/api", () => apiMocks);
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

const ingredient = {
  id: 1, dcb_name: "dipirona", normalized_name: "dipirona", synonyms: ["metamizol"],
  therapeutic_classes: ["analgésico"], common_brands: ["Medicamento Demo"], jurisdiction: "BR",
  source: "Anvisa/DCB", validation_status: "pending_review", created_at: "2026-01-01", updated_at: "2026-01-01",
};

const medication = {
  id: 1, active_ingredient_id: 1, brand_name: "Medicamento Demo", active_ingredient: "dipirona",
  commercial_aliases: ["Alias Demo"], therapeutic_class: "analgésico", therapeutic_classes: ["analgésico"],
  source_jurisdiction: "BR", evidence_source_type: "Anvisa", validation_status: "pending_review",
  concentration: "500 mg/mL", pharmaceutical_form: "solução", evidence_source_url: null,
  max_daily_dose_mg: 4000, dose_mg_per_kg: 10, dose_by_weight_enabled: true, max_duration_days: 3,
  max_cumulative_dose_mg: null, continuous_use: false, monitoring_required: true,
  monitoring_notes: "Revisão demonstrativa", condition_specific_limits: {}, allowed_routes: ["oral"],
  contraindications: [], renal_caution: true, hepatic_caution: true, cardiac_caution: false,
  gastrointestinal_caution: false, elderly_caution: true, mechanism_of_action: null, absorption_notes: null,
  distribution_notes: null, metabolism_organs: ["fígado"], elimination_organs: ["rins"],
  renal_elimination_level: "moderado", hepatic_metabolism_level: "moderado", cyp_interactions: [],
  pharmacodynamic_notes: null, pharmacokinetic_notes: null, clinical_interpretation: null,
  neuropsychiatric_cautions: [], reproductive_cautions: [], organs_involved: ["rins"],
  relevant_adverse_effects: ["náusea"], structured_contraindications: [], therapeutic_action: "analgesia",
  alternative_group: null, related_medications: [], knowledge_source: "demo", notes: null,
} as Medication;

const summary = {
  id: 1, medication_id: 1, active_ingredient_id: 1, jurisdiction: "BR", generated_by: "fallback",
  validation_status: "pending_review", confidence: "moderada", requires_review: true,
  patient_friendly_summary: "Resumo fictício para orientação.", professional_summary: "Revisão humana obrigatória.",
  source_id: "anvisa-demo", source_name: "Anvisa", source_url: null, source_version: "demo", provider_name: null,
  main_adverse_effects: ["náusea"], patient_relevant_effects: [], activity_warnings: ["atenção ao dirigir"],
  driving_warning: true, machine_operation_warning: false, work_at_height_warning: false, fall_risk_warning: false,
  sedation_attention_warning: false, red_flags: ["sinal demo"], sleep_effects: [], appetite_weight_effects: [],
  mood_behavior_effects: [], libido_sexual_effects: [], neurologic_effects: [], tremor_warning: false,
  headache_warning: false, temperature_regulation_effects: [], blood_pressure_warning: false,
  gastrointestinal_effects: [], renal_effects: [], hepatic_effects: [], reproductive_contraceptive_effects: [],
  monitoring_required: [], extracted_evidence: [], created_at: "2026-07-29T12:00:00Z", updated_at: "2026-07-29T12:00:00Z",
} as MedicationCounselingSummary;

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><Medications /></QueryClientProvider>);
}

beforeEach(() => {
  authMock.mockReturnValue({ can: () => true });
  apiMocks.fetchMedications.mockResolvedValue([medication]);
  apiMocks.fetchActiveIngredients.mockResolvedValue([ingredient]);
  apiMocks.fetchAdverseEffectTaxonomy.mockResolvedValue([{ category: "neurológico", code: "headache", label: "Cefaleia" }]);
  apiMocks.fetchMedicationCurationQueue.mockResolvedValue([{ id: 3, query: "dipirona", source_name: "Anvisa", source_url: null, source_text_excerpt: "fonte", extracted_payload: { active_ingredient: "dipirona" }, provider: "fallback", model: null, validation_status: "pending", review_status: "pending_review", reviewed_by: null, created_by: 1 }]);
  apiMocks.searchMedicationCatalog.mockResolvedValue([{ query: "Novalgina", match_type: "brand_alias", active_ingredient: ingredient, matched_brands: ["Medicamento Demo"], drug_products: [], knowledge_sources: [] }]);
  apiMocks.lookupAnvisaSource.mockResolvedValue({ query: "Novalgina", source: "Anvisa", jurisdiction: "BR", status: "local_first", active_ingredient: "dipirona", commercial_matches: [], source_url: "https://consultas.anvisa.gov.br/", validation_status: "pending_review", guidance: "Confirme na fonte oficial." });
  apiMocks.fetchMedicationCounselingSummary.mockResolvedValue(summary);
  apiMocks.lookupMedicationKnowledge.mockResolvedValue({ id: 8, review_status: "pending_review" });
  apiMocks.bulkImportMedicationKnowledge.mockResolvedValue([]);
  apiMocks.reviewMedicationKnowledge.mockResolvedValue({});
  apiMocks.generateMedicationCounselingSummary.mockResolvedValue(summary);
  apiMocks.reviewMedicationCounselingSummary.mockResolvedValue({ ...summary, validation_status: "validated" });
  apiMocks.createMedication.mockResolvedValue(medication);
  apiMocks.updateMedication.mockResolvedValue(medication);
});

describe("catálogo de medicamentos", () => {
  it("expõe aliases, fonte e pendência em desktop e mobile", async () => {
    renderPage();
    expect((await screen.findAllByText("Medicamento Demo")).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Alias Demo/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Anvisa/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Não validado|pendente/).length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText("Filtrar"), { target: { value: "inexistente" } });
    expect(screen.getByRole("heading", { name: "Nenhum medicamento corresponde aos filtros" })).toBeVisible();
  });

  it("mantém estruturação e curadoria sob revisão humana", async () => {
    renderPage();
    await screen.findByText(/Alias comercial resolvido/);
    fireEvent.change(screen.getByLabelText("Texto da fonte"), { target: { value: "Texto de fonte fictícia" } });
    fireEvent.click(screen.getByRole("button", { name: "Estruturar fonte" }));
    fireEvent.click(screen.getByRole("button", { name: "Importar lote" }));
    fireEvent.click(screen.getByRole("button", { name: "Aprovar" }));
    await waitFor(() => expect(apiMocks.lookupMedicationKnowledge).toHaveBeenCalled());
    expect(apiMocks.bulkImportMedicationKnowledge).toHaveBeenCalled();
    expect(apiMocks.reviewMedicationKnowledge).toHaveBeenCalled();
    expect(await screen.findByText(/enviado para curadoria/)).toBeVisible();
  });

  it("abre orientação, gera, revisa e navega pela taxonomia", async () => {
    renderPage();
    await screen.findAllByText("Medicamento Demo");
    fireEvent.click(screen.getAllByRole("button", { name: /^Orientações$/ })[0]);
    expect(await screen.findByText("Resumo fictício para orientação.")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Gerar resumo" }));
    fireEvent.click(screen.getByRole("button", { name: "Aprovar resumo" }));
    fireEvent.click(screen.getByRole("button", { name: "Taxonomia" }));
    expect(screen.getByText("headache")).toBeVisible();
    await waitFor(() => expect(apiMocks.generateMedicationCounselingSummary).toHaveBeenCalled());
    expect(apiMocks.reviewMedicationCounselingSummary).toHaveBeenCalled();
  });

  it("diferencia erro, vazio e perfil somente leitura", async () => {
    apiMocks.fetchMedications.mockRejectedValue(new Error("offline"));
    authMock.mockReturnValue({ can: () => false });
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent("Não foi possível carregar o catálogo");
    expect(screen.queryByRole("heading", { name: "Novo medicamento" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
  });
});
