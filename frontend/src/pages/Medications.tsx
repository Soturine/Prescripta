import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Database, ExternalLink, Pencil, Search } from "lucide-react";
import { useState } from "react";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import MedicationForm from "../components/MedicationForm";
import SourceBadge from "../components/SourceBadge";
import { useAuth } from "../context/AuthContext";
import {
  createMedication,
  fetchActiveIngredients,
  fetchMedications,
  lookupAnvisaSource,
  searchMedicationCatalog,
  updateMedication,
} from "../services/api";
import type { Medication, MedicationPayload } from "../types/medication";
import { formatDose, joinList } from "../utils/formatters";

export default function Medications() {
  const { canAccess } = useAuth();
  const canManageMedication = canAccess(["admin"]);
  const [selectedMedication, setSelectedMedication] = useState<Medication | undefined>();
  const [catalogQuery, setCatalogQuery] = useState("Novalgina");
  const queryClient = useQueryClient();
  const { data: medications = [], isLoading } = useQuery({
    queryKey: ["medications"],
    queryFn: fetchMedications,
  });
  const { data: activeIngredients = [] } = useQuery({
    queryKey: ["active-ingredients"],
    queryFn: fetchActiveIngredients,
  });
  const { data: catalogResults = [], isFetching: searchingCatalog } = useQuery({
    queryKey: ["medication-catalog", catalogQuery],
    queryFn: () => searchMedicationCatalog(catalogQuery),
    enabled: catalogQuery.trim().length >= 2,
  });
  const { data: anvisaLookup } = useQuery({
    queryKey: ["anvisa-lookup", catalogQuery],
    queryFn: () => lookupAnvisaSource(catalogQuery),
    enabled: catalogQuery.trim().length >= 2,
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

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-bold text-ink">Busca por principio ativo ou alias</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Nomes comerciais apontam para o principio ativo DCB quando cadastrados no catalogo
              local.
            </p>
          </div>
          <label className="grid min-w-[260px] gap-1.5">
            <span className="label">Pesquisar</span>
            <span className="relative">
              <Search
                aria-hidden="true"
                className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400"
              />
              <input
                className="field pl-9"
                onChange={(event) => setCatalogQuery(event.target.value)}
                placeholder="Novalgina, Anador, dipirona"
                value={catalogQuery}
              />
            </span>
          </label>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-bold text-ink">Resultado do catalogo</h3>
              {searchingCatalog ? (
                <span className="text-xs font-semibold text-slate-500">buscando...</span>
              ) : null}
            </div>
            <div className="mt-3 grid gap-3">
              {catalogResults.length ? (
                catalogResults.map((result) => (
                  <article className="rounded-lg border border-slate-200 bg-white p-3" key={result.active_ingredient.id}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-bold text-ink">
                          {result.active_ingredient.dcb_name}
                        </p>
                        <p className="mt-1 text-xs font-semibold text-slate-500">
                          {result.match_type === "brand_alias"
                            ? "Alias comercial resolvido"
                            : "Principio ativo"}
                        </p>
                      </div>
                      <SourceBadge
                        jurisdiction={result.active_ingredient.jurisdiction}
                        source={result.active_ingredient.source}
                        status={result.active_ingredient.validation_status}
                      />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {result.active_ingredient.common_brands.map((brand) => (
                        <span className="rounded-lg bg-cyan-50 px-2 py-1 text-xs font-bold text-cyan-900" key={brand}>
                          {brand}
                        </span>
                      ))}
                    </div>
                    <p className="mt-3 text-sm text-slate-600">
                      Classes: {joinList(result.active_ingredient.therapeutic_classes) || "-"}
                    </p>
                  </article>
                ))
              ) : (
                <p className="text-sm text-slate-500">Nenhum resultado local para a busca atual.</p>
              )}
            </div>
          </div>

          <div className="rounded-lg border border-amber-100 bg-amber-50 p-4">
            <div className="flex items-center gap-2">
              <Database aria-hidden="true" className="h-4 w-4 text-amber-800" />
              <h3 className="text-sm font-bold text-amber-950">Fonte Anvisa/DCB</h3>
            </div>
            {anvisaLookup ? (
              <div className="mt-3 grid gap-2 text-sm leading-6 text-amber-950">
                <SourceBadge
                  jurisdiction={anvisaLookup.jurisdiction}
                  source={anvisaLookup.source}
                  status={anvisaLookup.validation_status}
                />
                <p>Status: {anvisaLookup.status}</p>
                <p>Principio ativo: {anvisaLookup.active_ingredient ?? "pendente"}</p>
                <p>{anvisaLookup.guidance}</p>
                <a
                  className="inline-flex w-fit items-center gap-2 text-sm font-bold text-amber-950 underline"
                  href={anvisaLookup.source_url}
                  rel="noreferrer"
                  target="_blank"
                >
                  Abrir busca oficial
                  <ExternalLink aria-hidden="true" className="h-4 w-4" />
                </a>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold text-ink">Catalogo de principios ativos</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {activeIngredients.map((ingredient) => (
              <span
                className="inline-flex min-h-9 items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700"
                key={ingredient.id}
              >
                {ingredient.dcb_name}
                <SourceBadge
                  jurisdiction={ingredient.jurisdiction}
                  source={ingredient.source}
                  status={ingredient.validation_status}
                />
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold text-ink">Politica de conflito de fontes</h2>
          <div className="mt-3 grid gap-2 text-sm leading-6 text-slate-600">
            <p>Para contexto brasileiro, fontes BR/Anvisa/DCB tem prioridade.</p>
            <p>Fontes internacionais entram como apoio secundario e precisam de aviso claro.</p>
            <p>Dipirona/metamizol e exibida como diferenca regulatoria, nao como erro automatico.</p>
          </div>
        </div>
      </section>

      {canManageMedication ? (
        <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-bold text-ink">
            {selectedMedication ? "Editar medicamento" : "Novo medicamento"}
          </h2>
          <div className="mt-5">
            <MedicationForm
              activeIngredients={activeIngredients}
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
              Cancelar edicao
            </button>
          ) : null}
          {createMutation.isError || updateMutation.isError ? (
            <p className="mt-3 text-sm font-semibold text-danger">
              Nao foi possivel salvar medicamento.
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
              <table className="w-full min-w-[1240px] text-left text-sm">
                <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Nome</th>
                    <th className="px-4 py-3">Principio ativo</th>
                    <th className="px-4 py-3">Aliases</th>
                    <th className="px-4 py-3">Fonte</th>
                    <th className="px-4 py-3">Classe</th>
                    <th className="px-4 py-3">Dose maxima</th>
                    <th className="px-4 py-3">Cautelas</th>
                    <th className="px-4 py-3">Vias</th>
                    <th className="px-4 py-3 text-right">Acao</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {medications.map((medication) => (
                    <tr key={medication.id} className="text-slate-700">
                      <td className="px-4 py-3 font-semibold text-ink">{medication.brand_name}</td>
                      <td className="px-4 py-3">{medication.active_ingredient}</td>
                      <td className="px-4 py-3">{joinList(medication.commercial_aliases) || "-"}</td>
                      <td className="px-4 py-3">
                        <SourceBadge
                          jurisdiction={medication.source_jurisdiction}
                          source={medication.evidence_source_type}
                          status={medication.validation_status}
                        />
                      </td>
                      <td className="px-4 py-3">{medication.therapeutic_class}</td>
                      <td className="px-4 py-3">{formatDose(medication.max_daily_dose_mg)}</td>
                      <td className="px-4 py-3">
                        {[
                          medication.renal_caution ? "renal" : "",
                          medication.hepatic_caution ? "hepatica" : "",
                          medication.gastrointestinal_caution ? "gastrointestinal" : "",
                          medication.elderly_caution ? "idosos" : "",
                        ]
                          .filter(Boolean)
                          .join(", ") || "-"}
                      </td>
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
