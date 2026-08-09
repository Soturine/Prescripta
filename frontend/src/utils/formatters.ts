import type { PrescriptionStatus, RiskLevel } from "../types/prescription";
import type { UserRole } from "../types/user";
import i18n, { currentLocale } from "../i18n";

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
  const key = `risk.${level}`;
  return i18n.exists(key) ? i18n.t(key) : humanizeTechnicalValue(level);
}

export function formatStatus(status: PrescriptionStatus | string) {
  const key = `status.${status}`;
  return i18n.exists(key) ? i18n.t(key) : humanizeTechnicalValue(status);
}

export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat(currentLocale(), {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatDose(value: number | null | undefined) {
  return value === null || value === undefined
    ? (currentLocale() === "en-US" ? "Not calculable" : "Não calculável")
    : `${value.toLocaleString(currentLocale())} mg`;
}

export function formatRole(role: UserRole | string | null | undefined) {
  if (!role) return "-";
  const key = `roles.${role as UserRole}`;
  return i18n.exists(key) ? i18n.t(key) : humanizeTechnicalValue(role);
}

export function humanizeTechnicalValue(value: string) {
  const spaced = value.replace(/[._-]+/g, " ").trim();
  return spaced ? spaced.charAt(0).toLocaleUpperCase(currentLocale()) + spaced.slice(1) : "-";
}

export function formatAuditAction(action: string) {
  const labels: Record<string, string> = {
    "patient.create": "Criou paciente",
    "patient.update": "Editou paciente",
    "patient.quick_triage": "Atualizou triagem clínica",
    "medication.create": "Criou medicamento",
    "medication.update": "Editou medicamento",
    "prescription.check": "Verificou prescrição",
    "prescription.alert_fired": "Registrou alerta de prescrição",
    "prescription.clinical_intelligence_evaluated": "Avaliou inteligência clínica",
    "prescription.explain": "Gerou explicação da prescrição",
    "decision_override.requested": "Solicitou override clínico",
    "decision_override.reviewed": "Revisou override clínico",
    "auth.login_succeeded": "Autenticou sessão",
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
  if (currentLocale() === "en-US") return humanizeTechnicalValue(action);
  return labels[action] ?? humanizeTechnicalValue(action);
}
