import { GitCommitHorizontal } from "lucide-react";
import { useTranslation } from "react-i18next";

type AttritionPresentationStep = {
  sequence: number;
  label: string;
  before_count: number;
  excluded_count: number;
  after_count: number;
};

export default function AttritionFlow({ steps }: { steps: AttritionPresentationStep[] }) {
  const { t } = useTranslation();
  const baseline = Math.max(steps[0]?.before_count ?? 0, 1);

  return (
    <section aria-label={t("research.attrition")} className="mt-5">
      <h4 className="flex items-center gap-2 text-sm font-black text-ink"><GitCommitHorizontal aria-hidden="true" className="h-5 w-5 text-ocean" />{t("research.attrition")}</h4>
      <ol className="mt-4 grid gap-3">
        {steps.map((step) => {
          const percentage = step.before_count ? Math.round(step.excluded_count / step.before_count * 100) : 0;
          const remainingWidth = Math.max(6, Math.round(step.after_count / baseline * 100));
          return (
            <li aria-label={t("research.attritionStep", { label: step.label, before: step.before_count, after: step.after_count })} className="rounded-xl border border-cyan-950/10 bg-slate-50/70 p-3" key={step.sequence}>
              <div className="flex items-start justify-between gap-3 text-sm"><strong>{step.sequence}. {step.label}</strong><span className="shrink-0 font-black tabular-nums text-ink">{step.before_count} → {step.after_count}</span></div>
              <div aria-hidden="true" className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-ocean" style={{ width: `${remainingWidth}%` }} /></div>
              <p className="mt-2 text-xs text-slate-500">{t("research.removed", { count: step.excluded_count, percentage })}</p>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
