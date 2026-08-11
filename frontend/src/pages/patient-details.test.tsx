import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Patient } from "../types/patient";
import PatientDetails from "./PatientDetails";

const apiMocks = vi.hoisted(() => ({
  createPatientAccessGrant: vi.fn(), createPatientDocument: vi.fn(), extractPatientDocument: vi.fn(),
  fetchPatient: vi.fn(), fetchPatientAccessGrants: vi.fn(), fetchPatientCareTeam: vi.fn(),
  fetchPatientClinicalContext: vi.fn(), fetchPatientDocuments: vi.fn(), fetchPatientFunctionalProfile: vi.fn(),
  fetchPatientKnowledgeBundle: vi.fn(), fetchPatientPsychologicalContext: vi.fn(), fetchPatientTimeline: vi.fn(),
  quickTriagePatient: vi.fn(), reviewPatientDocumentExtraction: vi.fn(), revokePatientAccessGrant: vi.fn(),
  updatePatient: vi.fn(), updatePatientFunctionalProfile: vi.fn(), updatePatientPsychologicalContext: vi.fn(),
}));
const authMock = vi.hoisted(() => vi.fn());
vi.mock("../services/api", () => apiMocks);
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

const patient = {
  id: 7, name: "Paciente Workspace", birth_date: "1980-01-01", age: 46, weight_kg: 70,
  height_cm: 165, sex_for_dosing_calculation: "female", phone: null, email: null, mother_name: null,
  allergies: ["substância demo"], comorbidities: ["hipertensão"], current_medications: ["medicamento demo"],
  renal_condition: "renal_normal", hepatic_condition: null, cardiac_condition: null, gastrointestinal_history: null,
  hypertension: true, diabetes: false, pregnancy_or_lactation: false, mental_health_factors: ["adesão"],
  reproductive_gynecologic_factors: [], adverse_reactions: [], clinical_notes: "Nota fictícia",
  clinical_profile_reviewed_at: null, clinical_profile_completeness_score: 88, clinical_profile_badge: "Adequado",
  identifiers: [], possible_duplicate_matches: [],
} as Patient;

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/patients/7"]}><Routes><Route path="/patients/:patientId" element={<PatientDetails />} /></Routes></MemoryRouter></QueryClientProvider>);
}

beforeEach(() => {
  authMock.mockReturnValue({ can: () => true });
  apiMocks.fetchPatient.mockResolvedValue(patient);
  apiMocks.fetchPatientClinicalContext.mockResolvedValue({ patient_id: 7, patient_name: patient.name, nodes: [{ id: "patient", label: patient.name, type: "patient" }], edges: [], clinical_profile_completeness_score: 88, educational_notice: "Demo" });
  apiMocks.fetchPatientFunctionalProfile.mockResolvedValue({
    id: 1, patient_id: 7, drives_regularly: true, professional_driver: false, operates_machinery: null,
    works_at_height: false, fall_risk_activity: null, night_shift: false, caregiver_responsibility: true,
    high_attention_activity: true, frequent_alcohol_use: false, history_of_falls: false,
    low_tolerance_to_sedation_or_dizziness: null, source: "patient_reported", notes: "Fictício",
    last_reviewed_at: null, created_at: null, updated_at: null, unknown_fields: ["operates_machinery"], educational_notice: "Demo",
  });
  apiMocks.fetchPatientDocuments.mockResolvedValue([{ id: 2, patient_id: 7, document_type: "clinical_note", title: "Laudo fictício", summary: "Resumo", source_type: "manual_text", source_system: "prescripta", document_date: null, uploaded_at: "2026-07-29", raw_text: "Texto", structured_payload: {}, extracted_entities: { allergy: "demo" }, confidence: 0.9, validation_status: "pending", review_status: "pending_review", file_hash: null, storage_path: null }]);
  apiMocks.fetchPatientTimeline.mockResolvedValue([{ id: 1, title: "Cadastro", event_type: "patient.created" }]);
  apiMocks.fetchPatientKnowledgeBundle.mockResolvedValue({ reviewed_documents: [{}], reviewed_extractions: [{}], medication_history: [], missing_data: ["creatinina"] });
  apiMocks.fetchPatientPsychologicalContext.mockResolvedValue({ id: 4, patient_id: 7, purpose: "treatment", medication_safety_factors: ["adesão"], confidential_notes: "Nota confidencial fictícia", consent_status: "recorded", policy_reference: "POL-DEMO", updated_by_user_id: 3, created_at: "2026-01-01", updated_at: "2026-07-29" });
  apiMocks.fetchPatientAccessGrants.mockResolvedValue([{ id: 5, patient_id: 7, user_id: 2, institution_id: "demo", capability: "patient.read", purpose: "treatment", reason: "Equipe assistencial", starts_at: "2026-01-01", expires_at: null, revoked_at: null, status: "active", care_episode_id: null }]);
  apiMocks.fetchPatientCareTeam.mockResolvedValue([{ id: 6, patient_id: 7, user_id: 3, institution_id: "demo", team_code: "equipe-demo", care_role: "farmacêutico", capabilities: ["patient.read"], purpose: "treatment", starts_at: "2026-01-01", expires_at: null, revoked_at: null }]);
  apiMocks.extractPatientDocument.mockResolvedValue({ id: 9, provider: "fallback", confidence: 0.8, extracted_entities: { allergy: "demo" } });
  apiMocks.reviewPatientDocumentExtraction.mockResolvedValue({});
  apiMocks.createPatientDocument.mockResolvedValue({});
  apiMocks.updatePatientPsychologicalContext.mockResolvedValue({});
  apiMocks.createPatientAccessGrant.mockResolvedValue({});
  apiMocks.revokePatientAccessGrant.mockResolvedValue({});
  apiMocks.updatePatient.mockResolvedValue(patient);
  apiMocks.quickTriagePatient.mockResolvedValue(patient);
  apiMocks.updatePatientFunctionalProfile.mockResolvedValue({});
});

