import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { PrescriptionCheckResult } from "../types/prescription";
import PrescriptionCheck from "./PrescriptionCheck";

const apiMocks = vi.hoisted(() => ({
  checkPrescription: vi.fn(), downloadPatientGuidanceReport: vi.fn(), downloadPrescriptionTechnicalReport: vi.fn(),
  explainPrescription: vi.fn(), exportPrescriptionJson: vi.fn(), fetchMedications: vi.fn(), fetchPatients: vi.fn(),
  fetchPrescriptionEvidence: vi.fn(), fetchPrescriptionReportPreview: vi.fn(), fetchPrescriptionTimeline: vi.fn(),
  requestDecisionOverride: vi.fn(),
}));
const authMock = vi.hoisted(() => vi.fn());
vi.mock("../services/api", () => apiMocks);
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

const alert = { code: "DOSE_DEMO", title: "Dose requer revisão", description: "Achado determinístico fictício", severity: "alto", recommendation: "Revisar cálculo" } as const;

const result = {
  decision: {
    schema_version: "1", decision_status: "review_required", legacy_status: "atencao", highest_severity: "alto",
    coverage: { status: "partially_covered", sufficient: false, evaluated: ["dose"], not_evaluated: [{ module: "interaction" }], reasons: ["fonte pendente"], source_ids: ["rule-demo"] },
    findings: [{ ...alert, module: "dose", source_ids: ["rule-demo"], hard_block: false }],
    required_actions: ["Revisar dose com segundo profissional"], missing_data: ["creatinina"], rule_versions: ["dose-v1"], source_snapshot: [],
    override_policy: { allowed: true, reason_required: true, second_reviewer_role: "medico", policy_status: "active", note: "Segundo revisor obrigatório" },
    human_review_required: true, evaluated_at: "2026-07-29T12:00:00Z", correlation_id: "corr-demo", recommendation: "Revisão necessária antes de prosseguir.",
  },
  coverage_status: "partially_covered", status: "atencao", risk_level: "alto", alerts: [alert],
  recommendation: "Revisar antes de administrar.", human_review_required: true, audit_id: 21,
  dose_summary: {
    daily_total_mg: 200, duration_days: 3, estimated_cumulative_dose_mg: 600, max_daily_dose_mg: 400,
    max_duration_days: 5, max_cumulative_dose_mg: 2000, continuous_use: false, monitoring_required: true,
    monitoring_notes: "Monitorar", exposure_plan: { dose_per_administration_mg: 100, administrations_per_day: 2, calculated_daily_dose_mg: 200, calculated_cumulative_dose_mg: 600, has_missing_duration_for_cumulative_dose: false },
    mechanism_profile: { mechanism_of_action: "demo", absorption_notes: null, distribution_notes: null, metabolism_organs: ["fígado"], elimination_organs: ["rins"], renal_elimination_level: "moderado", hepatic_metabolism_level: "moderado", cyp_interactions: [], pharmacodynamic_notes: null, pharmacokinetic_notes: null, clinical_interpretation: null },
    condition_specific_limits: {}, weight_based_rule: { enabled: true, dose_mg_per_kg: 10, patient_weight_kg: 70, calculated_limit_mg_per_day: 700, calculated_daily_dose_mg: 200, was_considered: true },
    anthropometrics: { age: 46, age_group: "adult", weight_kg: 70, height_cm: 165, bmi: 25.7, bmi_considered: true },
  },
  compatibility: { level: "moderada", score: 60, patient_factors_considered: ["peso"], medication_factors_considered: ["dose"], reasons: ["fonte pendente"], review_required: true, educational_notice: "Demo" },
  patient_factors_considered: ["peso 70 kg"], medication_factors_considered: ["limite diário"],
  rag_evidence: [{ source: "Anvisa", excerpt: "Trecho fictício", score: 0.8, matched_terms: ["dose"], educational_notice: "Educacional", jurisdiction: "BR", source_name: "Anvisa", source_url: null, evidence_type: "bula", validation_status: "pending_review", active_ingredient: "substância demo", commercial_names: [], extracted_sections: [], retrieved_at: null, version: "demo" }],
  clinical_context_graph: { nodes: [{ id: "patient", label: "Paciente Demo", type: "patient" }], edges: [], patient_factors: ["peso"], medication_factors: ["dose"] },
  alternatives: [{ medication_id: 2, name: "Alternativa Demo", active_ingredient: "substância B", therapeutic_class: "classe", similarity_reason: "mesmo grupo", status: "liberado", risk_level: "baixo", top_alerts: [], observation: "Passou pelo motor" }],
  patient_counseling: { summary: null, orientation_points: ["Orientação fictícia"], red_flags: [], source_label: "fallback", review_status: "pending_review", generated_by_ai: false, requires_review: true, functional_context: { profile_known: false, unknown_fields: ["drives"], personalized_warnings: [], generic_warnings: ["Cautela em atividades"], question: { should_ask: true, question: "Dirige regularmente?", options: ["Sim", "Não"], reason: "sedação" } }, missing_data_mode: { incomplete_history: true, message: "Histórico incompleto", limitation_summary: "Cobertura limitada", missing_data: ["creatinina"], does_not_block_flow: true }, educational_notice: "Orientação educacional" },
  missing_data_mode: { incomplete_history: true, message: "Histórico incompleto", limitation_summary: "Cobertura limitada", missing_data: ["creatinina"], does_not_block_flow: true },
  contextual_question: { should_ask: true, question: "Dirige regularmente?", options: ["Sim", "Não"], reason: "sedação" },
  patient_knowledge_bundle: { reviewed_documents: [{}], timeline: [{}] },
  clinical_view: { status: "atencao", risk_level: "alto", primary_recommendation: "Revisar", patient_data_considered: [{ label: "Peso", value: "70 kg" }], missing_data: ["creatinina"], relevant_alerts: [{ ...alert }], technical_details_available: true },
  technical_details: {},
  dose_intelligence: { status: "review_required", calculated_dose: 200, calculated_unit: "mg/day", calculation_formula: "100 × 2", calculation_basis: "structured", usual_range: { low: 100, high: 300 }, max_limits: { daily: 400 }, alerts: [], missing_data: [], validation_status: "validated", requires_human_review: true, educational_notice: "Cálculo determinístico" },
  psychotropic_safety: [{ code: "PSY-DEMO", title: "Atenção à sedação", description: "Demo", severity: "moderado", recommendation: "Revisar", policy_status: "pending", source_ids: ["rule-demo"] }],
  prescribing_policy: { status: "review_required", prescriber_profile: {}, required_specialties: [], recommended_specialties: [], prescription_form_requirements: [], warnings: ["Política demonstrativa"], institutional_notes: [], source_refs: ["policy-demo"], requires_human_review: true, educational_notice: "Demo" },
} as unknown as PrescriptionCheckResult;

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><PrescriptionCheck /></QueryClientProvider>);
}

