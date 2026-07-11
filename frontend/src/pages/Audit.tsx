import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, Eye, FileJson, FileText, RotateCcw } from "lucide-react";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import RiskBadge from "../components/RiskBadge";
import SourceBadge from "../components/SourceBadge";
import {
  downloadAuditReport,
  exportAuditCsv,
  exportAuditJson,
  fetchAudit,
  fetchAuditEvidence,
  fetchAuditTimeline,
} from "../services/api";
import type { AuditRecord } from "../types/audit";
import type { AuditFilters } from "../types/report";
import { formatAuditAction, formatDateTime, formatRole } from "../utils/formatters";

export default function Audit() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useMemo(() => paramsToFilters(searchParams), [searchParams]);
  const [draft, setDraft] = useState<AuditFilters>(filters);
  const [selected, setSelected] = useState<AuditRecord | null>(null);
  const { data: records = [], isLoading } = useQuery({
    queryKey: ["audit", filters],
    queryFn: () => fetchAudit(filters),
  });
  const { data: timeline = [] } = useQuery({
    queryKey: ["audit-timeline", selected?.id],
    queryFn: () => fetchAuditTimeline(Number(selected?.id)),
    enabled: Boolean(selected),
  });
  const { data: evidence = [] } = useQuery({
    queryKey: ["audit-evidence", selected?.id],
    queryFn: () => fetchAuditEvidence(Number(selected?.id)),
    enabled: Boolean(selected),
  });
  const jsonMutation = useMutation({ mutationFn: () => exportAuditJson(filters) });
  const csvMutation = useMutation({ mutationFn: () => exportAuditCsv(filters) });
  const pdfMutation = useMutation({ mutationFn: () => downloadAuditReport(filters) });

  function applyFilters() {
    setSearchParams(filtersToParams(draft));
  }

  function clearFilters() {
    setDraft({});
    setSelected(null);
    setSearchParams({});
  }

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Auditoria</h1>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-5">
          <FilterInput label="Texto livre" value={draft.text} onChange={(text) => setDraft({ ...draft, text })} />
          <FilterInput label="Usuário" value={draft.user} onChange={(user) => setDraft({ ...draft, user })} />
          <FilterInput label="Paciente" value={draft.patient} onChange={(patient) => setDraft({ ...draft, patient })} />
          <FilterInput label="Medicamento" value={draft.medication} onChange={(medication) => setDraft({ ...draft, medication })} />
          <FilterInput label="Princípio ativo" value={draft.active_ingredient} onChange={(active_ingredient) => setDraft({ ...draft, active_ingredient })} />
          <FilterInput label="Protocolo" value={draft.protocol} onChange={(protocol) => setDraft({ ...draft, protocol })} />
          <FilterInput label="Categoria protocolo" value={draft.protocol_category} onChange={(protocol_category) => setDraft({ ...draft, protocol_category })} />
          <FilterInput label="Versão protocolo" value={draft.protocol_version} onChange={(protocol_version) => setDraft({ ...draft, protocol_version })} />
          <FilterInput label="Execução" value={draft.execution} onChange={(execution) => setDraft({ ...draft, execution })} />
          <FilterInput label="Tipo de evento" value={draft.action} onChange={(action) => setDraft({ ...draft, action })} />
          <FilterInput label="Risco" value={draft.risk_level} onChange={(risk_level) => setDraft({ ...draft, risk_level })} />
          <FilterInput label="Status" value={draft.status} onChange={(status) => setDraft({ ...draft, status })} />
          <FilterInput label="Provider IA" value={draft.ai_provider} onChange={(ai_provider) => setDraft({ ...draft, ai_provider })} />
          <FilterInput label="Modelo IA" value={draft.ai_model} onChange={(ai_model) => setDraft({ ...draft, ai_model })} />
          <FilterInput label="Fonte" value={draft.source} onChange={(source) => setDraft({ ...draft, source })} />
          <FilterInput label="Jurisdição" value={draft.jurisdiction} onChange={(jurisdiction) => setDraft({ ...draft, jurisdiction })} />
          <label className="grid gap-1.5">
            <span className="label">Data inicial</span>
            <input
              className="field"
              type="date"
              value={draft.date_from?.slice(0, 10) ?? ""}
              onChange={(event) => setDraft({ ...draft, date_from: event.target.value })}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="label">Data final</span>
            <input
              className="field"
              type="date"
              value={draft.date_to?.slice(0, 10) ?? ""}
              onChange={(event) => setDraft({ ...draft, date_to: event.target.value })}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="label">Ordenação</span>
            <select
              className="field"
              value={draft.sort ?? "desc"}
              onChange={(event) => setDraft({ ...draft, sort: event.target.value as "asc" | "desc" })}
            >
              <option value="desc">Mais recentes</option>
              <option value="asc">Mais antigos</option>
            </select>
          </label>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <button className="btn-primary" onClick={applyFilters} type="button">
            <Eye aria-hidden="true" className="h-4 w-4" />
            Filtrar
          </button>
          <button className="btn-secondary" onClick={clearFilters} type="button">
            <RotateCcw aria-hidden="true" className="h-4 w-4" />
            Limpar
          </button>
          <button className="btn-secondary" onClick={() => jsonMutation.mutate()} type="button">
            <FileJson aria-hidden="true" className="h-4 w-4" />
            Exportar JSON
          </button>
          <button className="btn-secondary" onClick={() => csvMutation.mutate()} type="button">
            <Download aria-hidden="true" className="h-4 w-4" />
            Exportar CSV
          </button>
          <button className="btn-secondary" onClick={() => pdfMutation.mutate()} type="button">
            <FileText aria-hidden="true" className="h-4 w-4" />
            Gerar PDF
          </button>
        </div>
        <ActiveFilterChips filters={filters} onClear={clearFilters} />
      </section>

      {isLoading ? <LoadingState label="Carregando auditoria" /> : null}
      {!isLoading && records.length === 0 ? (
        <EmptyState title="Nenhum evento registrado" />
      ) : null}
      {!isLoading && records.length > 0 ? (
        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
                <tr>
                  <th className="px-4 py-3">Data</th>
                  <th className="px-4 py-3">Usuário</th>
                  <th className="px-4 py-3">Perfil</th>
                  <th className="px-4 py-3">Ação</th>
                  <th className="px-4 py-3">Recurso</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Risco</th>
                  <th className="px-4 py-3">Badges</th>
                  <th className="px-4 py-3 text-right">Detalhe</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {records.map((record) => (
                  <tr key={record.id} className="align-top text-slate-700">
                    <td className="px-4 py-3">{formatDateTime(record.created_at)}</td>
                    <td className="px-4 py-3 font-semibold text-ink">
                      {record.user_name ?? "-"}
                      <div className="text-xs font-normal text-slate-500">
                        {record.user_email ?? ""}
                      </div>
                    </td>
                    <td className="px-4 py-3">{formatRole(record.user_role)}</td>
                    <td className="px-4 py-3">{formatAuditAction(record.action)}</td>
                    <td className="px-4 py-3">
                      {record.resource_type}
                      {record.resource_id ? ` #${record.resource_id}` : ""}
                    </td>
                    <td className="px-4 py-3">
                      {record.status ? <RiskBadge status={record.status} /> : "-"}
                    </td>
                    <td className="px-4 py-3">
                      {record.risk_level ? <RiskBadge level={record.risk_level} /> : "-"}
                    </td>
                    <td className="px-4 py-3">
                      <AuditBadges record={record} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button className="btn-secondary" onClick={() => setSelected(record)} type="button">
                        <Eye aria-hidden="true" className="h-4 w-4" />
                        Ver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {selected ? (
        <AuditDetail record={selected} evidence={evidence} timeline={timeline} />
      ) : null}
    </div>
  );
}

function ActiveFilterChips({ filters, onClear }: { filters: AuditFilters; onClear: () => void }) {
  const entries = Object.entries(filters).filter(
    ([, value]) => value !== undefined && value !== null && String(value).trim() !== "",
  );
  if (!entries.length) {
    return null;
  }
  return (
    <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4">
      {entries.map(([key, value]) => (
        <span
          className="rounded-lg bg-cyan-50 px-2.5 py-1 text-xs font-bold text-cyan-800"
          key={key}
        >
          {labelFilterKey(key)}: {String(value)}
        </span>
      ))}
      <button className="btn-secondary" onClick={onClear} type="button">
        Limpar filtros
      </button>
    </div>
  );
}

function labelFilterKey(key: string) {
  const labels: Record<string, string> = {
    action: "Evento",
    active_ingredient: "Princípio ativo",
    ai_model: "Modelo IA",
    ai_provider: "Provider IA",
    date_from: "Data inicial",
    date_to: "Data final",
    jurisdiction: "Jurisdição",
    medication: "Medicamento",
    patient: "Paciente",
    protocol: "Protocolo",
    protocol_category: "Categoria protocolo",
    protocol_version: "Versão protocolo",
    execution: "Execução",
    risk_level: "Risco",
    sort: "Ordenação",
    source: "Fonte",
    status: "Status",
    text: "Texto",
    user: "Usuário",
  };
  return labels[key] ?? key;
}

function FilterInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value?: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1.5">
      <span className="label">{label}</span>
      <input className="field" value={value ?? ""} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function AuditBadges({ record }: { record: AuditRecord }) {
  const provider = record.details.ai_provider ?? record.details.provider;
  const model = record.details.ai_model ?? record.details.model;
  const source = record.details.source;
  const jurisdiction = record.details.jurisdiction;
  return (
    <div className="flex flex-wrap gap-2">
      <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-700">
        {record.resource_type}
      </span>
      {provider ? (
        <span className="rounded-lg bg-cyan-50 px-2.5 py-1 text-xs font-bold text-cyan-800">
          {String(provider)} {model ? `/ ${String(model)}` : ""}
        </span>
      ) : null}
      {source || jurisdiction ? (
        <SourceBadge
          jurisdiction={String(jurisdiction ?? "BR")}
          source={String(source ?? "fonte")}
          status={String(record.details.validation_status ?? "registrado")}
        />
      ) : null}
    </div>
  );
}

function AuditDetail({
  record,
  evidence,
  timeline,
}: {
  record: AuditRecord;
  evidence: Array<Record<string, unknown>>;
  timeline: Array<Record<string, unknown>>;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-bold text-ink">Detalhe do evento #{record.id}</h2>
          <p className="mt-1 text-sm text-slate-600">
            {formatAuditAction(record.action)} - {formatDateTime(record.created_at)}
          </p>
        </div>
        <AuditBadges record={record} />
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
          <h3 className="text-sm font-bold text-ink">Linha do tempo da decisão</h3>
          <ol className="mt-3 grid gap-2">
            {timeline.map((item, index) => (
              <li className="text-sm text-slate-700" key={index}>
                <span className="font-bold">{String(item.title ?? "Evento")}</span>:{" "}
                {String(item.status ?? "-")}
              </li>
            ))}
          </ol>
        </div>
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
          <h3 className="text-sm font-bold text-ink">Ver evidências</h3>
          <div className="mt-3 grid gap-2">
            {evidence.length ? (
              evidence.map((item, index) => (
                <p className="text-sm leading-6 text-slate-700" key={index}>
                  {String(item.code ?? item.source_id ?? "fonte")}:{" "}
                  {String(item.evidence_summary ?? item.source_name ?? "-")}
                </p>
              ))
            ) : (
              <p className="text-sm text-slate-600">Sem evidência vinculada.</p>
            )}
          </div>
        </div>
      </div>
      <pre className="mt-4 max-h-80 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">
        {JSON.stringify(record.details, null, 2)}
      </pre>
    </section>
  );
}

function paramsToFilters(params: URLSearchParams): AuditFilters {
  const filters: AuditFilters = {};
  params.forEach((value, key) => {
    if (value) {
      filters[key as keyof AuditFilters] = value as never;
    }
  });
  return filters;
}

function filtersToParams(filters: AuditFilters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      params.set(key, String(value));
    }
  });
  return params;
}
