import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TerminologyOmopPanel from "./TerminologyOmopPanel";

const api = vi.hoisted(() => ({
  executeOmopAdapter: vi.fn(),
  fetchOmopCompatibility: vi.fn(),
  fetchOmopRuns: vi.fn(),
  fetchTerminologyMappings: vi.fn(),
  fetchTerminologyReleases: vi.fn(),
  fetchTerminologySources: vi.fn(),
  reviewTerminologyMapping: vi.fn(),
  searchTerminologyConcepts: vi.fn(),
}));

vi.mock("../../services/api", () => api);

function renderPanel(area: "terminology" | "omop") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <TerminologyOmopPanel
        area={area}
        canExportOmop
        canPreviewOmop
        canReadTerminology
        canReviewMappings
        cohortRunId="cohort-run-1"
        studyId="study-1"
      />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  api.fetchTerminologySources.mockResolvedValue([
    { id: "source-1", public_name: "LOINC subset sintético", family: "loinc", steward: "Regenstrief", canonical_system: "http://loinc.org" },
  ]);
  api.fetchTerminologyReleases.mockResolvedValue([
    { id: "release-1", version: "demo-1", status: "imported", license_status: "authorized", license_name: "Fixture only", source_checksum: "a".repeat(64) },
  ]);
  api.searchTerminologyConcepts.mockResolvedValue({
    items: [{ id: "concept-1", source_code: "DEMO-1", display: "Medição sintética", source_system: "fixture", domain: "Measurement", standard_status: "Standard" }],
    total: 1,
    offset: 0,
    limit: 50,
    suggestion_only: true,
  });
  api.fetchTerminologyMappings.mockResolvedValue([
    { id: "mapping-1", version: 1, relationship_type: "Maps to", status: "proposed", mapping_hash: "b".repeat(64), mapping_method: "explicit_fixture" },
  ]);
  api.reviewTerminologyMapping.mockResolvedValue({});
  api.fetchOmopCompatibility.mockResolvedValue({
    targets: [{ target: "DataQualityDashboard", level: "not_tested", proven: "none", missing: "real execution" }],
  });
  api.fetchOmopRuns.mockResolvedValue([
    { id: "omop-run-1", status: "previewed", cdm_version: "5.4", source_snapshot_marker: "synthetic-v1", export_hash: "c".repeat(64) },
  ]);
  api.executeOmopAdapter.mockResolvedValue({ id: "omop-run-2" });
});

describe("Terminology and partial OMOP workspace", () => {
  it("shows governed releases, suggestion search, and independent mapping review", async () => {
    renderPanel("terminology");
    expect(await screen.findByText("LOINC subset sintético")).toBeVisible();
    expect(screen.getByText("Fixture only · SHA-256 aaaaaaaaaaaa…")).toBeVisible();
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "medição" } });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    expect(await screen.findByText(/DEMO-1/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Aprovar para demo" }));
    await waitFor(() => expect(api.reviewTerminologyMapping).toHaveBeenCalledWith(
      "mapping-1",
      "approved_for_demo",
      expect.stringContaining("Revisão humana independente"),
    ));
  });

  it("states compatibility limits and runs synthetic preview/export", async () => {
    renderPanel("omop");
    expect(await screen.findByText("DataQualityDashboard")).toBeVisible();
    expect(screen.getByText(/Não validado com DQD/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Gerar prévia" }));
    await waitFor(() => expect(api.executeOmopAdapter).toHaveBeenCalledWith(
      "preview",
      expect.objectContaining({ study_id: "study-1", cohort_run_id: "cohort-run-1" }),
    ));
    fireEvent.click(screen.getByRole("button", { name: "Exportar sintético" }));
    await waitFor(() => expect(api.executeOmopAdapter).toHaveBeenCalledWith(
      "exports",
      expect.anything(),
    ));
  });
});
