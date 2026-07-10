import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, FileJson, FileText, RotateCw, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import {
  downloadAuditReport,
  downloadPatientGuidanceReport,
  downloadPrescriptionTechnicalReport,
  downloadReconciliationReport,
  exportReportJson,
  fetchPrescriptionEvidence,
  fetchPrescriptionReportPreview,
  fetchPrescriptionTimeline,
  fetchReports,
} from "../services/api";
import type { DecisionEvidenceItem, DecisionTimelineItem, GeneratedReport } from "../types/report";
import { formatDateTime } from "../utils/formatters";

export default function Reports() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });
  const selected = useMemo(
    () => reports.find((report) => report.id === selectedId) ?? reports[0] ?? null,
    [reports, selectedId],
  );
  const prescriptionAuditId =
    selected?.target_type === "prescription_audit" ? Number(selected.target_id) : null;
  const { data: preview } = useQuery({
    queryKey: ["report-preview", prescriptionAuditId],
    queryFn: () => fetchPrescriptionReportPreview(Number(prescriptionAuditId)),
    enabled: Boolean(prescriptionAuditId),
  });
  const { data: timeline = [] } = useQuery({
    queryKey: ["report-timeline", prescriptionAuditId],
    queryFn: () => fetchPrescriptionTimeline(Number(prescriptionAuditId)),
    enabled: Boolean(prescriptionAuditId),
  });
  const { data: evidence = [] } = useQuery({
    queryKey: ["report-evidence", prescriptionAuditId],
    queryFn: () => fetchPrescriptionEvidence(Number(prescriptionAuditId)),
    enabled: Boolean(prescriptionAuditId),
  });
  const exportMutation = useMutation({ mutationFn: exportReportJson });
  const regenerateMutation = useMutation({
    mutationFn: async (report: GeneratedReport) => {
      if (report.target_type === "prescription_audit") {
        if (report.report_type === "patient_guidance") {
          return downloadPatientGuidanceReport(Number(report.target_id));
        }
        return downloadPrescriptionTechnicalReport(Number(report.target_id), report.anonymized);
      }
      if (report.target_type === "clinical_import") {
        return downloadReconciliationReport(Number(report.target_id), report.anonymized);
      }
      return downloadAuditReport({});
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      await queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Relatórios</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Histórico auditável de relatórios gerados, hashes, versões de template e uso de IA.
        </p>
      </header>

      {isLoading ? <LoadingState label="Carregando relatórios" /> : null}
      {!isLoading && reports.length === 0 ? (
        <EmptyState
          title="Nenhum relatório gerado"
          description="Gere um PDF ou exportação a partir da checagem, importação ou auditoria."
        />
      ) : null}

      {reports.length ? (
        <section className="grid items-start gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="grid content-start gap-3">
            {reports.map((report) => (
              <ReportListItem
                isSelected={selected?.id === report.id}
                key={report.id}
                onSelect={() => setSelectedId(report.id)}
                report={report}
              />
            ))}
          </div>

          {selected ? (
            <ReportDetail
              evidence={evidence}
              exportDisabled={exportMutation.isPending}
              isRegenerating={regenerateMutation.isPending}
              onExportJson={() => exportMutation.mutate(selected.id)}
              onRegenerate={() => regenerateMutation.mutate(selected)}
              previewTitle={preview?.title ?? null}
              report={selected}
              timeline={timeline}
            />
          ) : null}
        </section>
      ) : null}

      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-medium leading-6 text-amber-900">
        <div className="flex gap-3">
          <ShieldCheck aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0" />
          Relatórios registram metadados, hash e provedor/modelo quando usados. API keys e
          segredos nunca são exportados.
        </div>
      </section>
    </div>
  );
}

function ReportListItem({
  report,
  isSelected,
  onSelect,
}: {
  report: GeneratedReport;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      className={[
        "rounded-lg border bg-white p-4 text-left shadow-sm transition",
        isSelected ? "border-ocean bg-cyan-50" : "border-slate-200 hover:bg-slate-50",
      ].join(" ")}
      onClick={onSelect}
      type="button"
    >
      <div className="flex flex-wrap items-center gap-2">
        <FileText aria-hidden="true" className="h-5 w-5 text-ocean" />
        <h2 className="text-base font-bold text-ink">
          #{report.id} {labelForReport(report.report_type)}
        </h2>
        <ReportBadge label={labelStatus(report.status)} />
        {report.anonymized ? <ReportBadge label="Anonimizado" tone="cyan" /> : null}
      </div>
      <p className="mt-2 text-sm text-slate-600">
        {formatDateTime(report.generated_at)} · {labelTarget(report.target_type)} #
        {report.target_id}
      </p>
      <p className="mt-2 truncate font-mono text-xs text-slate-500">
        {report.evidence_bundle_hash}
      </p>
    </button>
  );
}

function ReportDetail({
  report,
  previewTitle,
  timeline,
  evidence,
  exportDisabled,
  isRegenerating,
  onExportJson,
  onRegenerate,
}: {
  report: GeneratedReport;
  previewTitle: string | null;
  timeline: DecisionTimelineItem[];
  evidence: DecisionEvidenceItem[];
  exportDisabled: boolean;
  isRegenerating: boolean;
  onExportJson: () => void;
  onRegenerate: () => void;
}) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-bold text-ink">{labelForReport(report.report_type)}</h2>
          <p className="mt-1 text-sm text-slate-600">
            {previewTitle ?? `${labelTarget(report.target_type)} #${report.target_id}`}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="btn-secondary" disabled={exportDisabled} onClick={onExportJson} type="button">
            <FileJson aria-hidden="true" className="h-4 w-4" />
            JSON
          </button>
          <button className="btn-primary" disabled={isRegenerating} onClick={onRegenerate} type="button">
            <RotateCw aria-hidden="true" className="h-4 w-4" />
            {isRegenerating ? "Gerando..." : "Regenerar PDF"}
          </button>
          <Link className="btn-secondary" to={`/audit?text=${encodeURIComponent(report.evidence_bundle_hash)}`}>
            <Eye aria-hidden="true" className="h-4 w-4" />
            Auditoria
          </Link>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <ReportMeta label="Template" value={report.template_version} />
        <ReportMeta label="Prescripta" value={report.prescripta_version} />
        <ReportMeta label="IA" value={`${report.ai_provider ?? "fallback"} / ${report.ai_model ?? "determinístico"}`} />
        <ReportMeta label="Prompt" value={report.ai_prompt_version ?? "-"} />
        <ReportMeta label="Hash do arquivo" value={report.file_hash ?? "-"} />
        <ReportMeta label="Fallback" value={report.fallback_used ? "sim" : "não"} />
      </div>

      <p className="mt-4 break-all rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-600">
        EvidenceBundle {report.evidence_bundle_hash}
      </p>

      {timeline.length ? (
        <section className="mt-4 rounded-lg border border-slate-100 bg-slate-50 p-4">
          <h3 className="text-sm font-bold text-ink">Timeline da decisão</h3>
          <ol className="mt-3 grid gap-2">
            {timeline.map((item) => (
              <li className="text-sm text-slate-700" key={`${item.order}-${item.title}`}>
                <span className="font-bold">{item.title}</span>: {item.status}
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {evidence.length ? (
        <section className="mt-4 rounded-lg border border-slate-100 bg-slate-50 p-4">
          <h3 className="text-sm font-bold text-ink">Evidências</h3>
          <div className="mt-3 grid gap-2">
            {evidence.map((item, index) => (
              <p className="text-sm leading-6 text-slate-700" key={`${item.source_id}-${index}`}>
                <span className="font-bold">{item.source_id ?? item.code ?? "fonte"}</span>:{" "}
                {item.evidence_summary ?? item.source_name ?? "-"}
              </p>
            ))}
          </div>
        </section>
      ) : null}

      <pre className="mt-4 max-h-64 overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">
        {JSON.stringify(report.metadata_json, null, 2)}
      </pre>
    </article>
  );
}

function ReportMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
      <p className="text-xs font-bold uppercase tracking-normal text-slate-500">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}

function labelForReport(reportType: string) {
  const labels: Record<string, string> = {
    audit: "Relatório de Auditoria",
    patient_guidance: "Orientações ao Paciente",
    prescription_analysis: "Relatório Técnico de Prescrição",
    prescription_technical: "Relatório Técnico de Prescrição",
    reconciliation: "Relatório de Reconciliação Clínica",
  };
  return labels[reportType] ?? reportType;
}

function labelTarget(targetType: string) {
  const labels: Record<string, string> = {
    audit_events: "Auditoria filtrada",
    clinical_import: "Importação clínica",
    prescription_audit: "Checagem de prescrição",
  };
  return labels[targetType] ?? targetType;
}

function labelStatus(status: string) {
  const labels: Record<string, string> = {
    generated: "Gerado",
  };
  return labels[status] ?? status;
}

function ReportBadge({
  label,
  tone = "slate",
}: {
  label: string;
  tone?: "slate" | "cyan" | "green" | "amber";
}) {
  const classes = {
    slate: "bg-slate-100 text-slate-700",
    cyan: "bg-cyan-50 text-cyan-800",
    green: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-800",
  }[tone];
  return <span className={`rounded-lg px-2.5 py-1 text-xs font-bold ${classes}`}>{label}</span>;
}
