import { BookOpen, Bot, CircleHelp, ExternalLink, ShieldCheck, UserRoundCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import PageHeader from "../components/PageHeader";
import StatusPanel from "../components/ui/StatusPanel";

const guides = [
  ["nav.patients", "/patients", "patients.md"],
  ["nav.prescriptionCheck", "/prescription-check", "prescription-check.md"],
  ["nav.pharmacy", "/pharmacy", "pharmacy.md"],
  ["nav.research", "/research", "research/README.md"],
  ["nav.audit", "/audit", "audit.md"],
] as const;

export default function Help() {
  const { t } = useTranslation();

  return (
    <div className="grid gap-6">
      <PageHeader title={t("help.title")} description={t("help.description")} />

      <section className="clinical-hero grid gap-6 p-6 lg:grid-cols-[1fr_auto] lg:items-center">
        <div>
          <div className="flex items-center gap-2 text-sm font-black text-ocean">
            <CircleHelp aria-hidden="true" className="h-5 w-5" />
            {t("help.startTitle")}
          </div>
          <ol className="mt-5 grid gap-3 text-sm leading-6 text-slate-700 sm:grid-cols-2">
            {["demo", "profile", "start", "ai", "guide"].map((step, index) => (
              <li className="flex gap-3" key={step}>
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-ocean text-xs font-black text-white">{index + 1}</span>
                <span>{t(`help.${step}`)}</span>
              </li>
            ))}
          </ol>
        </div>
        <div className="hidden h-28 w-28 items-center justify-center rounded-[2rem] bg-white/75 text-ocean shadow-soft lg:flex">
          <UserRoundCheck aria-hidden="true" className="h-14 w-14" />
        </div>
      </section>

      <section className="surface-card p-5 sm:p-6">
        <h2 className="flex items-center gap-2 text-xl font-black text-ink"><BookOpen aria-hidden="true" className="h-5 w-5 text-ocean" />{t("help.routesTitle")}</h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {guides.map(([labelKey, route, guide]) => (
            <div className="subtle-panel flex min-h-32 flex-col justify-between p-4" key={route}>
              <h3 className="font-extrabold text-ink">{t(labelKey)}</h3>
              <div className="mt-4 flex flex-wrap gap-3 text-sm font-bold">
                <Link className="text-ocean hover:underline" to={route}>{t("common.aboutPage")}</Link>
                <a className="inline-flex items-center gap-1 text-slate-600 hover:text-ocean" href={`https://github.com/Soturine/Prescripta/blob/main/docs/user-guide/${guide}`} rel="noreferrer" target="_blank">
                  {t("help.openGuide")}<ExternalLink aria-hidden="true" className="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
          ))}
        </div>
        <a className="btn-secondary mt-5" href="https://github.com/Soturine/Prescripta/blob/main/docs/user-guide/glossary.md" rel="noreferrer" target="_blank">
          {t("help.glossary")}<ExternalLink aria-hidden="true" className="h-4 w-4" />
        </a>
      </section>

      <StatusPanel icon={<ShieldCheck aria-hidden="true" className="h-5 w-5" />} title={t("help.safetyTitle")} tone="info">
        <span className="inline-flex gap-2"><Bot aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" />{t("help.safetyBody")}</span>
      </StatusPanel>
    </div>
  );
}
