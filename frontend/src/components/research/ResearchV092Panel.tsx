import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bot,
  Download,
  FileSearch,
  FlaskConical,
  Play,
  Scale,
  ShieldCheck,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  advanceResearchAgent,
  createEvidenceSearchPlan,
  createResearchAgent,
  executeAITask,
  executeEvidenceSearchPlan,
  executeComparison,
  exportComparisonPackage,
  fetchComparisons,
  fetchEvidenceSources,
  previewResearchQuery,
} from "../../services/api";
import type {
  EvidenceSearchPlan,
  ResearchAgentRun,
  ResearchQueryPreview,
  StudyWorkspace,
} from "../../types/research";
import Badge from "../ui/Badge";
import StatusPanel from "../ui/StatusPanel";
import Tabs from "../ui/Tabs";

type Props = {
  studyId: string;
  workspace: StudyWorkspace;
  canExecute: boolean;
  canExport: boolean;
  canUseAI: boolean;
};

type Area =
  | "signal"
  | "comparison"
  | "methods"
  | "evidence"
  | "agent"
  | "copilot"
  | "query";

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value)
    ? value.filter(
        (item): item is Record<string, unknown> =>
          Boolean(item) && typeof item === "object" && !Array.isArray(item),
      )
    : [];
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function syntheticRecords(count: number, group: "exposed" | "comparator") {
  return Array.from({ length: count }, (_, index) => {
    const eventBoundary = Math.floor(count * (group === "exposed" ? 0.3 : 0.2));
    const outcome = index < eventBoundary;
    return {
      record_key: `${group === "exposed" ? "EXP" : "CMP"}-${String(index + 1).padStart(4, "0")}`,
      group,
      outcome,
      follow_up_days: 90 + (index % 30),
      event_day: outcome ? 7 + (index % 60) : null,
      covariates: {
        age: 42 + (index % 28) + (group === "exposed" ? 2 : 0),
        sex: index % 2 ? "F" : "M",
      },
    };
  });
}

