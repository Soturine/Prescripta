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
import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import DemoContext from "../components/ui/DemoContext";
import LoadingState from "../components/LoadingState";
import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import Badge from "../components/ui/Badge";
import StatusPanel from "../components/ui/StatusPanel";
import { APP_VERSION } from "../config/appVersion";
import { useAuth } from "../context/AuthContext";
import { fetchApiHealth, fetchDashboard } from "../services/api";
import type { RiskLevel } from "../types/prescription";
import type { Capability } from "../types/user";
import { formatRisk, formatRole } from "../utils/formatters";

const severities: RiskLevel[] = ["critico", "alto", "moderado", "baixo"];

export default function Dashboard() {
  const { can, canAny, user } = useAuth();
  const { t } = useTranslation();
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

  if (isLoading) return <LoadingState label={t("dashboard.loading")} />;
  if (error || !data) {
    return (
      <StatusPanel actions={<button className="btn-secondary" onClick={() => void refetch()} type="button">{t("common.tryAgain")}</button>} title={t("dashboard.errorTitle")} tone="danger">
        {t("dashboard.errorBody")}
      </StatusPanel>
    );
  }

  const metrics = [
    can("patient.read") ? { label: t("dashboard.assignedPatients"), value: data.patient_count, icon: Users, to: "/patients", detail: t("dashboard.authorizedLinks") } : null,
    can("medication.read") ? { label: t("dashboard.catalogMedications"), value: data.medication_count, icon: Pill, to: "/medications", detail: t("dashboard.demoBase") } : null,
    canAny("prescription.check", "audit.read") ? { label: t("dashboard.recordedDecisions"), value: data.prescription_checks, icon: ClipboardList, to: can("audit.read") ? "/audit" : "/prescription-check", detail: t("dashboard.accumulatedTrail") } : null,
    canAny("audit.read", "safety.review") ? { label: t("dashboard.highAlerts"), value: (data.alerts_by_severity.alto ?? 0) + (data.alerts_by_severity.critico ?? 0), icon: AlertTriangle, to: "/audit", detail: t("dashboard.requireAttention") } : null,
  ].filter(Boolean) as Array<{ label: string; value: number; icon: typeof Users; to: string; detail: string }>;
  const actions = quickActions(t).filter((action) => can(action.capability));

  const primaryAction = actions[0];

  return (
    <div className="grid gap-8 lg:gap-10">
      <section className="border-b border-slate-200 pb-6">
        <PageHeader
          title={t("dashboard.hello", { name: user?.name?.split(" ")[0] ?? t("dashboard.professionalFallback") })}
          description={t("dashboard.description", { role: formatRole(user?.role).toLocaleLowerCase() })}
          actions={<Badge tone="success" icon={<Activity aria-hidden="true" className="h-3.5 w-3.5" />}>{isFetching ? t("dashboard.updating") : t("dashboard.synced")}</Badge>}
        />
        <div className="mt-5"><DemoContext /></div>
      </section>

      <section className="grid gap-8 xl:grid-cols-[minmax(0,1.45fr)_minmax(19rem,.55fr)]">
        <div>
          <p className="eyebrow">{t("dashboard.continueWork")}</p>
          <h2 className="mt-2 text-2xl font-black tracking-tight text-ink">{t("dashboard.availableActions")}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{t("dashboard.continueDescription")}</p>
          {primaryAction ? <Link className="group mt-6 flex items-center gap-4 border-y border-slate-200 py-5" to={primaryAction.to}><span className="flex h-12 w-12 items-center justify-center rounded-lg bg-cyan-950 text-white"><primaryAction.icon aria-hidden="true" className="h-6 w-6" /></span><span className="min-w-0 flex-1"><span className="block text-base font-black text-ink">{primaryAction.label}</span><span className="mt-1 block text-sm text-slate-600">{primaryAction.description}</span></span><ArrowRight aria-hidden="true" className="h-5 w-5 text-ocean transition group-hover:translate-x-1" /></Link> : null}
          <div className="mt-2 divide-y divide-slate-200">
            {actions.slice(1).map((action) => {
              const Icon = action.icon;
              return <Link className="group flex min-h-16 items-center gap-3 py-3" key={action.to} to={action.to}><Icon aria-hidden="true" className="h-5 w-5 shrink-0 text-ocean" /><span className="min-w-0 flex-1"><span className="block text-sm font-extrabold text-ink">{action.label}</span><span className="block truncate text-xs text-slate-600">{action.description}</span></span><ArrowRight aria-hidden="true" className="h-4 w-4 text-slate-400 group-hover:text-ocean" /></Link>;
            })}
          </div>
        </div>

        <aside className="border-l-4 border-amber-500 bg-amber-50/70 p-5 sm:p-6">
          <p className="eyebrow text-amber-800">{t("dashboard.attentionNow")}</p>
          <p className="mt-2 text-sm leading-6 text-amber-950">{t("dashboard.attentionDescription")}</p>
          <dl className="mt-5 divide-y divide-amber-200 border-y border-amber-200">
            <div className="flex items-center justify-between gap-4 py-4"><dt className="text-sm font-bold text-amber-950">{t("dashboard.highAlerts")}</dt><dd className="tabular-number text-2xl font-black text-amber-950">{(data.alerts_by_severity.alto ?? 0) + (data.alerts_by_severity.critico ?? 0)}</dd></div>
            <div className="flex items-center justify-between gap-4 py-4"><dt className="text-sm font-bold text-amber-950">{t("dashboard.metricPending")}</dt><dd className="tabular-number text-2xl font-black text-amber-950">{data.catalog_quality.active_ingredients_pending ?? 0}</dd></div>
          </dl>
          {can("audit.read") ? <Link className="mt-4 inline-flex min-h-11 items-center gap-2 text-sm font-black text-amber-950 underline decoration-2 underline-offset-4" to="/audit">{t("dashboard.reviewAlerts")}<ArrowRight aria-hidden="true" className="h-4 w-4" /></Link> : null}
        </aside>
      </section>

      <section aria-labelledby="operational-context" className="workstation-section">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"><div><p className="eyebrow">{t("dashboard.dataState")}</p><h2 className="mt-1 text-xl font-black text-ink" id="operational-context">{t("dashboard.operationalContext")}</h2><p className="mt-1 text-sm text-slate-600">{t("dashboard.operationalDescription")}</p></div><Badge>{t("common.flows", { count: metrics.length })}</Badge></div>
        <div className="mt-5 grid gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => <Link className="flex min-h-28 flex-col bg-white p-4 hover:bg-cyan-50/40" key={metric.label} to={metric.to}><span className="flex items-center gap-2 text-xs font-bold text-slate-600"><metric.icon aria-hidden="true" className="h-4 w-4 text-ocean" />{metric.label}</span><span className="tabular-number mt-2 text-2xl font-black text-ink">{metric.value}</span><span className="mt-auto pt-2 text-xs text-slate-600">{metric.detail}</span></Link>)}
        </div>
      </section>

      {can("medication.read") ? (
        <section className="workstation-section">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-extrabold uppercase tracking-[0.14em] text-ocean">{t("dashboard.coverage")}</p><h2 className="mt-1 text-xl font-black tracking-tight text-ink">{t("dashboard.catalogQuality")}</h2><p className="mt-1 text-sm text-slate-600">{t("dashboard.catalogDescription")}</p></div><Link className="btn-secondary" to="/medications">{t("dashboard.reviewCatalog")}<ArrowRight aria-hidden="true" className="h-4 w-4" /></Link></div>
          <dl className="mt-6 grid gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 sm:grid-cols-2 lg:grid-cols-4">
            {catalogMetrics(data.catalog_quality, t).map(([label, value, tone]) => <div className="bg-white p-4" key={label}><dt className="text-xs font-bold leading-5 text-slate-500">{label}</dt><dd className={`mt-2 text-2xl font-black ${tone}`}>{value}</dd></div>)}
          </dl>
        </section>
      ) : null}

      {canAny("audit.read", "safety.review") ? (
        <section className="workstation-section">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="text-xl font-black tracking-tight text-ink">{t("dashboard.safetySignals")}</h2><p className="mt-1 text-sm text-slate-600">{t("dashboard.safetyDescription")}</p></div><Link className="text-sm font-extrabold text-ocean hover:underline" to="/audit">{t("dashboard.openTrail")}</Link></div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{severities.map((severity) => <div className="subtle-panel p-4" key={severity}><div className="flex items-center justify-between gap-3"><RiskBadge level={severity} /><span className="text-2xl font-black text-ink">{data.alerts_by_severity[severity] ?? 0}</span></div><p className="mt-3 text-xs font-semibold text-slate-500">{formatRisk(severity)}</p></div>)}</div>
        </section>
      ) : null}

      {canViewHealth ? <section className="workstation-section"><div className="flex items-center gap-3"><HeartPulse aria-hidden="true" className="h-5 w-5 text-emerald-700" /><div><h2 className="text-base font-black text-ink">{t("dashboard.systemHealth")}</h2><p className="text-xs text-slate-500">{t("dashboard.adminVisibility")}</p></div></div><dl className="mt-4 grid gap-px overflow-hidden rounded-lg border border-slate-200 bg-slate-200 sm:grid-cols-3">{[["API", health?.version ? `v${health.version}` : APP_VERSION], [t("dashboard.database"), health?.database ?? t("dashboard.unavailable")], [t("dashboard.ai"), health?.ai_provider ?? t("dashboard.deterministicFallback")]].map(([term, value]) => <div className="flex items-center justify-between gap-3 bg-white px-4 py-3" key={term}><dt className="text-xs font-bold text-slate-500">{term}</dt><dd className="text-right text-xs font-extrabold text-ink">{value}</dd></div>)}</dl></section> : <StatusPanel title={t("dashboard.sessionScope")} tone="info">{t("dashboard.sessionScopeBody")}</StatusPanel>}

      <p className="text-center text-xs leading-5 text-slate-600">{t("dashboard.footer", { version: APP_VERSION })}</p>
    </div>
  );
}

