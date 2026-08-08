from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from statistics import median
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    ConceptSetMemberModel,
    ConceptSetVersionModel,
    PatientClinicalTimelineEventModel,
    PatientModel,
)
from app.services.canonical_json import canonical_sha256, json_compatible

MAX_CRITERIA = 30
MAX_NESTING = 2
MAX_QUERY_COST = 100
MAX_SOURCE_PATIENTS = 10_000
MAX_SOURCE_EVENTS = 50_000
ENGINE_VERSION = "prescripta-cohort-deterministic-v1"
ALLOWED_GROUPS = {"all", "exclude"}
ALLOWED_CRITERIA = {
    "age",
    "sex",
    "medication_exposure",
    "condition",
    "measurement_exists",
    "procedure",
    "date",
    "demographic",
}
ALLOWED_OPERATORS = {
    "age": {"eq", "gte", "lte", "between"},
    "sex": {"eq", "in"},
    "medication_exposure": {"exists"},
    "condition": {"exists"},
    "measurement_exists": {"exists"},
    "procedure": {"exists"},
    "date": {"before", "after", "between"},
    "demographic": {"eq", "in", "exists"},
}
CRITERION_KEYS = {
    "criterion",
    "operator",
    "value",
    "field",
    "concept_set_version_id",
    "window",
    "label",
}
DEMOGRAPHIC_FIELDS = {"age", "sex_for_dosing_calculation"}


class CohortDSLValidationError(ValueError):
    pass


class CohortDSLValidator:
    def __init__(self, db: Session, institution_id: str) -> None:
        self.db = db
        self.institution_id = institution_id

    def validate(self, definition: dict) -> tuple[dict, list[dict], int]:
        if not isinstance(definition, dict) or not definition:
            raise CohortDSLValidationError("A definição da coorte deve ser um objeto.")
        unknown_groups = set(definition) - ALLOWED_GROUPS
        if unknown_groups:
            raise CohortDSLValidationError(
                f"Grupos não permitidos: {', '.join(sorted(unknown_groups))}."
            )
        criteria: list[dict] = []
        cost = 0
        for group in ("all", "exclude"):
            items = definition.get(group, [])
            if not isinstance(items, list):
                raise CohortDSLValidationError(f"{group} deve ser uma lista.")
            for raw in items:
                normalized, item_cost = self._criterion(raw, group)
                criteria.append(normalized)
                cost += item_cost
        if not criteria:
            raise CohortDSLValidationError("A coorte exige ao menos um critério.")
        if len(criteria) > MAX_CRITERIA:
            raise CohortDSLValidationError(
                f"A coorte excede o limite de {MAX_CRITERIA} critérios."
            )
        if cost > MAX_QUERY_COST:
            raise CohortDSLValidationError("Custo estimado da coorte excede o limite.")
        normalized = {
            group: [
                {key: value for key, value in item.items() if key != "group"}
                for item in criteria
                if item["group"] == group
            ]
            for group in ("all", "exclude")
        }
        return json_compatible(normalized), criteria, cost

    def _criterion(self, raw: Any, group: str) -> tuple[dict, int]:
        if not isinstance(raw, dict):
            raise CohortDSLValidationError("Cada critério deve ser um objeto.")
        unknown = set(raw) - CRITERION_KEYS
        if unknown:
            raise CohortDSLValidationError(
                f"Campos não permitidos no critério: {', '.join(sorted(unknown))}."
            )
        criterion = str(raw.get("criterion") or "")
        if criterion not in ALLOWED_CRITERIA:
            raise CohortDSLValidationError(f"Critério não permitido: {criterion or 'vazio'}.")
        operator = str(raw.get("operator") or self._default_operator(criterion))
        if operator not in ALLOWED_OPERATORS[criterion]:
            raise CohortDSLValidationError(
                f"Operador {operator} não é permitido para {criterion}."
            )
        concept_version_id = raw.get("concept_set_version_id")
        concept_criteria = {
            "medication_exposure",
            "condition",
            "measurement_exists",
            "procedure",
        }
        if criterion in concept_criteria:
            if not isinstance(concept_version_id, str) or not concept_version_id:
                raise CohortDSLValidationError(
                    f"{criterion} exige concept_set_version_id explícito."
                )
            version = self.db.get(ConceptSetVersionModel, concept_version_id)
            if version is None or version.institution_id != self.institution_id:
                raise CohortDSLValidationError("Concept set/version fora do escopo institucional.")
            if version.status not in {"human_reviewed", "approved_for_demo_study"}:
                raise CohortDSLValidationError(
                    "Concept set/version ainda não possui revisão humana."
                )
        elif concept_version_id is not None:
            raise CohortDSLValidationError("Este critério não aceita concept_set_version_id.")
        field = raw.get("field")
        if criterion == "demographic" and field not in DEMOGRAPHIC_FIELDS:
            raise CohortDSLValidationError("Campo demográfico não permitido.")
        self._validate_value(criterion, operator, raw.get("value"))
        window = raw.get("window") or {}
        self._validate_window(window)
        normalized = {
            "group": group,
            "criterion": criterion,
            "operator": operator,
            "value": raw.get("value"),
            "field": field,
            "concept_set_version_id": concept_version_id,
            "window": window,
            "label": str(raw.get("label") or criterion)[:240],
        }
        return normalized, 1 + (3 if concept_version_id else 0) + (2 if window else 0)

    @staticmethod
    def _default_operator(criterion: str) -> str:
        return "exists" if criterion not in {"age", "sex", "date", "demographic"} else "eq"

    @staticmethod
    def _validate_value(criterion: str, operator: str, value: Any) -> None:
        if operator == "exists":
            if value not in (None, True):
                raise CohortDSLValidationError("Operador exists não aceita valor arbitrário.")
            return
        if operator == "between":
            if not isinstance(value, list) or len(value) != 2:
                raise CohortDSLValidationError("Operador between exige dois limites.")
        elif value is None:
            raise CohortDSLValidationError(f"{criterion} exige value.")
        if criterion == "age":
            values = value if isinstance(value, list) else [value]
            if any(not isinstance(item, int) or item < 0 or item > 130 for item in values):
                raise CohortDSLValidationError("Idade fora da faixa permitida.")
        if operator == "in" and (not isinstance(value, list) or not value or len(value) > 20):
            raise CohortDSLValidationError("Operador in exige lista não vazia de até 20 itens.")
        if criterion == "date":
            values = value if isinstance(value, list) else [value]
            try:
                for item in values:
                    datetime.fromisoformat(str(item).replace("Z", "+00:00"))
            except ValueError as exc:
                raise CohortDSLValidationError("Data impossível ou inválida.") from exc

    @staticmethod
    def _validate_window(window: Any) -> None:
        if not isinstance(window, dict):
            raise CohortDSLValidationError("Window deve ser um objeto.")
        unknown = set(window) - {"before_index_days", "after_index_days"}
        if unknown:
            raise CohortDSLValidationError("Window contém campo não permitido.")
        for value in window.values():
            if not isinstance(value, int) or value < 0 or value > 3650:
                raise CohortDSLValidationError("Window deve usar dias entre 0 e 3650.")


