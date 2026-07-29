import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, ChevronLeft, ChevronRight, Filter, Plus, Search, UsersRound } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import PatientForm from "../components/PatientForm";
import Badge from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import StatusPanel from "../components/ui/StatusPanel";
import { useAuth } from "../context/AuthContext";
import { createPatient, fetchPatients } from "../services/api";
import type { PatientPayload } from "../types/patient";
import { joinList } from "../utils/formatters";

const pageSize = 8;

export default function Patients() {
  const { can } = useAuth();
  const canCreatePatient = can("patient.create");
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "incomplete" | "allergies">("all");
  const [page, setPage] = useState(1);
  const { data: patients = [], isLoading, error, refetch } = useQuery({
    queryKey: ["patients"],
    queryFn: fetchPatients,
    staleTime: 20_000,
  });
  const createMutation = useMutation({
    mutationFn: createPatient,
    onSuccess: async () => {
      setCreateOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const filtered = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("pt-BR");
    return patients.filter((patient) => {
      const matchesSearch = !term || [patient.name, ...patient.allergies, ...patient.current_medications]
        .join(" ")
        .toLocaleLowerCase("pt-BR")
        .includes(term);
      const matchesFilter = filter === "all"
        || (filter === "incomplete" && patient.clinical_profile_completeness_score < 80)
        || (filter === "allergies" && patient.allergies.length > 0);
      return matchesSearch && matchesFilter;
    });
  }, [filter, patients, search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const visiblePatients = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  async function handleCreate(payload: PatientPayload) {
    await createMutation.mutateAsync(payload);
  }

  return (
    <div className="grid gap-6 lg:gap-8">
      <PageHeader
        title="Pacientes"
        description="Somente registros cobertos por vínculo assistencial, grant explícito ou acesso emergencial ativo aparecem nesta lista."
        actions={canCreatePatient ? <button className="btn-primary" onClick={() => setCreateOpen(true)} type="button"><Plus aria-hidden="true" className="h-4 w-4" />Novo paciente</button> : undefined}
      />

      <section aria-label="Filtros de pacientes" className="surface-card p-4 sm:p-5">
        <div className="grid gap-3 lg:grid-cols-[minmax(16rem,1fr)_auto_auto] lg:items-end">
          <label className="grid gap-1.5">
            <span className="label">Buscar no escopo autorizado</span>
            <span className="relative">
              <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input className="field pl-10" onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Nome, alergia ou medicamento" type="search" value={search} />
            </span>
          </label>
          <label className="grid gap-1.5">
            <span className="label">Filtro clínico</span>
            <span className="relative">
              <Filter aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <select className="field min-w-56 pl-10" onChange={(event) => { setFilter(event.target.value as typeof filter); setPage(1); }} value={filter}>
                <option value="all">Todos no meu escopo</option>
                <option value="incomplete">Contexto incompleto</option>
                <option value="allergies">Com alergias registradas</option>
              </select>
            </span>
          </label>
          <div className="flex min-h-11 items-center justify-end text-sm font-bold text-slate-600" aria-live="polite">
            {filtered.length} {filtered.length === 1 ? "paciente" : "pacientes"}
          </div>
        </div>
      </section>

      {isLoading ? <LoadingState label="Carregando pacientes autorizados" /> : null}
      {error ? <StatusPanel actions={<button className="btn-secondary" onClick={() => void refetch()} type="button">Tentar novamente</button>} title="Falha ao carregar pacientes" tone="danger">O backend não retornou a lista. Nenhum dado em cache foi tratado como atual.</StatusPanel> : null}
      {!isLoading && !error && filtered.length === 0 ? <EmptyState title={patients.length ? "Nenhum paciente corresponde aos filtros" : "Nenhum paciente autorizado"} description={patients.length ? "Altere a busca ou o filtro clínico." : "Solicite um vínculo ou grant; pertencer à mesma instituição não é suficiente."} /> : null}

      {!isLoading && !error && visiblePatients.length > 0 ? (
        <section aria-label="Pacientes autorizados">
          <div className="hidden table-shell md:block">
            <div className="max-h-[42rem] overflow-auto">
              <table className="data-table min-w-[860px]">
                <thead><tr><th>Paciente</th><th>Contexto</th><th>Alergias</th><th>Uso contínuo</th><th><span className="sr-only">Ação</span></th></tr></thead>
                <tbody>
                  {visiblePatients.map((patient) => (
                    <tr key={patient.id}>
                      <td>
                        <p className="font-extrabold text-ink">{patient.name}</p>
                        <p className="mt-1 text-xs text-slate-500">{patient.age !== null ? `${patient.age} anos` : "Idade calculada por nascimento"} · vínculo autorizado</p>
                      </td>
                      <td><Completeness score={patient.clinical_profile_completeness_score} label={patient.clinical_profile_badge} /></td>
                      <td className="max-w-64"><span className="block whitespace-normal leading-5 text-slate-700">{joinList(patient.allergies) || "Nenhuma informada"}</span></td>
                      <td className="max-w-64"><span className="block whitespace-normal leading-5 text-slate-700">{joinList(patient.current_medications) || "Não informado"}</span></td>
                      <td className="text-right"><Link aria-label={`Abrir workspace de ${patient.name}`} className="btn-secondary" to={`/patients/${patient.id}`}>Abrir <ArrowRight aria-hidden="true" className="h-4 w-4" /></Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid gap-3 md:hidden">
            {visiblePatients.map((patient) => (
              <article className="surface-card p-4" key={patient.id}>
                <div className="flex items-start gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-50 text-ocean"><UsersRound aria-hidden="true" className="h-5 w-5" /></span>
                  <div className="min-w-0 flex-1">
                    <h2 className="font-extrabold text-ink">{patient.name}</h2>
                    <p className="mt-0.5 text-xs text-slate-500">{patient.age !== null ? `${patient.age} anos` : "Idade por data de nascimento"}</p>
                  </div>
                  <Badge tone="info">Autorizado</Badge>
                </div>
                <div className="mt-4"><Completeness score={patient.clinical_profile_completeness_score} label={patient.clinical_profile_badge} /></div>
                <dl className="mt-4 grid gap-3 text-sm">
                  <div><dt className="text-xs font-bold text-slate-500">Alergias</dt><dd className="mt-1 leading-5 text-slate-700">{joinList(patient.allergies) || "Nenhuma informada"}</dd></div>
                  <div><dt className="text-xs font-bold text-slate-500">Uso contínuo</dt><dd className="mt-1 leading-5 text-slate-700">{joinList(patient.current_medications) || "Não informado"}</dd></div>
                </dl>
                <Link className="btn-secondary mt-4 w-full" to={`/patients/${patient.id}`}>Abrir workspace <ArrowRight aria-hidden="true" className="h-4 w-4" /></Link>
              </article>
            ))}
          </div>

          <nav aria-label="Paginação de pacientes" className="mt-4 flex items-center justify-between gap-3">
            <p className="text-xs font-semibold text-slate-500">Página {currentPage} de {totalPages}</p>
            <div className="flex gap-2">
              <button aria-label="Página anterior" className="icon-button" disabled={currentPage === 1} onClick={() => setPage((value) => Math.max(1, value - 1))} type="button"><ChevronLeft aria-hidden="true" className="h-4 w-4" /></button>
              <button aria-label="Próxima página" className="icon-button" disabled={currentPage === totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))} type="button"><ChevronRight aria-hidden="true" className="h-4 w-4" /></button>
            </div>
          </nav>
        </section>
      ) : null}

      <Modal description="Use apenas dados fictícios. O registro será vinculado ao criador conforme as capacidades concedidas." onClose={() => setCreateOpen(false)} open={createOpen} title="Novo paciente">
        <PatientForm onSubmit={handleCreate} submitLabel="Criar paciente" />
        {createMutation.isError ? <p className="field-error mt-3" role="alert">Não foi possível criar o paciente. Revise os campos e sua capacidade.</p> : null}
      </Modal>
    </div>
  );
}

function Completeness({ score, label }: { score: number; label: string }) {
  const tone = score >= 80 ? "success" : score >= 50 ? "warning" : "danger";
  return (
    <div className="min-w-40">
      <div className="flex items-center justify-between gap-2"><Badge tone={tone}>{label}</Badge><span className="text-xs font-extrabold text-slate-600">{score}%</span></div>
      <div aria-label={`${score}% do contexto preenchido`} aria-valuemax={100} aria-valuemin={0} aria-valuenow={score} className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200" role="progressbar"><span className={`block h-full rounded-full ${score >= 80 ? "bg-emerald-600" : score >= 50 ? "bg-amber-600" : "bg-red-600"}`} style={{ width: `${Math.min(100, Math.max(0, score))}%` }} /></div>
    </div>
  );
}