export default function ResearchV092Panel({
  studyId,
  workspace,
  canExecute,
  canExport,
  canUseAI,
}: Props) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [area, setArea] = useState<Area>("signal");
  const [queryText, setQueryText] = useState(
    "SELECT id, status, exposed_n, comparator_n FROM research_aggregate_comparisons",
  );
  const [queryPreview, setQueryPreview] = useState<ResearchQueryPreview | null>(null);
  const [evidenceQuery, setEvidenceQuery] = useState("medication safety synthetic study");
  const [evidencePlan, setEvidencePlan] = useState<EvidenceSearchPlan | null>(null);
  const [agentRun, setAgentRun] = useState<ResearchAgentRun | null>(null);
  const [copilotOutput, setCopilotOutput] = useState<Record<string, unknown> | null>(null);

  const comparisons = useQuery({
    queryKey: ["research-comparisons", studyId],
    queryFn: () => fetchComparisons(studyId),
  });
  const evidence = useQuery({
    queryKey: ["evidence-sources"],
    queryFn: fetchEvidenceSources,
  });
  const current = comparisons.data?.[0];
  const methods = asRecord(current?.results.adjusted);
  const psm = asRecord(methods.psm);
  const iptw = asRecord(methods.iptw);
  const sensitivity = asRecord(methods.sensitivity);
  const tableOne = asRecord(current?.results.table_1);
  const tableRows = asArray(tableOne.rows);
  const runs = workspace.runs;
  const exposedRun = runs[0];
  const comparatorRun = runs[1];
  const reviewedOutcomes = workspace.outcomes.filter(
    (outcome) => outcome.review_status === "reviewed_demo",
  );
  const dataQuality = workspace.data_quality;
  const dqId = typeof dataQuality.id === "string" ? dataQuality.id : "";
  const dqHash =
    typeof dataQuality.data_snapshot_hash === "string"
      ? dataQuality.data_snapshot_hash
      : "";
  const canRunFixture = Boolean(
    canExecute &&
      exposedRun &&
      comparatorRun &&
      exposedRun.id !== comparatorRun.id &&
      exposedRun.data_snapshot_marker === comparatorRun.data_snapshot_marker &&
      exposedRun.result_count + comparatorRun.result_count <= 5000 &&
      dqId &&
      dqHash &&
      reviewedOutcomes.length,
  );

  const tabs = useMemo(
    () => [
      { id: "signal", label: t("research.v092.tabs.signal") },
      { id: "comparison", label: t("research.v092.tabs.comparison") },
      { id: "methods", label: t("research.v092.tabs.methods") },
      { id: "evidence", label: t("research.v092.tabs.evidence") },
      { id: "agent", label: t("research.v093.tabs.agent") },
      { id: "copilot", label: t("research.v092.tabs.copilot") },
      { id: "query", label: t("research.v092.tabs.query") },
    ],
    [t],
  );

  const runComparison = useMutation({
    mutationFn: async () => {
      if (!exposedRun || !comparatorRun || !canRunFixture) {
        throw new Error("comparison_prerequisites_missing");
      }
      return executeComparison(studyId, {
        exposed_cohort_run_id: exposedRun.id,
        comparator_cohort_run_id: comparatorRun.id,
        data_quality_run_id: dqId,
        outcome_version_ids: reviewedOutcomes.map((outcome) => outcome.id),
        dataset_snapshot_marker: exposedRun.data_snapshot_marker,
        dataset_snapshot_hash: dqHash,
        terminology_release_ids: [],
        mapping_ids: [],
        covariates: ["age", "sex"],
        records: [
          ...syntheticRecords(exposedRun.result_count, "exposed"),
          ...syntheticRecords(comparatorRun.result_count, "comparator"),
        ],
        denominator_unit: "person_years",
        continuity_correction: 0.5,
        small_cell_threshold: 5,
        psm: {
          enabled: true,
          estimand: "ATT",
          covariates: ["age", "sex"],
          ratio: 1,
          caliper: 0.2,
          replacement: false,
          seed: 902,
          missing_data_policy: "complete_case",
          normalization: "standardize",
        },
        iptw: {
          enabled: true,
          estimand: "ATE",
          covariates: ["age", "sex"],
          stabilized: true,
          truncation_percentiles: [1, 99],
          seed: 902,
          missing_data_policy: "complete_case",
        },
        sensitivity: {
          enabled: true,
          psm_calipers: [0.1, 0.2],
          psm_ratios: [1, 2],
          iptw_truncations: [[1, 99], [5, 95]],
          iptw_stabilized: [true, false],
        },
        causal_assumptions: {
          consistency: "needs_review",
          exchangeability: "needs_review",
          positivity: "needs_review",
          interference: "needs_review",
          residual_confounding:
            "Residual and unmeasured confounding remain possible in this synthetic demonstration.",
          covariate_roles: { age: "confounder", sex: "prognostic" },
        },
        synthetic_only: true,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["research-comparisons", studyId],
      });
      setArea("comparison");
    },
  });
  const packageMutation = useMutation({
    mutationFn: (comparisonId: string) => exportComparisonPackage(comparisonId),
  });
  const queryMutation = useMutation({
    mutationFn: () =>
      previewResearchQuery({
        study_id: studyId,
        dataset_snapshot_marker:
          exposedRun?.data_snapshot_marker ?? "synthetic-v092",
        natural_language_question: t("research.v092.query.defaultQuestion"),
        proposed_sql: queryText,
        row_limit: 100,
        timeout_ms: 3000,
        lock_timeout_ms: 500,
        cost_budget: 10000,
        max_ast_nodes: 200,
        max_ast_depth: 12,
        max_total_cost: 5000,
        max_plan_rows: 10000,
        max_plan_nodes: 40,
        max_output_bytes: 200000,
        purpose: "human_reviewed_aggregate_preview",
      }),
    onSuccess: setQueryPreview,
  });
  const evidencePlanMutation = useMutation({
    mutationFn: () =>
      createEvidenceSearchPlan({
        study_id: studyId,
        providers: ["pubmed", "crossref", "openalex"],
        canonical_query: evidenceQuery,
        filters: { limit: 20, metadata_only: true },
      }),
    onSuccess: setEvidencePlan,
  });
  const evidenceExecuteMutation = useMutation({
    mutationFn: (planId: string) => executeEvidenceSearchPlan(planId),
    onSuccess: async (plan) => {
      setEvidencePlan(plan);
      await queryClient.invalidateQueries({ queryKey: ["evidence-sources"] });
    },
  });
  const agentCreateMutation = useMutation({
    mutationFn: () =>
      createResearchAgent({
        study_id: studyId,
        template: "evidence_review",
        goal: "Prepare a source-grounded evidence shortlist for human review",
        budget: {
          max_steps: 4,
          max_wall_time_seconds: 300,
          max_tool_calls: 4,
          max_tokens: 4000,
          max_cost_usd: 1,
        },
        data_classification: "public",
        source_ids: [],
      }),
    onSuccess: setAgentRun,
  });
  const agentStepMutation = useMutation({
    mutationFn: (runId: string) =>
      advanceResearchAgent(runId, {
        tool: "propose_evidence_shortlist",
        output: { source_ids: [], note: "No source selected without human review" },
        token_usage: 0,
        cost_usd: 0,
      }),
    onSuccess: setAgentRun,
  });
  const copilotMutation = useMutation({
    mutationFn: (task: string) =>
      executeAITask({
        task_type: task,
        data_classification: "synthetic",
        study_id: studyId,
        source_ids: [],
        schema_version: task.includes("comparative") ? "v2" : "v1",
        preferred_provider: "fallback",
        allowed_providers: ["fallback"],
        allowed_models: [],
        source_grounding_required: false,
        purpose: "research_copilot_contextual_proposal",
        input: {
          question: workspace.study.research_question,
          protocol: workspace.protocol_versions[0] ?? {},
          numeric_refs: [],
          assumptions: {},
        },
      }),
    onSuccess: (interaction) => setCopilotOutput(interaction.output_payload),
  });

  return (
    <section className="grid gap-4">
      <StatusPanel title={t("research.v092.noticeTitle")} tone="warning">
        {t("research.v092.notice")}
      </StatusPanel>
      <div className="surface-card p-3 sm:p-4">
        <Tabs
          label={t("research.v092.areaLabel")}
          onChange={(value) => setArea(value as Area)}
          options={tabs}
          value={area}
        />
      </div>

      {area === "signal" ? (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)]">
          <div className="surface-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="eyebrow">{t("research.v092.signal.eyebrow")}</p>
                <h2 className="mt-1 text-xl font-black">
                  {t("research.v092.signal.title")}
                </h2>
              </div>
              <Badge tone="warning">{t("research.v092.experimental")}</Badge>
            </div>
            <dl className="mt-5 grid gap-3 sm:grid-cols-2">
              {[
                ["exposure", exposedRun?.id],
                ["comparator", comparatorRun?.id],
                ["outcome", reviewedOutcomes[0]?.name],
                ["timeAtRisk", "90–119 days"],
              ].map(([key, value]) => (
                <div className="rounded-xl border border-slate-200 p-3" key={key}>
                  <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    {t(`research.v092.signal.${key}`)}
                  </dt>
                  <dd className="mt-1 break-all text-sm font-bold">
                    {value ?? t("research.v092.notReady")}
                  </dd>
                </div>
              ))}
            </dl>
            <button
              className="btn-primary mt-5"
              disabled={!canRunFixture || runComparison.isPending}
              onClick={() => runComparison.mutate()}
              type="button"
            >
              <Play aria-hidden="true" className="h-4 w-4" />
              {runComparison.isPending
                ? t("research.v092.running")
                : t("research.v092.signal.run")}
            </button>
            {!canRunFixture ? (
              <p className="mt-3 text-sm text-amber-800">
                {t("research.v092.signal.prerequisites")}
              </p>
            ) : null}
          </div>
          <div className="surface-card p-5">
            <FlaskConical aria-hidden="true" className="h-7 w-7 text-cyan-700" />
            <h3 className="mt-3 font-black">{t("research.v092.journey.title")}</h3>
            <p className="mt-2 text-sm text-slate-600">
              {t("research.v092.journey.body")}
            </p>
            <ol className="mt-4 grid gap-2 text-sm">
              {["start", "switch", "refill", "overlap", "outcome"].map(
                (step, index) => (
                  <li className="flex items-center gap-3" key={step}>
                    <span className="grid h-7 w-7 place-items-center rounded-full bg-cyan-50 font-black text-cyan-800">
                      {index + 1}
                    </span>
                    {t(`research.v092.journey.${step}`)}
                  </li>
                ),
              )}
            </ol>
          </div>
        </div>
      ) : null}

      {area === "comparison" ? (
        <div className="grid gap-4">
          {!current ? (
            <StatusPanel title={t("research.v092.comparison.emptyTitle")} tone="info">
              {t("research.v092.comparison.emptyBody")}
            </StatusPanel>
          ) : (
            <>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {[
                  ["exposed", tableOne.exposed_n],
                  ["comparator", tableOne.comparator_n],
                  ["status", current.status],
                  ["hash", `${current.content_hash.slice(0, 12)}…`],
                ].map(([key, value]) => (
                  <div className="surface-card p-4" key={key as string}>
                    <p className="text-xs font-bold uppercase text-slate-500">
                      {t(`research.v092.comparison.${key}`)}
                    </p>
                    <p className="mt-2 break-all text-lg font-black">{String(value)}</p>
                  </div>
                ))}
              </div>
              <div className="surface-card overflow-hidden">
                <div className="flex flex-wrap items-center justify-between gap-3 p-5">
                  <div>
                    <h2 className="font-black">{t("research.v092.tableOne.title")}</h2>
                    <p className="text-sm text-slate-500">
                      {t("research.v092.tableOne.body")}
                    </p>
                  </div>
                  {canExport ? (
                    <button
                      className="btn-secondary"
                      disabled={packageMutation.isPending}
                      onClick={() => packageMutation.mutate(current.id)}
                      type="button"
                    >
                      <Download aria-hidden="true" className="h-4 w-4" />
                      {t("research.v092.packageV3")}
                    </button>
                  ) : null}
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <caption className="sr-only">
                      {t("research.v092.tableOne.caption")}
                    </caption>
                    <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                      <tr>
                        <th className="p-3" scope="col">{t("research.v092.tableOne.variable")}</th>
                        <th className="p-3" scope="col">{t("research.v092.tableOne.exposed")}</th>
                        <th className="p-3" scope="col">{t("research.v092.tableOne.comparator")}</th>
                        <th className="p-3" scope="col">SMD</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tableRows.map((row, index) => (
                        <tr className="border-t border-slate-100" key={`${String(row.variable)}-${index}`}>
                          <th className="p-3 font-bold" scope="row">
                            {String(row.variable)}
                            {row.level ? ` · ${String(row.level)}` : ""}
                          </th>
                          <td className="p-3"><code>{JSON.stringify(row.exposed)}</code></td>
                          <td className="p-3"><code>{JSON.stringify(row.comparator)}</code></td>
                          <td className="p-3">{String(row.smd_before ?? "not_computable")}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      ) : null}

      {area === "methods" ? (
        <div className="grid gap-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <MethodCard icon={Scale} method="PSM" result={psm} />
            <MethodCard icon={ShieldCheck} method="IPTW" result={iptw} />
          </div>
          <div className="surface-card p-5">
            <h2 className="font-black">{t("research.v093.sensitivity.title")}</h2>
            <p className="mt-2 text-sm text-slate-600">
              {t("research.v093.sensitivity.body")}
            </p>
            <pre className="mt-4 max-h-64 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
              {JSON.stringify(sensitivity, null, 2)}
            </pre>
          </div>
        </div>
      ) : null}

      {area === "evidence" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="surface-card p-5">
            <FileSearch aria-hidden="true" className="h-7 w-7 text-cyan-700" />
            <h2 className="mt-3 font-black">{t("research.v092.evidence.title")}</h2>
            <p className="mt-2 text-sm text-slate-600">
              {t("research.v092.evidence.body")}
            </p>
            <label className="mt-4 block text-sm font-bold">
              {t("research.v093.evidence.query")}
              <input
                className="field mt-1 w-full"
                onChange={(event) => setEvidenceQuery(event.target.value)}
                value={evidenceQuery}
              />
            </label>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                className="btn-secondary"
                disabled={evidencePlanMutation.isPending}
                onClick={() => evidencePlanMutation.mutate()}
                type="button"
              >
                {t("research.v093.evidence.createPlan")}
              </button>
              <button
                className="btn-primary"
                disabled={!evidencePlan || evidenceExecuteMutation.isPending}
                onClick={() => evidencePlan && evidenceExecuteMutation.mutate(evidencePlan.id)}
                type="button"
              >
                {t("research.v093.evidence.execute")}
              </button>
            </div>
            {evidencePlan ? (
              <p className="mt-3 text-sm">
                v{evidencePlan.version} · {evidencePlan.status} · {evidencePlan.result_count}{" "}
                {t("research.v093.evidence.results")}
              </p>
            ) : null}
          </div>
          <div className="surface-card p-5">
            <h3 className="font-black">{t("research.v092.evidence.registered")}</h3>
            <div className="mt-3 grid gap-2">
              {(evidence.data ?? []).map((source) => (
                <div className="rounded-xl border border-slate-200 p-3" key={source.id}>
                  <strong className="text-sm">{source.title}</strong>
                  <p className="mt-1 text-xs text-slate-500">
                    {source.identifier} · {source.review_status}
                  </p>
                </div>
              ))}
              {!evidence.data?.length ? (
                <p className="text-sm text-slate-500">{t("research.v092.evidence.empty")}</p>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}

      {area === "agent" ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <div className="surface-card p-5">
            <Bot aria-hidden="true" className="h-7 w-7 text-cyan-700" />
            <h2 className="mt-3 font-black">{t("research.v093.agent.title")}</h2>
            <p className="mt-2 text-sm text-slate-600">
              {t("research.v093.agent.body")}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                className="btn-primary"
                disabled={agentCreateMutation.isPending}
                onClick={() => agentCreateMutation.mutate()}
                type="button"
              >
                {t("research.v093.agent.create")}
              </button>
              <button
                className="btn-secondary"
                disabled={!agentRun || agentRun.state !== "queued" || agentStepMutation.isPending}
                onClick={() => agentRun && agentStepMutation.mutate(agentRun.id)}
                type="button"
              >
                {t("research.v093.agent.checkpoint")}
              </button>
            </div>
          </div>
          <div className="surface-card p-5">
            <Badge tone={agentRun?.state === "waiting_human" ? "warning" : "info"}>
              {agentRun?.state ?? t("research.v093.agent.notStarted")}
            </Badge>
            <p className="mt-4 text-xs font-bold uppercase text-slate-500">
              {t("research.v093.agent.tools")}
            </p>
            <p className="mt-2 text-sm">{agentRun?.allowed_tools.join(" · ") ?? "—"}</p>
            {agentRun ? (
              <pre className="mt-4 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
                {JSON.stringify({ budget: agentRun.budgets, usage: agentRun.usage }, null, 2)}
              </pre>
            ) : null}
          </div>
        </div>
      ) : null}

      {area === "copilot" ? (
        <div className="surface-card p-5">
          <div className="flex items-start gap-3">
            <Bot aria-hidden="true" className="h-7 w-7 text-cyan-700" />
            <div>
              <h2 className="font-black">Research Copilot v2</h2>
              <p className="mt-1 text-sm text-slate-600">
                {t("research.v092.copilot.body")}
              </p>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {[
              "research_question_structuring",
              "protocol_completeness_review",
              "cohort_drafting",
              "analysis_plan_draft",
              "data_quality_explanation",
              "results_explanation",
            ].map((task) => (
              <button
                className="btn-secondary"
                disabled={!canUseAI || copilotMutation.isPending}
                key={task}
                onClick={() => copilotMutation.mutate(task)}
                type="button"
              >
                {t(`research.copilotTasks.${task}`)}
              </button>
            ))}
          </div>
          {copilotOutput ? (
            <pre className="mt-4 max-h-80 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
              {JSON.stringify(copilotOutput, null, 2)}
            </pre>
          ) : null}
        </div>
      ) : null}

      {area === "query" ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="surface-card p-5">
            <h2 className="font-black">{t("research.v092.query.title")}</h2>
            <p className="mt-2 text-sm text-slate-600">{t("research.v092.query.body")}</p>
            <label className="mt-4 block text-sm font-bold">
              {t("research.v092.query.proposal")}
              <textarea
                className="field mt-1 min-h-32 w-full font-mono text-xs"
                onChange={(event) => setQueryText(event.target.value)}
                value={queryText}
              />
            </label>
            <button
              className="btn-primary mt-3"
              disabled={queryMutation.isPending}
              onClick={() => queryMutation.mutate()}
              type="button"
            >
              <FileSearch aria-hidden="true" className="h-4 w-4" />
              {t("research.v092.query.preview")}
            </button>
          </div>
          <div className="surface-card p-5">
            <Badge tone={queryPreview?.enabled ? "success" : "warning"}>
              {queryPreview?.status ?? t("research.v092.query.defaultOff")}
            </Badge>
            <p className="mt-3 text-sm">{t("research.v092.query.policy")}</p>
            {queryPreview ? (
              <>
                <p className="mt-3 text-xs text-slate-500">
                  {t("research.v092.query.cost", { cost: queryPreview.estimated_cost })}
                </p>
                <pre className="mt-3 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
                  {queryPreview.normalized_query}
                </pre>
                <pre className="mt-3 overflow-auto rounded-xl bg-slate-100 p-3 text-xs text-slate-800">
                  {JSON.stringify(
                    asRecord(asRecord(queryPreview.structured_interpretation).planner),
                    null,
                    2,
                  )}
                </pre>
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function MethodCard({
  icon: Icon,
  method,
  result,
}: {
  icon: typeof Scale;
  method: "PSM" | "IPTW";
  result: Record<string, unknown>;
}) {
  const { t } = useTranslation();
  const balance = asArray(result.balance);
  const status = String(result.status ?? "not_run");
  const ess = numberValue(result.effective_sample_size);
  return (
    <article className="surface-card p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <Icon aria-hidden="true" className="h-7 w-7 text-cyan-700" />
          <div>
            <p className="eyebrow">{t("research.v092.experimental")}</p>
            <h2 className="font-black">{method}</h2>
          </div>
        </div>
        <Badge tone={status.includes("computed") ? "success" : "warning"}>{status}</Badge>
      </div>
      {ess !== null ? (
        <p className="mt-4 text-sm font-bold">ESS: {ess.toFixed(2)}</p>
      ) : null}
      <div
        aria-label={t("research.v092.methods.balanceSummary", { method })}
        className="mt-4 grid gap-3"
        role="img"
      >
        {balance.slice(0, 8).map((item, index) => {
          const before = Math.min(1, Math.abs(numberValue(item.smd_before) ?? 0));
          const after = Math.min(1, Math.abs(numberValue(item.smd_after) ?? 0));
          return (
            <div key={`${String(item.variable)}-${index}`}>
              <div className="flex justify-between text-xs">
                <span>{String(item.variable)}</span>
                <span>{before.toFixed(2)} → {after.toFixed(2)}</span>
              </div>
              <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-cyan-600"
                  style={{ width: `${Math.max(2, after * 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <caption className="sr-only">
            {t("research.v092.methods.balanceTable", { method })}
          </caption>
          <thead><tr><th className="p-2">Variable</th><th className="p-2">Before</th><th className="p-2">After</th></tr></thead>
          <tbody>
            {balance.map((item, index) => (
              <tr className="border-t border-slate-100" key={`${String(item.variable)}-table-${index}`}>
                <th className="p-2" scope="row">{String(item.variable)}</th>
                <td className="p-2">{String(item.smd_before ?? "—")}</td>
                <td className="p-2">{String(item.smd_after ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <StatusPanel title={t("research.v092.methods.limitTitle")} tone="warning">
        {t("research.v092.methods.limit")}
      </StatusPanel>
    </article>
  );
}
