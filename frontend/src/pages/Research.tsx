import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bot,
  CheckCircle2,
  Download,
  FileBarChart,
  FlaskConical,
  Play,
  Plus,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import CohortBuilder, {
  initialCohortDefinition,
} from "../components/research/CohortBuilder";
import PopulationAnalytics from "../components/research/PopulationAnalytics";
import ResearchV092Panel from "../components/research/ResearchV092Panel";
import TerminologyOmopPanel from "../components/research/TerminologyOmopPanel";
import Badge from "../components/ui/Badge";
import DemoContext from "../components/ui/DemoContext";
import StatusPanel from "../components/ui/StatusPanel";
import Tabs from "../components/ui/Tabs";
import TechnicalDetails from "../components/ui/TechnicalDetails";
import { useAuth } from "../context/AuthContext";
import {
  acknowledgeDataQualityFinding,
  createAnalysisPlan,
  createCohortVersion,
  createMedicationSafetyResearchDraft,
  createOutcomeDefinition,
  createResearchStudy,
  createStudyProtocolVersion,
  executeAITask,
  executeAnalysisPlan,
  executeCohortVersion,
  exportResearchPackage,
  fetchConceptSets,
  fetchDataQualityFindings,
  fetchPatientJourney,
  fetchResearchStudies,
  fetchResearchWorkspace,
  fetchStudyWorkspace,
  reviewAnalysisPlan,
  reviewCohortVersion,
  reviewOutcomeDefinition,
  reviewStudyProtocolVersion,
  runDataQuality,
} from "../services/api";
import type {
  AnalysisPlanPayload,
  CohortDefinitionV2,
  ResearchStudyPayload,
  StudyWorkspace,
} from "../types/research";
import {
  formatDateTime,
  formatStatus,
  humanizeTechnicalValue,
} from "../utils/formatters";

const emptyStudy: ResearchStudyPayload = {
  title: "",
  slug: "",
  description: "",
  research_question: "",
  objective: "",
  design: "retrospective_cohort",
  data_source_classification: "synthetic",
};

const defaultProtocol = {
  population: "",
  exposure: "",
  comparator: "",
  outcome: "",
  indexDate: "data_snapshot_marker",
  washoutDays: 0,
  followUpDays: 90,
  censoring: "none_demo",
  missingData: "report_missingness",
  limitations: "Synthetic data without external validity.",
  sourceRef: "synthetic-dataset:prescripta:v090",
};