function quickActions(t: TFunction): Array<{ to: string; label: string; description: string; icon: typeof ShieldCheck; capability: Capability }> {
  return [
    { to: "/prescription-check", label: t("actions.checkTitle"), description: t("actions.checkDescription"), icon: ShieldCheck, capability: "prescription.check" },
    { to: "/patients", label: t("actions.patientsTitle"), description: t("actions.patientsDescription"), icon: Users, capability: "patient.read" },
    { to: "/clinical-imports", label: t("actions.reconcileTitle"), description: t("actions.reconcileDescription"), icon: DatabaseZap, capability: "reconciliation.review" },
    { to: "/protocols", label: t("actions.protocolsTitle"), description: t("actions.protocolsDescription"), icon: Siren, capability: "report.read" },
    { to: "/reports", label: t("actions.reportsTitle"), description: t("actions.reportsDescription"), icon: FileText, capability: "report.read" },
    { to: "/audit", label: t("actions.auditTitle"), description: t("actions.auditDescription"), icon: FileClock, capability: "audit.read" },
    { to: "/settings/ai", label: t("actions.aiTitle"), description: t("actions.aiDescription"), icon: Settings, capability: "ai.status.view" },
  ];
}

function catalogMetrics(quality: Record<string, number>, t: TFunction): Array<[string, number, string]> {
  return [
    [t("dashboard.metricActiveIngredients"), quality.active_ingredients_total ?? 0, "text-ink"],
    [t("dashboard.metricCurated"), quality.active_ingredients_curated ?? 0, "text-emerald-700"],
    [t("dashboard.metricPending"), quality.active_ingredients_pending ?? 0, "text-amber-700"],
    [t("dashboard.metricDemo"), quality.medications_demo ?? 0, "text-slate-700"],
    [t("dashboard.metricNoSource"), quality.medications_without_source ?? 0, "text-amber-700"],
    [t("dashboard.metricNoDose"), quality.medications_without_dose_rule ?? 0, "text-red-700"],
    [t("dashboard.metricNoPolicy"), quality.medications_without_policy ?? 0, "text-red-700"],
    [t("dashboard.metricCounseling"), quality.counseling_summaries ?? 0, "text-ocean"],
  ];
}
