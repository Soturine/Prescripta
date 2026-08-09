import { CircleHelp } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

export default function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  const { t } = useTranslation();
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="mb-2 text-xs font-black uppercase tracking-[0.16em] text-ocean">Prescripta · {t("shell.kicker")}</p>
        <h1 className="text-3xl font-black tracking-[-0.04em] text-ink outline-none sm:text-4xl" id="page-title" tabIndex={-1}>{title}</h1>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{description}</p> : null}
      </div>
      <div className="flex flex-wrap gap-2">
        {actions}
        <a className="btn-secondary" href="/help"><CircleHelp aria-hidden="true" className="h-4 w-4" />{t("common.aboutPage")}</a>
      </div>
    </header>
  );
}
