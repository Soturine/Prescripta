import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import CohortBuilder, {
  initialCohortDefinition,
} from "../components/research/CohortBuilder";
import PopulationAnalytics from "../components/research/PopulationAnalytics";
import Evidence from "./Evidence";
import Pharmacy from "./Pharmacy";
import Research from "./Research";

const apiMocks = vi.hoisted(() => ({
  acknowledgeDataQualityFinding: vi.fn(),
  createAnalysisPlan: vi.fn(),
  createCohortVersion: vi.fn(),
  createConceptSet: vi.fn(),
  createEvidenceLink: vi.fn(),
  createEvidenceSource: vi.fn(),
  createOutcomeDefinition: vi.fn(),
  createPharmacyIntervention: vi.fn(),
  createResearchStudy: vi.fn(),
  createStudyProtocolVersion: vi.fn(),
  decidePharmacyIntervention: vi.fn(),
  executeAITask: vi.fn(),
  executeAnalysisPlan: vi.fn(),
  executeCohortVersion: vi.fn(),
  exportResearchPackage: vi.fn(),
  fetchConceptSets: vi.fn(),
  fetchDataQualityFindings: vi.fn(),
  fetchEvidenceLinks: vi.fn(),
  fetchEvidenceSources: vi.fn(),
  fetchPatientJourney: vi.fn(),
  fetchPatients: vi.fn(),
  fetchMedications: vi.fn(),
  fetchPharmacyInterventions: vi.fn(),
  fetchResearchStudies: vi.fn(),
  fetchResearchWorkspace: vi.fn(),
  fetchStudyWorkspace: vi.fn(),
  resolvePharmacyIntervention: vi.fn(),
  reviewAnalysisPlan: vi.fn(),
  reviewCohortVersion: vi.fn(),
  reviewConceptSetVersion: vi.fn(),
  reviewOutcomeDefinition: vi.fn(),
  reviewStudyProtocolVersion: vi.fn(),
  runDataQuality: vi.fn(),
}));
const authMock = vi.hoisted(() => vi.fn());

vi.mock("../services/api", () => apiMocks);
vi.mock("../context/AuthContext", () => ({ useAuth: authMock }));

