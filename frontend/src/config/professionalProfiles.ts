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
  "clinical_protocol.read": "Ler protocolos institucionais",
  "clinical_protocol.manage": "Gerenciar protocolos institucionais",
  "clinical_protocol.review": "Revisar protocolos institucionais",
  "pharmacy.intervention.read": "Ler intervenções farmacêuticas",
  "pharmacy.intervention.write": "Registrar intervenções farmacêuticas",
  "pharmacy.intervention.decide": "Decidir intervenção farmacêutica",
  "pharmacy.reconciliation.write": "Executar reconciliação medicamentosa",
  "pharmacy.formulation.review": "Revisar formulação e concentração",
  "research.study.read": "Ler estudos",
  "research.study.create": "Criar estudos",
  "research.study.write": "Editar drafts de estudo",
  "research.study.review": "Revisar artefatos de estudo",
  "research.cohort.read": "Ler coortes e runs",
  "research.cohort.write": "Criar versões de coorte",
  "research.cohort.execute": "Executar coorte determinística",
  "research.concept_set.read": "Ler concept sets",
  "research.concept_set.write": "Criar concept sets",
  "research.analysis.read": "Ler análises descritivas",
  "research.analysis.write": "Editar planos de análise",
  "research.ai.use": "Usar IA assistiva em pesquisa",
  "evidence.read": "Ler evidências",
  "evidence.write": "Cadastrar e vincular evidências",
  "data_quality.read": "Ler achados de qualidade",
  "data_quality.run": "Executar regras de qualidade",
  "patient.timeline.read": "Ler timeline autorizada",
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

const researchCapabilities: Capability[] = [
  "research.study.read",
  "research.study.create",
  "research.study.write",
  "research.study.review",
  "research.cohort.read",
  "research.cohort.write",
  "research.cohort.execute",
  "research.concept_set.read",
  "research.concept_set.write",
  "research.analysis.read",
  "research.analysis.write",
  "research.ai.use",
  "evidence.read",
  "evidence.write",
  "data_quality.read",
  "data_quality.run",
];

export const PROFESSIONAL_TEMPLATES: Record<UserRole, ProfileTemplate> = {
  admin: {
    profession: "administration",
    description: "Administração do sistema sem acesso clínico automático.",
    capabilities: ["dashboard.view", "user.manage", "access.manage", "clinical_protocol.read", "clinical_protocol.manage", "clinical_protocol.review", "medication.read", "medication.manage", "patient.timeline.read", ...researchCapabilities, "audit.read", "ai.status.view", "ai.settings.manage", "system.health.view"],
  },
  medico: {
    profession: "medicine",
    description: "Prescrição, revisão e orientação dentro de vínculo assistencial.",
    capabilities: ["dashboard.view", "patient.create", "patient.read", "patient.write", "prescription.check", "prescription.override", "medication.read", "report.read", "report.create", "patient_guidance.create", "break_glass.invoke", "patient.timeline.read", "clinical_protocol.read", "pharmacy.intervention.decide", "ai.status.view"],
  },
  enfermagem: {
    profession: "nursing",
    description: "Administração e prescrição somente sob protocolo institucional válido.",
    capabilities: ["dashboard.view", "patient.read", "patient.write", "administration.review", "nursing.protocol_prescribe", "prescription.check", "clinical_protocol.read", "medication.read", "report.read", "patient_guidance.create", "break_glass.invoke", "patient.timeline.read", "ai.status.view"],
  },
  farmaceutico: {
    profession: "pharmacy",
    description: "Reconciliação, intervenção e segurança medicamentosa.",
    capabilities: ["dashboard.view", "patient.read", "medication.read", "reconciliation.review", "pharmacy.intervention.read", "pharmacy.intervention.write", "pharmacy.reconciliation.write", "pharmacy.formulation.review", "prescription.check", "report.read", "report.create", "patient_guidance.create", "break_glass.invoke", "patient.timeline.read", "ai.status.view"],
  },
  psicologo: {
    profession: "psychology",
    description: "Contexto psicológico segmentado, somente quando autorizado.",
    capabilities: ["dashboard.view", "patient.read", "patient.sensitive_psychology.read", "psychology.context.write", "break_glass.invoke"],
  },
  auditor: {
    profession: "audit",
    description: "Trilhas, evidência e pesquisa sem acesso assistencial implícito.",
    capabilities: ["dashboard.view", "audit.read", "report.read", "ai.status.view", "research.study.read", "research.cohort.read", "research.concept_set.read", "research.analysis.read", "evidence.read", "data_quality.read"],
  },
  pesquisador: {
    profession: "research",
    description: "Estudos sintéticos aggregate-first, sem acesso automático a pacientes.",
    capabilities: ["dashboard.view", ...researchCapabilities, "ai.status.view"],
  },
  clinical_safety_officer: {
    profession: "clinical_safety",
    description: "Hazards, rulesets, protocolos, evidência e governança clínica.",
    capabilities: ["dashboard.view", "audit.read", "safety.review", "ruleset.review", "clinical_protocol.read", "clinical_protocol.manage", "clinical_protocol.review", "medication.read", "report.read", "access.manage", "research.study.read", "research.study.review", "research.cohort.read", "research.concept_set.read", "evidence.read", "evidence.write", "data_quality.read", "data_quality.run", "ai.status.view", "system.health.view"],
  },
};
