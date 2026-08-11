import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { StudyWorkspace } from "../../types/research";
import ResearchV092Panel from "./ResearchV092Panel";

const api = vi.hoisted(() => ({
  executeAITask: vi.fn(),
  executeComparison: vi.fn(),
  exportComparisonPackage: vi.fn(),
  fetchComparisons: vi.fn(),
  fetchEvidenceSources: vi.fn(),
  previewResearchQuery: vi.fn(),
}));

vi.mock("../../services/api", () => api);

const workspace = {
  study: {
    id: "study-1",
    research_question: "Synthetic comparative question?",
  },
  protocol_versions: [],
  cohort_versions: [],
  outcomes: [{ id: "outcome-1", name: "Synthetic outcome", review_status: "reviewed_demo" }],
  runs: [
    {
      id: "exposed-run",
      result_count: 20,
      data_snapshot_marker: "synthetic-v092",
    },
    {
      id: "comparator-run",
      result_count: 20,
      data_snapshot_marker: "synthetic-v092",
    },
  ],
  concept_set_version_ids: [],
  analysis_plans: [],
  analysis_runs: [],
  data_quality: {
    id: "dq-run",
    data_snapshot_hash: "a".repeat(64),
  },
  readiness: [],
  research_packages: [],
} as unknown as StudyWorkspace;

function renderPanel() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ResearchV092Panel
        canExecute
        canExport
        canUseAI
        studyId="study-1"
        workspace={workspace}
      />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  api.fetchEvidenceSources.mockResolvedValue([
    {
      id: "source-1",
      title: "Synthetic registered article",
      identifier: "doi:synthetic",
      review_status: "pending_review",
    },
  ]);
  api.fetchComparisons.mockResolvedValue([
    {
      id: "comparison-1",
      status: "completed_experimental_synthetic",
      content_hash: "b".repeat(64),
      results: {
        table_1: {
          exposed_n: 20,
          comparator_n: 20,
          rows: [
            {
              variable: "age",
              type: "continuous",
              exposed: { n: 20, mean: 56 },
              comparator: { n: 20, mean: 54 },
              smd_before: 0.2,
            },
          ],
        },
        adjusted: {
          psm: {
            status: "computed_experimental",
            balance: [{ variable: "age", smd_before: 0.2, smd_after: 0.04 }],
          },
          iptw: {
            status: "computed_experimental",
            effective_sample_size: 35.2,
            balance: [{ variable: "age", smd_before: 0.2, smd_after: 0.03 }],
          },
        },
      },
      diagnostics: {},
      provenance: {},
    },
  ]);
  api.previewResearchQuery.mockResolvedValue({
    id: "preview-1",
    status: "disabled_by_default",
    enabled: false,
    executed: false,
    estimated_cost: 900,
    normalized_query:
      "SELECT id FROM research_aggregate_comparisons WHERE institution_id = :institution_id AND study_id = :study_id LIMIT 100",
  });
});

describe("Research Copilot v2 and comparative RWE workspace", () => {
  it("keeps the signal explicitly non-causal and prerequisites visible", async () => {
    renderPanel();
    expect(screen.getByText(/Sinal exploratório de pesquisa/)).toBeVisible();
    expect(screen.getByRole("heading", { name: "Signal Explorer" })).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Executar comparação sintética limitada" }),
    ).toBeEnabled();
  });

  it("shows accessible Table 1 and PSM/IPTW balance diagnostics", async () => {
    renderPanel();
    fireEvent.click(screen.getByRole("tab", { name: "Comparação" }));
    expect(await screen.findByRole("table", { name: /Table 1 acessível/ })).toBeVisible();
    expect(screen.getByRole("rowheader", { name: "age" })).toBeVisible();

    fireEvent.click(screen.getByRole("tab", { name: "Métodos causais" }));
    expect(screen.getByRole("heading", { name: "PSM" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "IPTW" })).toBeVisible();
    expect(screen.getByText("ESS: 35.20")).toBeVisible();
    expect(screen.getAllByText(/Balance melhorou/)).toHaveLength(2);
  });

  it("previews AST-scoped SQL while showing default-off state", async () => {
    renderPanel();
    fireEvent.click(screen.getByRole("tab", { name: "Preview NL→SQL" }));
    fireEvent.click(screen.getByRole("button", { name: "Validar e visualizar" }));
    await waitFor(() => expect(api.previewResearchQuery).toHaveBeenCalled());
    expect(await screen.findByText("disabled_by_default")).toBeVisible();
    expect(screen.getByText(/:institution_id/)).toBeVisible();
    expect(screen.queryByRole("button", { name: /executar/i })).not.toBeInTheDocument();
  });
});
