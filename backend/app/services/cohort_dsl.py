from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from statistics import median, pstdev
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
SMALL_CELL_THRESHOLD = 5
ENGINE_VERSION = "prescripta-cohort-deterministic-v2"
ALLOWED_CRITERIA = {
    "age",
    "sex",
    "drug_exposure",
    "medication_exposure",  # v1 compatibility
    "condition",
    "measurement",
    "measurement_exists",  # v1 compatibility
    "procedure",
    "visit",
    "medication_concurrency",
    "date_window",
    "date",  # v1 compatibility
    "demographic",
}
ALLOWED_OPERATORS = {
    "age": {"eq", "gte", "lte", "between"},
    "sex": {"eq", "in"},
    "drug_exposure": {"exists"},
    "medication_exposure": {"exists"},
    "condition": {"exists"},
    "measurement": {"exists"},
    "measurement_exists": {"exists"},
    "procedure": {"exists"},
    "visit": {"exists"},
    "medication_concurrency": {"exists"},
    "date_window": {"before", "after", "between"},
    "date": {"before", "after", "between"},
    "demographic": {"eq", "in", "exists"},
}
CRITERION_KEYS = {
    "id",
    "criterion",
    "operator",
    "value",
    "field",
    "concept_set_version_id",
    "window",
    "temporal_relationship",
    "label",
}
GROUP_KEYS = {"id", "operator", "items", "label"}
DEMOGRAPHIC_FIELDS = {"age", "sex_for_dosing_calculation"}


class CohortDSLValidationError(ValueError):
    pass


