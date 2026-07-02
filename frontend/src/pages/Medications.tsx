import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil } from "lucide-react";
import { useState } from "react";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import MedicationForm from "../components/MedicationForm";
import { useAuth } from "../context/AuthContext";
import { createMedication, fetchMedications, updateMedication } from "../services/api";
import type { Medication, MedicationPayload } from "../types/medication";
import { formatDose, joinList } from "../utils/formatters";

export default function Medications() {
  const { canAccess } = useAuth();
  const canManageMedication = canAccess(["admin"]);
  const [selectedMedication, setSelectedMedication] = useState<Medication | undefined>();
  const queryClient = useQueryClient();
  const { data: medications = [], isLoading } = useQuery({
    queryKey: ["medications"],
    queryFn: fetchMedications,
  });
  const createMutation = useMutation({
    mutationFn: createMedication,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["medications"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
  const updateMutation = useMutation({
    mutationFn: (payload: MedicationPayload) =>
      updateMedication(Number(selectedMedication?.id), payload),
    onSuccess: async () => {
      setSelectedMedication(undefined);
      await queryClient.invalidateQueries({ queryKey: ["medications"] });
    },
  });

  async function handleSubmit(payload: MedicationPayload) {
    if (selectedMedication) {
      await updateMutation.mutateAsync(payload);
      return;
    }
    await createMutation.mutateAsync(payload);
  }

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Medicamentos</h1>
      </header>

      {canManageMedication ? (
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold text-ink">
            {selectedMedication ? "Editar medicamento" : "Novo medicamento"}
          </h2>
          <div className="mt-5">
            <MedicationForm
              key={selectedMedication?.id ?? "new"}
              initialMedication={selectedMedication}
              onSubmit={handleSubmit}
              submitLabel={selectedMedication ? "Salvar medicamento" : "Criar medicamento"}
            />
          </div>
          {selectedMedication ? (
            <button
              className="btn-secondary mt-3"
              onClick={() => setSelectedMedication(undefined)}
              type="button"
            >
              Cancelar edição
            </button>
          ) : null}
          {createMutation.isError || updateMutation.isError ? (
            <p className="mt-3 text-sm font-semibold text-danger">
              Não foi possível salvar medicamento.
            </p>
          ) : null}
        </section>
      ) : null}

      <section className="grid gap-3">
        <h2 className="text-lg font-bold text-ink">Lista de medicamentos</h2>
        {isLoading ? <LoadingState label="Carregando medicamentos" /> : null}
        {!isLoading && medications.length === 0 ? (
          <EmptyState title="Nenhum medicamento cadastrado" />
        ) : null}
        {!isLoading && medications.length > 0 ? (
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[880px] text-left text-sm">
                <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Nome</th>
                    <th className="px-4 py-3">Princípio ativo</th>
                    <th className="px-4 py-3">Classe</th>
                    <th className="px-4 py-3">Dose máxima</th>
                    <th className="px-4 py-3">Vias</th>
                    <th className="px-4 py-3 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {medications.map((medication) => (
                    <tr key={medication.id} className="text-slate-700">
                      <td className="px-4 py-3 font-semibold text-ink">{medication.brand_name}</td>
                      <td className="px-4 py-3">{medication.active_ingredient}</td>
                      <td className="px-4 py-3">{medication.therapeutic_class}</td>
                      <td className="px-4 py-3">{formatDose(medication.max_daily_dose_mg)}</td>
                      <td className="px-4 py-3">{joinList(medication.allowed_routes)}</td>
                      <td className="px-4 py-3 text-right">
                        {canManageMedication ? (
                          <button
                            className="btn-secondary"
                            onClick={() => setSelectedMedication(medication)}
                            title={`Editar ${medication.brand_name}`}
                            type="button"
                          >
                            <Pencil aria-hidden="true" className="h-4 w-4" />
                            Editar
                          </button>
                        ) : (
                          "-"
                        )}
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
