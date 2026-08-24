import { FlaskConical, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function DemoContext({ experimental = false }: { experimental?: boolean }) {
  const { t } = useTranslation();
  return (
    <div className="inline-flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-bold text-slate-600">
      <span className="inline-flex items-center gap-1.5"><ShieldCheck aria-hidden="true" className="h-4 w-4 text-emerald-700" />{t("common.syntheticData")}</span>
      <span aria-hidden="true" className="text-slate-300">/</span><span>{t("common.demoEnvironment")}</span>
      {experimental ? <><span aria-hidden="true" className="text-slate-300">/</span><span className="inline-flex items-center gap-1.5 text-violet-800"><FlaskConical aria-hidden="true" className="h-4 w-4" />{t("common.experimental")}</span></> : null}
    </div>
  );
}