class CohortDSLValidator:
    """Validates a bounded, declarative DSL. It never accepts SQL or free-form expressions."""

    def __init__(self, db: Session, institution_id: str) -> None:
        self.db = db
        self.institution_id = institution_id
        self._sequence = 0

    def validate(self, definition: dict) -> tuple[dict, list[dict], int]:
        if not isinstance(definition, dict) or not definition:
            raise CohortDSLValidationError("A definição da coorte deve ser um objeto.")
        version = str(definition.get("schema_version", "1"))
        if version not in {"1", "2"}:
            raise CohortDSLValidationError("Versão da DSL não suportada.")
        if version == "1":
            unknown = set(definition) - {"all", "exclude"}
            if unknown:
                raise CohortDSLValidationError(
                    f"Grupos não permitidos: {', '.join(sorted(unknown))}."
                )
            definition = {
                "schema_version": "2",
                "inclusion": {
                    "id": "inclusion",
                    "operator": "all",
                    "items": definition.get("all", []),
                    "label": "Critérios de inclusão",
                },
                "exclusion": {
                    "id": "exclusion",
                    "operator": "any",
                    "items": definition.get("exclude", []),
                    "label": "Critérios de exclusão",
                },
            }
        elif set(definition) - {"schema_version", "inclusion", "exclusion"}:
            raise CohortDSLValidationError("A DSL v2 contém campos de topo não permitidos.")

        flat: list[dict] = []
        inclusion, cost = self._group(definition.get("inclusion"), "inclusion", 1, flat)
        exclusion, exclusion_cost = self._group(
            definition.get("exclusion", {"operator": "any", "items": []}),
            "exclusion",
            1,
            flat,
            allow_empty=True,
        )
        cost += exclusion_cost
        if not flat:
            raise CohortDSLValidationError("A coorte exige ao menos um critério.")
        if len(flat) > MAX_CRITERIA:
            raise CohortDSLValidationError(f"A coorte excede o limite de {MAX_CRITERIA} critérios.")
        if cost > MAX_QUERY_COST:
            raise CohortDSLValidationError("Custo estimado da coorte excede o limite.")
        normalized = {
            "schema_version": "2",
            "inclusion": inclusion,
            "exclusion": exclusion,
        }
        return json_compatible(normalized), flat, cost

    def _group(
        self,
        raw: Any,
        phase: str,
        depth: int,
        flat: list[dict],
        *,
        allow_empty: bool = False,
    ) -> tuple[dict, int]:
        if depth > MAX_NESTING:
            raise CohortDSLValidationError(f"Nesting excede o limite de {MAX_NESTING} níveis.")
        if not isinstance(raw, dict) or set(raw) - GROUP_KEYS:
            raise CohortDSLValidationError("Grupo de coorte inválido.")
        operator = str(raw.get("operator", "all"))
        if operator not in {"all", "any"}:
            raise CohortDSLValidationError("Grupo aceita somente os operadores all ou any.")
        items = raw.get("items", [])
        if not isinstance(items, list) or (not items and not allow_empty):
            raise CohortDSLValidationError("Grupo deve conter uma lista não vazia.")
        normalized_items: list[dict] = []
        cost = 1
        for raw_item in items:
            if isinstance(raw_item, dict) and "items" in raw_item:
                nested, nested_cost = self._group(raw_item, phase, depth + 1, flat)
                normalized_items.append(nested)
                cost += nested_cost
            else:
                criterion, item_cost = self._criterion(raw_item, phase)
                normalized_items.append(
                    {key: value for key, value in criterion.items() if key != "group"}
                )
                flat.append(criterion)
                cost += item_cost
        return {
            "id": str(raw.get("id") or f"{phase}-{depth}")[:80],
            "operator": operator,
            "items": normalized_items,
            "label": str(raw.get("label") or phase)[:240],
        }, cost

    def _criterion(self, raw: Any, phase: str) -> tuple[dict, int]:
        if not isinstance(raw, dict):
            raise CohortDSLValidationError("Cada critério deve ser um objeto.")
        unknown = set(raw) - CRITERION_KEYS
        if unknown:
            raise CohortDSLValidationError(
                f"Campos não permitidos no critério: {', '.join(sorted(unknown))}."
            )
        kind = str(raw.get("criterion") or "")
        if kind not in ALLOWED_CRITERIA:
            raise CohortDSLValidationError(f"Critério não permitido: {kind or 'vazio'}.")
        operator = str(raw.get("operator") or self._default_operator(kind))
        if operator not in ALLOWED_OPERATORS[kind]:
            raise CohortDSLValidationError(f"Operador {operator} não é permitido para {kind}.")
        concept_version_id = raw.get("concept_set_version_id")
        concept_kinds = {
            "drug_exposure",
            "medication_exposure",
            "condition",
            "measurement",
            "measurement_exists",
            "procedure",
            "medication_concurrency",
        }
        if kind in concept_kinds:
            if not isinstance(concept_version_id, str) or not concept_version_id:
                raise CohortDSLValidationError(f"{kind} exige concept_set_version_id explícito.")
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
        if kind == "demographic" and field not in DEMOGRAPHIC_FIELDS:
            raise CohortDSLValidationError("Campo demográfico não permitido.")
        self._validate_value(kind, operator, raw.get("value"))
        window = raw.get("window") or {}
        self._validate_window(window)
        temporal = raw.get("temporal_relationship")
        if temporal not in {None, "before_index", "after_index", "on_index", "during_window"}:
            raise CohortDSLValidationError("Relação temporal não permitida.")
        self._sequence += 1
        normalized = {
            "id": str(raw.get("id") or f"criterion-{self._sequence}")[:80],
            "group": phase,
            "criterion": kind,
            "operator": operator,
            "value": raw.get("value"),
            "field": field,
            "concept_set_version_id": concept_version_id,
            "window": window,
            "temporal_relationship": temporal,
            "label": str(raw.get("label") or kind)[:240],
        }
        return normalized, 1 + (3 if concept_version_id else 0) + (2 if window else 0)

    @staticmethod
    def _default_operator(kind: str) -> str:
        return (
            "exists" if kind not in {"age", "sex", "date", "date_window", "demographic"} else "eq"
        )

    @staticmethod
    def _validate_value(kind: str, operator: str, value: Any) -> None:
        if operator == "exists":
            if value not in (None, True):
                raise CohortDSLValidationError("Operador exists não aceita valor arbitrário.")
            return
        if operator == "between":
            if not isinstance(value, list) or len(value) != 2:
                raise CohortDSLValidationError("Operador between exige dois limites.")
        elif value is None:
            raise CohortDSLValidationError(f"{kind} exige value.")
        if kind == "age":
            values = value if isinstance(value, list) else [value]
            if any(not isinstance(item, int) or item < 0 or item > 130 for item in values):
                raise CohortDSLValidationError("Idade fora da faixa permitida.")
        if operator == "in" and (not isinstance(value, list) or not value or len(value) > 20):
            raise CohortDSLValidationError("Operador in exige lista não vazia de até 20 itens.")
        if kind in {"date", "date_window"}:
            try:
                for item in value if isinstance(value, list) else [value]:
                    datetime.fromisoformat(str(item).replace("Z", "+00:00"))
            except ValueError as exc:
                raise CohortDSLValidationError("Data impossível ou inválida.") from exc

    @staticmethod
    def _validate_window(window: Any) -> None:
        if not isinstance(window, dict) or set(window) - {"before_index_days", "after_index_days"}:
            raise CohortDSLValidationError("Window inválida.")
        if any(
            not isinstance(value, int) or value < 0 or value > 3650 for value in window.values()
        ):
            raise CohortDSLValidationError("Window deve usar dias entre 0 e 3650.")


