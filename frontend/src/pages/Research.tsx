import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Beaker,
  Bot,
  CheckCircle2,
  Database,
  FlaskConical,
  GitBranch,
  Play,
  Plus,
  ShieldAlert,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import AttritionFlow from "../components/research/AttritionFlow";
import Badge from "../components/ui/Badge";
import StatusPanel from "../components/ui/StatusPanel";
import Tabs from "../components/ui/Tabs";
import { useAuth } from "../context/AuthContext";
import {
  createCohortVersion,
  createConceptSet,
  createOutcomeDefinition,
  createResearchStudy,
  createStudyProtocolVersion,
  executeAITask,
  executeCohortVersion,
  fetchConceptSets,
  fetchDataQualityFindings,
  fetchResearchStudies,
  fetchResearchWorkspace,
  fetchStudyWorkspace,
  reviewCohortVersion,
  reviewConceptSetVersion,
  reviewStudyProtocolVersion,
  runDataQuality,
} from "../services/api";
import type { CohortDefinition, ResearchStudyPayload } from "../types/research";
import { formatDateTime, formatStatus, humanizeTechnicalValue } from "../utils/formatters";

const emptyStudy: ResearchStudyPayload = {
  title: "",
  slug: "",
  description: "",
  research_question: "",
  objective: "",
  design: "retrospective_cohort",
  data_source_classification: "synthetic",
};

