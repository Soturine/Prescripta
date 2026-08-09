import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import enUS from "./locales/en-US.json";
import ptBR from "./locales/pt-BR.json";

export const SUPPORTED_LOCALES = ["pt-BR", "en-US"] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];
export const LOCALE_STORAGE_KEY = "prescripta:locale";

export function normalizeLocale(value: string | null | undefined): SupportedLocale | null {
  if (!value) return null;
  const normalized = value.replace("_", "-").toLowerCase();
  if (normalized === "pt" || normalized.startsWith("pt-")) return "pt-BR";
  if (normalized === "en" || normalized.startsWith("en-")) return "en-US";
  return null;
}

export function resolveLocale(options: {
  manual?: string | null;
  persisted?: string | null;
  languages?: readonly string[];
  language?: string | null;
}): SupportedLocale {
  const candidates = [
    options.manual,
    options.persisted,
    ...(options.languages ?? []),
    options.language,
  ];
  for (const candidate of candidates) {
    const locale = normalizeLocale(candidate);
    if (locale) return locale;
  }
  return "pt-BR";
}

export function detectBrowserLocale(): SupportedLocale {
  return resolveLocale({
    persisted: window.localStorage.getItem(LOCALE_STORAGE_KEY),
    languages: navigator.languages,
    language: navigator.language,
  });
}

void i18n.use(initReactI18next).init({
  resources: {
    "pt-BR": { translation: ptBR },
    "en-US": { translation: enUS },
  },
  lng: typeof window === "undefined" ? "pt-BR" : detectBrowserLocale(),
  fallbackLng: "pt-BR",
  supportedLngs: [...SUPPORTED_LOCALES],
  load: "currentOnly",
  interpolation: { escapeValue: false },
  returnNull: false,
});

export async function selectLocale(locale: SupportedLocale): Promise<void> {
  window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  await i18n.changeLanguage(locale);
  document.documentElement.lang = locale;
}

export function currentLocale(): SupportedLocale {
  return normalizeLocale(i18n.resolvedLanguage ?? i18n.language) ?? "pt-BR";
}

export default i18n;
