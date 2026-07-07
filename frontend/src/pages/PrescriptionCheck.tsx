import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, FileText, HelpCircle, ListChecks, Route, Sparkles } from "lucide-react";
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
  explainPrescription,
  fetchMedications,
  fetchPatients,
} from "../services/api";
import type {
  FunctionalContextSummary,
  MissingDataMode,
  PatientCounselingResponse,
  PrescriptionCheckPayload,
  PrescriptionExplanationPayload,
} from "../types/prescription";

export default function PrescriptionCheck() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [lastPayload, setLastPayload] = useState<PrescriptionCheckPayload | null>(null);
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

  const isLoading = loadingPatients || loadingMedications;
  const hasRequiredData = patients.length > 0 && medications.length > 0;
  const selectedMedication = lastPayload
    ? medications.find((item) => item.id === lastPayload.medication_id)
    : undefined;

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
          </div>

          <DoseAccumulationCard summary={checkMutation.data.dose_summary} />

          <div className="grid gap-4 xl:grid-cols-2">
            <PatientCounselingCard counseling={checkMutation.data.patient_counseling} />
            <FunctionalContextCard
              context={checkMutation.data.patient_counseling?.functional_context ?? null}
              onAnswer={handleContextualAnswer}
            />
            <MissingDataCard mode={checkMutation.data.missing_data_mode} />
            <PracticalSafetySummaryCard counseling={checkMutation.data.patient_counseling} />
          </div>

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

          <div className="grid gap-4 lg:grid-cols-2">
            <PatientRiskFactorsCard factors={checkMutation.data.patient_factors_considered} />
            <MedicationOrganProcessingCard factors={checkMutation.data.medication_factors_considered} />
          </div>

          <RagEvidencePanel evidence={checkMutation.data.rag_evidence} />

          <AlternativeMedicationsCard alternatives={checkMutation.data.alternatives} />

          <ClinicalContextGraphCard graph={checkMutation.data.clinical_context_graph} />

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
          <h2 className="text-lg font-bold text-ink">Orientacoes ao paciente</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {counseling?.educational_notice ?? "Resumo pratico nao disponivel."}
          </p>
        </div>
      </div>
      <ul className="mt-4 grid gap-2 text-sm leading-6 text-slate-700">
        {(counseling?.orientation_points.length
          ? counseling.orientation_points
          : ["Gerar ou revisar resumo pratico para este medicamento."]
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
                {["Sim", "Nao", "Nao informado"].map((answer) => (
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
            {mode?.message ?? "Historico clinico nao avaliado."}
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
      <h2 className="text-lg font-bold text-ink">Resumo pratico de seguranca</h2>
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
              {summary.requires_review ? "pendente de revisao" : "revisado"}
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
        <p className="mt-4 text-sm text-slate-600">Resumo pratico ainda nao gerado.</p>
      )}
    </section>
  );
}