export default function Research() {
  const { t } = useTranslation();
  const { can, user } = useAuth();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedStudyId, setSelectedStudyId] = useState(() => searchParams.get("study") ?? "");
  const allowedAreas = ["overview", "protocol", "cohort", "analysis", "results", "evidence", "provenance"];
  const requestedArea = searchParams.get("area");
  const [tab, setTab] = useState(
    requestedArea && allowedAreas.includes(requestedArea) ? requestedArea : "overview",
  );
  const [analysisArea, setAnalysisArea] = useState("comparison");
  const [provenanceArea, setProvenanceArea] = useState("terminology");
  const [showCreateStudy, setShowCreateStudy] = useState(false);
  const [studyForm, setStudyForm] = useState(emptyStudy);
  const [protocol, setProtocol] = useState(defaultProtocol);
  const [cohortName, setCohortName] = useState("Synthetic adult cohort");
  const [cohort, setCohort] = useState<CohortDefinitionV2>(
    initialCohortDefinition(),
  );
  const [snapshot, setSnapshot] = useState("synthetic-demo-v090");
  const [journeyPatientId, setJourneyPatientId] = useState(1);
  const [copilotTask, setCopilotTask] = useState(
    "research_question_structuring",
  );
  const [copilotResult, setCopilotResult] = useState<Record<
    string,
    unknown
  > | null>(null);

  const workspaceQuery = useQuery({
    queryKey: ["research-workspace"],
    queryFn: fetchResearchWorkspace,
  });
  const studiesQuery = useQuery({
    queryKey: ["research-studies"],
    queryFn: fetchResearchStudies,
  });
  const conceptsQuery = useQuery({
    queryKey: ["research-concept-sets"],
    queryFn: fetchConceptSets,
  });
  const dqQuery = useQuery({
    queryKey: ["data-quality-findings"],
    queryFn: fetchDataQualityFindings,
    enabled: can("data_quality.read"),
  });
  const studyQuery = useQuery({
    queryKey: ["study-workspace", selectedStudyId],
    queryFn: () => fetchStudyWorkspace(selectedStudyId),
    enabled: Boolean(selectedStudyId),
  });
  const journeyQuery = useQuery({
    queryKey: ["research-journey", selectedStudyId, journeyPatientId],
    queryFn: () => fetchPatientJourney(selectedStudyId, journeyPatientId),
    enabled: false,
    retry: false,
  });

  useEffect(() => {
    if (!selectedStudyId && studiesQuery.data?.length) {
      setSelectedStudyId(studiesQuery.data[0].id);
    }
  }, [selectedStudyId, studiesQuery.data]);

  function selectStudy(id: string) {
    setSelectedStudyId(id);
    const next = new URLSearchParams(searchParams);
    next.set("study", id);
    setSearchParams(next, { replace: true });
  }

  function selectArea(area: string) {
    setTab(area);
    const next = new URLSearchParams(searchParams);
    next.set("area", area);
    setSearchParams(next, { replace: true });
  }

  async function refresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["research-workspace"] }),
      queryClient.invalidateQueries({ queryKey: ["research-studies"] }),
      queryClient.invalidateQueries({ queryKey: ["study-workspace"] }),
      queryClient.invalidateQueries({ queryKey: ["data-quality-findings"] }),
    ]);
  }

  const mutation = useMutation({
    mutationFn: async (action: () => Promise<unknown>) => action(),
    onSuccess: refresh,
  });
  const createStudyMutation = useMutation({
    mutationFn: createResearchStudy,
    onSuccess: async (study) => {
      setSelectedStudyId(study.id);
      setShowCreateStudy(false);
      setStudyForm(emptyStudy);
      await refresh();
    },
  });
  const medicationDraftMutation = useMutation({
    mutationFn: () =>
      createMedicationSafetyResearchDraft(selectedStudyId, {
        source_finding_id: searchParams.get("finding"),
        medication_candidate:
          searchParams.get("medication") ?? "Medication exposure",
        outcome_candidate: searchParams.get("outcome") ?? "Safety outcome",
        suggested_question: `Is ${searchParams.get("outcome") ?? "the safety outcome"} more frequent after ${searchParams.get("medication") ?? "the exposure"}?`,
        source_evidence_ids: [],
        limitations: [
          "Exploratory synthetic research signal; not a causal or clinical conclusion.",
        ],
        synthetic_only: true,
      }),
    onSuccess: () => {
      const next = new URLSearchParams(searchParams);
      ["finding", "medication", "outcome"].forEach((key) => next.delete(key));
      setSearchParams(next, { replace: true });
    },
  });

  const studyWorkspace = studyQuery.data;
  const currentRun = studyWorkspace?.runs[0];
  const currentAnalysisRun = studyWorkspace?.analysis_runs[0];
  const currentDataQualityRunId =
    typeof studyWorkspace?.data_quality.id === "string"
      ? studyWorkspace.data_quality.id
      : "";
  const reviewedConcepts = (conceptsQuery.data ?? [])
    .filter((item) =>
      ["human_reviewed", "approved_for_demo_study"].includes(
        item.version?.status ?? "",
      ),
    )
    .map((item) => ({ id: item.version?.id ?? "", label: item.name }))
    .filter((item) => item.id);
  const tabs = useMemo(
    () => [
      { id: "overview", label: t("research.tabs.overview") },
      { id: "protocol", label: t("research.tabs.protocol") },
      { id: "cohort", label: t("research.tabs.cohort") },
      { id: "analysis", label: t("research.tabs.analysis") },
      { id: "results", label: t("research.tabs.results") },
      { id: "evidence", label: t("research.tabs.evidence") },
      { id: "provenance", label: t("research.tabs.provenance") },
    ],
    [t],
  );

  function createProtocol() {
    if (!selectedStudyId) return;
    mutation.mutate(() =>
      createStudyProtocolVersion(selectedStudyId, {
        population: { description: protocol.population },
        exposure: { description: protocol.exposure },
        comparator: { description: protocol.comparator },
        outcome: { description: protocol.outcome },
        index_date: { event: protocol.indexDate },
        washout: { days: protocol.washoutDays },
        follow_up: { days: protocol.followUpDays },
        censoring: { strategy: protocol.censoring },
        inclusion: [{ criterion: "visual_cohort_definition" }],
        exclusion: [],
        covariates: [],
        missing_data_strategy: { strategy: protocol.missingData },
        statistical_plan: { methods: ["descriptive_only"] },
        limitations: [protocol.limitations],
        source_refs: [protocol.sourceRef],
      }),
    );
  }

  function createOutcome() {
    if (!selectedStudyId) return;
    mutation.mutate(() =>
      createOutcomeDefinition(selectedStudyId, {
        name: t("research.defaultOutcomeName"),
        domain: "event",
        concept_set_version_ids: [],
        event_qualification: { minimum_events: 1 },
        observation_window: { after_index_days: protocol.followUpDays },
        temporal_relationship: "after_index",
        source_refs: [protocol.sourceRef],
        limitations: [protocol.limitations],
      }),
    );
  }

  function createPlan() {
    if (!selectedStudyId || !currentRun || !currentDataQualityRunId) return;
    const reviewedOutcomeIds = (studyWorkspace?.outcomes ?? [])
      .filter((item) => item.review_status === "reviewed_demo")
      .map((item) => item.id);
    if (!reviewedOutcomeIds.length) return;
    const payload: AnalysisPlanPayload = {
      cohort_run_id: currentRun.id,
      data_quality_run_id: currentDataQualityRunId,
      outcome_version_ids: reviewedOutcomeIds,
      objectives: [
        studyWorkspace?.study.objective ?? t("research.descriptiveObjective"),
      ],
      variables: [
        { name: "age_years", type: "numeric" },
        { name: "sex", type: "categorical" },
      ],
      steps: [
        { method: "population_count" },
        { method: "baseline_table_1" },
        { method: "prevalence" },
      ],
      descriptive_metrics: [
        "n",
        "missing",
        "mean",
        "sd",
        "median",
        "q1",
        "q3",
        "iqr",
        "min",
        "max",
      ],
      subgroup_definitions: [],
      missing_data_approach: "report_only",
      methods: [
        "population_count",
        "numeric_summary",
        "categorical_distribution",
        "prevalence",
        "baseline_table_1",
        "resource_utilization",
      ],
      planned_outputs: [
        "summary_cards",
        "table_1",
        "distribution_chart",
        "attrition_table",
        "research_package",
      ],
      output_specification: { aggregate_only: true, small_cell_threshold: 5 },
      source_refs: currentRun.source_version_refs,
      limitations: [t("research.syntheticLimitation")],
    };
    mutation.mutate(() => createAnalysisPlan(selectedStudyId, payload));
  }

  function executeCopilot() {
    if (!studyWorkspace) return;
    mutation.mutate(
      async () => {
        const interaction = await executeAITask({
          task_type: copilotTask,
          data_classification: "synthetic",
          study_id: selectedStudyId,
          ...(copilotTask === "patient_journey_summary"
            ? { patient_id: journeyPatientId }
            : {}),
          source_ids: [],
          preferred_provider: "fallback",
          allowed_providers: ["fallback"],
          purpose: "research_proposal_only",
          input: {
            question: studyWorkspace.study.research_question,
            protocol: studyWorkspace.protocol_versions[0] ?? {},
            results: currentAnalysisRun?.results ?? currentRun?.analytics ?? {},
            events: journeyQuery.data?.events ?? [],
          },
        });
        setCopilotResult(interaction.output_payload);
        return interaction;
      },
      { onSuccess: () => undefined },
    );
  }

  if (workspaceQuery.isLoading || studiesQuery.isLoading) {
    return <LoadingState label={t("research.loading")} />;
  }
  if (!workspaceQuery.data || workspaceQuery.isError || studiesQuery.isError) {
    return (
      <StatusPanel title={t("research.errorTitle")} tone="danger">
        {t("research.errorBody")}
      </StatusPanel>
    );
  }

  return (
    <div className="grid gap-6 lg:gap-8">
      <PageHeader
        actions={
          <div className="flex flex-wrap gap-2">
            <Badge tone="warning">{t("research.synthetic")}</Badge>
            <Badge tone="info">{t("research.aggregate")}</Badge>
            {can("research.study.create") ? (
              <button
                className="btn-primary"
                onClick={() => setShowCreateStudy(true)}
                type="button"
              >
                <Plus aria-hidden="true" className="h-4 w-4" />{" "}
                {t("research.newStudy")}
              </button>
            ) : null}
          </div>
        }
        description={t("research.description")}
        title={t("research.title")}
      />
      <DemoContext experimental />
      <StatusPanel title={t("research.useLimit")} tone="warning">
        {workspaceQuery.data.synthetic_demo_notice} {t("research.useLimitBody")}
      </StatusPanel>
      {searchParams.get("finding") ? (
        <StatusPanel title={t("research.v092.bridge.title")} tone="info">
          <p>{t("research.v092.bridge.body")}</p>
          <button
            className="btn-primary mt-3"
            disabled={!selectedStudyId || medicationDraftMutation.isPending}
            onClick={() => medicationDraftMutation.mutate()}
            type="button"
          >
            <FlaskConical aria-hidden="true" className="h-4 w-4" />
            {t("research.v092.bridge.create")}
          </button>
        </StatusPanel>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-[18rem_minmax(0,1fr)]">
        <aside className="surface-card h-fit p-4">
          <div className="flex items-center justify-between gap-2">
            <h2 className="font-black">{t("research.studies")}</h2>
            <Badge>{studiesQuery.data?.length ?? 0}</Badge>
          </div>
          <div className="mt-3 grid gap-2">
            {studiesQuery.data?.map((study) => (
              <button
                aria-current={study.id === selectedStudyId ? "page" : undefined}
                className={`rounded-xl border p-3 text-left ${study.id === selectedStudyId ? "border-cyan-400 bg-cyan-50" : "border-slate-200"}`}
                key={study.id}
                onClick={() => selectStudy(study.id)}
                type="button"
              >
                <span className="block text-sm font-black">{study.title}</span>
                <span className="mt-1 block text-xs text-slate-500">
                  {humanizeTechnicalValue(study.design)}
                </span>
              </button>
            ))}
            {!studiesQuery.data?.length ? (
              <p className="py-4 text-sm text-slate-500">{t("research.noStudies")}</p>
            ) : null}
          </div>
        </aside>

        <main className="min-w-0 grid gap-4">
          {!selectedStudyId ? (
            <StatusPanel title={t("research.selectStudyTitle")} tone="info">
              {t("research.selectStudyBody")}
            </StatusPanel>
          ) : studyQuery.isLoading ? (
            <LoadingState label={t("research.workspaceLoading")} />
          ) : !studyWorkspace || studyQuery.isError ? (
            <StatusPanel
              title={t("research.workspaceErrorTitle")}
              tone="danger"
            >
              {t("research.workspaceErrorBody")}
            </StatusPanel>
          ) : (
            <>
              <StudyHeader workspace={studyWorkspace} />
              <div className="surface-card p-3 sm:p-4">
                <Tabs
                  label={t("research.studyAreas")}
                  onChange={selectArea}
                  options={tabs}
                  value={tab}
                />
              </div>

              {tab === "overview" ? <StudyOverview workspace={studyWorkspace} /> : null}

              {tab === "protocol" ? (
                <DesignPanel
                  canReview={can("research.study.review")}
                  canWrite={can("research.study.write")}
                  createOutcome={createOutcome}
                  createProtocol={createProtocol}
                  currentUserId={user?.id}
                  mutationPending={mutation.isPending}
                  protocol={protocol}
                  reviewOutcome={(id) =>
                    mutation.mutate(() =>
                      reviewOutcomeDefinition(
                        id,
                        "reviewed_demo",
                        t("research.humanReviewNote"),
                      ),
                    )
                  }
                  reviewProtocol={(id) =>
                    mutation.mutate(() =>
                      reviewStudyProtocolVersion(
                        id,
                        "reviewed_demo",
                        t("research.humanReviewNote"),
                      ),
                    )
                  }
                  setProtocol={setProtocol}
                  workspace={studyWorkspace}
                />
              ) : null}

              {tab === "cohort" ? (
                <section className="grid gap-4">
                  <div className="surface-card p-5">
                    <h2 className="mb-4 font-black">{t("research.cohortBuilder")}</h2>
                    <div className="flex flex-wrap items-end gap-3">
                      <label className="min-w-64 flex-1 text-sm font-bold">
                        {t("research.cohortName")}
                        <input
                          className="field mt-1 w-full"
                          onChange={(event) =>
                            setCohortName(event.target.value)
                          }
                          value={cohortName}
                        />
                      </label>
                      {can("research.cohort.write") ? (
                        <button
                          className="btn-primary"
                          disabled={mutation.isPending || cohortName.length < 3}
                          onClick={() =>
                            mutation.mutate(() =>
                              createCohortVersion(
                                selectedStudyId,
                                cohortName,
                                cohort,
                              ),
                            )
                          }
                          type="button"
                        >
                          {t("research.saveVersion")}
                        </button>
                      ) : null}
                    </div>
                    <div className="mt-5">
                      <CohortBuilder
                        conceptVersions={reviewedConcepts}
                        onChange={setCohort}
                        value={cohort}
                      />
                    </div>
                    <TechnicalDetails label={t("research.advancedJson")} copyValue={JSON.stringify(cohort, null, 2)}>
                      <pre className="mt-2 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
                        {JSON.stringify(cohort, null, 2)}
                      </pre>
                    </TechnicalDetails>
                  </div>
                  <div className="surface-card p-5">
                    <h3 className="font-black">
                      {t("research.cohortPreview")}
                    </h3>
                    <label className="mt-3 block text-sm font-bold">
                      {t("research.snapshot")}
                      <input
                        className="field mt-1 w-full"
                        onChange={(event) => setSnapshot(event.target.value)}
                        value={snapshot}
                      />
                    </label>
                    <div className="mt-4 grid gap-3">
                      {studyWorkspace.cohort_versions.map((version) => (
                        <VersionRow
                          author={version.authored_by_user_id}
                          canReview={can("research.study.review")}
                          currentUserId={user?.id}
                          hash={version.definition_hash}
                          key={version.id}
                          label={`v${version.version} · ${t("research.cost", { cost: version.query_cost })}`}
                          onExecute={
                            version.status === "reviewed_demo" &&
                            can("research.cohort.execute")
                              ? () =>
                                  mutation.mutate(() =>
                                    executeCohortVersion(version.id, snapshot),
                                  )
                              : undefined
                          }
                          onReview={
                            version.status === "draft"
                              ? () =>
                                  mutation.mutate(() =>
                                    reviewCohortVersion(
                                      version.id,
                                      "reviewed_demo",
                                      t("research.humanReviewNote"),
                                    ),
                                  )
                              : undefined
                          }
                          status={version.status}
                        />
                      ))}
                    </div>
                    {currentRun ? (
                      <PopulationAnalytics cohortRun={currentRun} />
                    ) : null}
                  </div>
                </section>
              ) : null}

              {tab === "analysis" ? (
                <section className="grid gap-4">
                  <div className="surface-card p-3">
                    <Tabs label={t("research.analysisAreas")} onChange={setAnalysisArea} options={[
                      { id: "comparison", label: t("research.analysisTabs.comparison") },
                      { id: "quality", label: t("research.analysisTabs.quality") },
                    ]} value={analysisArea} />
                  </div>
                  {analysisArea === "comparison" ? <ResearchV092Panel
                    canExecute={can("research.analysis.execute")}
                    canExport={can("research.package.export")}
                    canUseAI={can("research.ai.use")}
                    studyId={selectedStudyId}
                    workspace={studyWorkspace}
                  /> : <AnalysisPanel
                  canAcknowledge={can("data_quality.acknowledge")}
                  canExecute={can("research.analysis.execute")}
                  canReview={can("research.study.review")}
                  canRunDQ={can("data_quality.run")}
                  canWrite={can("research.analysis.write")}
                  createPlan={createPlan}
                  currentUserId={user?.id}
                  findings={dqQuery.data ?? []}
                  mutationPending={mutation.isPending}
                  onAcknowledge={(id) =>
                    mutation.mutate(() =>
                      acknowledgeDataQualityFinding(
                        id,
                        t("research.dqAcknowledgement"),
                      ),
                    )
                  }
                  onExecute={(id) =>
                    mutation.mutate(() => executeAnalysisPlan(id))
                  }
                  onReview={(id) =>
                    mutation.mutate(() =>
                      reviewAnalysisPlan(id, t("research.humanReviewNote")),
                    )
                  }
                  onRunDQ={() =>
                    currentRun
                      ? mutation.mutate(() =>
                          runDataQuality(selectedStudyId, currentRun.id),
                        )
                      : undefined
                  }
                    workspace={studyWorkspace}
                  />}
                </section>
              ) : null}

              {tab === "results" ? (
                <section className="grid gap-4">
                  <div className="surface-card p-5">
                    <h2 className="font-black">
                      {t("research.populationAnalytics")}
                    </h2>
                    <div className="mt-4">
                      <PopulationAnalytics
                        analysisRun={currentAnalysisRun}
                        cohortRun={currentRun}
                      />
                    </div>
                  </div>
                  {can("research.patient_journey.read") ? (
                    <div className="surface-card p-5">
                      <h2 className="font-black">
                        {t("research.patientJourney")}
                      </h2>
                      <p className="mt-1 text-sm text-slate-600">
                        {t("research.patientJourneyBody")}
                      </p>
                      <div className="mt-4 flex gap-2">
                        <input
                          aria-label={t("research.syntheticPatientId")}
                          className="field"
                          min={1}
                          onChange={(event) =>
                            setJourneyPatientId(Number(event.target.value))
                          }
                          type="number"
                          value={journeyPatientId}
                        />
                        <button
                          className="btn-secondary"
                          onClick={() => journeyQuery.refetch()}
                          type="button"
                        >
                          {t("research.loadJourney")}
                        </button>
                      </div>
                      {journeyQuery.isError ? (
                        <p className="mt-3 text-sm font-bold text-red-700">
                          {t("research.journeyFailedClosed")}
                        </p>
                      ) : null}
                      {journeyQuery.data ? (
                        <ol className="mt-4 grid gap-2">
                          {journeyQuery.data.events.map((event) => (
                            <li
                              className="rounded-xl border border-slate-200 p-3 text-sm"
                              key={String(event.event_ref)}
                            >
                              <strong>{String(event.title)}</strong>
                              <span className="mt-1 block text-xs text-slate-500">
                                {String(event.occurred_at)} ·{" "}
                                {String(event.event_type)}
                              </span>
                              <p className="mt-2">{String(event.summary)}</p>
                            </li>
                          ))}
                        </ol>
                      ) : null}
                    </div>
                  ) : null}
                </section>
              ) : null}

              {tab === "provenance" ? (
                <section className="grid gap-4">
                  <div className="surface-card p-3">
                    <Tabs label={t("research.provenanceAreas")} onChange={setProvenanceArea} options={[
                      { id: "terminology", label: t("research.tabs.terminology") },
                      { id: "omop", label: t("research.tabs.omop") },
                    ]} value={provenanceArea} />
                  </div>
                  <TerminologyOmopPanel
                  area={provenanceArea as "terminology" | "omop"}
                  canExportOmop={can("omop.export")}
                  canPreviewOmop={can("omop.preview")}
                  canReadTerminology={can("terminology.read")}
                  canReviewMappings={can("terminology.mapping.review")}
                  cohortRunId={currentRun?.id}
                    studyId={selectedStudyId}
                  />
                </section>
              ) : null}

              {tab === "evidence" ? (
                <EvidencePanel
                  canExport={can("research.package.export")}
                  copilotResult={copilotResult}
                  copilotTask={copilotTask}
                  executeCopilot={executeCopilot}
                  exportPackage={(id) =>
                    mutation.mutate(() => exportResearchPackage(id))
                  }
                  mutationPending={mutation.isPending}
                  setCopilotTask={setCopilotTask}
                  workspace={studyWorkspace}
                />
              ) : null}
            </>
          )}
        </main>
      </section>

      {showCreateStudy ? (
        <StudyDialog
          close={() => setShowCreateStudy(false)}
          form={studyForm}
          pending={createStudyMutation.isPending}
          setForm={setStudyForm}
          submit={() => createStudyMutation.mutate(studyForm)}
        />
      ) : null}
    </div>
  );
}

function StudyHeader({ workspace }: { workspace: StudyWorkspace }) {
  const { t } = useTranslation();
  return (
    <section className="surface-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-wide text-ocean">
            {t("research.studyWorkspace")}
          </p>
          <h2 className="mt-1 text-2xl font-black">{workspace.study.title}</h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            {workspace.study.research_question}
          </p>
        </div>
        <Badge
          tone={
            workspace.study.status.includes("reviewed") ? "success" : "warning"
          }
        >
          {formatStatus(workspace.study.status)}
        </Badge>
      </div>
      <ol
        aria-label={t("research.readiness")}
        className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-8"
      >
        {workspace.readiness.map((item, index) => (
          <li
            className={`rounded-xl p-2 text-center text-xs font-bold ${item.ready ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-500"}`}
            key={item.step}
          >
            <span className="block text-base">
              {item.ready ? "✓" : index + 1}
            </span>
            {t(`research.readinessSteps.${item.step}`)}
          </li>
        ))}
      </ol>
    </section>
  );
}

function StudyOverview({ workspace }: { workspace: StudyWorkspace }) {
  const { t } = useTranslation();
  const protocol = workspace.protocol_versions[0];
  const run = workspace.runs[0];
  const items = [
    [t("research.overview.question"), workspace.study.research_question],
    [t("research.overview.objective"), workspace.study.objective],
    [t("research.overview.design"), humanizeTechnicalValue(workspace.study.design)],
    [t("research.overview.exposure"), String(protocol?.exposure.description ?? "—")],
    [t("research.overview.comparator"), String(protocol?.comparator.description ?? "—")],
    [t("research.overview.outcome"), String(protocol?.outcome.description ?? "—")],
  ];
  return (
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(18rem,.65fr)]">
      <div className="surface-card p-5">
        <p className="eyebrow">{t("research.overview.title")}</p>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          {items.map(([label, value]) => (
            <div className="border-l-2 border-cyan-700 pl-3" key={label}>
              <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</dt>
              <dd className="mt-1 text-sm font-semibold text-ink">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
      <div className="surface-card p-5">
        <h3 className="font-black">{t("research.overview.execution")}</h3>
        <dl className="mt-4 grid gap-3 text-sm">
          <div><dt className="text-slate-500">{t("research.overview.snapshot")}</dt><dd className="font-bold">{run?.data_snapshot_marker ?? "—"}</dd></div>
          <div><dt className="text-slate-500">{t("research.overview.protocol")}</dt><dd className="font-bold">{protocol ? `v${protocol.version} · ${formatStatus(protocol.status)}` : "—"}</dd></div>
          <div><dt className="text-slate-500">{t("research.overview.quality")}</dt><dd className="font-bold">{workspace.data_quality.status ? formatStatus(String(workspace.data_quality.status)) : t("research.overview.notAvailable")}</dd></div>
          <div><dt className="text-slate-500">{t("research.overview.lastRun")}</dt><dd className="font-bold">{run ? formatDateTime(run.executed_at) : t("research.overview.notRun")}</dd></div>
        </dl>
        <div className="mt-4">
          <TechnicalDetails copyValue={workspace.study.id}>
            <code className="break-all text-xs">study_id: {workspace.study.id}<br />run_id: {run?.id ?? "—"}</code>
          </TechnicalDetails>
        </div>
      </div>
    </section>
  );
}

function DesignPanel({
  workspace,
  protocol,
  setProtocol,
  createProtocol,
  createOutcome,
  reviewProtocol,
  reviewOutcome,
  canWrite,
  canReview,
  currentUserId,
  mutationPending,
}: {
  workspace: StudyWorkspace;
  protocol: typeof defaultProtocol;
  setProtocol: (value: typeof defaultProtocol) => void;
  createProtocol: () => void;
  createOutcome: () => void;
  reviewProtocol: (id: string) => void;
  reviewOutcome: (id: string) => void;
  canWrite: boolean;
  canReview: boolean;
  currentUserId?: number;
  mutationPending: boolean;
}) {
  const { t } = useTranslation();
  const fields: Array<{
    key: keyof typeof defaultProtocol;
    label: string;
    numeric?: boolean;
  }> = [
    { key: "population", label: t("research.protocolFields.population") },
    { key: "exposure", label: t("research.protocolFields.exposure") },
    { key: "comparator", label: t("research.protocolFields.comparator") },
    { key: "outcome", label: t("research.protocolFields.outcome") },
    { key: "indexDate", label: t("research.protocolFields.indexDate") },
    {
      key: "washoutDays",
      label: t("research.protocolFields.washout"),
      numeric: true,
    },
    {
      key: "followUpDays",
      label: t("research.protocolFields.followUp"),
      numeric: true,
    },
    { key: "censoring", label: t("research.protocolFields.censoring") },
    { key: "missingData", label: t("research.protocolFields.missingData") },
    { key: "limitations", label: t("research.protocolFields.limitations") },
    { key: "sourceRef", label: t("research.protocolFields.source") },
  ];
  return (
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(18rem,.75fr)]">
      <div className="surface-card p-5">
        <h3 className="font-black">{t("research.protocolEditor")}</h3>
        <p className="mt-1 text-sm text-slate-600">
          {t("research.immutableVersions")}
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {fields.map((field) => (
            <label className="grid gap-1 text-sm font-bold" key={field.key}>
              {field.label}
              <input
                className="field"
                onChange={(event) =>
                  setProtocol({
                    ...protocol,
                    [field.key]: field.numeric
                      ? Number(event.target.value)
                      : event.target.value,
                  })
                }
                type={field.numeric ? "number" : "text"}
                value={protocol[field.key]}
              />
            </label>
          ))}
        </div>
        {canWrite ? (
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              className="btn-primary"
              disabled={mutationPending}
              onClick={createProtocol}
              type="button"
            >
              {t("research.newVersion")}
            </button>
            <button
              className="btn-secondary"
              disabled={mutationPending}
              onClick={createOutcome}
              type="button"
            >
              {t("research.createOutcome")}
            </button>
          </div>
        ) : null}
      </div>
      <div className="grid content-start gap-4">
        <VersionList
          canReview={canReview}
          currentUserId={currentUserId}
          items={workspace.protocol_versions.map((item) => ({
            id: item.id,
            author: item.authored_by_user_id,
            label: `${t("research.protocol")} v${item.version}`,
            status: item.status,
            hash: item.definition_hash,
          }))}
          onReview={reviewProtocol}
        />
        <VersionList
          canReview={canReview}
          currentUserId={currentUserId}
          items={workspace.outcomes.map((item) => ({
            id: item.id,
            author: item.authored_by_user_id,
            label: `${item.name} · v${item.version}`,
            status: item.review_status,
            hash: item.definition_hash,
          }))}
          onReview={reviewOutcome}
        />
        <TechnicalDetails label={t("research.technicalDetails")}>
          <p className="mt-3 text-xs text-slate-600">
            {t("research.conceptSets")}:{" "}
            {workspace.concept_set_version_ids.length}
          </p>
        </TechnicalDetails>
      </div>
    </section>
  );
}

function AnalysisPanel({
  workspace,
  findings,
  createPlan,
  onRunDQ,
  onReview,
  onExecute,
  onAcknowledge,
  canWrite,
  canReview,
  canExecute,
  canRunDQ,
  canAcknowledge,
  currentUserId,
  mutationPending,
}: {
  workspace: StudyWorkspace;
  findings: Array<{
    id: string;
    rule: string;
    severity: string;
    message: string;
    status: string;
  }>;
  createPlan: () => void;
  onRunDQ: () => void;
  onReview: (id: string) => void;
  onExecute: (id: string) => void;
  onAcknowledge: (id: string) => void;
  canWrite: boolean;
  canReview: boolean;
  canExecute: boolean;
  canRunDQ: boolean;
  canAcknowledge: boolean;
  currentUserId?: number;
  mutationPending: boolean;
}) {
  const { t } = useTranslation();
  const dqSummary = workspace.data_quality as {
    analysis_blocked?: boolean;
    dimensions?: Record<string, number>;
  };
  return (
    <section className="grid gap-4 xl:grid-cols-2">
      <div className="surface-card p-5">
        <div className="flex flex-wrap justify-between gap-3">
          <div>
            <h3 className="font-black">{t("research.dataQuality")}</h3>
            <p className="text-sm text-slate-600">
              {t("research.dataQualityBody")}
            </p>
          </div>
          {canRunDQ ? (
            <button
              className="btn-secondary"
              disabled={mutationPending}
              onClick={onRunDQ}
              type="button"
            >
              {t("research.runChecks")}
            </button>
          ) : null}
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2">
          {Object.entries(dqSummary.dimensions ?? {}).map(([name, value]) => (
            <div className="rounded-xl bg-slate-50 p-3" key={name}>
              <strong className="text-xl">{value}</strong>
              <span className="block text-xs text-slate-500">
                {humanizeTechnicalValue(name)}
              </span>
            </div>
          ))}
        </div>
        {dqSummary.analysis_blocked ? (
          <p className="mt-3 text-sm font-bold text-red-700" role="alert">
            {t("research.analysisBlocked")}
          </p>
        ) : null}
        <div className="mt-4 grid gap-2">
          {findings.slice(0, 8).map((finding) => (
            <div
              className="rounded-xl border border-slate-200 p-3"
              key={finding.id}
            >
              <div className="flex justify-between gap-2">
                <strong className="text-sm">
                  {formatStatus(finding.rule)}
                </strong>
                <Badge
                  tone={
                    finding.severity === "critical" ||
                    finding.severity === "high"
                      ? "danger"
                      : "warning"
                  }
                >
                  {formatStatus(finding.severity)}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-slate-600">{finding.message}</p>
              {canAcknowledge && finding.status === "open" ? (
                <button
                  className="btn-secondary mt-2"
                  onClick={() => onAcknowledge(finding.id)}
                  type="button"
                >
                  {t("research.acknowledge")}
                </button>
              ) : null}
            </div>
          ))}
        </div>
      </div>
      <div className="surface-card p-5">
        <div className="flex flex-wrap justify-between gap-3">
          <div>
            <h3 className="font-black">{t("research.analysisPlan")}</h3>
            <p className="text-sm text-slate-600">
              {t("research.analysisPlanBody")}
            </p>
          </div>
          {canWrite ? (
            <button
              className="btn-primary"
              disabled={!workspace.runs.length || mutationPending}
              onClick={createPlan}
              type="button"
            >
              <Plus aria-hidden="true" className="h-4 w-4" />
              {t("research.createPlan")}
            </button>
          ) : null}
        </div>
        <div className="mt-4 grid gap-3">
          {workspace.analysis_plans.map((plan) => (
            <VersionRow
              author={plan.authored_by_user_id}
              canReview={canReview}
              currentUserId={currentUserId}
              hash={plan.definition_hash}
              key={plan.id}
              label={`${t("research.analysisPlan")} v${plan.version}`}
              onExecute={
                plan.status === "reviewed_demo" && canExecute
                  ? () => onExecute(plan.id)
                  : undefined
              }
              onReview={
                plan.status === "draft" ? () => onReview(plan.id) : undefined
              }
              status={plan.status}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

function EvidencePanel({
  workspace,
  exportPackage,
  canExport,
  copilotTask,
  setCopilotTask,
  executeCopilot,
  copilotResult,
  mutationPending,
}: {
  workspace: StudyWorkspace;
  exportPackage: (id: string) => void;
  canExport: boolean;
  copilotTask: string;
  setCopilotTask: (task: string) => void;
  executeCopilot: () => void;
  copilotResult: Record<string, unknown> | null;
  mutationPending: boolean;
}) {
  const { t } = useTranslation();
  const tasks = [
    "research_question_structuring",
    "protocol_completeness_review",
    "cohort_drafting",
    "analysis_plan_draft",
    "data_quality_explanation",
    "results_explanation",
    "patient_journey_summary",
  ];
  return (
    <section className="grid gap-4 xl:grid-cols-2">
      <div className="surface-card p-5">
        <div className="flex items-center gap-2">
          <FileBarChart aria-hidden="true" className="h-5 w-5 text-ocean" />
          <h3 className="font-black">{t("research.researchPackage")}</h3>
        </div>
        <p className="mt-2 text-sm text-slate-600">
          {t("research.researchPackageBody")}
        </p>
        <div className="mt-4 grid gap-3">
          {workspace.analysis_runs.map((run) => (
            <div
              className="rounded-xl border border-slate-200 p-3"
              key={run.id}
            >
              <div className="flex flex-wrap justify-between gap-2">
                <div>
                  <strong>{formatDateTime(run.executed_at)}</strong>
                  <p className="mt-1 break-all font-mono text-xs text-slate-500">
                    {run.content_hash}
                  </p>
                </div>
                {canExport ? (
                  <button
                    className="btn-secondary"
                    disabled={mutationPending}
                    onClick={() => exportPackage(run.id)}
                    type="button"
                  >
                    <Download aria-hidden="true" className="h-4 w-4" />
                    {t("research.exportPackage")}
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
        {workspace.research_packages.map((item) => (
          <details className="mt-3 rounded-xl bg-emerald-50 p-3" key={item.id}>
            <summary className="cursor-pointer text-sm font-bold text-emerald-900">
              {t("research.packageReady")} · {item.content_hash.slice(0, 12)}
            </summary>
            <pre className="mt-2 overflow-auto text-xs">
              {JSON.stringify(item.manifest, null, 2)}
            </pre>
          </details>
        ))}
        <details className="mt-4">
          <summary className="cursor-pointer text-sm font-bold text-ocean">
            {t("research.provenance")}
          </summary>
          <pre className="mt-2 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
            {JSON.stringify(
              workspace.analysis_runs[0]?.provenance ?? {},
              null,
              2,
            )}
          </pre>
        </details>
      </div>
      <div className="surface-card p-5">
        <div className="flex items-center gap-2">
          <Bot aria-hidden="true" className="h-5 w-5 text-violet-700" />
          <h3 className="font-black">{t("research.copilot")}</h3>
        </div>
        <p className="mt-2 text-sm text-slate-600">
          {t("research.copilotBody")}
        </p>
        <label className="mt-4 grid gap-1 text-sm font-bold">
          {t("research.copilotTask")}
          <select
            className="field"
            onChange={(event) => setCopilotTask(event.target.value)}
            value={copilotTask}
          >
            {tasks.map((task) => (
              <option key={task} value={task}>
                {t(`research.copilotTasks.${task}`)}
              </option>
            ))}
          </select>
        </label>
        <button
          className="btn-secondary mt-3"
          disabled={mutationPending}
          onClick={executeCopilot}
          type="button"
        >
          {t("research.generateProposal")}
        </button>
        {copilotResult ? (
          <pre className="mt-4 max-h-80 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
            {JSON.stringify(copilotResult, null, 2)}
          </pre>
        ) : null}
      </div>
    </section>
  );
}

function StudyDialog({
  form,
  setForm,
  submit,
  close,
  pending,
}: {
  form: ResearchStudyPayload;
  setForm: (form: ResearchStudyPayload) => void;
  submit: () => void;
  close: () => void;
  pending: boolean;
}) {
  const { t } = useTranslation();
  const fields: Array<{
    key: "title" | "slug" | "research_question" | "objective" | "description";
    label: string;
  }> = [
    { key: "title", label: t("research.studyTitle") },
    { key: "slug", label: t("research.studySlug") },
    { key: "research_question", label: t("research.question") },
    { key: "objective", label: t("research.objective") },
    { key: "description", label: t("research.studyDescription") },
  ];
  const valid =
    form.title.length >= 5 &&
    form.slug.length >= 3 &&
    form.research_question.length >= 10 &&
    form.objective.length >= 10;
  return (
    <div
      aria-labelledby="create-study-title"
      aria-modal="true"
      className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4"
      role="dialog"
    >
      <form
        className="surface-card max-h-[90vh] w-full max-w-2xl overflow-auto p-6"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <div className="flex justify-between gap-3">
          <h2 className="text-xl font-black" id="create-study-title">
            {t("research.newStudy")}
          </h2>
          <button
            aria-label={t("common.close")}
            className="rounded-lg p-2"
            onClick={close}
            type="button"
          >
            <X aria-hidden="true" />
          </button>
        </div>
        <p className="mt-2 text-sm text-slate-600">
          {t("research.studyWizardBody")}
        </p>
        <div className="mt-5 grid gap-3">
          {fields.map((field, index) => (
            <label className="grid gap-1 text-sm font-bold" key={field.key}>
              {`${index + 1}. ${field.label}`}
              {field.key === "research_question" ||
              field.key === "objective" ||
              field.key === "description" ? (
                <textarea
                  className="field min-h-20"
                  onChange={(event) =>
                    setForm({ ...form, [field.key]: event.target.value })
                  }
                  value={form[field.key]}
                />
              ) : (
                <input
                  className="field"
                  onChange={(event) =>
                    setForm({
                      ...form,
                      [field.key]:
                        field.key === "slug"
                          ? event.target.value
                              .toLowerCase()
                              .replace(/[^a-z0-9-]/g, "-")
                          : event.target.value,
                    })
                  }
                  value={form[field.key]}
                />
              )}
            </label>
          ))}
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button className="btn-secondary" onClick={close} type="button">
            {t("research.cancel")}
          </button>
          <button
            className="btn-primary"
            disabled={!valid || pending}
            type="submit"
          >
            {t("research.createStudy")}
          </button>
        </div>
      </form>
    </div>
  );
}

function VersionList({
  items,
  onReview,
  canReview,
  currentUserId,
}: {
  items: Array<{
    id: string;
    author: number;
    label: string;
    status: string;
    hash: string;
  }>;
  onReview: (id: string) => void;
  canReview: boolean;
  currentUserId?: number;
}) {
  return (
    <div className="surface-card grid gap-2 p-4">
      {items.map((item) => (
        <VersionRow
          author={item.author}
          canReview={canReview}
          currentUserId={currentUserId}
          hash={item.hash}
          key={item.id}
          label={item.label}
          onReview={
            item.status === "draft" || item.status === "pending_review"
              ? () => onReview(item.id)
              : undefined
          }
          status={item.status}
        />
      ))}
      {!items.length ? <p className="text-sm text-slate-500">—</p> : null}
    </div>
  );
}

function VersionRow({
  label,
  status,
  hash,
  author,
  onReview,
  onExecute,
  canReview,
  currentUserId,
}: {
  label: string;
  status: string;
  hash: string;
  author: number;
  onReview?: () => void;
  onExecute?: () => void;
  canReview: boolean;
  currentUserId?: number;
}) {
  const { t } = useTranslation();
  return (
    <div className="rounded-xl border border-slate-200 p-3">
      <div className="flex flex-wrap justify-between gap-2">
        <strong className="text-sm">{label}</strong>
        <Badge
          tone={
            status === "reviewed_demo" || status === "completed_demo"
              ? "success"
              : "warning"
          }
        >
          {formatStatus(status)}
        </Badge>
      </div>
      <p className="mt-2 break-all font-mono text-[0.6875rem] text-slate-500">
        {hash}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {onReview && canReview && author !== currentUserId ? (
          <button className="btn-secondary" onClick={onReview} type="button">
            <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
            {t("research.reviewDemo")}
          </button>
        ) : null}
        {onExecute ? (
          <button className="btn-primary" onClick={onExecute} type="button">
            <Play aria-hidden="true" className="h-4 w-4" />
            {t("research.execute")}
          </button>
        ) : null}
      </div>
    </div>
  );
}
