import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Download,
  FileJson,
  FileText,
  HelpCircle,
  History,
  ListChecks,
  Route,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useState } from "react";

import AlertCard from "../components/AlertCard";
import AlternativeMedicationsCard from "../components/AlternativeMedicationsCard";
import ClinicalContextGraphCard from "../components/ClinicalContextGraphCard";
import CompatibilityBadge from "../components/CompatibilityBadge";
import DoseAccumulationCard from "../components/DoseAccumulationCard";
import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import MedicationOrganProcessingCard from "../components/MedicationOrganProcessingCard";
import PatientRiskFactorsCard from "../components/PatientRiskFactorsCard";
import PrescriptionForm from "../components/PrescriptionForm";
import RagEvidencePanel from "../components/RagEvidencePanel";
import RiskBadge from "../components/RiskBadge";
import SourceBadge from "../components/SourceBadge";
import { useAuth } from "../context/AuthContext";
import {
  checkPrescription,
  downloadPatientGuidanceReport,
  downloadPrescriptionTechnicalReport,
  exportPrescriptionJson,
  explainPrescription,
  fetchPrescriptionEvidence,
  fetchPrescriptionReportPreview,
  fetchPrescriptionTimeline,
  fetchMedications,
  fetchPatients,
} from "../services/api";
import type {
  FunctionalContextSummary,
  MissingDataMode,
  PatientCounselingResponse,
  PrescriptionCheckPayload,
  PrescriptionCheckResult,
  PrescriptionExplanationPayload,
} from "../types/prescription";
import type { DecisionEvidenceItem, DecisionTimelineItem, ReportPreview } from "../types/report";

