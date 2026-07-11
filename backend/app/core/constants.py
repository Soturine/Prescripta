from typing import Final

APP_JURISDICTION: Final = "BR"
DEMO_CREDENTIAL_STATUS: Final = "demo_unverified"
PENDING_REVIEW: Final = "pending_review"

POLICY_TYPES: Final = frozenset(
    {"legal_regulatory", "institutional_policy", "clinical_recommendation", "demo_policy"}
)
POLICY_STRENGTHS: Final = frozenset({"warning_only", "requires_review", "soft_block", "hard_block"})
DOSE_BASES: Final = frozenset(
    {"fixed", "actual_weight", "ideal_weight", "adjusted_weight", "lean_body_mass", "bsa"}
)
DOSE_UNITS: Final = frozenset(
    {"mg", "mcg", "mg/kg", "mg/kg/dia", "mcg/kg", "mg/m²", "mcg/kg/min", "mg/kg/h"}
)

SPECIALTY_LABELS: Final = {
    "general_practice": "Medicina geral",
    "family_medicine": "Medicina de família e comunidade",
    "internal_medicine": "Clínica médica",
    "pediatrics": "Pediatria",
    "geriatrics": "Geriatria",
    "psychiatry": "Psiquiatria",
    "neurology": "Neurologia",
    "anesthesiology": "Anestesiologia",
    "emergency_medicine": "Medicina de emergência",
    "intensive_care": "Medicina intensiva",
    "oncology": "Oncologia",
    "pain_medicine": "Medicina da dor",
    "palliative_care": "Cuidados paliativos",
    "cardiology": "Cardiologia",
    "infectious_disease": "Infectologia",
    "obstetrics_gynecology": "Ginecologia e obstetrícia",
    "surgery": "Cirurgia",
    "other": "Outra especialidade demo",
}
