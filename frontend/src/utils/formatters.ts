import type { PrescriptionStatus, RiskLevel } from "../types/prescription";

export function splitList(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function joinList(value: string[] | null | undefined) {
  return value?.join(", ") ?? "";
}

export function formatRisk(level: RiskLevel | string) {
  const labels: Record<string, string> = {
    baixo: "Baixo",
    moderado: "Moderado",
    alto: "Alto",
    critico: "Crítico",
  };
  return labels[level] ?? level;
}

export function formatStatus(status: PrescriptionStatus | string) {
  const labels: Record<string, string> = {
    liberado: "Liberado",
    atencao: "Atenção",
    bloqueado: "Bloqueado",
  };
  return labels[status] ?? status;
}

export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatDose(value: number) {
  return `${value.toLocaleString("pt-BR")} mg`;
}
