from dataclasses import dataclass

from app.domain.alert import Alert, PrescriptionStatus, RiskLevel


@dataclass(frozen=True)
class PrescriptionInput:
    dose_mg: float
    frequency_per_day: int
    route: str

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
