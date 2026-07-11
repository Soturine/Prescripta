from dataclasses import asdict, dataclass, field
from typing import Any

from app.domain.alert import RiskLevel


@dataclass(frozen=True)
class PsychotropicRiskSignal:
    code: str
    title: str
    description: str
    severity: RiskLevel
    confidence: str = "medium"
    mechanism: str = ""
    medication_classes: list[str] = field(default_factory=list)
    patient_factors: list[str] = field(default_factory=list)
    interacting_medications: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    recommendation: str = "Revisar clinicamente antes de prosseguir."
    source_ids: list[str] = field(default_factory=lambda: ["prescripta:demo:v0.8.4"])
    policy_status: str = "demo_seed"
    requires_human_review: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["severity"] = self.severity.value
        payload["deduplication_key"] = self.deduplication_key
        return payload

    @property
    def deduplication_key(self) -> str:
        medications = "+".join(sorted(set(self.interacting_medications))) or "none"
        factors = "+".join(sorted(set(self.patient_factors))) or "none"
        return f"{self.code}|{medications}|{factors}"


@dataclass(frozen=True)
class DoseIntelligenceResult:
    status: str
    calculated_dose: float | None
    calculated_unit: str
    calculation_formula: str
    calculation_basis: str
    inputs_used: dict[str, Any]
    usual_range: dict[str, float | None]
    max_limits: dict[str, float | None]
    alerts: list[dict[str, Any]]
    missing_data: list[str]
    source_refs: list[str]
    validation_status: str
    requires_human_review: bool
    educational_notice: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PrescribingPolicyResult:
    status: str
    rules_applied: list[dict[str, Any]]
    prescriber_profile: dict[str, Any]
    required_specialties: list[str]
    recommended_specialties: list[str]
    missing_credentials: list[str]
    prescription_form_requirements: list[str]
    warnings: list[str]
    legal_regulatory_notes: list[str]
    institutional_notes: list[str]
    source_refs: list[str]
    requires_human_review: bool
    educational_notice: str = (
        "Política demonstrativa; não substitui norma vigente nem decisão profissional."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