beforeEach(() => {
  authMock.mockReturnValue({ can: () => true });
  apiMocks.fetchPatients.mockResolvedValue([{ id: 7, name: "Paciente Demo", clinical_profile_completeness_score: 88 }]);
  apiMocks.fetchMedications.mockResolvedValue([{ id: 1, brand_name: "Medicamento Demo", active_ingredient: "substância demo", source_jurisdiction: "BR", evidence_source_type: "Anvisa", validation_status: "pending_review" }]);
  apiMocks.checkPrescription.mockResolvedValue(result);
  apiMocks.explainPrescription.mockResolvedValue({ provider: "fallback", model: null, used_fallback: true, simple_explanation: "Explicação simples fictícia", technical_summary: "Resumo técnico", review_questions: ["Confirmar dose?"], educational_notice: "IA não decide", prescription_status: "atencao", risk_level: "alto", critical_alert_codes: [], missing_patient_data: ["creatinina"], rag_sources: ["rule-demo"], how_to_explain_to_patient: "Orientar revisão" });
  apiMocks.fetchPrescriptionReportPreview.mockResolvedValue({ report_mode: "complete_internal", evidence_bundle_hash: "hash-demo", narrative: { executive_summary: "Resumo do bundle", confidence: 0.8 }, narrative_metadata: { fallback_used: true, provider: "fallback", model: null } });
  apiMocks.fetchPrescriptionEvidence.mockResolvedValue([{ code: "DOSE_DEMO", severity: "alto", jurisdiction: "BR", evidence_type: "rule", validation_status: "validated", evidence_summary: "Regra determinística" }]);
  apiMocks.fetchPrescriptionTimeline.mockResolvedValue([{ order: 1, title: "Checagem", status: "completed" }]);
  apiMocks.downloadPrescriptionTechnicalReport.mockResolvedValue(undefined);
  apiMocks.downloadPatientGuidanceReport.mockResolvedValue(undefined);
  apiMocks.exportPrescriptionJson.mockResolvedValue(undefined);
  apiMocks.requestDecisionOverride.mockResolvedValue({ id: 1 });
});

