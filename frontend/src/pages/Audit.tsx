import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, Eye, FileJson, FileText, RotateCcw } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
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
import { formatAuditAction, formatDateTime, formatRole, formatStatus } from "../utils/formatters";

export default function Audit() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useMemo(() => paramsToFilters(searchParams), [searchParams]);
  const [draft, setDraft] = useState<AuditFilters>(filters);
  const [selected, setSelected] = useState<AuditRecord | null>(null);
  const { data: auditPage, isLoading } = useQuery({
    queryKey: ["audit", filters],
    queryFn: () => fetchAudit(filters),
  });
  const records = auditPage?.items ?? [];
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
      <PageHeader title={t("audit.title")} description={t("audit.description")} />

      <section className="surface-card p-5">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <FilterInput label={t("audit.freeText")} value={draft.text} onChange={(text) => setDraft({ ...draft, text })} />
          <FilterInput label={t("audit.user")} value={draft.user} onChange={(user) => setDraft({ ...draft, user })} />
          <FilterInput label={t("audit.patient")} value={draft.patient} onChange={(patient) => setDraft({ ...draft, patient })} />
          <FilterInput label={t("audit.eventType")} value={draft.action} onChange={(action) => setDraft({ ...draft, action })} />
        </div>
        <details className="mt-4 rounded-xl border border-slate-200 bg-slate-50/70 p-4">
          <summary className="cursor-pointer text-sm font-black text-ocean">{t("audit.advancedFilters")}</summary>
          <div className="mt-4 grid gap-3 md:grid-cols-3 xl:grid-cols-5">
          <FilterInput label={t("audit.medication")} value={draft.medication} onChange={(medication) => setDraft({ ...draft, medication })} />
          <FilterInput label={t("audit.activeIngredient")} value={draft.active_ingredient} onChange={(active_ingredient) => setDraft({ ...draft, active_ingredient })} />
          <FilterInput label={t("audit.protocol")} value={draft.protocol} onChange={(protocol) => setDraft({ ...draft, protocol })} />
          <FilterInput label={t("audit.protocolCategory")} value={draft.protocol_category} onChange={(protocol_category) => setDraft({ ...draft, protocol_category })} />
          <FilterInput label={t("audit.protocolVersion")} value={draft.protocol_version} onChange={(protocol_version) => setDraft({ ...draft, protocol_version })} />
          <FilterInput label={t("audit.execution")} value={draft.execution} onChange={(execution) => setDraft({ ...draft, execution })} />
          <FilterInput label={t("audit.risk")} value={draft.risk_level} onChange={(risk_level) => setDraft({ ...draft, risk_level })} />
          <FilterInput label={t("audit.status")} value={draft.status} onChange={(status) => setDraft({ ...draft, status })} />
          <FilterInput label={t("audit.aiProvider")} value={draft.ai_provider} onChange={(ai_provider) => setDraft({ ...draft, ai_provider })} />
          <FilterInput label={t("audit.aiModel")} value={draft.ai_model} onChange={(ai_model) => setDraft({ ...draft, ai_model })} />
          <FilterInput label={t("audit.source")} value={draft.source} onChange={(source) => setDraft({ ...draft, source })} />
          <FilterInput label={t("audit.jurisdiction")} value={draft.jurisdiction} onChange={(jurisdiction) => setDraft({ ...draft, jurisdiction })} />
          <label className="grid gap-1.5">
            <span className="label">{t("audit.startDate")}</span>
            <input
              className="field"
              type="date"
              value={draft.date_from?.slice(0, 10) ?? ""}
              onChange={(event) => setDraft({ ...draft, date_from: event.target.value })}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="label">{t("audit.endDate")}</span>
            <input
              className="field"
              type="date"
              value={draft.date_to?.slice(0, 10) ?? ""}
              onChange={(event) => setDraft({ ...draft, date_to: event.target.value })}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="label">{t("audit.sort")}</span>
            <select
              className="field"
              value={draft.sort ?? "desc"}
              onChange={(event) => setDraft({ ...draft, sort: event.target.value as "asc" | "desc" })}
            >
              <option value="desc">{t("audit.newest")}</option>
              <option value="asc">{t("audit.oldest")}</option>
            </select>
          </label>
          </div>
        </details>
        <div className="mt-4 flex flex-wrap gap-3">
          <button className="btn-primary" onClick={applyFilters} type="button">
            <Eye aria-hidden="true" className="h-4 w-4" />
            {t("audit.filter")}
          </button>
          <button className="btn-secondary" onClick={clearFilters} type="button">
            <RotateCcw aria-hidden="true" className="h-4 w-4" />
            {t("audit.clear")}
          </button>
          <button className="btn-secondary" onClick={() => jsonMutation.mutate()} type="button">
            <FileJson aria-hidden="true" className="h-4 w-4" />
            {t("audit.exportJson")}
          </button>
          <button className="btn-secondary" onClick={() => csvMutation.mutate()} type="button">
            <Download aria-hidden="true" className="h-4 w-4" />
            {t("audit.exportCsv")}
          </button>
          <button className="btn-secondary" onClick={() => pdfMutation.mutate()} type="button">
            <FileText aria-hidden="true" className="h-4 w-4" />
            {t("audit.generatePdf")}
          </button>
        </div>
        <ActiveFilterChips filters={filters} onClear={clearFilters} />
      </section>

      {isLoading ? <LoadingState label={t("audit.loading")} /> : null}
      {!isLoading && records.length === 0 ? (
        <EmptyState title={t("audit.empty")} />
      ) : null}
      {!isLoading && records.length > 0 ? (
        <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="bg-slate-50 text-xs font-bold uppercase tracking-normal text-slate-500">
                <tr>
                  <th className="px-4 py-3">{t("audit.date")}</th>
                  <th className="px-4 py-3">{t("audit.user")}</th>
                  <th className="px-4 py-3">{t("audit.profile")}</th>
                  <th className="px-4 py-3">{t("audit.action")}</th>
                  <th className="px-4 py-3">{t("audit.resource")}</th>
                  <th className="px-4 py-3">{t("audit.status")}</th>
                  <th className="px-4 py-3">{t("audit.risk")}</th>
                  <th className="px-4 py-3">{t("audit.badges")}</th>
                  <th className="px-4 py-3 text-right">{t("audit.detail")}</th>
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
                        {t("audit.view")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3 text-sm">
            <span>{t("audit.pagination", { total: auditPage?.total ?? 0, page: auditPage?.page ?? 1, pages: auditPage?.total_pages || 1 })}</span>
            <div className="flex gap-2">
              <button className="btn-secondary" disabled={!auditPage?.has_previous} onClick={() => setSearchParams(filtersToParams({ ...filters, page: (auditPage?.page ?? 1) - 1 }))} type="button">{t("audit.previous")}</button>
              <button className="btn-secondary" disabled={!auditPage?.has_next} onClick={() => setSearchParams(filtersToParams({ ...filters, page: (auditPage?.page ?? 1) + 1 }))} type="button">{t("audit.next")}</button>
            </div>
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
  const { t } = useTranslation();
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
          {t(labelFilterKey(key))}: {String(value)}
        </span>
      ))}
      <button className="btn-secondary" onClick={onClear} type="button">
        {t("audit.clearFilters")}
      </button>
    </div>
  );
}

