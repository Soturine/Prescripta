import type { PrescriptionStatus, RiskLevel } from "../types/prescription";
import type { UserRole } from "../types/user";

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

export function formatRole(role: UserRole | string | null | undefined) {
  const labels: Record<string, string> = {
    admin: "Admin",
    medico: "Médico",
    enfermagem: "Enfermagem",
    auditor: "Auditor",
  };
  return role ? (labels[role] ?? role) : "-";
}

export function formatAuditAction(action: string) {
  const labels: Record<string, string> = {
    "patient.create": "Criou paciente",
    "patient.update": "Editou paciente",
    "patient.quick_triage": "Atualizou triagem clínica",
    "medication.create": "Criou medicamento",
    "medication.update": "Editou medicamento",
    "prescription.check": "Verificou prescrição",
    "user.create": "Criou usuário",
    "user.status_update": "Alterou status de usuário",
    "user.role_update": "Alterou perfil de usuário",
  };
  return labels[action] ?? action;
}
