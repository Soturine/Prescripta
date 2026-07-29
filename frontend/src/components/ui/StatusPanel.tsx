import { AlertCircle, CheckCircle2, Info, ShieldAlert, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

type StatusTone = "info" | "success" | "warning" | "danger" | "critical";

const styles: Record<StatusTone, { icon: typeof Info; className: string }> = {
  info: { icon: Info, className: "border-cyan-200 bg-cyan-50 text-cyan-950" },
  success: { icon: CheckCircle2, className: "border-emerald-200 bg-emerald-50 text-emerald-950" },
  warning: { icon: TriangleAlert, className: "border-amber-300 bg-amber-50 text-amber-950" },
  danger: { icon: AlertCircle, className: "border-red-300 bg-red-50 text-red-950" },
  critical: { icon: ShieldAlert, className: "border-red-500 bg-red-50 text-red-950" },
};

export default function StatusPanel({
  title,
  children,
  tone = "info",
  actions,
  live = false,
}: {
  title: string;
  children?: ReactNode;
  tone?: StatusTone;
  actions?: ReactNode;
  live?: boolean;
}) {
  const Icon = styles[tone].icon;
  return (
    <section
      aria-live={live ? "polite" : undefined}
      className={`rounded-2xl border p-4 sm:p-5 ${styles[tone].className}`}
      role={tone === "critical" || tone === "danger" ? "alert" : "status"}
    >
      <div className="flex items-start gap-3">
        <Icon aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0" />
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-extrabold">{title}</h2>
          {children ? <div className="mt-1 text-sm leading-6 opacity-90">{children}</div> : null}
          {actions ? <div className="mt-4 flex flex-wrap gap-2">{actions}</div> : null}
        </div>
      </div>
    </section>
  );
}
