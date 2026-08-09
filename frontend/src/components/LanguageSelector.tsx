import { Languages } from "lucide-react";
import { useTranslation } from "react-i18next";

import { currentLocale, selectLocale, SUPPORTED_LOCALES, type SupportedLocale } from "../i18n";

export default function LanguageSelector({ compact = false }: { compact?: boolean }) {
  const { t } = useTranslation();

  return (
    <label className="relative inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-700 shadow-xs">
      <Languages aria-hidden="true" className="h-4 w-4 text-ocean" />
      <span className={compact ? "sr-only" : "hidden xl:inline"}>{t("common.language")}</span>
      <select
        aria-label={t("locale.selectorLabel")}
        className="min-h-9 max-w-40 appearance-none bg-transparent pr-4 text-xs font-extrabold outline-none"
        onChange={(event) => void selectLocale(event.target.value as SupportedLocale)}
        value={currentLocale()}
      >
        {SUPPORTED_LOCALES.map((locale) => (
          <option key={locale} value={locale}>{t(`locale.${locale}`)}</option>
        ))}
      </select>
    </label>
  );
}
