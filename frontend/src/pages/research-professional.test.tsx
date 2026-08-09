import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Evidence from "./Evidence";
import Pharmacy from "./Pharmacy";
import Research from "./Research";

const apiMocks = vi.hoisted(() => ({
  createCohortVersion: vi.fn(), createConceptSet: vi.fn(), createEvidenceLink: vi.fn(), createEvidenceSource: vi.fn(), createOutcomeDefinition: vi.fn(), createPharmacyIntervention: vi.fn(), createResearchStudy: vi.fn(), createStudyProtocolVersion: vi.fn(), decidePharmacyIntervention: vi.fn(), executeAITask: vi.fn(), executeCohortVersion: vi.fn(), fetchConceptSets: vi.fn(), fetchDataQualityFindings: vi.fn(), fetchEvidenceLinks: vi.fn(), fetchEvidenceSources: vi.fn(), fetchPharmacyInterventions: vi.fn(), fetchResearchStudies: vi.fn(), fetchResearchWorkspace: vi.fn(), fetchStudyWorkspace: vi.fn(), resolvePharmacyIntervention: vi.fn(), reviewCohortVersion: vi.fn(), reviewConceptSetVersion: vi.fn(), reviewStudyProtocolVersion: vi.fn(), runDataQuality: vi.fn(),
}));
const authMock = vi.hoisted(() => vi.fn());

vi.mock("../services/api", () => apiMocks);
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

const study = {
  id: "study-1", institution_id: "demo", title: "Estudo sintético", slug: "estudo-sintetico", description: "Demo", research_question: "Qual o perfil da coorte sintética adulta?", objective: "Descrever agregados sintéticos com rastreabilidade.", design: "retrospective_cohort", status: "protocol_reviewed_demo", owner_user_id: 1, current_protocol_version_id: "protocol-1", demo_only: true, data_source_classification: "synthetic", archived_at: null, created_at: "2026-08-08T12:00:00Z", updated_at: "2026-08-08T12:00:00Z",
};
const run = {
  id: "run-1", study_id: "study-1", cohort_version_id: "cohort-1", protocol_version_id: "protocol-1", institution_id: "demo", data_snapshot_marker: "synthetic-v1", executed_at: "2026-08-08T12:00:00Z", executed_by_user_id: 1, definition_hash: "a".repeat(64), source_version_refs: ["synthetic:v1"], result_count: 1, attrition: [{ sequence: 1, criterion: { criterion: "age", operator: "gte", value: 18 }, label: "Adultos", before_count: 3, excluded_count: 1, after_count: 2, criterion_hash: "b".repeat(64) }, { sequence: 2, criterion: { criterion: "condition", operator: "exists" }, label: "Condição demo", before_count: 2, excluded_count: 1, after_count: 1, criterion_hash: "c".repeat(64) }], analytics: { n: 1 }, engine_version: "engine-v1", prescripta_version: "0.8.8", status: "completed_demo", warnings: ["demo"], run_hash: "d".repeat(64), synthetic_demo_notice: "Dados sintéticos/demonstrativos.",
};
const concept = {
  id: "concept-1", institution_id: "demo", name: "Condição demo", domain: "condition", status: "approved_for_demo_study", owner_user_id: 1, reviewer_user_id: 2, current_version_id: "concept-version-1", created_at: "2026-08-08T12:00:00Z", version: { id: "concept-version-1", concept_set_id: "concept-1", institution_id: "demo", version: 1, status: "approved_for_demo_study", terminology_versions: { "CID-10": "demo" }, include_descendants: false, source_refs: ["fixture:v1"], license_metadata: { fixture: true }, provenance: { demo: true }, definition_hash: "e".repeat(64), authored_by_user_id: 1, reviewed_by_user_id: 2, reviewed_at: "2026-08-08T12:00:00Z", created_at: "2026-08-08T12:00:00Z" }, members: [],
};
const studyWorkspace = {
  study,
  protocol_versions: [{ id: "protocol-1", study_id: "study-1", institution_id: "demo", version: 1, population: {}, exposure: {}, comparator: {}, outcome: {}, index_date: {}, washout: {}, follow_up: {}, censoring: {}, inclusion: [], exclusion: [], covariates: [], missing_data_strategy: {}, statistical_plan: {}, limitations: ["demo"], source_refs: ["synthetic:v1"], status: "reviewed_demo", definition_hash: "a".repeat(64), authored_by_user_id: 1, reviewed_by_user_id: 2, reviewed_at: "2026-08-08T12:00:00Z", created_at: "2026-08-08T12:00:00Z" }],
  cohort_versions: [{ id: "cohort-1", cohort_definition_id: "definition-1", study_id: "study-1", institution_id: "demo", version: 1, definition: { all: [{ criterion: "age", operator: "gte", value: 18 }], exclude: [] }, definition_hash: "f".repeat(64), status: "reviewed_demo", query_cost: 1, authored_by_user_id: 1, reviewed_by_user_id: 2, reviewed_at: "2026-08-08T12:00:00Z", created_at: "2026-08-08T12:00:00Z" }],
  outcomes: [{ id: "outcome-1", study_id: "study-1", institution_id: "demo", name: "Outcome demo", domain: "condition", concept_set_version_ids: ["concept-version-1"], event_qualification: {}, observation_window: {}, temporal_relationship: "after_index", source_refs: ["synthetic:v1"], limitations: ["demo"], version: 1, review_status: "pending_review", definition_hash: "g".repeat(64), authored_by_user_id: 1, reviewed_by_user_id: null, created_at: "2026-08-08T12:00:00Z" }],
  runs: [run], concept_set_version_ids: ["concept-version-1"],
};

