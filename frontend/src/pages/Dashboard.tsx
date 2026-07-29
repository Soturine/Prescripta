import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  ClipboardList,
  DatabaseZap,
  FileClock,
  FileText,
  HeartPulse,
  Pill,
  Settings,
  ShieldCheck,
  Siren,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import Badge from "../components/ui/Badge";
import StatusPanel from "../components/ui/StatusPanel";
import { APP_VERSION } from "../config/appVersion";
import { useAuth } from "../context/AuthContext";
import { fetchApiHealth, fetchDashboard } from "../services/api";
import type { Capability } from "../types/user";
import type { RiskLevel } from "../types/prescription";
import { formatRisk, formatRole } from "../utils/formatters";

const severities: RiskLevel[] = ["critico", "alto", "moderado", "baixo"];

export default function Dashboard() {
  const { can, canAny, user } = useAuth();
  const { data, error, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboard,
    staleTime: 30_000,
  });
  const canViewHealth = can("system.health.view");
  const { data: health } = useQuery({
    queryKey: ["api-health"],
    queryFn: fetchApiHealth,
    enabled: canViewHealth,
    staleTime: 30_000,
  });

  if (isLoading) return <LoadingState label="Carregando visão geral" />;

  if (error || !data) {
    return (
      <StatusPanel
        actions={<button className="btn-secondary" onClick={() => void refetch()} type="button">Tentar novamente</button>}
        title="Não foi possível carregar o workspace"
        tone="danger"
      >
        Confirme a conexão e a sessão antes de repetir. Nenhuma decisão clínica foi executada.
      </StatusPanel>
    );
  }

  const metrics = [
    can("patient.read") ? { label: "Pacientes atribuídos", value: data.patient_count, icon: Users, to: "/patients", detail: "Vínculos autorizados" } : null,
    can("medication.read") ? { label: "Medicamentos no catálogo", value: data.medication_count, icon: Pill, to: "/medications", detail: "Base demonstrativa" } : null,
    canAny("prescription.check", "audit.read") ? { label: "Decisões registradas", value: data.prescription_checks, icon: ClipboardList, to: can("audit.read") ? "/audit" : "/prescription-check", detail: "Trilha acumulada" } : null,
    canAny("audit.read", "safety.review") ? { label: "Alertas altos e críticos", value: (data.alerts_by_severity.alto ?? 0) + (data.alerts_by_severity.critico ?? 0), icon: AlertTriangle, to: "/audit", detail: "Exigem atenção" } : null,
  ].filter(Boolean) as Array<{ label: string; value: number; icon: typeof Users; to: string; detail: string }>;

  const actions = quickActions.filter((action) => can(action.capability));

  return (
    <div className="grid gap-6 lg:gap-8">
      <PageHeader
        title={`Olá, ${user?.name?.split(" ")[0] ?? "profissional"}`}
        description={`Workspace de ${formatRole(user?.role).toLowerCase()}, organizado pelas capacidades efetivamente concedidas à sua sessão.`}
        actions={<Badge tone="success" icon={<Activity aria-hidden="true" className="h-3.5 w-3.5" />}>{isFetching ? "Atualizando" : "Dados sincronizados"}</Badge>}
      />

      <section aria-label="Resumo operacional" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Link className="group surface-card flex min-h-36 flex-col justify-between p-5 transition hover:-translate-y-0.5 hover:border-cyan-300 hover:shadow-float" key={metric.label} to={metric.to}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-50 text-ocean">
                  <Icon aria-hidden="true" className="h-5 w-5" />
                </div>
                <ArrowRight aria-hidden="true" className="h-4 w-4 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-ocean" />
              </div>
              <div className="mt-5">
                <p className="text-3xl font-black tracking-[-0.04em] text-ink">{metric.value}</p>
                <p className="mt-1 text-sm font-extrabold text-slate-700">{metric.label}</p>
                <p className="mt-1 text-xs text-slate-500">{metric.detail}</p>
              </div>
            </Link>
          );
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(20rem,.65fr)]">
        <div className="surface-card overflow-hidden">
          <div className="border-b border-slate-200 px-5 py-4 sm:px-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-black tracking-tight text-ink">Ações disponíveis</h2>
                <p className="mt-1 text-sm text-slate-600">Atalhos úteis, filtrados por capacidade profissional.</p>
              </div>
              <Badge>{actions.length} fluxos</Badge>
            </div>
          </div>
          <div className="grid sm:grid-cols-2">
            {actions.map((action) => {
              const Icon = action.icon;
              return (
                <Link className="group flex min-h-32 gap-4 border-b border-slate-100 p-5 transition hover:bg-cyan-50/50 sm:border-r" key={action.to} to={action.to}>
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-ocean transition group-hover:bg-white">
                    <Icon aria-hidden="true" className="h-5 w-5" />
                  </span>
                  <span className="min-w-0">
                    <span className="flex items-center gap-2 text-sm font-extrabold text-ink">
                      {action.label}
                      <ArrowRight aria-hidden="true" className="h-4 w-4 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-ocean" />
                    </span>
                    <span className="mt-1 block text-xs leading-5 text-slate-500">{action.description}</span>
                  </span>
                </Link>
              );
            })}
          </div>
        </div>

        {canViewHealth ? (
          <section className="surface-card p-5 sm:p-6">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700"><HeartPulse aria-hidden="true" className="h-5 w-5" /></span>
              <div>
                <h2 className="text-lg font-black text-ink">Saúde do sistema</h2>
                <p className="text-xs text-slate-500">Visível pela capacidade administrativa</p>
              </div>
            </div>
            <dl className="mt-5 grid gap-3">
              {[["API", health?.version ? `v${health.version}` : APP_VERSION], ["Banco", health?.database ?? "Indisponível"], ["IA", health?.ai_provider ?? "Fallback determinístico"]].map(([term, value]) => (
                <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2.5" key={term}>
                  <dt className="text-xs font-bold text-slate-500">{term}</dt>
                  <dd className="text-right text-xs font-extrabold text-ink">{value}</dd>
                </div>
              ))}
            </dl>
          </section>
        ) : (
          <StatusPanel title="Escopo da sessão" tone="info">
            Você vê somente módulos compatíveis com suas capacidades. Um perfil global, por si só, não concede acesso a pacientes.
          </StatusPanel>
        )}
      </section>

      {can("medication.read") ? (
        <section className="surface-card p-5 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-ocean">Cobertura</p>
              <h2 className="mt-1 text-xl font-black tracking-tight text-ink">Qualidade do catálogo</h2>
              <p className="mt-1 text-sm text-slate-600">Lacunas permanecem visíveis; “demo” e “pendente” nunca aparentam validação.</p>
            </div>
            <Link className="btn-secondary" to="/medications">Revisar catálogo <ArrowRight aria-hidden="true" className="h-4 w-4" /></Link>
          </div>
          <dl className="mt-6 grid gap-px overflow-hidden rounded-2xl border border-slate-200 bg-slate-200 sm:grid-cols-2 lg:grid-cols-4">
            {catalogMetrics(data.catalog_quality).map(([label, value, tone]) => (
              <div className="bg-white p-4" key={label}>
                <dt className="text-xs font-bold leading-5 text-slate-500">{label}</dt>
                <dd className={`mt-2 text-2xl font-black ${tone}`}>{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      ) : null}

      {canAny("audit.read", "safety.review") ? (
        <section className="surface-card p-5 sm:p-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xl font-black tracking-tight text-ink">Sinais de segurança registrados</h2>
              <p className="mt-1 text-sm text-slate-600">Contagem acumulada na trilha de auditoria; não representa incidência clínica.</p>
            </div>
            <Link className="text-sm font-extrabold text-ocean hover:underline" to="/audit">Abrir trilha</Link>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {severities.map((severity) => (
              <div className="subtle-panel p-4" key={severity}>
                <div className="flex items-center justify-between gap-3">
                  <RiskBadge level={severity} />
                  <span className="text-2xl font-black text-ink">{data.alerts_by_severity[severity] ?? 0}</span>
                </div>
                <p className="mt-3 text-xs font-semibold text-slate-500">{formatRisk(severity)}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <p className="text-center text-xs leading-5 text-slate-500">
        Prescripta {APP_VERSION} · ambiente demonstrativo · decisões críticas permanecem determinísticas e auditáveis.
      </p>
    </div>
  );
}

const quickActions: Array<{
  to: string;
  label: string;
  description: string;
  icon: typeof ShieldCheck;
  capability: Capability;
}> = [
  { to: "/prescription-check", label: "Checar prescrição", description: "Dose estruturada, contexto, cobertura e decisão persistida.", icon: ShieldCheck, capability: "prescription.check" },
  { to: "/patients", label: "Abrir pacientes", description: "Somente pacientes com vínculo ou grant ativo.", icon: Users, capability: "patient.read" },
  { to: "/clinical-imports", label: "Reconciliar dados", description: "Aceitar ou rejeitar cada item sem sobrescrita automática.", icon: DatabaseZap, capability: "reconciliation.review" },
  { to: "/protocols", label: "Consultar protocolos", description: "Etapas demonstrativas com fonte e limites explícitos.", icon: Siren, capability: "report.read" },
  { to: "/reports", label: "Relatórios e evidências", description: "Bundles, hashes, exportações e narrativa controlada.", icon: FileText, capability: "report.read" },
  { to: "/audit", label: "Trilha de auditoria", description: "Decisões, negações e eventos de segurança.", icon: FileClock, capability: "audit.read" },
  { to: "/settings/ai", label: "Saúde da IA", description: "Provider, fallback e status, sem expor credenciais.", icon: Settings, capability: "ai.status.view" },
];

function catalogMetrics(quality: Record<string, number>): Array<[string, number, string]> {
  return [
    ["Princípios ativos", quality.active_ingredients_total ?? 0, "text-ink"],
    ["Curados ou validados", quality.active_ingredients_curated ?? 0, "text-emerald-700"],
    ["Pendentes de revisão", quality.active_ingredients_pending ?? 0, "text-amber-700"],
    ["Medicamentos demo", quality.medications_demo ?? 0, "text-slate-700"],
    ["Sem fonte externa", quality.medications_without_source ?? 0, "text-amber-700"],
    ["Regra de dose pendente", quality.medications_without_dose_rule ?? 0, "text-red-700"],
    ["Política pendente", quality.medications_without_policy ?? 0, "text-red-700"],
    ["Resumos para orientação", quality.counseling_summaries ?? 0, "text-ocean"],
  ];
}
