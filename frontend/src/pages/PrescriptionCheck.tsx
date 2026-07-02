import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Sparkles } from "lucide-react";
import { useState } from "react";

import AlertCard from "../components/AlertCard";
import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import PrescriptionForm from "../components/PrescriptionForm";
import RiskBadge from "../components/RiskBadge";
import { useAuth } from "../context/AuthContext";
import {
  checkPrescription,
  explainPrescription,
  fetchMedications,
  fetchPatients,
} from "../services/api";
import type {
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

  async function handleSubmit(payload: PrescriptionCheckPayload) {
    setLastPayload(payload);
    explanationMutation.reset();
    await checkMutation.mutateAsync(payload);
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
            </section>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
