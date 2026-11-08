import { beforeEach, describe, expect, it } from "vitest";

import { selectLocale } from "../i18n";
import { formatAuditAction, formatDose, formatRisk, formatRole, formatStatus, joinList, splitList } from "./formatters";

describe("formatadores de domínio", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    await selectLocale("pt-BR");
  });

  it("normaliza listas sem manter itens vazios", () => {
    expect(splitList(" renal, , hepática ")).toEqual(["renal", "hepática"]);
    expect(joinList(["renal", "hepática"])).toBe("renal, hepática");
    expect(joinList(undefined)).toBe("");
  });

  it("traduz risco, status, papel e auditoria", () => {
    expect(formatRisk("critico")).toBe("Crítico");
    expect(formatStatus("bloqueado")).toBe("Bloqueado");
    expect(formatRole("farmaceutico")).toBe("Farmacêutico");
    expect(formatAuditAction("patient.create")).toBe("Criou paciente");
    expect(formatAuditAction("decision_override.reviewed")).toBe("Revisou override clínico");
    expect(formatAuditAction("custom.event")).toBe("Custom event");
  });

  it("formata dose no locale brasileiro", () => {
    expect(formatDose(1250)).toContain("mg");
    expect(formatDose(null)).toBe("Não calculável");
  });
});

describe("formatDose sem ambiguidade (NEW-14)", () => {
  it("não arredonda doses pequenas e mantém zero à esquerda", async () => {
    const i18n = (await import("../i18n")).default;
    await i18n.changeLanguage("pt-BR");
    const { formatDose } = await import("./formatters");
    expect(formatDose(0.0625)).toBe("0,0625 mg");
    expect(formatDose(0.0005)).toBe("0,0005 mg");
    expect(formatDose(0.5)).toBe("0,5 mg");
    expect(formatDose(5)).toBe("5 mg");
    expect(formatDose(1200.5)).toBe("1200,5 mg");
    await i18n.changeLanguage("en-US");
    expect(formatDose(0.0625)).toBe("0.0625 mg");
    expect(formatDose(1200.5)).toBe("1200.5 mg");
    await i18n.changeLanguage("pt-BR");
  });
});