class DeterministicCohortEngine:
    def __init__(self, db: Session, institution_id: str) -> None:
        self.db = db
        self.institution_id = institution_id

    def execute(self, definition: dict, *, executed_at: datetime) -> tuple[int, list[dict], dict]:
        patients = list(
            self.db.scalars(
                select(PatientModel)
                .where(PatientModel.institution_id == self.institution_id)
                .limit(MAX_SOURCE_PATIENTS + 1)
            )
        )
        events = list(
            self.db.scalars(
                select(PatientClinicalTimelineEventModel)
                .where(PatientClinicalTimelineEventModel.institution_id == self.institution_id)
                .limit(MAX_SOURCE_EVENTS + 1)
            )
        )
        if len(patients) > MAX_SOURCE_PATIENTS or len(events) > MAX_SOURCE_EVENTS:
            raise CohortDSLValidationError("Dataset excede o orçamento do engine demonstrativo.")
        by_patient: dict[int, list[PatientClinicalTimelineEventModel]] = {}
        for event in events:
            by_patient.setdefault(event.patient_id, []).append(event)
        if "schema_version" not in definition:  # immutable v1 rows remain executable
            definition = CohortDSLValidator(self.db, self.institution_id).validate(definition)[0]
        remaining = patients
        attrition: list[dict] = []
        for phase in ("inclusion", "exclusion"):
            root = definition[phase]
            for item in root.get("items", []):
                before = len(remaining)
                if phase == "inclusion":
                    remaining = [
                        p
                        for p in remaining
                        if self._matches_node(p, by_patient.get(p.id, []), item, executed_at)
                    ]
                else:
                    remaining = [
                        p
                        for p in remaining
                        if not self._matches_node(p, by_patient.get(p.id, []), item, executed_at)
                    ]
                attrition.append(
                    {
                        "sequence": len(attrition) + 1,
                        "phase": phase,
                        "criterion": item,
                        "label": item.get("label") or item.get("criterion") or phase,
                        "before_count": before,
                        "excluded_count": before - len(remaining),
                        "after_count": len(remaining),
                        "criterion_hash": canonical_sha256(item),
                    }
                )
        selected_events = [
            event for patient in remaining for event in by_patient.get(patient.id, [])
        ]
        return len(remaining), attrition, self._analytics(remaining, selected_events)

    def _matches_node(
        self, patient: PatientModel, events: list, node: dict, anchor: datetime
    ) -> bool:
        if "items" in node:
            matches = [self._matches_node(patient, events, item, anchor) for item in node["items"]]
            return all(matches) if node.get("operator") == "all" else any(matches)
        return self._matches(patient, events, node, anchor)

    def _matches(
        self, patient: PatientModel, events: list, criterion: dict, anchor: datetime
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
        if kind in {"date", "date_window"}:
            return any(
                self._compare_date(event.event_date or event.created_at, operator, value)
                for event in events
            )
        if kind == "visit":
            return any(event.event_type in {"encounter", "hospitalization"} for event in events)
        codes, labels = self._concept_members(criterion["concept_set_version_id"])
        event_types = {
            "drug_exposure": {"medication_start", "dose_change"},
            "medication_exposure": {"medication_start", "dose_change"},
            "condition": {"diagnosis", "adverse_event"},
            "measurement": {"measurement"},
            "measurement_exists": {"measurement"},
            "procedure": {"procedure"},
            "medication_concurrency": {"medication_start", "dose_change"},
        }[kind]
        matching = [
            event
            for event in events
            if event.event_type in event_types
            and self._in_window(
                event.event_date or event.created_at, criterion.get("window") or {}, anchor
            )
            and (
                str(event.concept_code or "").casefold() in codes
                or str(event.concept_label or "").casefold() in labels
            )
        ]
        if matching:
            return len(matching) >= (2 if kind == "medication_concurrency" else 1)
        fallback = (
            patient.current_medications
            if kind in {"drug_exposure", "medication_exposure", "medication_concurrency"}
            else patient.comorbidities
        )
        count = sum(str(item).casefold() in codes | labels for item in fallback or [])
        return count >= (2 if kind == "medication_concurrency" else 1)

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
    def _numeric(values: list[int | float], missing: int) -> dict:
        ordered = sorted(float(value) for value in values)
        if not ordered:
            return {
                "n": 0,
                "missing": missing,
                "mean": None,
                "sd": None,
                "median": None,
                "q1": None,
                "q3": None,
                "iqr": None,
                "min": None,
                "max": None,
            }

        def percentile(position: float) -> float:
            index = (len(ordered) - 1) * position
            low, high = int(index), min(int(index) + 1, len(ordered) - 1)
            return ordered[low] + (ordered[high] - ordered[low]) * (index - low)

        q1, q3 = percentile(0.25), percentile(0.75)

        def clean(value: float) -> str:
            return format(value, ".6g")

        return {
            "n": len(ordered),
            "missing": missing,
            "mean": clean(sum(ordered) / len(ordered)),
            "sd": clean(pstdev(ordered)),
            "median": clean(float(median(ordered))),
            "q1": clean(q1),
            "q3": clean(q3),
            "iqr": clean(q3 - q1),
            "min": clean(ordered[0]),
            "max": clean(ordered[-1]),
        }

    @staticmethod
    def _categorical(values: list[str], total: int, missing: int = 0) -> dict:
        rows = []
        for value, count in sorted(Counter(values).items()):
            rows.append(
                {
                    "value": value,
                    "n": count if count >= SMALL_CELL_THRESHOLD else None,
                    "percent": format(100 * count / total, ".4g")
                    if total and count >= SMALL_CELL_THRESHOLD
                    else None,
                    "suppressed": count < SMALL_CELL_THRESHOLD,
                }
            )
        return {
            "n": total - missing,
            "missing": missing,
            "categories": rows,
            "small_cell_threshold": SMALL_CELL_THRESHOLD,
        }

    @classmethod
    def _analytics(
        cls, patients: list[PatientModel], events: list[PatientClinicalTimelineEventModel]
    ) -> dict:
        total = len(patients)
        ages = [patient.age for patient in patients if patient.age is not None]
        sex_values = [
            patient.sex_for_dosing_calculation
            for patient in patients
            if patient.sex_for_dosing_calculation
        ]
        conditions = Counter(
            str(item) for patient in patients for item in (patient.comorbidities or [])
        )
        medications = Counter(
            str(item) for patient in patients for item in (patient.current_medications or [])
        )
        prevalence = [
            {
                "label": label,
                "numerator": count if count >= SMALL_CELL_THRESHOLD else None,
                "denominator": total,
                "percent": format(100 * count / total, ".4g")
                if total and count >= SMALL_CELL_THRESHOLD
                else None,
                "window": "data_snapshot",
                "suppressed": count < SMALL_CELL_THRESHOLD,
            }
            for label, count in conditions.most_common(10)
        ]
        event_counts = Counter(event.event_type for event in events)
        return {
            "n": total,
            "numeric": {"age_years": cls._numeric(ages, total - len(ages))},
            "categorical": {"sex": cls._categorical(sex_values, total, total - len(sex_values))},
            "prevalence": prevalence,
            "incidence": {
                "status": "deferred",
                "reason": "person-time denominator is not validated",
            },
            "utilization": {
                "events_by_type": dict(sorted(event_counts.items())),
                "total_events": len(events),
            },
            "frequent_medications": [
                {
                    "label": label,
                    "n": count if count >= SMALL_CELL_THRESHOLD else None,
                    "suppressed": count < SMALL_CELL_THRESHOLD,
                }
                for label, count in medications.most_common(10)
            ],
            "missingness": {
                "age": total - len(ages),
                "sex": total - len(sex_values),
                "height_cm": sum(patient.height_cm is None for patient in patients),
            },
            "table_1": [
                {"variable": "Age, years", **cls._numeric(ages, total - len(ages))},
                {"variable": "Sex", **cls._categorical(sex_values, total, total - len(sex_values))},
            ],
            "aggregate_only": True,
            "small_cell_policy": {"threshold": SMALL_CELL_THRESHOLD, "suppressed_value": None},
        }
