from app.domain.alert import Alert, RiskLevel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.services.text import any_token_matches


def check_allergies(patient: Patient, medication: Medication) -> list[Alert]:
    medication_terms = [
        medication.brand_name,
        medication.active_ingredient,
        medication.therapeutic_class,
    ]

    if not any_token_matches(patient.allergies, medication_terms):
        return []

    return [
        Alert(
            code="ALLERGY_BLOCK",
            title="Alergia relevante identificada",
            description=(
                "A alergia registrada coincide com o medicamento, princípio ativo "
                "ou classe terapêutica."
            ),
            severity=RiskLevel.CRITICAL,
            recommendation="Bloquear a prescrição e revisar alternativa terapêutica.",
        )
    ]