const timestamp = "2026-08-08T12:00:00Z";
const study = {
  id: "study-1",
  institution_id: "demo",
  title: "Estudo sintético",
  slug: "estudo-sintetico",
  description: "Demo",
  research_question: "Qual o perfil da coorte sintética adulta?",
  objective: "Descrever agregados sintéticos com rastreabilidade.",
  design: "retrospective_cohort",
  status: "protocol_reviewed_demo",
  owner_user_id: 1,
  current_protocol_version_id: "protocol-1",
  demo_only: true,
  data_source_classification: "synthetic",
  archived_at: null,
  created_at: timestamp,
  updated_at: timestamp,
};
const run = {
  id: "run-1",
  study_id: "study-1",
  cohort_version_id: "cohort-1",
  protocol_version_id: "protocol-1",
  institution_id: "demo",
  data_snapshot_marker: "synthetic-v1",
  executed_at: timestamp,
  executed_by_user_id: 1,
  definition_hash: "a".repeat(64),
  source_version_refs: ["synthetic:v1"],
  result_count: 1,
  attrition: [
    { sequence: 1, criterion: { criterion: "age", operator: "gte", value: 18 }, label: "Adultos", before_count: 3, excluded_count: 1, after_count: 2, criterion_hash: "b".repeat(64) },
    { sequence: 2, criterion: { criterion: "condition", operator: "exists" }, label: "Condição demo", before_count: 2, excluded_count: 1, after_count: 1, criterion_hash: "c".repeat(64) },
  ],
  analytics: {
    n: 1,
    numeric: { age_years: { n: 1, missing: 0, mean: "48", sd: "0", median: "48", q1: "48", q3: "48", iqr: "0", min: "48", max: "48" } },
    categorical: { sex: { n: 1, missing: 0, categories: [{ value: "female", n: null, percent: null, suppressed: true }], small_cell_threshold: 5 } },
  },
  engine_version: "prescripta-cohort-deterministic-v2",
  prescripta_version: "0.9.1",
  status: "completed_demo",
  warnings: ["demo"],
  run_hash: "d".repeat(64),
  synthetic_demo_notice: "Dados sintéticos/demonstrativos.",
};
const concept = {
  id: "concept-1",
  institution_id: "demo",
  name: "Condição demo",
  domain: "condition",
  status: "approved_for_demo_study",
  owner_user_id: 1,
  reviewer_user_id: 2,
  current_version_id: "concept-version-1",
  created_at: timestamp,
  version: { id: "concept-version-1", concept_set_id: "concept-1", institution_id: "demo", version: 1, status: "approved_for_demo_study", terminology_versions: { "CID-10": "demo" }, include_descendants: false, source_refs: ["fixture:v1"], license_metadata: { fixture: true }, provenance: { demo: true }, definition_hash: "e".repeat(64), authored_by_user_id: 1, reviewed_by_user_id: 2, reviewed_at: timestamp, created_at: timestamp },
  members: [],
};
const protocol = {
  id: "protocol-1", study_id: "study-1", institution_id: "demo", version: 1,
  population: {}, exposure: {}, comparator: {}, outcome: {}, index_date: {}, washout: {}, follow_up: {}, censoring: {}, inclusion: [], exclusion: [], covariates: [], missing_data_strategy: {}, statistical_plan: {}, limitations: ["demo"], source_refs: ["synthetic:v1"], status: "reviewed_demo", definition_hash: "a".repeat(64), authored_by_user_id: 1, reviewed_by_user_id: 2, reviewed_at: timestamp, created_at: timestamp,
};
const cohortVersion = {
  id: "cohort-1", cohort_definition_id: "definition-1", study_id: "study-1", institution_id: "demo", version: 1,
  definition: { all: [{ criterion: "age", operator: "gte", value: 18 }], exclude: [] }, definition_hash: "f".repeat(64), status: "reviewed_demo", query_cost: 1, authored_by_user_id: 1, reviewed_by_user_id: 2, reviewed_at: timestamp, created_at: timestamp,
};
const outcome = {
  id: "outcome-1", study_id: "study-1", institution_id: "demo", name: "Outcome demo", domain: "condition", concept_set_version_ids: ["concept-version-1"], event_qualification: {}, observation_window: {}, temporal_relationship: "after_index", source_refs: ["synthetic:v1"], limitations: ["demo"], version: 1, review_status: "reviewed_demo", definition_hash: "g".repeat(64), authored_by_user_id: 1, reviewed_by_user_id: 2, reviewed_at: timestamp, created_at: timestamp,
};
const studyWorkspace = {
  study,
  protocol_versions: [protocol],
  cohort_versions: [cohortVersion],
  outcomes: [outcome],
  runs: [run],
  concept_set_version_ids: ["concept-version-1"],
  analysis_plans: [
    { id: "plan-draft", authored_by_user_id: 1, status: "draft", version: 1, definition_hash: "h".repeat(64) },
    { id: "plan-reviewed", authored_by_user_id: 1, status: "reviewed_demo", version: 2, definition_hash: "i".repeat(64) },
  ],
  analysis_runs: [
    { id: "analysis-run-1", executed_at: timestamp, content_hash: "j".repeat(64), results: run.analytics, provenance: { engine: "deterministic-v2" } },
  ],
  data_quality: {
    id: "dq-run-1",
    cohort_run_id: "run-1",
    data_snapshot_marker: "snapshot:synthetic-v1",
    data_snapshot_hash: "z".repeat(64),
    ruleset_version: "prescripta-data-quality-v3",
    scope_status: "scoped",
    content_hash: "q".repeat(64),
    analysis_blocked: false,
    dimensions: { completeness: 0, validity: 1, consistency: 0, conformance: 0 },
  },
  readiness: ["question", "protocol", "cohort", "outcome", "data_quality", "analysis_plan", "results", "evidence_package"].map((step, index) => ({ step, ready: index < 5 })),
  research_packages: [
    { id: "package-1", content_hash: "k".repeat(64), manifest: { aggregate_only: true } },
  ],
};

function BuilderHarness() {
  const [definition, setDefinition] = useState(initialCohortDefinition());
  return (
    <CohortBuilder
      conceptVersions={[{ id: "concept-version-1", label: "Condição demo" }]}
      onChange={setDefinition}
      value={definition}
    />
  );
}

