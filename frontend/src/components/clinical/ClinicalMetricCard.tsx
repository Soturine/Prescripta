import { ArrowUpRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

export default function ClinicalMetricCard({ label, value, detail, icon: Icon, to }: {
  label: string;
  value: number;
  detail: string;
  icon: LucideIcon;
  to: string;
}) {
  return (
    <Link className="clinical-metric group" to={to}>
      <span className="clinical-metric__icon"><Icon aria-hidden="true" className="h-5 w-5" /></span>
      <ArrowUpRight aria-hidden="true" className="absolute right-4 top-4 h-4 w-4 text-slate-300 transition group-hover:text-ocean" />
      <strong className="mt-7 text-3xl font-black tracking-[-0.05em] text-ink">{value}</strong>
      <span className="mt-1 text-sm font-extrabold text-slate-700">{label}</span>
      <span className="mt-1 text-xs text-slate-500">{detail}</span>
    </Link>
  );
}
