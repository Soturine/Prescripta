import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import PatientForm from "../components/PatientForm";
import { fetchPatient, updatePatient } from "../services/api";
import type { PatientPayload } from "../types/patient";

export default function PatientDetails() {
  const queryClient = useQueryClient();
  const params = useParams();
  const patientId = Number(params.patientId);
  const { data: patient, isLoading } = useQuery({
    queryKey: ["patients", patientId],
    queryFn: () => fetchPatient(patientId),
    enabled: Number.isFinite(patientId),
  });
  const updateMutation = useMutation({
    mutationFn: (payload: PatientPayload) => updatePatient(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId] });
    },
  });

  if (isLoading) {
    return <LoadingState label="Carregando paciente" />;
  }

  if (!patient) {
    return (
      <div className="grid gap-4">
        <Link className="btn-secondary w-fit" to="/patients">
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          Voltar
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">
          Paciente não encontrado.
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-normal text-ink">{patient.name}</h1>
          <p className="mt-1 text-sm text-slate-500">Cadastro de paciente</p>
        </div>
        <Link className="btn-secondary w-fit" to="/patients">
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          Voltar
        </Link>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <PatientForm
          key={patient.id}
          initialPatient={patient}
          onSubmit={async (payload) => {
            await updateMutation.mutateAsync(payload);
          }}
          submitLabel="Salvar paciente"
        />
        {updateMutation.isError ? (
          <p className="mt-3 text-sm font-semibold text-danger">Não foi possível salvar.</p>
        ) : null}
        {updateMutation.isSuccess ? (
          <p className="mt-3 text-sm font-semibold text-mint">Paciente atualizado.</p>
        ) : null}
      </section>
    </div>
  );
}