describe("checagem de prescrição", () => {
  it("persiste decisão antes de liberar IA e distingue cobertura", async () => {
    renderPage();
    expect(screen.queryByRole("button", { name: "Explicar com IA" })).not.toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Executar checagem" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Revisão necessária");
    expect(screen.getByText("Cobertura: parcial")).toBeVisible();
    expect(screen.getByText("Revisar dose com segundo profissional")).toBeVisible();
    expect(apiMocks.checkPrescription).toHaveBeenCalled();
  });

  it("mostra detalhes técnicos, evidências e explicação por audit_id", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Executar checagem" }));
    await screen.findByText("Revisão necessária antes de prosseguir.");
    fireEvent.click(screen.getByRole("button", { name: "Modo técnico" }));
    expect(await screen.findByText("Evidências da decisão")).toBeVisible();
    expect(screen.getByText("Linha do tempo da decisão")).toBeVisible();
    expect(screen.getByText("Resumo do relatório")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Explicar com IA" }));
    expect(await screen.findByText("Explicação simples fictícia")).toBeVisible();
    expect(apiMocks.explainPrescription).toHaveBeenCalledWith({ audit_id: 21 }, expect.anything());
  });

  it("exporta, anonimiza e solicita override com segundo revisor", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Executar checagem" }));
    await screen.findByText("Revisão necessária antes de prosseguir.");
    fireEvent.click(screen.getByLabelText("Dados anonimizados"));
    fireEvent.click(screen.getByRole("button", { name: "Baixar relatório técnico" }));
    fireEvent.click(screen.getByRole("button", { name: "Baixar orientação ao paciente" }));
    fireEvent.click(screen.getByRole("button", { name: "Exportar JSON" }));
    fireEvent.click(screen.getByRole("button", { name: "Solicitar override" }));
    const dialog = screen.getByRole("dialog", { name: "Solicitar override clínico" });
    fireEvent.change(within(dialog).getByRole("textbox", { name: /Justificativa clínica/ }), { target: { value: "Justificativa clínica fictícia" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Registrar solicitação" }));
    await waitFor(() => expect(apiMocks.requestDecisionOverride).toHaveBeenCalledWith(21, "Justificativa clínica fictícia"));
    expect(apiMocks.downloadPrescriptionTechnicalReport).toHaveBeenCalledWith(21, true);
    expect(apiMocks.downloadPatientGuidanceReport).toHaveBeenCalledWith(21);
  });

  it("reexecuta contexto funcional sem apagar o payload dimensional", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Executar checagem" }));
    await screen.findByText("Dirige regularmente?");
    fireEvent.click(screen.getByRole("button", { name: "Sim" }));
    await waitFor(() => expect(apiMocks.checkPrescription).toHaveBeenCalledTimes(2));
    expect(apiMocks.checkPrescription.mock.calls[1][0]).toMatchObject({ contextual_activity_answer: "Sim", dose: { amount: 100 } });
  });

  it("não presume decisão em erro ou ausência de catálogo", async () => {
    apiMocks.checkPrescription.mockRejectedValue(new Error("backend recusou"));
    const { unmount } = renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Executar checagem" }));
    expect(await screen.findByText("A checagem não foi executada")).toBeVisible();
    unmount();
    apiMocks.fetchPatients.mockResolvedValue([]);
    renderPage();
    expect(await screen.findByRole("heading", { name: "Cadastre ao menos um paciente e um medicamento" })).toBeVisible();
  });
});
