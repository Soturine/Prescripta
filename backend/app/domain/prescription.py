from dataclasses import dataclass

from app.domain.alert import Alert, PrescriptionStatus, RiskLevel


@dataclass(frozen=True)
class PrescriptionInput:
    dose_mg: float
    frequency_per_day: int
    route: str
    duration_days: int | None = None
    indication: str | None = None
    professional_notes: str | None = None

    @property
    def daily_total_mg(self) -> float:
        return self.dose_mg * self.frequency_per_day


@dataclass(frozen=True)
class PrescriptionResult:
    status: PrescriptionStatus
    risk_level: RiskLevel
    alerts: list[Alert]
    recommendation: str
    human_review_required: bool
    dose_summary: dict
    compatibility: dict
    clinical_context_graph: dict
