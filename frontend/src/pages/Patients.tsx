import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import PatientForm from "../components/PatientForm";
import { useAuth } from "../context/AuthContext";
import { createPatient, fetchPatients } from "../services/api";
import type { PatientPayload } from "../types/patient";
import { joinList } from "../utils/formatters";

export default function Patients() {
  const { canAccess } = useAuth();
  const canManagePatients = canAccess(["admin", "medico"]);
  const queryClient = useQueryClient();
  const { data: patients = [], isLoading } = useQuery({
    queryKey: ["patients"],
    queryFn: fetchPatients,
  });
  const createMutation = useMutation({
    mutationFn: createPatient,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  async function handleCreate(payload: PatientPayload) {
    await createMutation.mutateAsync(payload);
  }

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Pacientes</h1>
      </header>

      {canManagePatients ? (
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold text-ink">Novo paciente</h2>
          <div className="mt-5">
            <PatientForm onSubmit={handleCreate} submitLabel="Criar paciente" />
          </div>
          {createMutation.isError ? (
            <p className="mt-3 text-sm font-semibold text-danger">
              Não foi possível criar paciente.
            </p>
          ) : null}
        </section>
      ) : null}

      <section className="grid gap-3">
        <h2 className="text-lg font-bold text-ink">Lista de pacientes</h2>
        {isLoading ? <LoadingState label="Carregando pacientes" /> : null}
        {!isLoading && patients.length === 0 ? (
          <EmptyState title="Nenhum paciente cadastrado" />
        ) : null}
        {!isLoading && patients.length > 0 ? (
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Nome</th>
                    <th className="px-4 py-3">Idade</th>
                    <th className="px-4 py-3">Alergias</th>
                    <th className="px-4 py-3">Medicamentos contínuos</th>
                    <th className="px-4 py-3 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {patients.map((patient) => (
                    <tr key={patient.id} className="text-slate-700">
                      <td className="px-4 py-3 font-semibold text-ink">{patient.name}</td>
                      <td className="px-4 py-3">{patient.age ?? "-"}</td>
                      <td className="px-4 py-3">{joinList(patient.allergies) || "-"}</td>
                      <td className="px-4 py-3">
                        {joinList(patient.current_medications) || "-"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          className="btn-secondary"
                          title={`Ver ${patient.name}`}
                          to={`/patients/${patient.id}`}
                        >
                          <ArrowRight aria-hidden="true" className="h-4 w-4" />
                          Ver
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}
