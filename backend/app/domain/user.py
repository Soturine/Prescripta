from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEDICO = "medico"
    ENFERMAGEM = "enfermagem"
    FARMACEUTICO = "farmaceutico"
    PSICOLOGO = "psicologo"
    AUDITOR = "auditor"
    CLINICAL_SAFETY_OFFICER = "clinical_safety_officer"


class Profession(StrEnum):
    ADMINISTRATION = "administration"
    MEDICINE = "medicine"
    NURSING = "nursing"
    PHARMACY = "pharmacy"
    PSYCHOLOGY = "psychology"
    AUDIT = "audit"
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
    UserRole.CLINICAL_SAFETY_OFFICER: Profession.CLINICAL_SAFETY,
}


PROFESSION_CAPABILITY_TEMPLATES: dict[Profession, tuple[Capability, ...]] = {
    Profession.ADMINISTRATION: (
        Capability.DASHBOARD_VIEW,
        Capability.USER_MANAGE,
        Capability.ACCESS_MANAGE,
        Capability.MEDICATION_READ,
        Capability.MEDICATION_MANAGE,
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
        Capability.AI_STATUS_VIEW,
    ),
    Profession.NURSING: (
        Capability.DASHBOARD_VIEW,
        Capability.PATIENT_READ,
        Capability.PATIENT_WRITE,
        Capability.ADMINISTRATION_REVIEW,
        Capability.NURSING_PROTOCOL_PRESCRIBE,
        Capability.MEDICATION_READ,
        Capability.REPORT_READ,
        Capability.PATIENT_GUIDANCE_CREATE,
        Capability.BREAK_GLASS_INVOKE,
        Capability.AI_STATUS_VIEW,
    ),
    Profession.PHARMACY: (
        Capability.DASHBOARD_VIEW,
        Capability.PATIENT_READ,
        Capability.MEDICATION_READ,
        Capability.RECONCILIATION_REVIEW,
        Capability.PRESCRIPTION_CHECK,
        Capability.REPORT_READ,
        Capability.REPORT_CREATE,
        Capability.PATIENT_GUIDANCE_CREATE,
        Capability.BREAK_GLASS_INVOKE,
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
    ),
    Profession.CLINICAL_SAFETY: (
        Capability.DASHBOARD_VIEW,
        Capability.AUDIT_READ,
        Capability.SAFETY_REVIEW,
        Capability.RULESET_REVIEW,
        Capability.MEDICATION_READ,
        Capability.REPORT_READ,
        Capability.ACCESS_MANAGE,
        Capability.AI_STATUS_VIEW,
        Capability.SYSTEM_HEALTH_VIEW,
    ),
}


def capability_values(profession: Profession | str) -> list[str]:
    normalized = Profession(profession)
    return [capability.value for capability in PROFESSION_CAPABILITY_TEMPLATES[normalized]]
