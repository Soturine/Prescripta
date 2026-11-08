"""NEW-04: alternativas viam só os 50 primeiros cadastros (paginação padrão do repositório)."""

from __future__ import annotations

from app.database.models import MedicationModel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.repositories.medication_repository import MedicationRepository
from app.services.alternative_service import AlternativeService


def _record(brand: str, group: str) -> MedicationModel:
    return MedicationModel(
        brand_name=brand,
        active_ingredient=brand.lower(),
        therapeutic_class="classe sintética",
        alternative_group=group,
        max_daily_dose_mg=1000,
        allowed_routes=["oral"],
        contraindications=[],
    )


def test_alternatives_consider_the_whole_catalog(db_session) -> None:
    original = _record("Aaa Original", "grupo-alvo")
    db_session.add(original)
    db_session.add_all(_record(f"Filler {index:03d}", f"outro-{index}") for index in range(60))
    late_alternative = _record("Zzz Alternativa", "grupo-alvo")
    db_session.add(late_alternative)
    db_session.commit()

    patient = Patient(
        id=1,
        name="Paciente fictício",
        birth_date=None,
        age=40,
        weight_kg=70,
        height_cm=170,
        allergies=[],
        comorbidities=[],
        current_medications=[],
    )
    options = AlternativeService(MedicationRepository(db_session)).evaluated_options(
        patient,
        Medication.from_record(original),
        PrescriptionInput(dose_mg=10, frequency_per_day=1, route="oral"),
        should_include=True,
    )

    assert [option["medication_id"] for option in options] == [late_alternative.id]
