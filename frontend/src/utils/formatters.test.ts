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