function renderPage(node: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}>{node}</QueryClientProvider>);
}

beforeEach(() => {
  authMock.mockReturnValue({ can: () => true, user: { id: 9 } });
  apiMocks.fetchResearchWorkspace.mockResolvedValue({ studies: 1, concept_sets: 1, cohort_runs: 1, open_data_quality_findings: 1, recent_runs: [run], synthetic_demo_notice: "Research/RWE opera exclusivamente sobre dados sintéticos/demonstrativos." });
  apiMocks.fetchResearchStudies.mockResolvedValue([study]);
  apiMocks.fetchConceptSets.mockResolvedValue([concept]);
  apiMocks.fetchStudyWorkspace.mockResolvedValue(studyWorkspace);
  apiMocks.fetchDataQualityFindings.mockResolvedValue([{ id: "dq-1", institution_id: "demo", rule: "unknown_unit", severity: "high", resource_type: "timeline", resource_id: "1", field: "payload.unit", message: "Unidade desconhecida", source: "dq-v1", detected_at: "2026-08-08T12:00:00Z", status: "open", resolution: null }]);
  apiMocks.executeAITask.mockResolvedValue({ output_payload: { status: "proposal_only_not_executed" } });
  apiMocks.runDataQuality.mockResolvedValue({ findings_created: 1, findings_open: 1, by_rule: { unknown_unit: 1 } });
  apiMocks.fetchEvidenceSources.mockResolvedValue([{ id: "source-1", institution_id: "demo", source_type: "other", title: "Fonte demo", identifier: "fixture:1", url: null, publisher: null, jurisdiction: "BR-demo", publication_date: null, access_date: null, source_version: "v1", review_status: "pending_review", reviewer_user_id: null, license_metadata: {}, content_hash: null, provenance: {}, created_by_user_id: 1, created_at: "2026-08-08T12:00:00Z" }]);
  apiMocks.fetchEvidenceLinks.mockResolvedValue([{ id: "link-1", institution_id: "demo", source_id: "source-1", target_type: "study", target_id: "study-1", relationship: "supports", locator: "section 1", review_status: "pending_review", created_by_user_id: 1, created_at: "2026-08-08T12:00:00Z" }]);
  apiMocks.fetchPharmacyInterventions.mockResolvedValue([{ id: 7, institution_id: "demo", patient_id: 4, medication_id: 3, pharmacist_user_id: 2, intervention_type: "dose", severity: "moderate", priority: "priority", problem: "Dose requer conferência humana.", recommendation: "Revisar dose com o prescritor.", source_refs: ["source:demo"], dose_snapshot: {}, status: "open", idempotency_key: "demo-key", version: 1, cosignature_required: false, cosigned_by_user_id: null, accepted: null, resolution: null, created_at: "2026-08-08T12:00:00Z", updated_at: "2026-08-08T12:00:00Z" }]);
  apiMocks.decidePharmacyIntervention.mockResolvedValue({});
  for (const mock of Object.values(apiMocks)) if (!mock.getMockImplementation()) mock.mockResolvedValue({});
});

describe("Research & RWE", () => {
  it("mostra workflow, builder, attrition, provenance, DQ e proposta de IA", async () => {
    renderPage(<Research />);
    expect(await screen.findByRole("heading", { name: "Estudo sintético" })).toBeVisible();
    expect(screen.getByText(/exclusivamente sobre dados sintéticos/)).toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Cohort" }));
    expect(await screen.findByRole("heading", { name: "Cohort Builder" })).toBeVisible();
    expect(screen.getByText(/JSON avançado/)).toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Runs" }));
    expect(await screen.findByText("N = 1")).toBeVisible();
    expect(screen.getByText(/3 → 2/)).toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Provenance" }));
    expect(await screen.findByRole("heading", { name: "Provenance" })).toBeVisible();
    expect(screen.getByText("Unidade não reconhecida")).toBeVisible();
    expect(screen.getByText("unknown_unit")).not.toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Overview" }));
    fireEvent.click(screen.getByRole("button", { name: "Estruturar pergunta" }));
    expect(await screen.findByText(/proposal_only_not_executed/)).toBeVisible();
  });

  it("respeita menor privilégio e estado vazio", async () => {
    authMock.mockReturnValue({ can: (capability: string) => capability.endsWith(".read"), user: { id: 9 } });
    apiMocks.fetchResearchStudies.mockResolvedValue([]);
    apiMocks.fetchConceptSets.mockResolvedValue([]);
    renderPage(<Research />);
    expect(await screen.findByText("Nenhum estudo criado.")).toBeVisible();
    expect(screen.queryByRole("button", { name: /Criar study/ })).not.toBeInTheDocument();
  });
});

describe("Evidence e Pharmacy", () => {
  it("renderiza apenas fontes/vínculos reais e cria source", async () => {
    renderPage(<Evidence />);
    expect(await screen.findByRole("heading", { name: "Fonte demo" })).toBeVisible();
    expect(screen.getByText(/study:study-1/)).toBeVisible();
    fireEvent.change(screen.getByLabelText("Título da fonte"), { target: { value: "Nova fonte demo" } });
    fireEvent.change(screen.getByLabelText("Identificador da fonte"), { target: { value: "fixture:2" } });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    await waitFor(() => expect(apiMocks.createEvidenceSource).toHaveBeenCalled());
  });

  it("mantém decisão farmacêutica explícita e versionada", async () => {
    renderPage(<Pharmacy />);
    expect(await screen.findByText(/Dose requer conferência/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Aceitar" }));
    await waitFor(() => expect(apiMocks.decidePharmacyIntervention).toHaveBeenCalledWith(7, "accepted", expect.any(String), 1));
  });
});
