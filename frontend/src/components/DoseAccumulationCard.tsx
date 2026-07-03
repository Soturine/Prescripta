import { Calculator } from "lucide-react";

import type { DoseSummary } from "../types/prescription";
import { formatDose } from "../utils/formatters";

export default function DoseAccumulationCard({ summary }: { summary: DoseSummary }) {
  const rows = [
    ["Dose diaria calculada", formatDose(summary.daily_total_mg)],
    ["Duracao planejada", summary.duration_days ? `${summary.duration_days} dias` : "Nao informada"],
    [
      "Dose acumulada estimada",
      summary.estimated_cumulative_dose_mg
        ? formatDose(summary.estimated_cumulative_dose_mg)
        : "-",
    ],
    ["Limite diario", formatDose(summary.max_daily_dose_mg)],
    ["Duracao maxima", summary.max_duration_days ? `${summary.max_duration_days} dias` : "-"],
    [
      "Limite acumulado",
      summary.max_cumulative_dose_mg ? formatDose(summary.max_cumulative_dose_mg) : "-",
    ],
    ["Uso continuo", summary.continuous_use ? "Sim" : "Nao"],
    ["Monitoramento necessario", summary.monitoring_required ? "Sim" : "Nao"],
  ];
  const mechanismRows = [
    ["Mecanismo", summary.mechanism_profile.mechanism_of_action ?? "-"],
    ["Metabolizacao", summary.mechanism_profile.metabolism_organs.join(", ") || "-"],
    ["Eliminacao", summary.mechanism_profile.elimination_organs.join(", ") || "-"],
    ["Eliminacao renal", summary.mechanism_profile.renal_elimination_level],
    ["Metabolismo hepatico", summary.mechanism_profile.hepatic_metabolism_level],
    ["CYP/interacoes", summary.mechanism_profile.cyp_interactions.join(", ") || "-"],
  ];

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <Calculator aria-hidden="true" className="h-5 w-5 text-ocean" />
        <h2 className="text-lg font-bold text-ink">Dose acumulada e duracao</h2>
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <dt className="label">{label}</dt>
            <dd className="mt-1 font-semibold text-ink">{value}</dd>
          </div>
        ))}
      </dl>
      {summary.monitoring_notes ? (
        <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm font-medium text-amber-900">
          {summary.monitoring_notes}
        </p>
      ) : null}
      <div className="mt-4 border-t border-slate-100 pt-4">
        <h3 className="text-sm font-bold text-ink">
          Perfil farmacocinetico/farmacodinamico
        </h3>
        <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
          {mechanismRows.map(([label, value]) => (
            <div key={label} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
              <dt className="label">{label}</dt>
              <dd className="mt-1 font-semibold text-ink">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
