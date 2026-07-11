import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, CheckCircle, Database, ExternalLink, Pencil, RefreshCw, Search } from "lucide-react";
import { useMemo, useState } from "react";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import MedicationForm from "../components/MedicationForm";
import SourceBadge from "../components/SourceBadge";
import { useAuth } from "../context/AuthContext";
import {
  createMedication,
  fetchAdverseEffectTaxonomy,
  fetchActiveIngredients,
  fetchMedicationCounselingSummary,
  fetchMedications,
  generateMedicationCounselingSummary,
  lookupAnvisaSource,
  reviewMedicationCounselingSummary,
  searchMedicationCatalog,
  updateMedication,
} from "../services/api";
import type {
  AdverseEffectTaxonomyEntry,
  Medication,
  MedicationCounselingSummary,
  MedicationPayload,
} from "../types/medication";
import { formatDose, joinList } from "../utils/formatters";

export default function Medications() {
  const { canAccess } = useAuth();
  const canManageMedication = canAccess(["admin"]);
  const canReviewCounseling = canAccess(["admin", "medico"]);
  const [selectedMedication, setSelectedMedication] = useState<Medication | undefined>();
  const [counselingMedication, setCounselingMedication] = useState<Medication | undefined>();
  const [catalogQuery, setCatalogQuery] = useState("Novalgina");
  const [medicationFilter, setMedicationFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("todos");
  const queryClient = useQueryClient();
  const { data: medications = [], isLoading } = useQuery({
    queryKey: ["medications"],
    queryFn: fetchMedications,
  });
  const { data: activeIngredients = [] } = useQuery({
    queryKey: ["active-ingredients"],
    queryFn: fetchActiveIngredients,
  });
  const { data: adverseEffectTaxonomy = [] } = useQuery({
    queryKey: ["adverse-effect-taxonomy"],
    queryFn: fetchAdverseEffectTaxonomy,
  });
  const { data: counselingSummary } = useQuery({
    queryKey: ["medications", counselingMedication?.id, "counseling-summary"],
    queryFn: () => fetchMedicationCounselingSummary(Number(counselingMedication?.id)),
    enabled: Boolean(counselingMedication),
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
  const filteredMedications = useMemo(() => {
    const query = medicationFilter.trim().toLowerCase();
    return medications.filter((medication) => {
      const matchesQuery =
        !query ||
        [
          medication.brand_name,
          medication.active_ingredient,
          medication.therapeutic_class,
          ...(medication.commercial_aliases ?? []),
        ]
          .join(" ")
          .toLowerCase()
          .includes(query);
      const matchesSource =
        sourceFilter === "todos" || medication.validation_status === sourceFilter;
      return matchesQuery && matchesSource;
    });
  }, [medications, medicationFilter, sourceFilter]);
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
  const generateCounselingMutation = useMutation({
    mutationFn: () =>
      generateMedicationCounselingSummary(Number(counselingMedication?.id), {
        force_regenerate: false,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["medications", counselingMedication?.id, "counseling-summary"],
      });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const reviewCounselingMutation = useMutation({
    mutationFn: (validation_status: "curated" | "validated") =>
      reviewMedicationCounselingSummary(Number(counselingMedication?.id), {
        validation_status,
        justification: "Revisão demonstrativa v0.7.0.",
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["medications", counselingMedication?.id, "counseling-summary"],
      });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
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
            <h2 className="text-lg font-bold text-ink">Busca por princípio ativo ou alias</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Nomes comerciais apontam para o princípio ativo DCB quando cadastrados no catálogo
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
              <h3 className="text-sm font-bold text-ink">Resultado do catálogo</h3>
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
                            : "Princípio ativo"}
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
                <p>Princípio ativo: {anvisaLookup.active_ingredient ?? "pendente"}</p>
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
          <h2 className="text-lg font-bold text-ink">Catálogo de princípios ativos</h2>
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
          <h2 className="text-lg font-bold text-ink">Política de conflito de fontes</h2>
          <div className="mt-3 grid gap-2 text-sm leading-6 text-slate-600">
            <p>Para contexto brasileiro, fontes BR/Anvisa/DCB têm prioridade.</p>
            <p>Fontes internacionais entram como apoio secundário e precisam de aviso claro.</p>
            <p>Dipirona/metamizol é exibida como diferença regulatória, não como erro automático.</p>
          </div>
        </div>
      </section>

      <MedicationCounselingPanel
        canReview={canReviewCounseling}
        isGenerating={generateCounselingMutation.isPending}
        isReviewing={reviewCounselingMutation.isPending}
        medication={counselingMedication}
        onGenerate={() => generateCounselingMutation.mutate()}
        onReview={(status) => reviewCounselingMutation.mutate(status)}
        summary={counselingSummary ?? null}
        taxonomy={adverseEffectTaxonomy}
      />

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
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <h2 className="text-lg font-bold text-ink">Lista de medicamentos</h2>
          <div className="grid gap-3 sm:grid-cols-[minmax(220px,1fr)_180px]">
            <label className="grid gap-1.5">
              <span className="label">Filtrar</span>
              <input
                className="field"
                onChange={(event) => setMedicationFilter(event.target.value)}
                placeholder="Nome, princípio ativo, alias"
                value={medicationFilter}
              />
            </label>
            <label className="grid gap-1.5">
              <span className="label">Status da fonte</span>
              <select
                className="field"
                onChange={(event) => setSourceFilter(event.target.value)}
                value={sourceFilter}
              >
                <option value="todos">Todos</option>
                <option value="demo">Demo</option>
                <option value="pending_review">Pendente</option>
                <option value="curated">Curado</option>
                <option value="validated">Validado</option>
              </select>
            </label>
          </div>
        </div>
        {isLoading ? <LoadingState label="Carregando medicamentos" /> : null}
        {!isLoading && medications.length === 0 ? (
          <EmptyState title="Nenhum medicamento cadastrado" />
        ) : null}
        {!isLoading && medications.length > 0 && filteredMedications.length === 0 ? (
          <EmptyState title="Nenhum medicamento corresponde aos filtros" />
        ) : null}
        {!isLoading && filteredMedications.length > 0 ? (
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1240px] text-left text-sm">
                <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Nome</th>
                    <th className="px-4 py-3">Princípio ativo</th>
                    <th className="px-4 py-3">Aliases</th>
                    <th className="px-4 py-3">Fonte</th>
                    <th className="px-4 py-3">Classe</th>
                    <th className="px-4 py-3">Dose máxima</th>
                    <th className="px-4 py-3">Cautelas</th>
                    <th className="px-4 py-3">Vias</th>
                    <th className="px-4 py-3 text-right">Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredMedications.map((medication) => (
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
                          medication.hepatic_caution ? "hepática" : "",
                          medication.gastrointestinal_caution ? "gastrointestinal" : "",
                          medication.elderly_caution ? "idosos" : "",
                        ]
                          .filter(Boolean)
                          .join(", ") || "-"}
                      </td>
                      <td className="px-4 py-3">{joinList(medication.allowed_routes)}</td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2">
                          <button
                            className="btn-secondary"
                            onClick={() => setCounselingMedication(medication)}
                            title={`Orientações de ${medication.brand_name}`}
                            type="button"
                          >
                            <BookOpen aria-hidden="true" className="h-4 w-4" />
                            Orientações
                          </button>
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
                          ) : null}
                        </div>
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

function MedicationCounselingPanel({
  medication,
  summary,
  taxonomy,
  canReview,
  isGenerating,
  isReviewing,
  onGenerate,
  onReview,
}: {
  medication: Medication | undefined;
  summary: MedicationCounselingSummary | null;
  taxonomy: AdverseEffectTaxonomyEntry[];
  canReview: boolean;
  isGenerating: boolean;
  isReviewing: boolean;
  onGenerate: () => void;
  onReview: (status: "curated" | "validated") => void;
}) {
  const [tab, setTab] = useState<"practical" | "taxonomy">("practical");
  const taxonomyGroups = taxonomy.reduce<Record<string, AdverseEffectTaxonomyEntry[]>>(
    (groups, item) => {
      groups[item.category] = [...(groups[item.category] ?? []), item];
      return groups;
    },
    {},
  );

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-bold text-ink">Resumo prático de segurança</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {medication
              ? `${medication.brand_name} (${medication.active_ingredient})`
              : "Selecione um medicamento na lista para abrir a aba de orientações práticas."}
          </p>
        </div>
        <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-1">
          <button
            className={[
              "rounded-md px-3 py-2 text-sm font-semibold",
              tab === "practical" ? "bg-white text-ocean shadow-sm" : "text-slate-600",
            ].join(" ")}
            onClick={() => setTab("practical")}
            type="button"
          >
            Orientações práticas
          </button>
          <button
            className={[
              "rounded-md px-3 py-2 text-sm font-semibold",
              tab === "taxonomy" ? "bg-white text-ocean shadow-sm" : "text-slate-600",
            ].join(" ")}
            onClick={() => setTab("taxonomy")}
            type="button"
          >
            Taxonomia
          </button>
        </div>
      </div>

      {tab === "practical" ? (
        <div className="mt-5 grid gap-4">
          {medication ? (
            <div className="flex flex-wrap items-center gap-2">
              <button
                className="btn-secondary"
                disabled={!canReview || isGenerating}
                onClick={onGenerate}
                title="Gerar resumo a partir da fonte/RAG"
                type="button"
              >
                <RefreshCw aria-hidden="true" className="h-4 w-4" />
                {isGenerating ? "Gerando..." : "Gerar resumo"}
              </button>
              <button
                className="btn-primary"
                disabled={!canReview || !summary || isReviewing}
                onClick={() => onReview("validated")}
                title="Revisar e aprovar resumo"
                type="button"
              >
                <CheckCircle aria-hidden="true" className="h-4 w-4" />
                {isReviewing ? "Revisando..." : "Aprovar resumo"}
              </button>
              {summary ? (
                <SourceBadge
                  jurisdiction={summary.jurisdiction}
                  source={summary.generated_by}
                  status={summary.validation_status}
                />
              ) : null}
            </div>
          ) : null}

          {summary ? (
            <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
              <article className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-bold text-ink">Orientações ao paciente</h3>
                  <span className="rounded-lg bg-white px-3 py-1 text-xs font-bold text-slate-700">
                    confiança {summary.confidence}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  {summary.patient_friendly_summary}
                </p>
                <div className="mt-4 grid gap-3">
                  <EffectChips title="Efeitos principais" values={summary.main_adverse_effects} />
                  <EffectChips title="Atividades" values={summary.activity_warnings} />
                  <EffectChips title="Sinais de alerta" values={summary.red_flags} />
                </div>
              </article>

              <article className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                <h3 className="text-sm font-bold text-ink">Resumo profissional</h3>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  {summary.professional_summary}
                </p>
                <dl className="mt-4 grid gap-2 text-sm text-slate-600">
                  <div>
                    <dt className="label">Fonte</dt>
                    <dd className="mt-1 font-semibold text-ink">
                      {summary.source_name} [{summary.jurisdiction}]
                    </dd>
                  </div>
                  <div>
                    <dt className="label">Status</dt>
                    <dd className="mt-1 font-semibold text-ink">
                      {summary.validation_status}
                      {summary.requires_review ? " - revisão pendente" : ""}
                    </dd>
                  </div>
                </dl>
                <div className="mt-4 grid gap-2">
                  <EffectChips title="Sono/atenção" values={summary.sleep_effects} />
                  <EffectChips title="Humor" values={summary.mood_behavior_effects} />
                  <EffectChips title="Sexual/reprodutivo" values={summary.libido_sexual_effects} />
                  <EffectChips title="Neurológico" values={summary.neurologic_effects} />
                  <EffectChips
                    title="Temperatura"
                    values={summary.temperature_regulation_effects}
                  />
                </div>
              </article>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              Nenhum resumo selecionado ou gerado para exibição.
            </div>
          )}
        </div>
      ) : (
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {Object.entries(taxonomyGroups).map(([category, entries]) => (
            <article className="rounded-lg border border-slate-100 bg-slate-50 p-4" key={category}>
              <h3 className="text-sm font-bold text-ink">{category}</h3>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {entries.map((entry) => (
                  <span
                    className="rounded-lg bg-white px-2 py-1 text-xs font-semibold text-slate-700"
                    key={entry.code}
                  >
                    {entry.code}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function EffectChips({ title, values }: { title: string; values: string[] }) {
  return (
    <div>
      <p className="text-xs font-bold uppercase tracking-normal text-slate-500">{title}</p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {values.length ? (
          values.map((value) => (
            <span
              className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-semibold text-slate-700"
              key={value}
            >
              {value}
            </span>
          ))
        ) : (
          <span className="text-sm text-slate-500">-</span>
        )}
      </div>
    </div>
  );
}
