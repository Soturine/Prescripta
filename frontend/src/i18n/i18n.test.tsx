import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import LanguageSelector from "../components/LanguageSelector";
import i18n, {
  LOCALE_STORAGE_KEY,
  resolveLocale,
  selectLocale,
} from ".";
import { formatDateTime, formatDose, formatStatus } from "../utils/formatters";

describe("locale resolution and presentation", () => {
  it("honors manual, persisted, navigator language order and fallback", () => {
    expect(resolveLocale({ manual: "en-US", persisted: "pt-BR", languages: ["pt-BR"] })).toBe("en-US");
    expect(resolveLocale({ persisted: "pt_BR", languages: ["en-US"] })).toBe("pt-BR");
    expect(resolveLocale({ languages: ["fr-FR", "en-GB"], language: "pt-BR" })).toBe("en-US");
    expect(resolveLocale({ languages: ["es-419"], language: "de-DE" })).toBe("pt-BR");
  });

  it("persists an accessible manual selection without health data", async () => {
    render(<LanguageSelector />);
    const selector = screen.getByRole("combobox", { name: "Selecionar idioma" });
    expect(screen.getByRole("option", { name: "Português (Brasil)" })).toBeVisible();
    expect(screen.getByRole("option", { name: "English (United States)" })).toBeVisible();
    fireEvent.change(selector, { target: { value: "en-US" } });
    await waitFor(() => expect(i18n.resolvedLanguage).toBe("en-US"));
    expect(window.localStorage).toHaveLength(1);
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("en-US");
    expect(document.documentElement.lang).toBe("en-US");
  });

  it("localizes statuses, numbers and dates while preserving clinical units", async () => {
    await selectLocale("pt-BR");
    expect(formatStatus("allowed_with_warning")).toBe("Permitido com ressalvas");
    const ptDate = formatDateTime("2026-08-09T12:30:00Z");
    expect(formatDose(1234.5)).toContain("mg");

    await selectLocale("en-US");
    expect(formatStatus("allowed_with_warning")).toBe("Allowed with warnings");
    expect(formatStatus("new_internal_state")).toBe("New internal state");
    expect(formatDateTime("2026-08-09T12:30:00Z")).not.toBe(ptDate);
    expect(formatDose(1234.5)).toContain("mg");
  });
});
