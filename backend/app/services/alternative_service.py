from __future__ import annotations

from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.repositories.medication_repository import MedicationRepository
from app.services.normalizer import normalize_text
from app.services.risk_engine import RiskEngine


class AlternativeService:
    def __init__(self, repository: MedicationRepository) -> None:
        self.repository = repository

    def evaluated_options(
        self,
        patient: Patient,
        medication: Medication,
        prescription: PrescriptionInput,
        *,
        should_include: bool,
    ) -> list[dict]:
        if not should_include:
            return []
        candidates = self._candidates(medication)
        options: list[dict] = []
        for record in candidates[:4]:
            candidate = Medication.from_record(record)
            result = RiskEngine().evaluate(patient, candidate, prescription)
            options.append(
                {
                    "medication_id": candidate.id,
                    "name": candidate.brand_name,
                    "active_ingredient": candidate.active_ingredient,
                    "therapeutic_class": candidate.therapeutic_class,
                    "similarity_reason": self._similarity_reason(medication, candidate),
                    "status": result.status.value,
                    "risk_level": result.risk_level.value,
                    "top_alerts": [alert.to_dict() for alert in result.alerts[:3]],
                    "observation": (
                        "Alternativa para avaliação profissional; não é recomendação automática."
                    ),
                }
            )
        return options

    def _candidates(self, medication: Medication) -> list:
        current_id = medication.id
        group = normalize_text(medication.alternative_group or medication.therapeutic_class)
        action = normalize_text(medication.therapeutic_action or "")
        candidates = []
        for record in self.repository.list():
            if record.id == current_id:
                continue
            record_group = normalize_text(record.alternative_group or record.therapeutic_class)
            same_group = group and record_group == group
            same_action = action and normalize_text(record.therapeutic_action or "") == action
            related = normalize_text(record.active_ingredient) in {
                normalize_text(item) for item in (medication.related_medications or [])
            }
            if same_group or same_action or related:
                candidates.append(record)
        return candidates

    def _similarity_reason(self, original: Medication, candidate: Medication) -> str:
        if normalize_text(original.alternative_group or "") == normalize_text(
            candidate.alternative_group or ""
        ):
            return "Mesmo grupo alternativo demonstrativo."
        if normalize_text(original.therapeutic_action or "") == normalize_text(
            candidate.therapeutic_action or ""
        ):
            return "Ação/finalidade terapêutica semelhante."
        return "Relacionamento demonstrativo cadastrado."
