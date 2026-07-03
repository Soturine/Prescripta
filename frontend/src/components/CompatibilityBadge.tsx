import { Activity } from "lucide-react";

type CompatibilityBadgeProps = {
  level: "alta" | "moderada" | "baixa";
};

const classes = {
  alta: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  moderada: "bg-amber-50 text-amber-700 ring-amber-200",
  baixa: "bg-red-50 text-red-700 ring-red-200",
};

export default function CompatibilityBadge({ level }: CompatibilityBadgeProps) {
  return (
    <span
      className={[
        "inline-flex min-h-7 items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-bold ring-1",
        classes[level],
      ].join(" ")}
    >
      <Activity aria-hidden="true" className="h-3.5 w-3.5" />
      Compatibilidade {level}
    </span>
  );
}
