from dataclasses import dataclass

from app.domain.alert import Alert, PrescriptionStatus, RiskLevel
from app.domain.dose import MedicationDoseInput


@dataclass(frozen=True)
class PrescriptionInput:
    dose_mg: float | None
    frequency_per_day: int | None
    route: str
    duration_days: int | None = None
    indication: str | None = None
    professional_notes: str | None = None
    dose: MedicationDoseInput | None = None

    @property
    def effective_dose(self) -> MedicationDoseInput:
        if self.dose is not None:
            return self.dose
        if self.dose_mg is None or self.frequency_per_day is None:
            raise ValueError("Dose legada incompleta.")
        return MedicationDoseInput.legacy_mg(
            dose_mg=self.dose_mg,
            frequency_per_day=self.frequency_per_day,
            route=self.route,
            duration_days=self.duration_days,
        )

    @property
    def daily_total_mg(self) -> float | None:
        value = self.effective_dose.daily_mass_mg
        return float(value) if value is not None else None


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
