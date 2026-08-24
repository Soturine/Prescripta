import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

export default function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  const { t } = useTranslation();
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="eyebrow mb-2">Prescripta · {t("shell.kicker")}</p>
        <h1 className="text-3xl font-black tracking-[-0.035em] text-ink outline-none sm:text-[2.5rem] sm:leading-tight" id="page-title" tabIndex={-1}>{title}</h1>
        {description ? <p className="mt-2 max-w-[72ch] text-sm leading-6 text-slate-600">{description}</p> : null}
      </div>
      <div className="flex flex-wrap gap-2">
        {actions}
      </div>
    </header>
  );
}
