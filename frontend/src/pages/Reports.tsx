import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, FileText, ShieldCheck } from "lucide-react";

import EmptyState from "../components/EmptyState";
import LoadingState from "../components/LoadingState";
import { exportReportJson, fetchReports } from "../services/api";
import { formatDateTime } from "../utils/formatters";

export default function Reports() {
  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });
  const exportMutation = useMutation({ mutationFn: exportReportJson });

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Relatórios</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Histórico auditável de relatórios gerados, hashes, versões de template e uso de IA.
        </p>
      </header>

      {isLoading ? <LoadingState label="Carregando relatorios" /> : null}
      {!isLoading && reports.length === 0 ? (
        <EmptyState title="Nenhum relatório gerado" />
      ) : null}

      <section className="grid gap-3">
        {reports.map((report) => (
          <article
            className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
            key={report.id}
          >
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <FileText aria-hidden="true" className="h-5 w-5 text-ocean" />
                  <h2 className="text-lg font-bold text-ink">
                    #{report.id} {labelForReport(report.report_type)}
                  </h2>
                  <ReportBadge label={report.status} />
                  {report.anonymized ? <ReportBadge label="Anonimizado" tone="cyan" /> : null}
                  {report.ai_used ? (
                    <ReportBadge label="Narrativa por IA" tone="green" />
                  ) : (
                    <ReportBadge label="Fallback determinístico" tone="amber" />
                  )}
                </div>
                <p className="mt-2 text-sm text-slate-600">
                  {formatDateTime(report.generated_at)} - alvo {report.target_type} #
                  {report.target_id}
                </p>
                <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
                  <p>Template: {report.template_version}</p>
                  <p>Prescripta: {report.prescripta_version}</p>
                  <p>
                    IA: {report.ai_provider ?? "fallback"} / {report.ai_model ?? "determinístico"}
                  </p>
                  <p>Prompt: {report.ai_prompt_version ?? "-"}</p>
                </div>
                <p className="mt-3 break-all rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-600">
                  EvidenceBundle {report.evidence_bundle_hash}
                </p>
              </div>
              <button
                className="btn-secondary w-fit"
                disabled={exportMutation.isPending}
                onClick={() => exportMutation.mutate(report.id)}
                title="Exportar JSON"
                type="button"
              >
                <Download aria-hidden="true" className="h-4 w-4" />
                Exportar JSON
              </button>
            </div>
          </article>
        ))}
      </section>

      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-medium leading-6 text-amber-900">
        <div className="flex gap-3">
          <ShieldCheck aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0" />
          Relatorios registram metadados, hash e provedor/modelo quando usados. API keys e segredos
          nunca são exportados.
        </div>
      </section>
    </div>
  );
}

function labelForReport(reportType: string) {
  const labels: Record<string, string> = {
    prescription_technical: "Relatório Técnico de Prescrição",
    patient_guidance: "Orientações ao Paciente",
    reconciliation: "Relatório de Reconciliação Clínica",
    audit: "Relatório de Auditoria",
  };
  return labels[reportType] ?? reportType;
}

function ReportBadge({ label, tone = "slate" }: { label: string; tone?: "slate" | "cyan" | "green" | "amber" }) {
  const classes = {
    slate: "bg-slate-100 text-slate-700",
    cyan: "bg-cyan-50 text-cyan-800",
    green: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-800",
  }[tone];
  return <span className={`rounded-lg px-2.5 py-1 text-xs font-bold ${classes}`}>{label}</span>;
}
