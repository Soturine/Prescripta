from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEDICO = "medico"
    ENFERMAGEM = "enfermagem"
    FARMACEUTICO = "farmaceutico"
    PSICOLOGO = "psicologo"
    AUDITOR = "auditor"
    PESQUISADOR = "pesquisador"
    CLINICAL_SAFETY_OFFICER = "clinical_safety_officer"


class Profession(StrEnum):
    ADMINISTRATION = "administration"
    MEDICINE = "medicine"
    NURSING = "nursing"
    PHARMACY = "pharmacy"
    PSYCHOLOGY = "psychology"
    AUDIT = "audit"
    RESEARCH = "research"
    CLINICAL_SAFETY = "clinical_safety"


class Capability(StrEnum):
    DASHBOARD_VIEW = "dashboard.view"
    PATIENT_CREATE = "patient.create"
    PATIENT_READ = "patient.read"
    PATIENT_WRITE = "patient.write"
    PATIENT_SENSITIVE_PSYCHOLOGY_READ = "patient.sensitive_psychology.read"
    PRESCRIPTION_CHECK = "prescription.check"
    PRESCRIPTION_OVERRIDE = "prescription.override"
    MEDICATION_READ = "medication.read"
    MEDICATION_MANAGE = "medication.manage"
    RECONCILIATION_REVIEW = "reconciliation.review"
    ADMINISTRATION_REVIEW = "administration.review"
    NURSING_PROTOCOL_PRESCRIBE = "nursing.protocol_prescribe"
    CLINICAL_PROTOCOL_READ = "clinical_protocol.read"
    CLINICAL_PROTOCOL_MANAGE = "clinical_protocol.manage"
    CLINICAL_PROTOCOL_REVIEW = "clinical_protocol.review"
    PHARMACY_INTERVENTION_READ = "pharmacy.intervention.read"
    PHARMACY_INTERVENTION_WRITE = "pharmacy.intervention.write"
    PHARMACY_INTERVENTION_DECIDE = "pharmacy.intervention.decide"
    PHARMACY_RECONCILIATION_WRITE = "pharmacy.reconciliation.write"
    PHARMACY_FORMULATION_REVIEW = "pharmacy.formulation.review"
    RESEARCH_STUDY_READ = "research.study.read"
    RESEARCH_STUDY_CREATE = "research.study.create"
    RESEARCH_STUDY_WRITE = "research.study.write"
    RESEARCH_STUDY_REVIEW = "research.study.review"
    RESEARCH_COHORT_READ = "research.cohort.read"
    RESEARCH_COHORT_WRITE = "research.cohort.write"
    RESEARCH_COHORT_EXECUTE = "research.cohort.execute"
    RESEARCH_CONCEPT_SET_READ = "research.concept_set.read"
    RESEARCH_CONCEPT_SET_WRITE = "research.concept_set.write"
    RESEARCH_ANALYSIS_READ = "research.analysis.read"
    RESEARCH_ANALYSIS_WRITE = "research.analysis.write"
    RESEARCH_ANALYSIS_EXECUTE = "research.analysis.execute"
    RESEARCH_PATIENT_JOURNEY_READ = "research.patient_journey.read"
    RESEARCH_PACKAGE_EXPORT = "research.package.export"
    RESEARCH_AI_USE = "research.ai.use"
    RESEARCH_AGENT_USE = "research.agent.use"
    TERMINOLOGY_READ = "terminology.read"
    TERMINOLOGY_MANAGE = "terminology.manage"
    TERMINOLOGY_MAPPING_PROPOSE = "terminology.mapping.propose"
    TERMINOLOGY_MAPPING_REVIEW = "terminology.mapping.review"
    OMOP_PREVIEW = "omop.preview"
    OMOP_EXPORT = "omop.export"
    EVIDENCE_READ = "evidence.read"
    EVIDENCE_WRITE = "evidence.write"
    DATA_QUALITY_READ = "data_quality.read"
    DATA_QUALITY_RUN = "data_quality.run"
    DATA_QUALITY_ACKNOWLEDGE = "data_quality.acknowledge"
    PATIENT_TIMELINE_READ = "patient.timeline.read"
    PSYCHOLOGY_CONTEXT_WRITE = "psychology.context.write"
    REPORT_READ = "report.read"
    REPORT_CREATE = "report.create"
    PATIENT_GUIDANCE_CREATE = "patient_guidance.create"
    AUDIT_READ = "audit.read"
    SAFETY_REVIEW = "safety.review"
    RULESET_REVIEW = "ruleset.review"
    ACCESS_MANAGE = "access.manage"
    BREAK_GLASS_INVOKE = "break_glass.invoke"
    USER_MANAGE = "user.manage"
    AI_STATUS_VIEW = "ai.status.view"
    AI_SETTINGS_MANAGE = "ai.settings.manage"
    SYSTEM_HEALTH_VIEW = "system.health.view"