function renderPage(node: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={client}>{node}</QueryClientProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  authMock.mockReturnValue({ can: () => true, user: { id: 9 } });
  apiMocks.fetchResearchWorkspace.mockResolvedValue({ studies: 1, concept_sets: 1, cohort_runs: 1, open_data_quality_findings: 1, recent_runs: [run], synthetic_demo_notice: "Research/RWE opera exclusivamente sobre dados sintéticos/demonstrativos." });
  apiMocks.fetchResearchStudies.mockResolvedValue([study]);
  apiMocks.fetchConceptSets.mockResolvedValue([concept]);
  apiMocks.fetchStudyWorkspace.mockResolvedValue(studyWorkspace);
  apiMocks.fetchDataQualityFindings.mockResolvedValue([{ id: "dq-1", run_id: "dq-run-1", institution_id: "demo", rule: "unknown_unit", severity: "high", resource_type: "timeline", resource_id: "1", field: "payload.unit", message: "Unidade desconhecida", source: "dq-v2", detected_at: timestamp, status: "open", resolution: null }]);
  apiMocks.executeAITask.mockResolvedValue({ output_payload: { status: "proposal_only_not_executed" } });
  apiMocks.runDataQuality.mockResolvedValue({ findings_created: 1, findings_open: 1, by_rule: { unknown_unit: 1 } });
  apiMocks.fetchEvidenceSources.mockResolvedValue([{ id: "source-1", institution_id: "demo", source_type: "other", title: "Fonte demo", identifier: "fixture:1", url: null, publisher: null, jurisdiction: "BR-demo", publication_date: null, access_date: null, source_version: "v1", review_status: "pending_review", reviewer_user_id: null, license_metadata: {}, content_hash: null, provenance: {}, created_by_user_id: 1, created_at: timestamp }]);
  apiMocks.fetchEvidenceLinks.mockResolvedValue([{ id: "link-1", institution_id: "demo", source_id: "source-1", target_type: "study", target_id: "study-1", relationship: "supports", locator: "section 1", review_status: "pending_review", created_by_user_id: 1, created_at: timestamp }]);
  apiMocks.fetchPharmacyInterventions.mockResolvedValue([{ id: 7, institution_id: "demo", patient_id: 4, medication_id: 3, pharmacist_user_id: 2, intervention_type: "dose", severity: "moderate", priority: "priority", problem: "Dose requer conferência humana.", recommendation: "Revisar dose com o prescritor.", source_refs: ["source:demo"], dose_snapshot: {}, status: "open", idempotency_key: "demo-key", version: 1, cosignature_required: false, cosigned_by_user_id: null, accepted: null, resolution: null, created_at: timestamp, updated_at: timestamp }]);
  apiMocks.fetchPatients.mockResolvedValue([{ id: 4, name: "Paciente autorizado" }]);
  apiMocks.fetchMedications.mockResolvedValue([{ id: 3, brand_name: "Medicamento demo", active_ingredient: "ingrediente demo" }]);
  apiMocks.decidePharmacyIntervention.mockResolvedValue({});
  for (const mock of Object.values(apiMocks)) if (!mock.getMockImplementation()) mock.mockResolvedValue({});
});

