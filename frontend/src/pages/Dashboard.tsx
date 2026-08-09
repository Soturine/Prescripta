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

import ClinicalMetricCard from "../components/clinical/ClinicalMetricCard";
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

  return (
    <div className="grid gap-6 lg:gap-8">
      <section className="clinical-hero p-5 sm:p-7">
        <PageHeader
          title={t("dashboard.hello", { name: user?.name?.split(" ")[0] ?? t("dashboard.professionalFallback") })}
          description={t("dashboard.description", { role: formatRole(user?.role).toLocaleLowerCase() })}
          actions={<Badge tone="success" icon={<Activity aria-hidden="true" className="h-3.5 w-3.5" />}>{isFetching ? t("dashboard.updating") : t("dashboard.synced")}</Badge>}
        />
      </section>

      <section aria-label={t("dashboard.operationalSummary")} className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => <ClinicalMetricCard {...metric} key={metric.label} />)}
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(20rem,.65fr)]">
        <div className="surface-card overflow-hidden">
          <div className="border-b border-slate-200 px-5 py-4 sm:px-6">
            <div className="flex items-start justify-between gap-4">
              <div><h2 className="text-lg font-black tracking-tight text-ink">{t("dashboard.availableActions")}</h2><p className="mt-1 text-sm text-slate-600">{t("dashboard.actionsDescription")}</p></div>
              <Badge>{t("common.flows", { count: actions.length })}</Badge>
            </div>
          </div>
          <div className="grid sm:grid-cols-2">
            {actions.map((action) => {
              const Icon = action.icon;
              return (
                <Link className="group flex min-h-32 gap-4 border-b border-slate-100 p-5 transition hover:bg-cyan-50/50 sm:border-r" key={action.to} to={action.to}>
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-ocean transition group-hover:bg-white"><Icon aria-hidden="true" className="h-5 w-5" /></span>
                  <span className="min-w-0"><span className="flex items-center gap-2 text-sm font-extrabold text-ink">{action.label}<ArrowRight aria-hidden="true" className="h-4 w-4 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-ocean" /></span><span className="mt-1 block text-xs leading-5 text-slate-500">{action.description}</span></span>
                </Link>
              );
            })}
          </div>
        </div>

        {canViewHealth ? (
          <section className="surface-card p-5 sm:p-6">
            <div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700"><HeartPulse aria-hidden="true" className="h-5 w-5" /></span><div><h2 className="text-lg font-black text-ink">{t("dashboard.systemHealth")}</h2><p className="text-xs text-slate-500">{t("dashboard.adminVisibility")}</p></div></div>
            <dl className="mt-5 grid gap-3">
              {[["API", health?.version ? `v${health.version}` : APP_VERSION], [t("dashboard.database"), health?.database ?? t("dashboard.unavailable")], [t("dashboard.ai"), health?.ai_provider ?? t("dashboard.deterministicFallback")]].map(([term, value]) => <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2.5" key={term}><dt className="text-xs font-bold text-slate-500">{term}</dt><dd className="text-right text-xs font-extrabold text-ink">{value}</dd></div>)}
            </dl>
          </section>
        ) : <StatusPanel title={t("dashboard.sessionScope")} tone="info">{t("dashboard.sessionScopeBody")}</StatusPanel>}
      </section>

      {can("medication.read") ? (
        <section className="surface-card p-5 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-xs font-extrabold uppercase tracking-[0.14em] text-ocean">{t("dashboard.coverage")}</p><h2 className="mt-1 text-xl font-black tracking-tight text-ink">{t("dashboard.catalogQuality")}</h2><p className="mt-1 text-sm text-slate-600">{t("dashboard.catalogDescription")}</p></div><Link className="btn-secondary" to="/medications">{t("dashboard.reviewCatalog")}<ArrowRight aria-hidden="true" className="h-4 w-4" /></Link></div>
          <dl className="mt-6 grid gap-px overflow-hidden rounded-2xl border border-slate-200 bg-slate-200 sm:grid-cols-2 lg:grid-cols-4">
            {catalogMetrics(data.catalog_quality, t).map(([label, value, tone]) => <div className="bg-white p-4" key={label}><dt className="text-xs font-bold leading-5 text-slate-500">{label}</dt><dd className={`mt-2 text-2xl font-black ${tone}`}>{value}</dd></div>)}
          </dl>
        </section>
      ) : null}

      {canAny("audit.read", "safety.review") ? (
        <section className="surface-card p-5 sm:p-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="text-xl font-black tracking-tight text-ink">{t("dashboard.safetySignals")}</h2><p className="mt-1 text-sm text-slate-600">{t("dashboard.safetyDescription")}</p></div><Link className="text-sm font-extrabold text-ocean hover:underline" to="/audit">{t("dashboard.openTrail")}</Link></div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{severities.map((severity) => <div className="subtle-panel p-4" key={severity}><div className="flex items-center justify-between gap-3"><RiskBadge level={severity} /><span className="text-2xl font-black text-ink">{data.alerts_by_severity[severity] ?? 0}</span></div><p className="mt-3 text-xs font-semibold text-slate-500">{formatRisk(severity)}</p></div>)}</div>
        </section>
      ) : null}

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