ALL_ROLES = tuple(UserRole)


ROLE_PROFESSION: dict[UserRole, Profession] = {
    UserRole.ADMIN: Profession.ADMINISTRATION,
    UserRole.MEDICO: Profession.MEDICINE,
    UserRole.ENFERMAGEM: Profession.NURSING,
    UserRole.FARMACEUTICO: Profession.PHARMACY,
    UserRole.PSICOLOGO: Profession.PSYCHOLOGY,
    UserRole.AUDITOR: Profession.AUDIT,
    UserRole.PESQUISADOR: Profession.RESEARCH,
    UserRole.CLINICAL_SAFETY_OFFICER: Profession.CLINICAL_SAFETY,
}


PROFESSION_CAPABILITY_TEMPLATES: dict[Profession, tuple[Capability, ...]] = {
    Profession.ADMINISTRATION: (
        Capability.DASHBOARD_VIEW,
        Capability.USER_MANAGE,
        Capability.ACCESS_MANAGE,
        Capability.CLINICAL_PROTOCOL_READ,
        Capability.CLINICAL_PROTOCOL_MANAGE,
        Capability.CLINICAL_PROTOCOL_REVIEW,
        Capability.MEDICATION_READ,
        Capability.MEDICATION_MANAGE,
        Capability.PATIENT_TIMELINE_READ,
        Capability.RESEARCH_STUDY_READ,
        Capability.RESEARCH_STUDY_CREATE,
        Capability.RESEARCH_STUDY_WRITE,
        Capability.RESEARCH_STUDY_REVIEW,
        Capability.RESEARCH_COHORT_READ,
        Capability.RESEARCH_COHORT_WRITE,
        Capability.RESEARCH_COHORT_EXECUTE,
        Capability.RESEARCH_CONCEPT_SET_READ,
        Capability.RESEARCH_CONCEPT_SET_WRITE,
        Capability.RESEARCH_ANALYSIS_READ,
        Capability.RESEARCH_ANALYSIS_WRITE,
        Capability.RESEARCH_ANALYSIS_EXECUTE,
        Capability.RESEARCH_PATIENT_JOURNEY_READ,
        Capability.RESEARCH_PACKAGE_EXPORT,
        Capability.RESEARCH_AI_USE,
        Capability.RESEARCH_AGENT_USE,
        Capability.TERMINOLOGY_READ,
        Capability.TERMINOLOGY_MANAGE,
        Capability.TERMINOLOGY_MAPPING_PROPOSE,
        Capability.TERMINOLOGY_MAPPING_REVIEW,
        Capability.OMOP_PREVIEW,
        Capability.OMOP_EXPORT,
        Capability.EVIDENCE_READ,
        Capability.EVIDENCE_WRITE,
        Capability.DATA_QUALITY_READ,
        Capability.DATA_QUALITY_RUN,
        Capability.DATA_QUALITY_ACKNOWLEDGE,
        Capability.AUDIT_READ,
        Capability.AI_STATUS_VIEW,
        Capability.AI_SETTINGS_MANAGE,
        Capability.SYSTEM_HEALTH_VIEW,
    ),
    Profession.MEDICINE: (
        Capability.DASHBOARD_VIEW,
        Capability.PATIENT_CREATE,
        Capability.PATIENT_READ,
        Capability.PATIENT_WRITE,
        Capability.PRESCRIPTION_CHECK,
        Capability.PRESCRIPTION_OVERRIDE,
        Capability.MEDICATION_READ,
        Capability.REPORT_READ,
        Capability.REPORT_CREATE,
        Capability.PATIENT_GUIDANCE_CREATE,
        Capability.BREAK_GLASS_INVOKE,
        Capability.PATIENT_TIMELINE_READ,
        Capability.CLINICAL_PROTOCOL_READ,
        Capability.PHARMACY_INTERVENTION_DECIDE,
        Capability.AI_STATUS_VIEW,
    ),
    Profession.NURSING: (
        Capability.DASHBOARD_VIEW,
        Capability.PATIENT_READ,
        Capability.PATIENT_WRITE,
        Capability.ADMINISTRATION_REVIEW,
        Capability.NURSING_PROTOCOL_PRESCRIBE,
        Capability.PRESCRIPTION_CHECK,
        Capability.CLINICAL_PROTOCOL_READ,
        Capability.MEDICATION_READ,
        Capability.REPORT_READ,
        Capability.PATIENT_GUIDANCE_CREATE,
        Capability.BREAK_GLASS_INVOKE,
        Capability.PATIENT_TIMELINE_READ,
        Capability.AI_STATUS_VIEW,
    ),
    Profession.PHARMACY: (
        Capability.DASHBOARD_VIEW,
        Capability.PATIENT_READ,
        Capability.MEDICATION_READ,
        Capability.RECONCILIATION_REVIEW,
        Capability.PHARMACY_INTERVENTION_READ,
        Capability.PHARMACY_INTERVENTION_WRITE,
        Capability.PHARMACY_RECONCILIATION_WRITE,
        Capability.PHARMACY_FORMULATION_REVIEW,
        Capability.PRESCRIPTION_CHECK,
        Capability.REPORT_READ,
        Capability.REPORT_CREATE,
        Capability.PATIENT_GUIDANCE_CREATE,
        Capability.BREAK_GLASS_INVOKE,
        Capability.PATIENT_TIMELINE_READ,
        Capability.AI_STATUS_VIEW,
    ),
    Profession.PSYCHOLOGY: (
        Capability.DASHBOARD_VIEW,
        Capability.PATIENT_READ,
        Capability.PATIENT_SENSITIVE_PSYCHOLOGY_READ,
        Capability.PSYCHOLOGY_CONTEXT_WRITE,
        Capability.BREAK_GLASS_INVOKE,
    ),
    Profession.AUDIT: (
        Capability.DASHBOARD_VIEW,
        Capability.AUDIT_READ,
        Capability.REPORT_READ,
        Capability.AI_STATUS_VIEW,
        Capability.RESEARCH_STUDY_READ,
        Capability.RESEARCH_COHORT_READ,
        Capability.RESEARCH_CONCEPT_SET_READ,
        Capability.RESEARCH_ANALYSIS_READ,
        Capability.TERMINOLOGY_READ,
        Capability.EVIDENCE_READ,
        Capability.DATA_QUALITY_READ,
    ),
    Profession.RESEARCH: (
        Capability.DASHBOARD_VIEW,
        Capability.RESEARCH_STUDY_READ,
        Capability.RESEARCH_STUDY_CREATE,
        Capability.RESEARCH_STUDY_WRITE,
        Capability.RESEARCH_STUDY_REVIEW,
        Capability.RESEARCH_COHORT_READ,
        Capability.RESEARCH_COHORT_WRITE,
        Capability.RESEARCH_COHORT_EXECUTE,
        Capability.RESEARCH_CONCEPT_SET_READ,
        Capability.RESEARCH_CONCEPT_SET_WRITE,
        Capability.RESEARCH_ANALYSIS_READ,
        Capability.RESEARCH_ANALYSIS_WRITE,
        Capability.RESEARCH_ANALYSIS_EXECUTE,
        Capability.RESEARCH_PATIENT_JOURNEY_READ,
        Capability.RESEARCH_PACKAGE_EXPORT,
        Capability.RESEARCH_AI_USE,
        Capability.RESEARCH_AGENT_USE,
        Capability.TERMINOLOGY_READ,
        Capability.TERMINOLOGY_MAPPING_PROPOSE,
        Capability.TERMINOLOGY_MAPPING_REVIEW,
        Capability.OMOP_PREVIEW,
        Capability.OMOP_EXPORT,
        Capability.EVIDENCE_READ,
        Capability.EVIDENCE_WRITE,
        Capability.DATA_QUALITY_READ,
        Capability.DATA_QUALITY_RUN,
        Capability.DATA_QUALITY_ACKNOWLEDGE,
        Capability.AI_STATUS_VIEW,
    ),
    Profession.CLINICAL_SAFETY: (
        Capability.DASHBOARD_VIEW,
        Capability.AUDIT_READ,
        Capability.SAFETY_REVIEW,
        Capability.RULESET_REVIEW,
        Capability.CLINICAL_PROTOCOL_READ,
        Capability.CLINICAL_PROTOCOL_MANAGE,
        Capability.CLINICAL_PROTOCOL_REVIEW,
        Capability.MEDICATION_READ,
        Capability.REPORT_READ,
        Capability.ACCESS_MANAGE,
        Capability.RESEARCH_STUDY_READ,
        Capability.RESEARCH_STUDY_REVIEW,
        Capability.RESEARCH_COHORT_READ,
        Capability.RESEARCH_CONCEPT_SET_READ,
        Capability.TERMINOLOGY_READ,
        Capability.TERMINOLOGY_MAPPING_REVIEW,
        Capability.OMOP_PREVIEW,
        Capability.EVIDENCE_READ,
        Capability.EVIDENCE_WRITE,
        Capability.DATA_QUALITY_READ,
        Capability.DATA_QUALITY_RUN,
        Capability.DATA_QUALITY_ACKNOWLEDGE,
        Capability.AI_STATUS_VIEW,
        Capability.SYSTEM_HEALTH_VIEW,
    ),
}


def capability_values(profession: Profession | str) -> list[str]:
    normalized = Profession(profession)
    return [capability.value for capability in PROFESSION_CAPABILITY_TEMPLATES[normalized]]
