import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowRight,
  ClipboardList,
  DatabaseZap,
  FileText,
  Pill,
  Settings,
  ShieldCheck,
  Siren,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import RiskBadge from "../components/RiskBadge";
import { APP_VERSION } from "../config/appVersion";
import { fetchApiHealth, fetchDashboard } from "../services/api";
import type { RiskLevel } from "../types/prescription";
import { formatRisk } from "../utils/formatters";

const severities: RiskLevel[] = ["baixo", "moderado", "alto", "critico"];

export default function Dashboard() {
  const { data, error, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboard,
  });
  const { data: health } = useQuery({
    queryKey: ["api-health"],
    queryFn: fetchApiHealth,
  });

  if (isLoading) {
    return <LoadingState label="Carregando dashboard" />;
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">
        Não foi possível carregar o dashboard.
      </div>
    );
  }

  const cards = [
    { label: "Pacientes", value: data.patient_count, icon: Users, color: "text-ocean" },
    { label: "Medicamentos", value: data.medication_count, icon: Pill, color: "text-mint" },
    {
      label: "Prescrições",
      value: data.prescription_checks,
      icon: ClipboardList,
      color: "text-warning",
    },
    { label: "Protocolos", value: 7, icon: Siren, color: "text-danger" },
  ];

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Dashboard</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Sistema educacional de apoio à identificação de riscos antes da prescrição.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <article key={card.label} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-500">{card.label}</p>
                  <p className="mt-2 text-3xl font-bold text-ink">{card.value}</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100">
                  <Icon aria-hidden="true" className={`h-6 w-6 ${card.color}`} />
                </div>
              </div>
            </article>
          );
        })}
      </section>

      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              className="group rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-ocean hover:bg-cyan-50"
              key={action.to}
              to={action.to}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-ocean">
                  <Icon aria-hidden="true" className="h-5 w-5" />
                </div>
                <ArrowRight
                  aria-hidden="true"
                  className="h-4 w-4 text-slate-400 transition group-hover:text-ocean"
                />
              </div>
              <p className="mt-3 text-sm font-bold text-ink">{action.label}</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">{action.description}</p>
            </Link>
          );
        })}
      </section>

      <section className="rounded-lg border border-cyan-100 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-ink">Comece por aqui</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-5">
          {[
            ["1", "Abra o paciente"],
            ["2", "Revise histórico/laudos"],
            ["3", "Cheque a prescrição"],
            ["4", "Gere orientação/relatório"],
            ["5", "Use protocolo rápido se necessário"],
          ].map(([step, label]) => (
            <div className="rounded-lg border border-slate-100 bg-slate-50 p-4" key={step}>
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-50 text-sm font-bold text-ocean">
                {step}
              </span>
              <p className="mt-3 text-sm font-bold text-ink">{label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-bold text-ink">Alertas por severidade</h2>
            <p className="mt-1 text-sm text-slate-500">Contagem acumulada em auditoria.</p>
          </div>
          <AlertCircle aria-hidden="true" className="h-6 w-6 text-ocean" />
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {severities.map((severity) => (
            <div key={severity} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
              <div className="flex items-center justify-between gap-2">
                <RiskBadge level={severity} />
                <span className="text-2xl font-bold text-ink">
                  {data.alerts_by_severity[severity] ?? 0}
                </span>
              </div>
              <p className="mt-3 text-sm font-medium text-slate-600">{formatRisk(severity)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-cyan-200 bg-cyan-50 p-4 text-sm leading-6 text-cyan-900">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-bold">Prescripta {APP_VERSION}</p>
            <p>
              Decisões críticas continuam vindo de regras determinísticas no backend; IA é
              explicativa, auditável e sempre substituível por fallback local.
            </p>
          </div>
          <div className="grid gap-1 text-xs font-semibold sm:text-right">
            <span>API: {health?.version ? `v${health.version}` : APP_VERSION}</span>
            <span>Banco: {health?.database ?? "-"}</span>
            <span>IA: {health?.ai_provider ?? "fallback"}</span>
          </div>
        </div>
      </section>
    </div>
  );
}

const quickActions = [
  {
    to: "/prescription-check",
    label: "Checar prescrição",
    description: "Validar dose, cautelas, interações e histórico disponível.",
    icon: ShieldCheck,
  },
  {
    to: "/clinical-imports",
    label: "Reconciliar importação",
    description: "Revisar itens FHIR, JSON ou CSV antes de aplicar no paciente.",
    icon: DatabaseZap,
  },
  {
    to: "/reports",
    label: "Abrir relatórios",
    description: "Ver PDFs, hashes, evidências e exportações geradas.",
    icon: FileText,
  },
  {
    to: "/protocols",
    label: "Abrir protocolos",
    description: "Consultar fluxos rápidos com fonte, contexto mínimo e auditoria.",
    icon: Siren,
  },
  {
    to: "/settings/ai",
    label: "Saúde da IA",
    description: "Conferir provider, fallback, cache e histórico recente.",
    icon: Settings,
  },
];