function labelFilterKey(key: string) {
  const labels: Record<string, string> = {
    action: "audit.event",
    active_ingredient: "audit.activeIngredient",
    ai_model: "audit.aiModel",
    ai_provider: "audit.aiProvider",
    date_from: "audit.startDate",
    date_to: "audit.endDate",
    jurisdiction: "audit.jurisdiction",
    medication: "audit.medication",
    patient: "audit.patient",
    protocol: "audit.protocol",
    protocol_category: "audit.protocolCategory",
    protocol_version: "audit.protocolVersion",
    execution: "audit.execution",
    risk_level: "audit.risk",
    sort: "audit.sort",
    source: "audit.source",
    status: "audit.status",
    text: "audit.freeText",
    user: "audit.user",
  };
  return labels[key] ?? "audit.detail";
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
  const { t } = useTranslation();
  return (
    <section className="surface-card p-5">
      <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-bold text-ink">{t("audit.eventDetail", { id: record.id })}</h2>
          <p className="mt-1 text-sm text-slate-600">
            {formatAuditAction(record.action)} - {formatDateTime(record.created_at)}
          </p>
        </div>
        <AuditBadges record={record} />
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
          <h3 className="text-sm font-bold text-ink">{t("audit.decisionTimeline")}</h3>
          <ol className="mt-3 grid gap-2">
            {timeline.map((item, index) => (
              <li className="text-sm text-slate-700" key={index}>
                <span className="font-bold">{String(item.title ?? t("audit.event"))}</span>:{" "}
                {formatStatus(String(item.status ?? "-"))}
              </li>
            ))}
          </ol>
        </div>
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
          <h3 className="text-sm font-bold text-ink">{t("audit.viewEvidence")}</h3>
          <div className="mt-3 grid gap-2">
            {evidence.length ? (
              evidence.map((item, index) => (
                <p className="text-sm leading-6 text-slate-700" key={index}>
                  {String(item.code ?? item.source_id ?? "fonte")}:{" "}
                  {String(item.evidence_summary ?? item.source_name ?? "-")}
                </p>
              ))
            ) : (
              <p className="text-sm text-slate-600">{t("audit.noEvidence")}</p>
            )}
          </div>
        </div>
      </div>
      <details className="mt-4"><summary className="cursor-pointer text-sm font-bold text-ocean">{t("audit.rawDetails")}</summary><pre className="mt-3 max-h-80 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(record.details, null, 2)}</pre></details>
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
