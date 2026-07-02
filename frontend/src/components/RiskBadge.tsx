import { ShieldAlert } from "lucide-react";

import type { PrescriptionStatus, RiskLevel } from "../types/prescription";
import { formatRisk, formatStatus } from "../utils/formatters";

type RiskBadgeProps = {
  level?: RiskLevel | string;
  status?: PrescriptionStatus | string;
};

const riskClasses: Record<string, string> = {
  baixo: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  moderado: "bg-amber-50 text-amber-700 ring-amber-200",
  alto: "bg-orange-50 text-orange-700 ring-orange-200",
  critico: "bg-red-50 text-red-700 ring-red-200",
};

const statusClasses: Record<string, string> = {
  liberado: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  atencao: "bg-amber-50 text-amber-700 ring-amber-200",
  bloqueado: "bg-red-50 text-red-700 ring-red-200",
};

export default function RiskBadge({ level, status }: RiskBadgeProps) {
  const value = level ?? status ?? "baixo";
  const className = level ? riskClasses[value] : statusClasses[value];

  return (
    <span
      className={[
        "inline-flex min-h-7 items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold ring-1",
        className ?? riskClasses.baixo,
      ].join(" ")}
    >
      <ShieldAlert aria-hidden="true" className="h-3.5 w-3.5" />
      {level ? formatRisk(value) : formatStatus(value)}
    </span>
  );
}
