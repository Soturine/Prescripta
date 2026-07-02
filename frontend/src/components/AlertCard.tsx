import { AlertTriangle, CheckCircle2 } from "lucide-react";

import type { Alert } from "../types/prescription";
import { formatRisk } from "../utils/formatters";
import RiskBadge from "./RiskBadge";

type AlertCardProps = {
  alert: Alert;
};

export default function AlertCard({ alert }: AlertCardProps) {
  const isCritical = alert.severity === "critico" || alert.severity === "alto";
  const Icon = isCritical ? AlertTriangle : CheckCircle2;

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-ocean">
            <Icon aria-hidden="true" className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-ink">{alert.title}</h3>
            <p className="mt-1 text-sm leading-6 text-slate-600">{alert.description}</p>
          </div>
        </div>
        <RiskBadge level={alert.severity} />
      </div>
      <div className="mt-4 border-t border-slate-100 pt-3 text-sm text-slate-700">
        <span className="font-semibold text-slate-900">{formatRisk(alert.severity)}:</span>{" "}
        {alert.recommendation}
      </div>
    </article>
  );
}
