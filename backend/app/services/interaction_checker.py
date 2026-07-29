from dataclasses import dataclass

from app.domain.alert import Alert, RiskLevel
from app.domain.medication import Medication
from app.services.normalizer import normalize_text
from app.services.terminology import terminology


@dataclass(frozen=True)
class InteractionRule:
    medication_a: str
    medication_b: str
    severity: RiskLevel
    description: str
    recommendation: str


DEMO_INTERACTIONS = [
    InteractionRule(
        medication_a="varfarina",
        medication_b="ibuprofeno",
        severity=RiskLevel.CRITICAL,
        description="Associação demonstrativa com maior risco de sangramento.",
        recommendation="Evitar associação sem revisão clínica especializada.",
    ),
    InteractionRule(
        medication_a="enalapril",
        medication_b="espironolactona",
        severity=RiskLevel.HIGH,
        description="Associação demonstrativa com risco de hipercalemia.",
        recommendation="Revisar necessidade e monitorar potássio quando aplicável.",
    ),
    InteractionRule(
        medication_a="sinvastatina",
        medication_b="claritromicina",
        severity=RiskLevel.CRITICAL,
        description="Associação demonstrativa com maior risco de toxicidade muscular.",
        recommendation="Considerar alternativa ou suspensão temporária conforme avaliação.",
    ),
    InteractionRule(
        medication_a="metformina",
        medication_b="contraste iodado",
        severity=RiskLevel.HIGH,
        description="Associação demonstrativa que exige cautela em função renal reduzida.",
        recommendation="Revisar função renal e protocolo local antes de prosseguir.",
    ),
    InteractionRule(
        medication_a="sertralina",
        medication_b="tramadol",
        severity=RiskLevel.HIGH,
        description="Associação demonstrativa com risco de síndrome serotoninérgica.",
        recommendation="Avaliar alternativa analgésica e sinais de toxicidade.",
    ),
]


def _medication_terms(medication: Medication) -> set[str]:
    return {
        normalize_text(medication.brand_name),
        normalize_text(medication.active_ingredient),
        normalize_text(medication.therapeutic_class),
    }


def _matches(value: str, terms: set[str]) -> bool:
    return terminology.any_confirmed_match([value], terms)


def check_interactions(
    medication: Medication,
    current_medications: list[str],
    interaction_rules: list[InteractionRule] | None = None,
) -> list[Alert]:
    rules = interaction_rules or DEMO_INTERACTIONS
    new_terms = _medication_terms(medication)
    current_terms = [normalize_text(item) for item in current_medications]
    alerts: list[Alert] = []

    for rule in rules:
        side_a = normalize_text(rule.medication_a)
        side_b = normalize_text(rule.medication_b)
        new_matches_a = _matches(side_a, new_terms)
        new_matches_b = _matches(side_b, new_terms)
        current_matches_a = terminology.any_confirmed_match([side_a], current_terms)
        current_matches_b = terminology.any_confirmed_match([side_b], current_terms)

        if (new_matches_a and current_matches_b) or (new_matches_b and current_matches_a):
            alerts.append(
                Alert(
                    code="DRUG_INTERACTION",
                    title="Interação medicamentosa demonstrativa",
                    description=rule.description,
                    severity=rule.severity,
                    recommendation=rule.recommendation,
                )
            )

    return alerts
