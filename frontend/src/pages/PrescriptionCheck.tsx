import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AlertCard from "../components/AlertCard";
import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import PrescriptionForm from "../components/PrescriptionForm";
import RiskBadge from "../components/RiskBadge";
import { checkPrescription, fetchMedications, fetchPatients } from "../services/api";
import type { PrescriptionCheckPayload } from "../types/prescription";

export default function PrescriptionCheck() {
  const queryClient = useQueryClient();
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

  const isLoading = loadingPatients || loadingMedications;
  const hasRequiredData = patients.length > 0 && medications.length > 0;

  async function handleSubmit(payload: PrescriptionCheckPayload) {
    await checkMutation.mutateAsync(payload);
  }

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
        </section>
      ) : null}
    </div>
  );
}
