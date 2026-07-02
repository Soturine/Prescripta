from dataclasses import dataclass

from app.domain.alert import Alert, RiskLevel
from app.domain.medication import Medication
from app.services.text import normalize_text


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
        description="Associacao demonstrativa com maior risco de sangramento.",
        recommendation="Evitar associacao sem revisao clinica especializada.",
    ),
    InteractionRule(
        medication_a="enalapril",
        medication_b="espironolactona",
        severity=RiskLevel.HIGH,
        description="Associacao demonstrativa com risco de hipercalemia.",
        recommendation="Revisar necessidade e monitorar potassio quando aplicavel.",
    ),
    InteractionRule(
        medication_a="sinvastatina",
        medication_b="claritromicina",
        severity=RiskLevel.CRITICAL,
        description="Associacao demonstrativa com maior risco de toxicidade muscular.",
        recommendation="Considerar alternativa ou suspensao temporaria conforme avaliacao.",
    ),
    InteractionRule(
        medication_a="metformina",
        medication_b="contraste iodado",
        severity=RiskLevel.HIGH,
        description="Associacao demonstrativa que exige cautela em funcao renal reduzida.",
        recommendation="Revisar funcao renal e protocolo local antes de prosseguir.",
    ),
    InteractionRule(
        medication_a="sertralina",
        medication_b="tramadol",
        severity=RiskLevel.HIGH,
        description="Associacao demonstrativa com risco de sindrome serotoninergica.",
        recommendation="Avaliar alternativa analgesica e sinais de toxicidade.",
    ),
]


def _medication_terms(medication: Medication) -> set[str]:
    return {
        normalize_text(medication.brand_name),
        normalize_text(medication.active_ingredient),
        normalize_text(medication.therapeutic_class),
    }


def _matches(value: str, terms: set[str]) -> bool:
    normalized = normalize_text(value)
    return any(normalized == term or normalized in term or term in normalized for term in terms)


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
        current_matches_a = any(side_a == current or side_a in current for current in current_terms)
        current_matches_b = any(side_b == current or side_b in current for current in current_terms)

        if (new_matches_a and current_matches_b) or (new_matches_b and current_matches_a):
            alerts.append(
                Alert(
                    code="DRUG_INTERACTION",
                    title="Interacao medicamentosa demonstrativa",
                    description=rule.description,
                    severity=rule.severity,
                    recommendation=rule.recommendation,
                )
            )

    return alerts
