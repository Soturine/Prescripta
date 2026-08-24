import { Braces, ChevronDown, Copy } from "lucide-react";
import { useId, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

export default function TechnicalDetails({ children, label, copyValue }: { children: ReactNode; label?: string; copyValue?: string }) {
  const { t } = useTranslation();
  const regionId = useId();
  return (
    <details className="group rounded-lg border border-slate-200 bg-slate-50">
      <summary aria-controls={regionId} className="flex min-h-11 list-none items-center gap-2 px-3 py-2 text-sm font-extrabold text-slate-700 hover:text-ink">
        <Braces aria-hidden="true" className="h-4 w-4 text-slate-500" />
        <span className="flex-1">{label ?? t("common.technicalDetails")}</span>
        <ChevronDown aria-hidden="true" className="h-4 w-4 transition group-open:rotate-180" />
      </summary>
      <div className="border-t border-slate-200 p-3" id={regionId}>
        {copyValue ? <div className="mb-2 flex justify-end"><button className="inline-flex min-h-10 items-center gap-2 rounded-lg px-3 text-xs font-bold text-ocean hover:bg-white" onClick={() => void navigator.clipboard?.writeText(copyValue)} type="button"><Copy aria-hidden="true" className="h-4 w-4" />{t("common.copy")}</button></div> : null}
        {children}
      </div>
    </details>
  );
}
