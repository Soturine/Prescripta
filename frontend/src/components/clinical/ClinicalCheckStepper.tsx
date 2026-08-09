import { Check } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function ClinicalCheckStepper({ hasResult }: { hasResult: boolean }) {
  const { t } = useTranslation();
  const steps = ["stepPatient", "stepMedication", "stepDose", "stepReview", "stepResult"];
  const activeIndex = hasResult ? 4 : 3;

  return (
    <nav aria-label={t("prescription.title")} className="surface-card overflow-x-auto p-3 sm:p-4">
      <ol className="grid min-w-[38rem] grid-cols-5 gap-2">
        {steps.map((step, index) => {
          const complete = index < activeIndex;
          const active = index === activeIndex;
          return (
            <li aria-current={active ? "step" : undefined} className={`relative flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-extrabold ${active ? "bg-cyan-50 text-ocean ring-1 ring-cyan-700/20" : "text-slate-500"}`} key={step}>
              <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${complete ? "bg-emerald-700 text-white" : active ? "bg-ocean text-white" : "bg-slate-100"}`}>{complete ? <Check aria-hidden="true" className="h-4 w-4" /> : index + 1}</span>
              <span>{t(`prescription.${step}`)}</span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