class DeterministicCohortEngine:
    def __init__(self, db: Session, institution_id: str) -> None:
        self.db = db
        self.institution_id = institution_id

    def execute(
        self,
        definition: dict,
        *,
        executed_at: datetime,
    ) -> tuple[int, list[dict], dict]:
        patients = list(
            self.db.scalars(
                select(PatientModel).where(PatientModel.institution_id == self.institution_id)
                .limit(MAX_SOURCE_PATIENTS + 1)
            )
        )
        events = list(
            self.db.scalars(
                select(PatientClinicalTimelineEventModel).where(
                    PatientClinicalTimelineEventModel.institution_id == self.institution_id
                )
                .limit(MAX_SOURCE_EVENTS + 1)
            )
        )
        if len(patients) > MAX_SOURCE_PATIENTS or len(events) > MAX_SOURCE_EVENTS:
            raise CohortDSLValidationError(
                "Dataset excede o orçamento do engine demonstrativo."
            )
        events_by_patient: dict[int, list[PatientClinicalTimelineEventModel]] = {}
        for event in events:
            events_by_patient.setdefault(event.patient_id, []).append(event)
        remaining = patients
        attrition: list[dict] = []
        sequence = 0
        for group in ("all", "exclude"):
            for criterion in definition.get(group, []):
                sequence += 1
                before = len(remaining)
                if group == "all":
                    remaining = [
                        patient
                        for patient in remaining
                        if self._matches(
                            patient,
                            events_by_patient.get(patient.id, []),
                            criterion,
                            executed_at,
                        )
                    ]
                else:
                    remaining = [
                        patient
                        for patient in remaining
                        if not self._matches(
                            patient,
                            events_by_patient.get(patient.id, []),
                            criterion,
                            executed_at,
                        )
                    ]
                after = len(remaining)
                attrition.append(
                    {
                        "sequence": sequence,
                        "criterion": criterion,
                        "label": criterion.get("label") or criterion["criterion"],
                        "before_count": before,
                        "excluded_count": before - after,
                        "after_count": after,
                        "criterion_hash": canonical_sha256(criterion),
                    }
                )
        return len(remaining), attrition, self._analytics(remaining)

    def _matches(
        self,
        patient: PatientModel,
        events: list[PatientClinicalTimelineEventModel],
        criterion: dict,
        anchor: datetime,
    ) -> bool:
        kind = criterion["criterion"]
        operator = criterion.get("operator", "exists")
        value = criterion.get("value")
        if kind == "age":
            return self._compare(patient.age, operator, value)
        if kind == "sex":
            return self._compare(patient.sex_for_dosing_calculation, operator, value)
        if kind == "demographic":
            return self._compare(getattr(patient, criterion["field"]), operator, value)
        if kind == "date":
            return any(
                self._compare_date(
                    event.event_date or event.created_at,
                    operator,
                    value,
                )
                for event in events
            )
        codes, labels = self._concept_members(criterion["concept_set_version_id"])
        event_types = {
            "medication_exposure": {"medication_start", "dose_change"},
            "condition": {"diagnosis", "adverse_event"},
            "measurement_exists": {"measurement"},
            "procedure": {"procedure"},
        }[kind]
        in_window = [
            event
            for event in events
            if event.event_type in event_types
            and self._in_window(
                event.event_date or event.created_at,
                criterion.get("window") or {},
                anchor,
            )
        ]
        if any(
            str(event.concept_code or "").casefold() in codes
            or str(event.concept_label or "").casefold() in labels
            for event in in_window
        ):
            return True
        fallback_values = (
            patient.current_medications if kind == "medication_exposure" else patient.comorbidities
        )
        return any(str(item).casefold() in codes | labels for item in fallback_values or [])

    def _concept_members(self, version_id: str) -> tuple[set[str], set[str]]:
        members = list(
            self.db.scalars(
                select(ConceptSetMemberModel).where(
                    ConceptSetMemberModel.concept_set_version_id == version_id
                )
            )
        )
        included = [item for item in members if not item.excluded]
        return (
            {item.concept_code.casefold() for item in included},
            {item.label.casefold() for item in included},
        )

    @staticmethod
    def _compare(actual: Any, operator: str, expected: Any) -> bool:
        if operator == "exists":
            return actual is not None
        if operator == "in":
            return str(actual).casefold() in {str(item).casefold() for item in expected}
        if operator == "eq":
            return str(actual).casefold() == str(expected).casefold()
        try:
            actual_number = Decimal(str(actual))
            if operator == "gte":
                return actual_number >= Decimal(str(expected))
            if operator == "lte":
                return actual_number <= Decimal(str(expected))
            if operator == "between":
                return Decimal(str(expected[0])) <= actual_number <= Decimal(str(expected[1]))
        except (InvalidOperation, TypeError, ValueError):
            return False
        return False

    @staticmethod
    def _compare_date(actual: datetime, operator: str, expected: Any) -> bool:
        values = expected if isinstance(expected, list) else [expected]
        parsed = [datetime.fromisoformat(str(item).replace("Z", "+00:00")) for item in values]
        parsed = [item.replace(tzinfo=UTC) if item.tzinfo is None else item for item in parsed]
        normalized = actual.replace(tzinfo=UTC) if actual.tzinfo is None else actual.astimezone(UTC)
        if operator == "before":
            return normalized < parsed[0]
        if operator == "after":
            return normalized > parsed[0]
        return parsed[0] <= normalized <= parsed[1]

    @staticmethod
    def _in_window(occurred_at: datetime, window: dict, anchor: datetime) -> bool:
        occurred = occurred_at.replace(tzinfo=UTC) if occurred_at.tzinfo is None else occurred_at
        lower = anchor - timedelta(days=int(window.get("before_index_days", 3650)))
        upper = anchor + timedelta(days=int(window.get("after_index_days", 0)))
        return lower <= occurred <= upper

    @staticmethod
    def _analytics(patients: list[PatientModel]) -> dict:
        ages = [patient.age for patient in patients if patient.age is not None]
        sexes = Counter(patient.sex_for_dosing_calculation or "missing" for patient in patients)
        conditions = Counter(
            str(item) for patient in patients for item in (patient.comorbidities or [])
        )
        medications = Counter(
            str(item) for patient in patients for item in (patient.current_medications or [])
        )
        return {
            "n": len(patients),
            "age": {
                "mean": str(sum(ages) / len(ages)) if ages else None,
                "median": str(median(ages)) if ages else None,
            },
            "sex_distribution_demo": dict(sexes),
            "condition_prevalence_demo": dict(conditions.most_common(10)),
            "frequent_medications_demo": dict(medications.most_common(10)),
            "missingness": {
                "age": sum(patient.age is None for patient in patients),
                "sex": sum(patient.sex_for_dosing_calculation is None for patient in patients),
                "height_cm": sum(patient.height_cm is None for patient in patients),
            },
        }