export default function PrescriptionCheck() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [lastPayload, setLastPayload] = useState<PrescriptionCheckPayload | null>(null);
  const [anonymizedReport, setAnonymizedReport] = useState(false);
  const [viewMode, setViewMode] = useState<"clinical" | "technical">("clinical");
  const { data: patients = [], isLoading: loadingPatients } = useQuery({
    queryKey: ["patients"],
    queryFn: fetchPatients,
  });
  const { data: medications = [], isLoading: loadingMedications } = useQuery({
    queryKey: ["medications"],
    queryFn: fetchMedications,
  });
  const checkMutation = useMutation({
    mutationFn: checkPrescription,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const explanationMutation = useMutation({
    mutationFn: explainPrescription,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const auditId = checkMutation.data?.audit_id ?? null;
  const reportPreviewQuery = useQuery({
    queryKey: ["prescription-report-preview", auditId, anonymizedReport],
    queryFn: () => fetchPrescriptionReportPreview(Number(auditId), anonymizedReport),
    enabled: Boolean(auditId),
  });
  const evidenceQuery = useQuery({
    queryKey: ["prescription-evidence", auditId],
    queryFn: () => fetchPrescriptionEvidence(Number(auditId)),
    enabled: Boolean(auditId),
  });
  const timelineQuery = useQuery({
    queryKey: ["prescription-timeline", auditId],
    queryFn: () => fetchPrescriptionTimeline(Number(auditId)),
    enabled: Boolean(auditId),
  });
  const technicalReportMutation = useMutation({
    mutationFn: () => downloadPrescriptionTechnicalReport(Number(auditId), anonymizedReport),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const patientGuidanceMutation = useMutation({
    mutationFn: () => downloadPatientGuidanceReport(Number(auditId)),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const exportJsonMutation = useMutation({
    mutationFn: () => exportPrescriptionJson(Number(auditId), anonymizedReport),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });

  const isLoading = loadingPatients || loadingMedications;
  const hasRequiredData = patients.length > 0 && medications.length > 0;
  const selectedMedication = lastPayload
    ? medications.find((item) => item.id === lastPayload.medication_id)
    : undefined;
  const canGenerateTechnical = user?.role === "admin" || user?.role === "medico";
  const canExport = canGenerateTechnical;
  const isTechnicalMode = viewMode === "technical";

  async function handleSubmit(payload: PrescriptionCheckPayload) {
    setLastPayload(payload);
    explanationMutation.reset();
    await checkMutation.mutateAsync(payload);
  }

  async function handleContextualAnswer(answer: string) {
    if (!lastPayload) {
      return;
    }
    const nextPayload = { ...lastPayload, contextual_activity_answer: answer };
    setLastPayload(nextPayload);
    await checkMutation.mutateAsync(nextPayload);
  }

  function buildExplanationPayload(): PrescriptionExplanationPayload | null {
    const result = checkMutation.data;
    if (!result || !lastPayload || !user) {
      return null;
    }

    const patient = patients.find((item) => item.id === lastPayload.patient_id);
    const medication = medications.find((item) => item.id === lastPayload.medication_id);
    if (!patient || !medication) {
      return null;
    }

    return {
      ...result,
      patient,
      medication,
      dose_mg: lastPayload.dose_mg,
      frequency_per_day: lastPayload.frequency_per_day,
      route: lastPayload.route,
      duration_days: lastPayload.duration_days,
      indication: lastPayload.indication,
      professional_notes: lastPayload.professional_notes,
      user_profile: user.role,
    };
  }

  async function handleExplain() {
    const payload = buildExplanationPayload();
    if (!payload) {
      return;
    }
    await explanationMutation.mutateAsync(payload);
  }

  const canExplain = Boolean(buildExplanationPayload());

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Checagem de prescrição</h1>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        {isLoading ? <LoadingState label="Carregando dados" /> : null}
        {!isLoading && !hasRequiredData ? (
          <EmptyState title="Cadastre ao menos um paciente e um medicamento" />
        ) : null}
        {!isLoading && hasRequiredData ? (
          <PrescriptionForm
            disabled={checkMutation.isPending}
            medications={medications}
            onSubmit={handleSubmit}
            patients={patients}
          />
        ) : null}
        {checkMutation.isError ? (
          <p className="mt-3 text-sm font-semibold text-danger">
            Não foi possível verificar a prescrição.
          </p>
        ) : null}
      </section>

      {checkMutation.data ? (
        <section className="grid gap-4">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-bold text-ink">Resultado</h2>
                <p className="mt-1 text-sm text-slate-600">{checkMutation.data.recommendation}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <RiskBadge status={checkMutation.data.status} />
                <RiskBadge level={checkMutation.data.risk_level} />
                <CompatibilityBadge level={checkMutation.data.compatibility.level} />
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                className={viewMode === "clinical" ? "btn-primary" : "btn-secondary"}
                onClick={() => setViewMode("clinical")}
                type="button"
              >
                <ShieldCheck aria-hidden="true" className="h-4 w-4" />
                Modo clínico
              </button>
              {canGenerateTechnical ? (
                <button
                  className={viewMode === "technical" ? "btn-primary" : "btn-secondary"}
                  onClick={() => setViewMode("technical")}
                  type="button"
                >
                  <FileJson aria-hidden="true" className="h-4 w-4" />
                  Modo técnico
                </button>
              ) : null}
            </div>
            <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
              <div>
                Revisão humana:{" "}
                <span className="font-semibold text-ink">
                  {checkMutation.data.human_review_required ? "Sim" : "Não"}
                </span>
              </div>
              <div>
                Auditoria:{" "}
                <span className="font-semibold text-ink">#{checkMutation.data.audit_id}</span>
              </div>
              <div className="sm:col-span-2">
                Fonte do medicamento:{" "}
                {selectedMedication ? (
                  <SourceBadge
                    jurisdiction={selectedMedication.source_jurisdiction}
                    source={selectedMedication.evidence_source_type}
                    status={selectedMedication.validation_status}
                  />
                ) : (
                  "-"
                )}
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-4">
              <button
                className="btn-secondary"
                disabled={!canExplain || explanationMutation.isPending}
                onClick={handleExplain}
                title="Explicar com IA"
                type="button"
              >
                <Sparkles aria-hidden="true" className="h-4 w-4" />
                {explanationMutation.isPending ? "Explicando..." : "Explicar com IA"}
              </button>
              {explanationMutation.data ? (
                <span className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-600">
                  {explanationMutation.data.used_fallback
                    ? "Fallback determinístico"
                    : "Provider configurado"}
                </span>
              ) : null}
              {explanationMutation.isError ? (
                <span className="text-sm font-semibold text-danger">
                  Não foi possível gerar a explicação.
                </span>
              ) : null}
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-4">
              <label className="flex min-h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700">
                <input
                  checked={anonymizedReport}
                  className="h-4 w-4 accent-ocean"
                  onChange={(event) => setAnonymizedReport(event.target.checked)}
                  type="checkbox"
                />
                Dados anonimizados
              </label>
              {canGenerateTechnical ? (
                <button
                  className="btn-secondary"
                  disabled={technicalReportMutation.isPending}
                  onClick={() => technicalReportMutation.mutate()}
                  title="Baixar relatório técnico"
                  type="button"
                >
                  <Download aria-hidden="true" className="h-4 w-4" />
                  {technicalReportMutation.isPending
                    ? "Gerando..."
                    : "Baixar relatório técnico"}
                </button>
              ) : null}
              <button
                className="btn-secondary"
                disabled={patientGuidanceMutation.isPending}
                onClick={() => patientGuidanceMutation.mutate()}
                title="Baixar orientação ao paciente"
                type="button"
              >
                <FileText aria-hidden="true" className="h-4 w-4" />
                {patientGuidanceMutation.isPending
                  ? "Gerando..."
                  : "Baixar orientação ao paciente"}
              </button>
              {canExport ? (
                <button
                  className="btn-secondary"
                  disabled={exportJsonMutation.isPending}
                  onClick={() => exportJsonMutation.mutate()}
                  title="Exportar JSON"
                  type="button"
                >
                  <FileJson aria-hidden="true" className="h-4 w-4" />
                  Exportar JSON
                </button>
              ) : null}
              {[technicalReportMutation, patientGuidanceMutation, exportJsonMutation].some(
                (mutation) => mutation.isError,
              ) ? (
                <span className="text-sm font-semibold text-danger">
                  Não foi possível gerar o arquivo solicitado.
                </span>
              ) : null}
            </div>
          </div>

          <DoseAccumulationCard summary={checkMutation.data.dose_summary} />

          <ClinicalIntelligenceCards
            dose={checkMutation.data.dose_intelligence}
            policy={checkMutation.data.prescribing_policy}
            psychotropic={checkMutation.data.psychotropic_safety}
            technical={isTechnicalMode}
          />

          <PatientDataConsideredCard
            clinicalView={checkMutation.data.clinical_view}
            patientBundle={checkMutation.data.patient_knowledge_bundle}
            technical={isTechnicalMode}
          />

          {isTechnicalMode ? (
            <ReportSummaryCard
              isLoading={reportPreviewQuery.isLoading}
              preview={reportPreviewQuery.data ?? null}
            />
          ) : null}

          <div className="grid gap-4 xl:grid-cols-2">
            <PatientCounselingCard counseling={checkMutation.data.patient_counseling} />
            <FunctionalContextCard
              context={checkMutation.data.patient_counseling?.functional_context ?? null}
              onAnswer={handleContextualAnswer}
            />
            <MissingDataCard mode={checkMutation.data.missing_data_mode} />
            <PracticalSafetySummaryCard counseling={checkMutation.data.patient_counseling} />
          </div>

          {isTechnicalMode ? (
          <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-bold text-ink">Compatibilidade paciente–medicação</h2>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <CompatibilityBadge level={checkMutation.data.compatibility.level} />
              <span className="text-sm font-semibold text-slate-600">
                Score demonstrativo: {checkMutation.data.compatibility.score}
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              {checkMutation.data.compatibility.educational_notice}
            </p>
            {checkMutation.data.compatibility.reasons.length ? (
              <ul className="mt-3 grid gap-2 text-sm text-slate-600">
                {checkMutation.data.compatibility.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            ) : null}
          </section>
          ) : null}

          {isTechnicalMode ? (
          <div className="grid gap-4 lg:grid-cols-2">
            <PatientRiskFactorsCard factors={checkMutation.data.patient_factors_considered} />
            <MedicationOrganProcessingCard factors={checkMutation.data.medication_factors_considered} />
          </div>
          ) : null}

          {isTechnicalMode ? <RagEvidencePanel evidence={checkMutation.data.rag_evidence} /> : null}

          {isTechnicalMode ? (
          <div className="grid gap-4 xl:grid-cols-2">
            <DecisionEvidenceCard evidence={evidenceQuery.data ?? []} />
            <DecisionTimelineCard timeline={timelineQuery.data ?? []} />
          </div>
          ) : null}

          <AlternativeMedicationsCard alternatives={checkMutation.data.alternatives} />

          {isTechnicalMode ? (
            <ClinicalContextGraphCard graph={checkMutation.data.clinical_context_graph} />
          ) : null}

          {checkMutation.data.alerts.length > 0 ? (
            <div className="grid gap-3">
              {checkMutation.data.alerts.map((alert, index) => (
                <AlertCard key={`${alert.code}-${index}`} alert={alert} />
              ))}
            </div>
          ) : (
            <EmptyState title="Nenhum alerta gerado" />
          )}

          {explanationMutation.data ? (
            <section className="rounded-lg border border-cyan-100 bg-white p-5 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-ocean">
                  <FileText aria-hidden="true" className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-ink">Explicação assistida</h2>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {explanationMutation.data.simple_explanation}
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
                <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                  <h3 className="text-sm font-bold text-ink">Resumo técnico</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {explanationMutation.data.technical_summary}
                  </p>
                </div>

                <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                  <h3 className="text-sm font-bold text-ink">Perguntas de revisão</h3>
                  <ul className="mt-2 grid gap-2 text-sm leading-6 text-slate-600">
                    {explanationMutation.data.review_questions.map((question) => (
                      <li key={question}>{question}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-medium leading-6 text-amber-900">
                {explanationMutation.data.educational_notice}
              </p>
              {explanationMutation.data.missing_patient_data.length ? (
                <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <h3 className="text-sm font-bold text-ink">Dados ainda faltantes</h3>
                  <p className="mt-2 text-sm text-slate-600">
                    {explanationMutation.data.missing_patient_data.join(", ")}
                  </p>
                </div>
              ) : null}
              {explanationMutation.data.how_to_explain_to_patient ? (
                <div className="mt-4 rounded-lg border border-cyan-100 bg-cyan-50 p-4">
                  <h3 className="text-sm font-bold text-ink">Como explicar ao paciente</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-700">
                    {explanationMutation.data.how_to_explain_to_patient}
                  </p>
                </div>
              ) : null}
            </section>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function ClinicalIntelligenceCards({
  dose,
  policy,
  psychotropic,
  technical,
}: {
  dose: PrescriptionCheckResult["dose_intelligence"];
  policy: PrescriptionCheckResult["prescribing_policy"];
  psychotropic: PrescriptionCheckResult["psychotropic_safety"];
  technical: boolean;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      <section className="rounded-lg border border-cyan-100 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-ink">Dose Intelligence</h2>
        <p className="mt-2 text-sm text-slate-600">Status: {dose.status}</p>
        <p className="mt-1 text-sm text-slate-600">
          Faixa calculada: {dose.calculated_dose ?? "dados insuficientes"} {dose.calculated_unit}
        </p>
        <p className="mt-3 text-xs leading-5 text-slate-500">{dose.educational_notice}</p>
        {technical ? <pre className="mt-3 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(dose, null, 2)}</pre> : null}
      </section>
      <section className="rounded-lg border border-violet-100 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-ink">Segurança psicotrópica</h2>
        <p className="mt-2 text-sm text-slate-600">{psychotropic.length} sinal(is) para revisão.</p>
        <ul className="mt-3 grid gap-2 text-sm text-slate-700">
          {psychotropic.slice(0, 4).map((signal) => <li key={signal.code}>{signal.title}</li>)}
        </ul>
        {technical ? <pre className="mt-3 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(psychotropic, null, 2)}</pre> : null}
      </section>
      <section className="rounded-lg border border-amber-100 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-ink">Política de prescrição</h2>
        <p className="mt-2 text-sm font-semibold text-slate-700">{policy.status}</p>
        <p className="mt-2 text-sm text-slate-600">Requer revisão: {policy.requires_human_review ? "Sim" : "Não"}</p>
        {policy.warnings.map((warning) => <p className="mt-2 text-xs text-amber-900" key={warning}>{warning}</p>)}
        {technical ? <pre className="mt-3 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(policy, null, 2)}</pre> : null}
      </section>
    </div>
  );
}

function PatientDataConsideredCard({
  clinicalView,
  patientBundle,
  technical,
}: {
  clinicalView: {
    patient_data_considered: Array<{ label: string; value: string }>;
    missing_data: string[];
    relevant_alerts: Array<{ code: string; title: string; severity: string; recommendation: string }>;
  };
  patientBundle: { reviewed_documents?: Array<Record<string, unknown>>; timeline?: Array<Record<string, unknown>> };
  technical: boolean;
}) {
  const considered = clinicalView.patient_data_considered ?? [];
  return (
    <section className="rounded-lg border border-cyan-100 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-bold text-ink">Dados do paciente considerados</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            Peso, idade, altura, alergias, medicamentos, condições e histórico revisado entram como
            contexto quando há regra cadastrada.
          </p>
        </div>
        <span className="w-fit rounded-lg bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-900">
          {technical ? "detalhes técnicos visíveis" : "visão clínica"}
        </span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {considered.length ? (
          considered.map((item) => (
            <div className="rounded-lg border border-slate-100 bg-slate-50 p-3" key={item.label}>
              <p className="text-xs font-bold uppercase tracking-normal text-slate-500">
                {item.label}
              </p>
              <p className="mt-1 text-sm font-semibold text-ink">{item.value}</p>
            </div>
          ))
        ) : (
          <p className="text-sm text-slate-600">Nenhum dado contextual disponível.</p>
        )}
      </div>
      {clinicalView.missing_data.length ? (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-sm font-bold text-amber-950">Dados faltantes</h3>
          <p className="mt-2 text-sm leading-6 text-amber-950">
            {clinicalView.missing_data.join(", ")}
          </p>
        </div>
      ) : null}
      {technical ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <h3 className="text-sm font-bold text-ink">Bundle do paciente</h3>
            <p className="mt-2 text-sm text-slate-600">
              Documentos revisados: {patientBundle.reviewed_documents?.length ?? 0}
            </p>
            <p className="mt-1 text-sm text-slate-600">
              Eventos na linha do tempo: {patientBundle.timeline?.length ?? 0}
            </p>
          </div>
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <h3 className="text-sm font-bold text-ink">Alertas relevantes</h3>
            <div className="mt-2 grid gap-2 text-sm text-slate-600">
              {clinicalView.relevant_alerts.length
                ? clinicalView.relevant_alerts.slice(0, 4).map((alert) => (
                    <p key={alert.code}>
                      {alert.title}: {alert.recommendation}
                    </p>
                  ))
                : "Sem alertas relevantes."}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function ReportSummaryCard({
  preview,
  isLoading,
}: {
  preview: ReportPreview | null;
  isLoading: boolean;
}) {
  if (isLoading) {
    return <LoadingState label="Preparando resumo do relatório" />;
  }
  if (!preview) {
    return null;
  }
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <ShieldCheck aria-hidden="true" className="h-5 w-5 text-ocean" />
            <h2 className="text-lg font-bold text-ink">Resumo do relatório</h2>
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
              {preview.narrative_metadata.fallback_used
                ? "Fallback determinístico"
                : "Narrativa por IA"}
            </span>
            {preview.report_mode === "anonymized" ? (
              <span className="rounded-lg bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-800">
                Dados anonimizados
              </span>
            ) : null}
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            {preview.narrative.executive_summary}
          </p>
        </div>
        <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
          <p>Provider: {preview.narrative_metadata.provider}</p>
          <p>Modelo: {preview.narrative_metadata.model ?? "determinístico"}</p>
          <p>Confiança: {Math.round(preview.narrative.confidence * 100)}%</p>
        </div>
      </div>
      <p className="mt-4 break-all rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-600">
        EvidenceBundle {preview.evidence_bundle_hash}
      </p>
    </section>
  );
}

function DecisionEvidenceCard({ evidence }: { evidence: DecisionEvidenceItem[] }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <ShieldCheck aria-hidden="true" className="h-5 w-5 text-ocean" />
        <h2 className="text-lg font-bold text-ink">Evidências da decisão</h2>
      </div>
      <div className="mt-4 grid gap-3">
        {evidence.length ? (
          evidence.map((item, index) => (
            <article className="rounded-lg border border-slate-100 bg-slate-50 p-3" key={index}>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-bold text-ink">{item.code ?? item.source_id}</span>
                {item.severity ? <RiskBadge level={item.severity as never} /> : null}
                <SourceBadge
                  jurisdiction={item.jurisdiction ?? "BR"}
                  source={item.evidence_type ?? item.source_name ?? "fonte"}
                  status={item.validation_status ?? "interno"}
                />
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {item.evidence_summary ?? item.source_name ?? "Fonte registrada no bundle."}
              </p>
            </article>
          ))
        ) : (
          <p className="text-sm text-slate-600">Nenhuma evidência adicional registrada.</p>
        )}
      </div>
    </section>
  );
}

function DecisionTimelineCard({ timeline }: { timeline: DecisionTimelineItem[] }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <History aria-hidden="true" className="h-5 w-5 text-ocean" />
        <h2 className="text-lg font-bold text-ink">Linha do tempo da decisão</h2>
      </div>
      <ol className="mt-4 grid gap-3">
        {timeline.length ? (
          timeline.map((item) => (
            <li className="flex gap-3" key={`${item.order}-${item.title}`}>
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-xs font-bold text-ocean">
                {item.order}
              </span>
              <div>
                <p className="font-semibold text-ink">{item.title}</p>
                <p className="mt-1 text-sm text-slate-600">{item.status}</p>
              </div>
            </li>
          ))
        ) : (
          <li className="text-sm text-slate-600">Sem eventos de timeline.</li>
        )}
      </ol>
    </section>
  );
}

function PatientCounselingCard({
  counseling,
}: {
  counseling: PatientCounselingResponse | null;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-ocean">
          <ListChecks aria-hidden="true" className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-ink">Orientações ao paciente</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {counseling?.educational_notice ?? "Resumo prático não disponível."}
          </p>
        </div>
      </div>
      <ul className="mt-4 grid gap-2 text-sm leading-6 text-slate-700">
        {(counseling?.orientation_points.length
          ? counseling.orientation_points
          : ["Gerar ou revisar resumo prático para este medicamento."]
        ).map((item) => (
          <li className="rounded-lg bg-slate-50 px-3 py-2" key={item}>
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

function FunctionalContextCard({
  context,
  onAnswer,
}: {
  context: FunctionalContextSummary | null;
  onAnswer: (answer: string) => Promise<void>;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-ocean">
          <Route aria-hidden="true" className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-ink">Contexto funcional</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {context?.profile_known ? "Perfil funcional cadastrado." : "Dados funcionais desconhecidos."}
          </p>
        </div>
      </div>
      <div className="mt-4 grid gap-2 text-sm leading-6 text-slate-700">
        {[...(context?.personalized_warnings ?? []), ...(context?.generic_warnings ?? [])].map(
          (item) => (
            <p className="rounded-lg bg-slate-50 px-3 py-2" key={item}>
              {item}
            </p>
          ),
        )}
      </div>
      {context?.question.should_ask ? (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <div className="flex gap-3">
            <HelpCircle aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-amber-800" />
            <div>
              <p className="text-sm font-semibold leading-6 text-amber-950">
                {context.question.question}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {["Sim", "Não", "Não informado"].map((answer) => (
                  <button
                    className="btn-secondary bg-white"
                    key={answer}
                    onClick={() => onAnswer(answer)}
                    type="button"
                  >
                    {answer}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function MissingDataCard({ mode }: { mode: MissingDataMode | null }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-50 text-amber-700">
          <AlertTriangle aria-hidden="true" className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-ink">Dados faltantes</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {mode?.message ?? "Histórico clínico não avaliado."}
          </p>
        </div>
      </div>
      {mode?.missing_data.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {mode.missing_data.map((item) => (
            <span
              className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-bold text-amber-900"
              key={item}
            >
              {item}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm font-semibold text-slate-600">Sem faltas principais.</p>
      )}
      {mode ? (
        <p className="mt-4 text-sm leading-6 text-slate-600">{mode.limitation_summary}</p>
      ) : null}
    </section>
  );
}

function PracticalSafetySummaryCard({
  counseling,
}: {
  counseling: PatientCounselingResponse | null;
}) {
  const summary = counseling?.summary;
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-bold text-ink">Resumo prático de segurança</h2>
      {summary ? (
        <div className="mt-4 grid gap-3">
          <p className="text-sm leading-6 text-slate-600">{summary.professional_summary}</p>
          <div className="flex flex-wrap gap-2">
            <SourceBadge
              jurisdiction={summary.jurisdiction}
              source={summary.generated_by}
              status={summary.validation_status}
            />
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
              {summary.requires_review ? "pendente de revisão" : "revisado"}
            </span>
            <span className="rounded-lg bg-slate-100 px-3 py-1 text-xs font-bold text-slate-700">
              fonte: {summary.source_name}
            </span>
          </div>
          <div className="grid gap-2 text-sm text-slate-700">
            <p>Efeitos: {summary.main_adverse_effects.join(", ") || "-"}</p>
            <p>Alertas: {summary.red_flags.join(", ") || "-"}</p>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-600">Resumo prático ainda não gerado.</p>
      )}
    </section>
  );
}