describe("Research & RWE", () => {
  it("mostra o fluxo profissional de coorte, análise, DQ, resultado, pacote e Copilot", async () => {
    renderPage(<Research />);
    expect(await screen.findByRole("heading", { name: "Estudo sintético" })).toBeVisible();
    expect(screen.getByText(/exclusivamente sobre dados sintéticos/)).toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Protocolo" }));
    fireEvent.click(screen.getByRole("button", { name: "Nova versão" }));
    await waitFor(() => expect(apiMocks.createStudyProtocolVersion).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Criar outcome demo" }));
    await waitFor(() => expect(apiMocks.createOutcomeDefinition).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("tab", { name: "Coorte" }));
    expect(await screen.findByRole("heading", { name: "Construtor de coorte" })).toBeVisible();
    expect(screen.getByText("DSL v2")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Salvar nova versão" }));
    await waitFor(() => expect(apiMocks.createCohortVersion).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Executar" }));
    await waitFor(() => expect(apiMocks.executeCohortVersion).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("tab", { name: "Resultados" }));
    expect(await screen.findByText("N = 1")).toBeVisible();
    expect(screen.getByText(/3 → 2/)).toBeVisible();
    fireEvent.click(screen.getByRole("tab", { name: "Análise" }));
    fireEvent.click(screen.getByRole("tab", { name: "Plano e qualidade" }));
    expect(await screen.findByText("Unidade desconhecida")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Executar checks" }));
    await waitFor(() => expect(apiMocks.runDataQuality).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Reconhecer achado" }));
    await waitFor(() => expect(apiMocks.acknowledgeDataQualityFinding).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Criar plano" }));
    await waitFor(() => expect(apiMocks.createAnalysisPlan).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Revisar demo" }));
    await waitFor(() => expect(apiMocks.reviewAnalysisPlan).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Executar" }));
    await waitFor(() => expect(apiMocks.executeAnalysisPlan).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("tab", { name: "Evidências" }));
    expect(await screen.findByRole("heading", { name: "Pacote de pesquisa" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Gerar pacote" }));
    await waitFor(() => expect(apiMocks.exportResearchPackage).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Gerar proposta" }));
    expect(await screen.findByText(/proposal_only_not_executed/)).toBeVisible();
  });

  it("cria estudo pelo wizard com slug normalizado", async () => {
    apiMocks.createResearchStudy.mockResolvedValue(study);
    renderPage(<Research />);
    fireEvent.click(
      await screen.findByRole("button", { name: /Novo estudo demonstrativo/ }),
    );
    fireEvent.change(screen.getByLabelText(/Título do estudo/), { target: { value: "Novo estudo sintético" } });
    fireEvent.change(screen.getByLabelText(/Slug do estudo/), { target: { value: "Novo Estudo 090" } });
    fireEvent.change(screen.getByLabelText(/Pergunta de pesquisa/), { target: { value: "Qual é o perfil agregado da coorte sintética?" } });
    fireEvent.change(screen.getByLabelText(/Objetivo/), { target: { value: "Descrever resultados sintéticos reprodutíveis." } });
    fireEvent.change(screen.getByLabelText(/Descrição/), { target: { value: "Fixture demonstrativa." } });
    fireEvent.click(screen.getByRole("button", { name: "Criar estudo" }));
    await waitFor(() =>
      expect(apiMocks.createResearchStudy).toHaveBeenCalledWith(
        expect.objectContaining({ slug: "novo-estudo-090" }),
        expect.anything(),
      ),
    );
  });

  it("edita, agrupa, ordena e limita critérios no construtor visual", () => {
    renderPage(<BuilderHarness />);
    fireEvent.click(screen.getAllByRole("button", { name: "Critério" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Grupo" })[0]);
    fireEvent.change(screen.getAllByLabelText("Tipo")[0], { target: { value: "condition" } });
    fireEvent.change(screen.getByLabelText("Conjunto de conceitos revisado"), { target: { value: "concept-version-1" } });
    fireEvent.change(screen.getAllByLabelText("Temporalidade")[0], { target: { value: "during_window" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Duplicar" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Mover para baixo" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Mover para cima" })[1]);
    fireEvent.click(screen.getAllByRole("button", { name: "Excluir" })[0]);
    expect(screen.getByText(/3\/30 critérios/)).toBeVisible();
  });

  it("mostra estados vazio e publicável da análise populacional", () => {
    const { rerender } = renderPage(<PopulationAnalytics />);
    expect(screen.getByText("Execute uma coorte para ver os resultados.")).toBeVisible();
    const publishable = {
      ...run,
      result_count: 8,
      analytics: {
        ...run.analytics,
        categorical: {
          sex: {
            n: 8,
            missing: 0,
            categories: [{ value: "female", n: 8, percent: "100", suppressed: false }],
            small_cell_threshold: 5,
          },
        },
      },
    };
    rerender(
      <QueryClientProvider client={new QueryClient()}>
        <PopulationAnalytics cohortRun={publishable as never} />
      </QueryClientProvider>,
    );
    expect(screen.getByText("8 (100%)")).toBeVisible();
  });

  it("respeita menor privilégio e estado vazio", async () => {
    authMock.mockReturnValue({ can: (capability: string) => capability.endsWith(".read"), user: { id: 9 } });
    apiMocks.fetchResearchStudies.mockResolvedValue([]);
    apiMocks.fetchConceptSets.mockResolvedValue([]);
    renderPage(<Research />);
    expect(await screen.findByText("Nenhum estudo criado.")).toBeVisible();
    expect(screen.queryByRole("button", { name: /Novo estudo/ })).not.toBeInTheDocument();
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
