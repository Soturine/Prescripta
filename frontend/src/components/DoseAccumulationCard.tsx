import { Calculator } from "lucide-react";

import type { DoseSummary } from "../types/prescription";
import { formatDose } from "../utils/formatters";

export default function DoseAccumulationCard({ summary }: { summary: DoseSummary }) {
  const rows = [
    ["Dose diária calculada", formatDose(summary.daily_total_mg)],
    ["Duração", summary.duration_days ? `${summary.duration_days} dias` : "Não informada"],
    [
      "Dose acumulada estimada",
      summary.estimated_cumulative_dose_mg
        ? formatDose(summary.estimated_cumulative_dose_mg)
        : "-",
    ],
    ["Limite diário", formatDose(summary.max_daily_dose_mg)],
    [
      "Limite acumulado",
      summary.max_cumulative_dose_mg ? formatDose(summary.max_cumulative_dose_mg) : "-",
    ],
  ];

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <Calculator aria-hidden="true" className="h-5 w-5 text-ocean" />
        <h2 className="text-lg font-bold text-ink">Dose acumulada e duração</h2>
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
            <dt className="label">{label}</dt>
            <dd className="mt-1 font-semibold text-ink">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