export default function Research() {
  const queryClient = useQueryClient();
  const { can, user } = useAuth();
  const { t } = useTranslation();
  const tabs = useMemo(() => [
    { id: "overview", label: t("research.tabs.overview") },
    { id: "protocol", label: t("research.tabs.protocol") },
    { id: "cohort", label: t("research.tabs.cohort") },
    { id: "concepts", label: t("research.tabs.concepts") },
    { id: "outcomes", label: t("research.tabs.outcomes") },
    { id: "runs", label: t("research.tabs.runs") },
    { id: "provenance", label: t("research.tabs.provenance") },
  ], [t]);
  const [selectedStudyId, setSelectedStudyId] = useState("");
  const [tab, setTab] = useState("overview");
  const [studyForm, setStudyForm] = useState(emptyStudy);
  const [conceptForm, setConceptForm] = useState({ name: "", code: "", label: "", source: "" });
  const [cohortName, setCohortName] = useState("Coorte adulta demonstrativa");
  const [minimumAge, setMinimumAge] = useState(18);
  const [selectedConceptVersion, setSelectedConceptVersion] = useState("");
  const [snapshotMarker, setSnapshotMarker] = useState("synthetic-demo-v088");
  const [copilotResult, setCopilotResult] = useState<Record<string, unknown> | null>(null);

  const workspaceQuery = useQuery({ queryKey: ["research-workspace"], queryFn: fetchResearchWorkspace });
  const studiesQuery = useQuery({ queryKey: ["research-studies"], queryFn: fetchResearchStudies });
  const conceptsQuery = useQuery({ queryKey: ["research-concept-sets"], queryFn: fetchConceptSets });
  const dqQuery = useQuery({ queryKey: ["data-quality-findings"], queryFn: fetchDataQualityFindings, enabled: can("data_quality.read") });
  const studyWorkspaceQuery = useQuery({
    queryKey: ["study-workspace", selectedStudyId],
    queryFn: () => fetchStudyWorkspace(selectedStudyId),
    enabled: Boolean(selectedStudyId),
  });

  useEffect(() => {
    if (!selectedStudyId && studiesQuery.data?.length) setSelectedStudyId(studiesQuery.data[0].id);
  }, [selectedStudyId, studiesQuery.data]);

  async function refreshResearch() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["research-workspace"] }),
      queryClient.invalidateQueries({ queryKey: ["research-studies"] }),
      queryClient.invalidateQueries({ queryKey: ["research-concept-sets"] }),
      queryClient.invalidateQueries({ queryKey: ["study-workspace"] }),
    ]);
  }

  const createStudyMutation = useMutation({
    mutationFn: createResearchStudy,
    onSuccess: async (study) => {
      setStudyForm(emptyStudy);
      setSelectedStudyId(study.id);
      await refreshResearch();
    },
  });
  const createConceptMutation = useMutation({
    mutationFn: () => createConceptSet({
      name: conceptForm.name,
      domain: "condition",
      terminology_versions: { "CID-10": "2026-demo" },
      include_descendants: false,
      source_refs: [conceptForm.source],
      license_metadata: { fixture: true, redistribution: "synthetic-only" },
      provenance: { origin: "manual-demo", demo_only: true },
      members: [{ terminology_system: "CID-10", terminology_version: "2026-demo", concept_code: conceptForm.code, label: conceptForm.label, excluded: false }],
    }),
    onSuccess: async (concept) => {
      setSelectedConceptVersion(concept.version?.id ?? "");
      setConceptForm({ name: "", code: "", label: "", source: "" });
      await refreshResearch();
    },
  });
  const protocolMutation = useMutation({
    mutationFn: () => createStudyProtocolVersion(selectedStudyId, {
      population: { description: "População sintética definida no study workspace" },
      exposure: { description: "Exposição demonstrativa" },
      comparator: { description: "Sem comparação causal nesta release" },
      outcome: { description: "Outcome versionado no workspace" },
      index_date: { event: "data_snapshot_marker" },
      washout: { days: 0 },
      follow_up: { days: 90 },
      censoring: { strategy: "none_demo" },
      inclusion: [{ criterion: `age_gte_${minimumAge}` }],
      exclusion: [],
      covariates: [],
      missing_data_strategy: { strategy: "report_missingness" },
      statistical_plan: { methods: ["descriptive_only"] },
      limitations: ["Dados sintéticos sem validade externa."],
      source_refs: ["synthetic-dataset:v088"],
    }),
    onSuccess: refreshResearch,
  });
  const cohortDefinition = useMemo<CohortDefinition>(() => ({
    all: [
      { criterion: "age", operator: "gte", value: minimumAge, label: `Idade ≥ ${minimumAge}` },
      ...(selectedConceptVersion ? [{ criterion: "condition" as const, operator: "exists", concept_set_version_id: selectedConceptVersion, label: "Condição no concept set revisado" }] : []),
    ],
    exclude: [],
  }), [minimumAge, selectedConceptVersion]);
  const cohortMutation = useMutation({
    mutationFn: () => createCohortVersion(selectedStudyId, cohortName, cohortDefinition),
    onSuccess: refreshResearch,
  });
  const outcomeMutation = useMutation({
    mutationFn: () => createOutcomeDefinition(selectedStudyId, {
      name: "Outcome demonstrativo em 90 dias",
      domain: "condition",
      concept_set_version_ids: selectedConceptVersion ? [selectedConceptVersion] : [],
      event_qualification: { minimum_events: 1 },
      observation_window: { after_index_days: 90 },
      temporal_relationship: "after_index",
      source_refs: ["synthetic-dataset:v088"],
      limitations: ["Definição demonstrativa pendente de validação externa."],
    }),
    onSuccess: refreshResearch,
  });
  const runMutation = useMutation({
    mutationFn: (versionId: string) => executeCohortVersion(versionId, snapshotMarker),
    onSuccess: refreshResearch,
  });
  const dqMutation = useMutation({
    mutationFn: runDataQuality,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["data-quality-findings"] });
      await queryClient.invalidateQueries({ queryKey: ["research-workspace"] });
    },
  });
  const copilotMutation = useMutation({
    mutationFn: () => executeAITask({
      task_type: "research_question_structuring",
      data_classification: "synthetic",
      study_id: selectedStudyId,
      source_ids: [],
      preferred_provider: "fallback",
      allowed_providers: ["fallback"],
      purpose: "research_protocol_draft",
      input: { question: studyWorkspaceQuery.data?.study.research_question },
    }),
    onSuccess: (interaction) => setCopilotResult(interaction.output_payload),
  });

  if (workspaceQuery.isLoading || studiesQuery.isLoading) return <LoadingState label={t("research.loading")} />;
  if (workspaceQuery.isError || studiesQuery.isError || !workspaceQuery.data) {
    return <StatusPanel title={t("research.errorTitle")} tone="danger">{t("research.errorBody")}</StatusPanel>;
  }
  const studyWorkspace = studyWorkspaceQuery.data;
  const selectedConcept = conceptsQuery.data?.find((item) => item.version?.id === selectedConceptVersion);
  const metrics: Array<{ label: string; value: number; Icon: LucideIcon }> = [
    { label: t("research.studies"), value: workspaceQuery.data.studies, Icon: FlaskConical },
    { label: t("research.conceptSets"), value: workspaceQuery.data.concept_sets, Icon: Database },
    { label: t("research.cohortRuns"), value: workspaceQuery.data.cohort_runs, Icon: GitBranch },
    {
      label: t("research.openDQ"),
      value: workspaceQuery.data.open_data_quality_findings,
      Icon: ShieldAlert,
    },
  ];

  return (
    <div className="grid gap-6 lg:gap-8">
      <PageHeader
        title={t("research.title")}
        description={t("research.description")}
        actions={<><Badge tone="warning">{t("research.synthetic")}</Badge><Badge tone="info">{t("research.aggregate")}</Badge></>}
      />
      <StatusPanel title={t("research.useLimit")} tone="warning">
        {workspaceQuery.data.synthetic_demo_notice} {t("research.useLimitBody")}
      </StatusPanel>

      <section aria-label={t("research.summary")} className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(({ label, value, Icon }) => (
          <div className="surface-card p-5" key={label}>
            <Icon aria-hidden="true" className="h-5 w-5 text-ocean" />
            <p className="mt-4 text-3xl font-black text-ink">{value}</p>
            <p className="text-sm font-bold text-slate-600">{label}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[22rem_minmax(0,1fr)]">
        <aside className="surface-card p-5">
          <div className="flex items-center justify-between gap-3"><h2 className="text-lg font-black">{t("research.studies")}</h2><Badge>{studiesQuery.data?.length ?? 0}</Badge></div>
          <div className="mt-4 grid gap-2">
            {studiesQuery.data?.map((study) => (
              <button className={`rounded-xl border p-3 text-left ${selectedStudyId === study.id ? "border-cyan-400 bg-cyan-50" : "border-slate-200 hover:bg-slate-50"}`} key={study.id} onClick={() => setSelectedStudyId(study.id)} type="button">
                <span className="block text-sm font-extrabold text-ink">{study.title}</span>
                <span className="mt-1 block text-xs text-slate-500">{humanizeTechnicalValue(study.design)} · {formatStatus(study.status)}</span>
              </button>
            ))}
            {!studiesQuery.data?.length ? <p className="py-6 text-sm text-slate-500">{t("research.noStudies")}</p> : null}
          </div>
          {can("research.study.create") ? <StudyForm form={studyForm} pending={createStudyMutation.isPending} setForm={setStudyForm} submit={() => createStudyMutation.mutate(studyForm)} /> : null}
        </aside>

        <div className="min-w-0 grid gap-5">
          {!selectedStudyId ? <StatusPanel title={t("research.selectStudyTitle")} tone="info">{t("research.selectStudyBody")}</StatusPanel> : studyWorkspaceQuery.isLoading ? <LoadingState label={t("research.workspaceLoading")} /> : studyWorkspaceQuery.isError || !studyWorkspace ? <StatusPanel title={t("research.workspaceErrorTitle")} tone="danger">{t("research.workspaceErrorBody")}</StatusPanel> : <>
            <div className="surface-card p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-black">{studyWorkspace.study.title}</h2><p className="mt-1 text-sm text-slate-600">{studyWorkspace.study.research_question}</p></div><Badge tone={studyWorkspace.study.status.includes("reviewed") ? "success" : "warning"}>{formatStatus(studyWorkspace.study.status)}</Badge></div><div className="mt-5"><Tabs label={t("research.studyAreas")} onChange={setTab} options={tabs} value={tab} /></div></div>
            {tab === "overview" ? <Overview study={studyWorkspace.study} copilotResult={copilotResult} canUseAI={can("research.ai.use")} onCopilot={() => copilotMutation.mutate()} pending={copilotMutation.isPending} /> : null}
            {tab === "protocol" ? <ProtocolPanel versions={studyWorkspace.protocol_versions} canWrite={can("research.study.write")} canReview={can("research.study.review")} currentUserId={user?.id} create={() => protocolMutation.mutate()} review={(id) => reviewStudyProtocolVersion(id, "reviewed_demo", "Revisão humana independente para uso demonstrativo.").then(refreshResearch)} pending={protocolMutation.isPending} /> : null}
            {tab === "concepts" ? <ConceptPanel concepts={conceptsQuery.data ?? []} form={conceptForm} setForm={setConceptForm} selected={selectedConceptVersion} setSelected={setSelectedConceptVersion} canWrite={can("research.concept_set.write")} canReview={can("research.study.review")} currentUserId={user?.id} create={() => createConceptMutation.mutate()} review={(id, decision) => reviewConceptSetVersion(id, decision, "Revisão humana da fixture terminológica demonstrativa.").then(refreshResearch)} pending={createConceptMutation.isPending} /> : null}
            {tab === "cohort" ? <CohortPanel versions={studyWorkspace.cohort_versions} name={cohortName} setName={setCohortName} age={minimumAge} setAge={setMinimumAge} concept={selectedConcept?.name} definition={cohortDefinition} canWrite={can("research.cohort.write")} canReview={can("research.study.review")} currentUserId={user?.id} create={() => cohortMutation.mutate()} review={(id) => reviewCohortVersion(id, "reviewed_demo", "DSL revisada por pessoa independente.").then(refreshResearch)} pending={cohortMutation.isPending} /> : null}
            {tab === "outcomes" ? <OutcomePanel outcomes={studyWorkspace.outcomes} concept={selectedConcept?.name} canWrite={can("research.study.write")} create={() => outcomeMutation.mutate()} pending={outcomeMutation.isPending} /> : null}
            {tab === "runs" ? <RunsPanel runs={studyWorkspace.runs} cohorts={studyWorkspace.cohort_versions} marker={snapshotMarker} setMarker={setSnapshotMarker} canExecute={can("research.cohort.execute")} execute={(id) => runMutation.mutate(id)} pending={runMutation.isPending} /> : null}
            {tab === "provenance" ? <ProvenancePanel workspace={studyWorkspace} /> : null}
          </>}
        </div>
      </section>

      {can("data_quality.read") ? <section className="surface-card p-5 sm:p-6"><div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-lg font-black">{t("research.dataQuality")}</h2><p className="mt-1 text-sm text-slate-600">{t("research.dataQualityBody")}</p></div>{can("data_quality.run") ? <button className="btn-secondary" disabled={dqMutation.isPending} onClick={() => dqMutation.mutate()} type="button">{dqMutation.isPending ? t("research.runningChecks") : t("research.runChecks")}</button> : null}</div><div className="mt-4 grid gap-2">{dqQuery.data?.slice(0, 8).map((item) => <div className="rounded-xl border border-slate-200 p-3" key={item.id}><div className="flex justify-between gap-3"><p className="text-sm font-extrabold">{formatStatus(item.rule)}</p><Badge tone={item.severity === "critical" || item.severity === "high" ? "danger" : "warning"}>{formatStatus(item.severity)}</Badge></div><p className="mt-1 text-xs text-slate-600">{item.message} · <code>{item.resource_type}.{item.field}</code></p><details className="mt-2 text-xs"><summary className="font-bold text-ocean">{t("research.technicalDetails")}</summary><code>{item.rule}</code></details></div>)}{!dqQuery.data?.length ? <p className="text-sm text-slate-500">{t("research.noFindings")}</p> : null}</div></section> : null}
    </div>
  );
}

function StudyForm({ form, setForm, submit, pending }: { form: ResearchStudyPayload; setForm: (value: ResearchStudyPayload) => void; submit: () => void; pending: boolean }) {
  const { t } = useTranslation();
  const valid = form.title.length >= 5 && form.slug.length >= 3 && form.research_question.length >= 10 && form.objective.length >= 10;
  return <form className="mt-6 grid gap-3 border-t border-slate-200 pt-5" onSubmit={(event) => { event.preventDefault(); submit(); }}><h3 className="text-sm font-black">{t("research.newStudy")}</h3><input aria-label={t("research.studyTitle")} className="field" onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder={t("research.studyTitle")} value={form.title} /><input aria-label={t("research.studySlug")} className="field" onChange={(event) => setForm({ ...form, slug: event.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })} placeholder="study-slug" value={form.slug} /><textarea aria-label={t("research.question")} className="field min-h-20" onChange={(event) => setForm({ ...form, research_question: event.target.value })} placeholder={t("research.question")} value={form.research_question} /><textarea aria-label={t("research.objective")} className="field min-h-20" onChange={(event) => setForm({ ...form, objective: event.target.value })} placeholder={t("research.objective")} value={form.objective} /><button className="btn-primary" disabled={!valid || pending} type="submit"><Plus aria-hidden="true" className="h-4 w-4" />{t("research.createStudy")}</button></form>;
}

function Overview({ study, canUseAI, onCopilot, pending, copilotResult }: { study: { objective: string; description: string; demo_only: boolean }; canUseAI: boolean; onCopilot: () => void; pending: boolean; copilotResult: Record<string, unknown> | null }) {
  const { t } = useTranslation();
  return <section className="grid gap-4 lg:grid-cols-2"><div className="surface-card p-5"><h3 className="font-black">{t("research.objective")}</h3><p className="mt-2 text-sm leading-6 text-slate-600">{study.objective}</p><p className="mt-4 text-xs font-bold text-amber-800">{t("research.demoOnly")}: {String(study.demo_only)}</p></div><div className="surface-card p-5"><div className="flex items-center gap-2"><Bot aria-hidden="true" className="h-5 w-5 text-violet-700" /><h3 className="font-black">{t("research.copilot")}</h3></div><p className="mt-2 text-sm text-slate-600">{t("research.copilotBody")}</p>{canUseAI ? <button className="btn-secondary mt-4" disabled={pending} onClick={onCopilot} type="button">{t("research.structureQuestion")}</button> : null}{copilotResult ? <pre className="mt-4 max-h-52 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(copilotResult, null, 2)}</pre> : null}</div></section>;
}

function ProtocolPanel({ versions, canWrite, canReview, currentUserId, create, review, pending }: { versions: Array<{ id: string; version: number; status: string; definition_hash: string; authored_by_user_id: number; source_refs: string[] }>; canWrite: boolean; canReview: boolean; currentUserId?: number; create: () => void; review: (id: string) => void; pending: boolean }) {
  const { t } = useTranslation();
  return <section className="surface-card p-5"><div className="flex justify-between gap-3"><div><h3 className="font-black">{t("research.protocolVersions")}</h3><p className="text-sm text-slate-600">{t("research.immutableVersions")}</p></div>{canWrite ? <button className="btn-primary" disabled={pending} onClick={create} type="button"><Plus aria-hidden="true" className="h-4 w-4" />{t("research.newVersion")}</button> : null}</div><div className="mt-4 grid gap-3">{versions.map((item) => <div className="rounded-xl border border-slate-200 p-4" key={item.id}><div className="flex flex-wrap justify-between gap-2"><p className="font-extrabold">v{item.version}</p><Badge tone={item.status === "reviewed_demo" ? "success" : "warning"}>{formatStatus(item.status)}</Badge></div><p className="mt-2 break-all font-mono text-[0.6875rem] text-slate-500">{item.definition_hash}</p>{canReview && item.status === "draft" && item.authored_by_user_id !== currentUserId ? <button className="btn-secondary mt-3" onClick={() => review(item.id)} type="button"><CheckCircle2 aria-hidden="true" className="h-4 w-4" />{t("research.reviewDemo")}</button> : null}</div>)}{!versions.length ? <p className="text-sm text-slate-500">{t("research.noProtocol")}</p> : null}</div></section>;
}

function ConceptPanel({ concepts, form, setForm, selected, setSelected, canWrite, canReview, currentUserId, create, review, pending }: { concepts: Array<{ id: string; name: string; status: string; version: { id: string; status: string; authored_by_user_id: number } | null }>; form: { name: string; code: string; label: string; source: string }; setForm: (value: { name: string; code: string; label: string; source: string }) => void; selected: string; setSelected: (id: string) => void; canWrite: boolean; canReview: boolean; currentUserId?: number; create: () => void; review: (id: string, decision: "human_reviewed" | "approved_for_demo_study") => void; pending: boolean }) {
  const { t } = useTranslation();
  const placeholders = { name: t("research.name"), code: t("research.demoCode"), label: t("research.label"), source: t("research.sourceRef") };
  return <section className="grid gap-4 lg:grid-cols-2"><div className="surface-card p-5"><h3 className="font-black">{t("research.conceptSets")}</h3><div className="mt-4 grid gap-2">{concepts.map((item) => <button className={`rounded-xl border p-3 text-left ${selected === item.version?.id ? "border-cyan-400 bg-cyan-50" : "border-slate-200"}`} key={item.id} onClick={() => setSelected(item.version?.id ?? "")} type="button"><span className="font-extrabold">{item.name}</span><span className="mt-1 block text-xs text-slate-500">{formatStatus(item.status)}</span>{canReview && item.version && item.version.authored_by_user_id !== currentUserId && item.version.status === "terminology_matched" ? <span className="btn-secondary mt-2" onClick={(event) => { event.stopPropagation(); review(item.version!.id, "human_reviewed"); }}>{t("research.reviewTerminology")}</span> : null}{canReview && item.version?.status === "human_reviewed" ? <span className="btn-secondary mt-2" onClick={(event) => { event.stopPropagation(); review(item.version!.id, "approved_for_demo_study"); }}>{t("research.approveDemo")}</span> : null}</button>)}</div></div>{canWrite ? <form className="surface-card grid content-start gap-3 p-5" onSubmit={(event) => { event.preventDefault(); create(); }}><h3 className="font-black">{t("research.newConceptSet")}</h3>{(["name", "code", "label", "source"] as const).map((field) => <input aria-label={placeholders[field]} className="field" key={field} onChange={(event) => setForm({ ...form, [field]: event.target.value })} placeholder={placeholders[field]} value={form[field]} />)}<button className="btn-primary" disabled={pending || Object.values(form).some((value) => value.length < 2)} type="submit">{t("research.createTerminologyVersion")}</button></form> : null}</section>;
}

function CohortPanel({ versions, name, setName, age, setAge, concept, definition, canWrite, canReview, currentUserId, create, review, pending }: { versions: Array<{ id: string; version: number; status: string; definition_hash: string; authored_by_user_id: number; query_cost: number }>; name: string; setName: (value: string) => void; age: number; setAge: (value: number) => void; concept?: string; definition: CohortDefinition; canWrite: boolean; canReview: boolean; currentUserId?: number; create: () => void; review: (id: string) => void; pending: boolean }) {
  const { t } = useTranslation();
  return <section className="grid gap-4 lg:grid-cols-[minmax(0,.8fr)_minmax(0,1.2fr)]"><form className="surface-card grid content-start gap-3 p-5" onSubmit={(event) => { event.preventDefault(); create(); }}><h3 className="font-black">{t("research.cohortBuilder")}</h3><label className="grid gap-1 text-sm font-bold">{t("research.name")}<input className="field" onChange={(event) => setName(event.target.value)} value={name} /></label><label className="grid gap-1 text-sm font-bold">{t("research.minimumAge")}<input className="field" min={0} onChange={(event) => setAge(Number(event.target.value))} type="number" value={age} /></label><div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600">{t("research.conditionConcept")}: <strong>{concept ?? t("research.notSelected")}</strong></div><details><summary className="cursor-pointer text-xs font-bold text-ocean">{t("research.advancedJson")}</summary><pre className="mt-2 overflow-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(definition, null, 2)}</pre></details>{canWrite ? <button className="btn-primary" disabled={pending || name.length < 3} type="submit">{t("research.saveVersion")}</button> : null}</form><div className="surface-card p-5"><h3 className="font-black">{t("research.versions")}</h3><div className="mt-4 grid gap-3">{versions.map((item) => <div className="rounded-xl border border-slate-200 p-4" key={item.id}><div className="flex justify-between gap-2"><p className="font-extrabold">v{item.version} · {t("research.cost", { cost: item.query_cost })}</p><Badge tone={item.status === "reviewed_demo" ? "success" : "warning"}>{formatStatus(item.status)}</Badge></div><p className="mt-2 break-all font-mono text-[0.6875rem] text-slate-500">{item.definition_hash}</p>{canReview && item.status === "draft" && item.authored_by_user_id !== currentUserId ? <button className="btn-secondary mt-3" onClick={() => review(item.id)} type="button">{t("research.reviewDsl")}</button> : null}</div>)}</div></div></section>;
}

function OutcomePanel({ outcomes, concept, canWrite, create, pending }: { outcomes: Array<{ id: string; name: string; version: number; review_status: string; definition_hash: string }>; concept?: string; canWrite: boolean; create: () => void; pending: boolean }) {
  const { t } = useTranslation();
  return <section className="surface-card p-5"><div className="flex flex-wrap justify-between gap-3"><div><h3 className="font-black">{t("research.outcomeDefinitions")}</h3><p className="text-sm text-slate-600">{t("research.selectedConcept", { concept: concept ?? t("research.none") })}</p></div>{canWrite ? <button className="btn-primary" disabled={pending} onClick={create} type="button"><Plus aria-hidden="true" className="h-4 w-4" />{t("research.createOutcome")}</button> : null}</div><div className="mt-4 grid gap-3">{outcomes.map((item) => <div className="rounded-xl border border-slate-200 p-4" key={item.id}><div className="flex justify-between gap-2"><p className="font-extrabold">{item.name} · v{item.version}</p><Badge tone="warning">{formatStatus(item.review_status)}</Badge></div><p className="mt-2 break-all font-mono text-[0.6875rem] text-slate-500">{item.definition_hash}</p></div>)}</div></section>;
}

function RunsPanel({ runs, cohorts, marker, setMarker, canExecute, execute, pending }: { runs: Array<{ id: string; result_count: number; executed_at: string; status: string; run_hash: string; attrition: Array<{ sequence: number; label: string; before_count: number; excluded_count: number; after_count: number }> }>; cohorts: Array<{ id: string; version: number; status: string }>; marker: string; setMarker: (value: string) => void; canExecute: boolean; execute: (id: string) => void; pending: boolean }) {
  const { t } = useTranslation();
  const reviewed = cohorts.filter((item) => item.status === "reviewed_demo");
  return <section className="grid gap-4"><div className="surface-card p-5"><div className="flex flex-wrap items-end gap-3"><label className="min-w-64 flex-1 text-sm font-bold">{t("research.snapshot")}<input className="field mt-1 w-full" onChange={(event) => setMarker(event.target.value)} value={marker} /></label>{canExecute ? reviewed.map((item) => <button className="btn-primary" disabled={pending || marker.length < 3} key={item.id} onClick={() => execute(item.id)} type="button"><Play aria-hidden="true" className="h-4 w-4" />{t("research.executeCohort", { version: item.version })}</button>) : null}</div></div>{runs.map((run) => <article className="surface-card p-5" key={run.id}><div className="flex flex-wrap justify-between gap-3"><div><p className="text-3xl font-black">N = {run.result_count}</p><p className="text-xs text-slate-500">{formatDateTime(run.executed_at)}</p></div><Badge tone="success">{formatStatus(run.status)}</Badge></div><AttritionFlow steps={run.attrition} /><p className="mt-4 break-all font-mono text-[0.6875rem] text-slate-500">run {run.run_hash}</p></article>)}{!runs.length ? <StatusPanel title={t("research.noRunsTitle")} tone="info">{t("research.noRunsBody")}</StatusPanel> : null}</section>;
}

function ProvenancePanel({ workspace }: { workspace: { protocol_versions: Array<{ id: string; definition_hash: string; source_refs: string[] }>; cohort_versions: Array<{ id: string; definition_hash: string }>; runs: Array<{ id: string; run_hash: string; engine_version: string; prescripta_version: string; source_version_refs: string[] }> } }) {
  const { t } = useTranslation();
  const records = [...workspace.protocol_versions.map((item) => ({ type: "protocol", id: item.id, hash: item.definition_hash, meta: item.source_refs.join(", ") })), ...workspace.cohort_versions.map((item) => ({ type: "cohort", id: item.id, hash: item.definition_hash, meta: t("research.validatedDsl") })), ...workspace.runs.map((item) => ({ type: "run", id: item.id, hash: item.run_hash, meta: `${item.engine_version} · Prescripta ${item.prescripta_version} · ${item.source_version_refs.join(", ")}` }))];
  return <section className="surface-card p-5"><div className="flex items-center gap-2"><Beaker aria-hidden="true" className="h-5 w-5 text-ocean" /><h3 className="font-black">{t("research.provenance")}</h3></div><div className="mt-4 grid gap-3">{records.map((item) => <div className="rounded-xl border border-slate-200 p-3" key={`${item.type}-${item.id}`}><p className="text-xs font-extrabold uppercase text-ocean">{humanizeTechnicalValue(item.type)}</p><p className="mt-1 break-all font-mono text-[0.6875rem]">{item.hash}</p><p className="mt-1 text-xs text-slate-500">{item.meta}</p></div>)}</div></section>;
}
