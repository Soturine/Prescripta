import type { PrescriptionStatus, RiskLevel } from "../types/prescription";
import type { UserRole } from "../types/user";
import { ROLE_LABELS } from "../config/labels";
import { RISK_LABELS, STATUS_LABELS } from "../config/statuses";

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
  return RISK_LABELS[level] ?? level;
}

export function formatStatus(status: PrescriptionStatus | string) {
  return STATUS_LABELS[status] ?? status;
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
  return role ? (ROLE_LABELS[role as UserRole] ?? role) : "-";
}

export function formatAuditAction(action: string) {
  const labels: Record<string, string> = {
    "patient.create": "Criou paciente",
    "patient.update": "Editou paciente",
    "patient.quick_triage": "Atualizou triagem clínica",
    "medication.create": "Criou medicamento",
    "medication.update": "Editou medicamento",
    "prescription.check": "Verificou prescrição",
    "medication_counseling.generate": "Gerou resumo prático",
    "medication_counseling.review": "Revisou resumo prático",
    "patient.functional_profile.update": "Atualizou perfil funcional",
    "clinical_reconciliation.item.accepted": "Aceitou item reconciliado",
    "clinical_reconciliation.item.rejected": "Rejeitou item reconciliado",
    "clinical_reconciliation.safe_items.accepted": "Aceitou itens sem conflito",
    "user.create": "Criou usuário",
    "user.status_update": "Alterou status de usuário",
    "user.role_update": "Alterou perfil de usuário",
  };
  return labels[action] ?? action;
}
