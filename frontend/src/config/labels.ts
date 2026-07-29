import type { UserRole } from "../types/user";

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Administração",
  medico: "Médico",
  enfermagem: "Enfermagem",
  farmaceutico: "Farmacêutico",
  psicologo: "Psicólogo",
  auditor: "Auditoria",
  clinical_safety_officer: "Clinical safety officer",
};

export const PROFESSION_LABELS = {
  administration: "Administração",
  medicine: "Medicina",
  nursing: "Enfermagem",
  pharmacy: "Farmácia",
  psychology: "Psicologia",
  audit: "Auditoria",
  clinical_safety: "Segurança clínica",
} as const;

export const POLICY_LABELS: Record<string, string> = {
  legal_regulatory: "Legal/regulatória",
  institutional_policy: "Política institucional",
  clinical_recommendation: "Recomendação clínica",
  demo_policy: "Política demonstrativa",
};

export const AI_LABELS = {
  title: "IA assistiva",
  fallback: "Fallback determinístico",
  limitation: "A IA explica e extrai; não decide nem valida regras.",
} as const;
