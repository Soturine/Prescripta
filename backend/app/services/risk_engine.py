from app.domain.alert import Alert, PrescriptionStatus, RiskLevel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput, PrescriptionResult
from app.services.allergy_checker import check_allergies
from app.services.dose_calculator import check_max_daily_dose
from app.services.interaction_checker import check_interactions
from app.services.text import any_token_matches, normalize_text

RISK_ORDER = [
    RiskLevel.LOW,
    RiskLevel.MODERATE,
    RiskLevel.HIGH,
    RiskLevel.CRITICAL,
]


def _max_risk(alerts: list[Alert]) -> RiskLevel:
    if not alerts:
        return RiskLevel.LOW
    return max((alert.severity for alert in alerts), key=lambda level: RISK_ORDER.index(level))


def _increase_risk(level: RiskLevel) -> RiskLevel:
    index = min(RISK_ORDER.index(level) + 1, len(RISK_ORDER) - 1)
    return RISK_ORDER[index]


def _status_for_risk(level: RiskLevel) -> PrescriptionStatus:
    if level == RiskLevel.CRITICAL:
        return PrescriptionStatus.BLOCKED
    if level in {RiskLevel.MODERATE, RiskLevel.HIGH}:
        return PrescriptionStatus.ATTENTION
    return PrescriptionStatus.RELEASED


def _recommendation(status: PrescriptionStatus) -> str:
    if status == PrescriptionStatus.BLOCKED:
        return "Nao prosseguir sem revisao humana e ajuste da prescricao."
    if status == PrescriptionStatus.ATTENTION:
        return "Revisar alertas antes de liberar a prescricao."
    return "Nenhum risco relevante foi identificado pelas regras cadastradas."


class RiskEngine:
    def evaluate(
        self,
        patient: Patient,
        medication: Medication,
        prescription: PrescriptionInput,
    ) -> PrescriptionResult:
        alerts: list[Alert] = []
        alerts.extend(check_allergies(patient, medication))
        alerts.extend(check_max_daily_dose(medication, prescription))
        alerts.extend(check_interactions(medication, patient.current_medications))
        alerts.extend(self._check_polypharmacy(patient))
        alerts.extend(self._check_contraindications(patient, medication))
        alerts.extend(self._check_route(medication, prescription))

        risk_level = _max_risk(alerts)
        if self._is_elderly(patient):
            alerts.append(
                Alert(
                    code="AGE_RISK",
                    title="Fator de risco por idade",
                    description="Paciente com idade igual ou superior a 65 anos.",
                    severity=RiskLevel.LOW,
                    recommendation="Aplicar revisao cuidadosa da prescricao.",
                )
            )
            risk_level = _increase_risk(risk_level)

        status = _status_for_risk(risk_level)
        return PrescriptionResult(
            status=status,
            risk_level=risk_level,
            alerts=alerts,
            recommendation=_recommendation(status),
            human_review_required=status != PrescriptionStatus.RELEASED,
        )

    def _check_polypharmacy(self, patient: Patient) -> list[Alert]:
        if len(patient.current_medications) < 5:
            return []
        return [
            Alert(
                code="POLYPHARMACY",
                title="Polifarmacia identificada",
                description="Paciente usa cinco ou mais medicamentos continuos.",
                severity=RiskLevel.MODERATE,
                recommendation="Revisar necessidade, duplicidades e risco cumulativo.",
            )
        ]

    def _check_contraindications(self, patient: Patient, medication: Medication) -> list[Alert]:
        if not any_token_matches(patient.comorbidities, medication.contraindications):
            return []
        return [
            Alert(
                code="CONTRAINDICATION",
                title="Contraindicacao por comorbidade",
                description="Comorbidade do paciente coincide com contraindicação cadastrada.",
                severity=RiskLevel.HIGH,
                recommendation="Revisar a prescricao e considerar alternativa terapeutica.",
            )
        ]

    def _check_route(self, medication: Medication, prescription: PrescriptionInput) -> list[Alert]:
        informed_route = normalize_text(prescription.route)
        allowed_routes = [normalize_text(route) for route in medication.allowed_routes]
        if informed_route in allowed_routes:
            return []
        return [
            Alert(
                code="INVALID_ROUTE",
                title="Via nao permitida",
                description="Via informada nao consta nas vias permitidas do medicamento.",
                severity=RiskLevel.HIGH,
                recommendation="Ajustar a via de administracao antes de prosseguir.",
            )
        ]

    def _is_elderly(self, patient: Patient) -> bool:
        age = patient.computed_age
        return age is not None and age >= 65