describe("workspace do paciente", () => {
  it("segmenta perfil, documentos, contexto sensível e vínculo", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "Paciente Workspace" })).toBeVisible();
    expect(screen.getByRole("navigation", { name: "Seções do paciente" })).toBeVisible();
    expect(screen.getByText("Contexto psicológico segmentado")).toBeVisible();
    expect(screen.getByText("Nota confidencial fictícia")).toBeVisible();
    expect(screen.getByText("Profissional #2")).toBeVisible();
    expect(screen.getByText("equipe-demo · patient.read")).toBeVisible();
    expect(screen.getByText(/Dados faltantes: creatinina/)).toBeVisible();
  });

  it("salva somente o segmento psicológico minimizado", async () => {
    renderPage();
    await screen.findByText("Contexto psicológico segmentado");
    fireEvent.change(screen.getByRole("textbox", { name: /Fatores de segurança medicamentosa/ }), { target: { value: "adesão, sedação" } });
    fireEvent.change(screen.getByRole("textbox", { name: /Notas confidenciais/ }), { target: { value: "Conteúdo fictício" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar segmento protegido" }));
    await waitFor(() => expect(apiMocks.updatePatientPsychologicalContext).toHaveBeenCalledWith(7, expect.objectContaining({ medication_safety_factors: ["adesão", "sedação"], confidential_notes: "Conteúdo fictício" })));
  });

  it("concede e revoga grant com motivo auditável", async () => {
    renderPage();
    await screen.findByText("Equipe, vínculo e grants");
    fireEvent.change(screen.getByLabelText("ID do profissional"), { target: { value: "8" } });
    fireEvent.change(screen.getByLabelText("Capacidade"), { target: { value: "patient.write" } });
    fireEvent.change(screen.getByLabelText("Motivo do vínculo"), { target: { value: "Atendimento temporário" } });
    fireEvent.click(screen.getByRole("button", { name: "Conceder acesso" }));
    await waitFor(() => expect(apiMocks.createPatientAccessGrant).toHaveBeenCalledWith(7, expect.objectContaining({ user_id: 8, capability: "patient.write" })));

    fireEvent.click(screen.getByRole("button", { name: "Revogar grant" }));
    const dialog = screen.getByRole("dialog", { name: "Revogar acesso ao paciente" });
    fireEvent.change(within(dialog).getByLabelText("Motivo da revogação"), { target: { value: "Fim do atendimento" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Confirmar revogação" }));
    await waitFor(() => expect(apiMocks.revokePatientAccessGrant).toHaveBeenCalledWith(5, "Fim do atendimento"));
  });

  it("extrai documento mas exige aceite humano", async () => {
    renderPage();
    await screen.findByText("Laudo fictício");
    fireEvent.click(screen.getByRole("button", { name: "Extrair dados" }));
    expect(await screen.findByText("Extração pendente de revisão")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Aceitar itens" }));
    await waitFor(() => expect(apiMocks.reviewPatientDocumentExtraction).toHaveBeenCalled());
  });

  it("não consulta nem mostra conteúdo sensível sem capacidade", async () => {
    authMock.mockReturnValue({ can: (capability: string) => capability === "patient.read" });
    renderPage();
    expect(await screen.findByText("Segmento psicológico protegido")).toBeVisible();
    expect(screen.getByText(/Nenhum conteúdo sensível foi consultado/)).toBeVisible();
    expect(apiMocks.fetchPatientPsychologicalContext).not.toHaveBeenCalled();
    expect(apiMocks.fetchPatientAccessGrants).not.toHaveBeenCalled();
    expect(screen.getByText("Vínculo assistencial aplicado")).toBeVisible();
  });

  it("distingue registro inexistente", async () => {
    apiMocks.fetchPatient.mockResolvedValue(null);
    renderPage();
    expect(await screen.findByText("Paciente não encontrado.")).toBeVisible();
  });
});
