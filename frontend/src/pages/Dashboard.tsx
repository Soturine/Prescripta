import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ClipboardList, Pill, Users } from "lucide-react";

import LoadingState from "../components/LoadingState";
import RiskBadge from "../components/RiskBadge";
import { fetchDashboard } from "../services/api";
import type { RiskLevel } from "../types/prescription";
import { formatRisk } from "../utils/formatters";

const severities: RiskLevel[] = ["baixo", "moderado", "alto", "critico"];

export default function Dashboard() {
  const { data, error, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: fetchDashboard,
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
  ];

  return (
    <div className="grid gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-normal text-ink">Dashboard</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          Sistema educacional de apoio à identificação de riscos antes da prescrição.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
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
        Prescripta v0.5.0 prioriza catalogo farmacologico Brasil/Anvisa/DCB, principio ativo
        primeiro, aliases comerciais e vocabulario clinico controlado. As decisoes criticas
        continuam vindo de regras deterministicas cadastradas no backend.
      </section>
    </div>
  );
}
