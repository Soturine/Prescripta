import type { Capability, Profession, UserRole } from "../types/user";

export const CAPABILITY_LABELS: Record<Capability, string> = {
  "dashboard.view": "Ver dashboard",
  "patient.create": "Criar paciente",
  "patient.read": "Ler paciente autorizado",
  "patient.write": "Editar paciente autorizado",
  "patient.sensitive_psychology.read": "Ler segmento psicológico autorizado",
  "prescription.check": "Checar prescrição",
  "prescription.override": "Solicitar/revisar override",
  "medication.read": "Ler catálogo",
  "medication.manage": "Gerenciar catálogo",
  "reconciliation.review": "Revisar reconciliação",
  "administration.review": "Revisar administração",
  "nursing.protocol_prescribe": "Prescrever sob protocolo de enfermagem",
  "psychology.context.write": "Editar contexto psicológico",
  "report.read": "Ler relatórios",
  "report.create": "Criar relatório técnico",
  "patient_guidance.create": "Criar orientação ao paciente",
  "audit.read": "Ler auditoria",
  "safety.review": "Revisar eventos de segurança",
  "ruleset.review": "Revisar rulesets",
  "access.manage": "Gerenciar vínculos e grants",
  "break_glass.invoke": "Invocar break-glass",
  "user.manage": "Gerenciar usuários",
  "ai.status.view": "Ver status da IA",
  "ai.settings.manage": "Configurar IA",
  "system.health.view": "Ver saúde do sistema",
};

type ProfileTemplate = {
  profession: Profession;
  capabilities: Capability[];
  description: string;
};

export const PROFESSIONAL_TEMPLATES: Record<UserRole, ProfileTemplate> = {
  admin: {
    profession: "administration",
    description: "Administração do sistema sem acesso clínico automático.",
    capabilities: ["dashboard.view", "user.manage", "access.manage", "medication.read", "medication.manage", "audit.read", "ai.status.view", "ai.settings.manage", "system.health.view"],
  },
  medico: {
    profession: "medicine",
    description: "Prescrição, revisão e orientação dentro de vínculo assistencial.",
    capabilities: ["dashboard.view", "patient.create", "patient.read", "patient.write", "prescription.check", "prescription.override", "medication.read", "report.read", "report.create", "patient_guidance.create", "break_glass.invoke", "ai.status.view"],
  },
  enfermagem: {
    profession: "nursing",
    description: "Administração, dupla checagem e protocolo institucional válido.",
    capabilities: ["dashboard.view", "patient.read", "patient.write", "administration.review", "nursing.protocol_prescribe", "medication.read", "report.read", "patient_guidance.create", "break_glass.invoke", "ai.status.view"],
  },
  farmaceutico: {
    profession: "pharmacy",
    description: "Reconciliação, intervenção e segurança medicamentosa.",
    capabilities: ["dashboard.view", "patient.read", "medication.read", "reconciliation.review", "prescription.check", "report.read", "report.create", "patient_guidance.create", "break_glass.invoke", "ai.status.view"],
  },
  psicologo: {
    profession: "psychology",
    description: "Contexto psicológico segmentado, somente quando autorizado.",
    capabilities: ["dashboard.view", "patient.read", "patient.sensitive_psychology.read", "psychology.context.write", "break_glass.invoke"],
  },
  auditor: {
    profession: "audit",
    description: "Trilhas e relatórios sem capacidade assistencial implícita.",
    capabilities: ["dashboard.view", "audit.read", "report.read", "ai.status.view"],
  },
  clinical_safety_officer: {
    profession: "clinical_safety",
    description: "Hazards, rulesets, eventos de segurança e governança clínica.",
    capabilities: ["dashboard.view", "audit.read", "safety.review", "ruleset.review", "medication.read", "report.read", "access.manage", "ai.status.view", "system.health.view"],
  },
};
