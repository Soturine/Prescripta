from __future__ import annotations

from dataclasses import dataclass

from app.domain.medication import Medication
from app.domain.prescription import PrescriptionInput


@dataclass(frozen=True)
class MedicationExposurePlan:
    patient_id: int | None
    medication_id: int | None
    active_ingredient_id: int | None
    dose_per_administration_mg: float
    administrations_per_day: int
    duration_days: int | None
    calculated_daily_dose_mg: float
    calculated_cumulative_dose_mg: float | None
    max_daily_dose_mg: float | None
    max_cumulative_dose_mg: float | None
    max_duration_days: int | None
    continuous_use: bool
    monitoring_required: bool
    monitoring_notes: str | None

    @property
    def has_missing_data(self) -> bool:
        return self.duration_days is None and bool(
            self.max_duration_days or self.max_cumulative_dose_mg
        )


class MedicationExposureService:
    def build_plan(
        self,
        *,
        patient_id: int | None,
        medication: Medication,
        prescription: PrescriptionInput,
    ) -> MedicationExposurePlan:
        cumulative = (
            prescription.daily_total_mg * prescription.duration_days
            if prescription.duration_days is not None
            else None
        )
        return MedicationExposurePlan(
            patient_id=patient_id,
            medication_id=medication.id,
            active_ingredient_id=medication.active_ingredient_id,
            dose_per_administration_mg=prescription.dose_mg,
            administrations_per_day=prescription.frequency_per_day,
            duration_days=prescription.duration_days,
            calculated_daily_dose_mg=prescription.daily_total_mg,
            calculated_cumulative_dose_mg=cumulative,
            max_daily_dose_mg=medication.max_daily_dose_mg,
            max_cumulative_dose_mg=medication.max_cumulative_dose_mg,
            max_duration_days=medication.max_duration_days,
            continuous_use=medication.continuous_use,
            monitoring_required=medication.monitoring_required,
            monitoring_notes=medication.monitoring_notes,
        )

