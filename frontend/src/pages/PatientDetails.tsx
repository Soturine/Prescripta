import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import ClinicalContextGraphCard from "../components/ClinicalContextGraphCard";
import ClinicalProfileCard from "../components/ClinicalProfileCard";
import LoadingState from "../components/LoadingState";
import PatientForm from "../components/PatientForm";
import QuickTriageForm from "../components/QuickTriageForm";
import { useAuth } from "../context/AuthContext";
import {
  fetchPatient,
  fetchPatientClinicalContext,
  quickTriagePatient,
  updatePatient,
} from "../services/api";
import type { PatientPayload, QuickTriagePayload } from "../types/patient";

export default function PatientDetails() {
  const { canAccess } = useAuth();
  const canManagePatient = canAccess(["admin", "medico"]);
  const queryClient = useQueryClient();
  const params = useParams();
  const patientId = Number(params.patientId);
  const { data: patient, isLoading } = useQuery({
    queryKey: ["patients", patientId],
    queryFn: () => fetchPatient(patientId),
    enabled: Number.isFinite(patientId),
  });
  const { data: clinicalContext } = useQuery({
    queryKey: ["patients", patientId, "clinical-context"],
    queryFn: () => fetchPatientClinicalContext(patientId),
    enabled: Number.isFinite(patientId),
  });
  const updateMutation = useMutation({
    mutationFn: (payload: PatientPayload) => updatePatient(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId] });
    },
  });
  const quickTriageMutation = useMutation({
    mutationFn: (payload: QuickTriagePayload) => quickTriagePatient(patientId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId] });
      await queryClient.invalidateQueries({ queryKey: ["patients", patientId, "clinical-context"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
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
        {canManagePatient ? (
          <>
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
          </>
        ) : (
          <dl className="grid gap-4 text-sm md:grid-cols-2">
            <div>
              <dt className="label">Idade</dt>
              <dd className="mt-1 font-semibold text-ink">{patient.age ?? "-"}</dd>
            </div>
            <div>
              <dt className="label">Peso</dt>
              <dd className="mt-1 font-semibold text-ink">{patient.weight_kg} kg</dd>
            </div>
            <div>
              <dt className="label">Alergias</dt>
              <dd className="mt-1 font-semibold text-ink">
                {patient.allergies.join(", ") || "-"}
              </dd>
            </div>
            <div>
              <dt className="label">Comorbidades</dt>
              <dd className="mt-1 font-semibold text-ink">
                {patient.comorbidities.join(", ") || "-"}
              </dd>
            </div>
            <div className="md:col-span-2">
              <dt className="label">Medicamentos contínuos</dt>
              <dd className="mt-1 font-semibold text-ink">
                {patient.current_medications.join(", ") || "-"}
              </dd>
            </div>
          </dl>
        )}
      </section>

      <ClinicalProfileCard patient={patient} />

      {canManagePatient ? (
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold text-ink">Triagem rápida</h2>
          <div className="mt-5">
            <QuickTriageForm
              onSubmit={async (payload) => {
                await quickTriageMutation.mutateAsync(payload);
              }}
            />
          </div>
          {quickTriageMutation.isSuccess ? (
            <p className="mt-3 text-sm font-semibold text-mint">Triagem atualizada.</p>
          ) : null}
        </section>
      ) : null}

      {clinicalContext ? <ClinicalContextGraphCard graph={clinicalContext} /> : null}
    </div>
  );
}
