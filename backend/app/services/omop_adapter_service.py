from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    CohortRunModel,
    OmopEtlRunModel,
    PatientClinicalTimelineEventModel,
    PatientModel,
    ResearchSnapshotModel,
    ResearchStudyModel,
    TerminologyConceptModel,
    TerminologyMappingModel,
    TerminologyReleaseModel,
    UserModel,
)
from app.schemas.omop_schema import OmopPreviewRequest
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256

CDM_VERSION = "5.4"
ADAPTER_VERSION = "prescripta-omop-cdm54-partial-v1"
SOURCE_SCHEMA_VERSION = "prescripta-canonical-timeline-v1"
MAX_SOURCE_EVENTS = 50_000

TABLE_COLUMNS = {
    "PERSON": [
        "person_id", "gender_concept_id", "year_of_birth", "month_of_birth",
        "day_of_birth", "birth_datetime", "race_concept_id", "ethnicity_concept_id",
        "location_id", "provider_id", "care_site_id", "person_source_value",
        "gender_source_value", "gender_source_concept_id", "race_source_value",
        "race_source_concept_id", "ethnicity_source_value", "ethnicity_source_concept_id",
    ],
    "VISIT_OCCURRENCE": [
        "visit_occurrence_id", "person_id", "visit_concept_id", "visit_start_date",
        "visit_start_datetime", "visit_end_date", "visit_end_datetime",
        "visit_type_concept_id", "provider_id", "care_site_id", "visit_source_value",
        "visit_source_concept_id", "admitted_from_concept_id", "admitted_from_source_value",
        "discharged_to_concept_id", "discharged_to_source_value", "preceding_visit_occurrence_id",
    ],
    "CONDITION_OCCURRENCE": [
        "condition_occurrence_id", "person_id", "condition_concept_id",
        "condition_start_date", "condition_start_datetime", "condition_end_date",
        "condition_end_datetime", "condition_type_concept_id", "condition_status_concept_id",
        "stop_reason", "provider_id", "visit_occurrence_id", "visit_detail_id",
        "condition_source_value", "condition_source_concept_id", "condition_status_source_value",
    ],
    "DRUG_EXPOSURE": [
        "drug_exposure_id", "person_id", "drug_concept_id", "drug_exposure_start_date",
        "drug_exposure_start_datetime", "drug_exposure_end_date", "drug_exposure_end_datetime",
        "verbatim_end_date", "drug_type_concept_id", "stop_reason", "refills", "quantity",
        "days_supply", "sig", "route_concept_id", "lot_number", "provider_id",
        "visit_occurrence_id", "visit_detail_id", "drug_source_value", "drug_source_concept_id",
        "route_source_value", "dose_unit_source_value",
    ],
    "MEASUREMENT": [
        "measurement_id", "person_id", "measurement_concept_id", "measurement_date",
        "measurement_datetime", "measurement_time", "measurement_type_concept_id",
        "operator_concept_id", "value_as_number", "value_as_concept_id", "unit_concept_id",
        "range_low", "range_high", "provider_id", "visit_occurrence_id", "visit_detail_id",
        "measurement_source_value", "measurement_source_concept_id", "unit_source_value",
        "value_source_value", "measurement_event_id", "meas_event_field_concept_id",
    ],
    "PROCEDURE_OCCURRENCE": [
        "procedure_occurrence_id", "person_id", "procedure_concept_id", "procedure_date",
        "procedure_datetime", "procedure_end_date", "procedure_end_datetime",
        "procedure_type_concept_id", "modifier_concept_id", "quantity", "provider_id",
        "visit_occurrence_id", "visit_detail_id", "procedure_source_value",
        "procedure_source_concept_id", "modifier_source_value",
    ],
    "OBSERVATION": [
        "observation_id", "person_id", "observation_concept_id", "observation_date",
        "observation_datetime", "observation_type_concept_id", "value_as_number",
        "value_as_string", "value_as_concept_id", "qualifier_concept_id", "unit_concept_id",
        "provider_id", "visit_occurrence_id", "visit_detail_id", "observation_source_value",
        "observation_source_concept_id", "unit_source_value", "qualifier_source_value",
        "value_source_value", "observation_event_id", "obs_event_field_concept_id",
    ],
}

EVENT_TABLE = {
    "diagnosis": ("CONDITION_OCCURRENCE", "Condition"),
    "medication_start": ("DRUG_EXPOSURE", "Drug"),
    "medication_stop": ("DRUG_EXPOSURE", "Drug"),
    "dose_change": ("DRUG_EXPOSURE", "Drug"),
    "measurement": ("MEASUREMENT", "Measurement"),
    "procedure": ("PROCEDURE_OCCURRENCE", "Procedure"),
    "observation": ("OBSERVATION", "Observation"),
}


class OmopAdapterError(ValueError):
    pass


class OmopAdapterService:
    """Deterministic synthetic-only OMOP CDM 5.4 partial adapter."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(
        self, payload: OmopPreviewRequest, actor: UserModel, *, persist_export: bool
    ) -> OmopEtlRunModel:
        started = datetime.now(UTC)
        study = self._study(payload.study_id, actor)
        cohort = self._cohort(payload.cohort_run_id, study, actor)
        snapshot = self.db.scalar(
            select(ResearchSnapshotModel).where(
                ResearchSnapshotModel.cohort_run_id == cohort.id
            )
        )
        if snapshot is None:
            raise OmopAdapterError("Snapshot da coorte não encontrado.")
        release_ids = sorted(set(payload.terminology_release_ids))
        for release_id in release_ids:
            release = self.db.get(TerminologyReleaseModel, release_id)
            if release is None or release.institution_id != actor.institution_id:
                raise OmopAdapterError("Terminology release cross-tenant ou inexistente.")
            if release.requires_license and release.license_status != "authorized":
                raise OmopAdapterError("License required para terminology release selecionada.")
        patients = list(
            self.db.scalars(
                select(PatientModel)
                .where(PatientModel.institution_id == actor.institution_id)
                .order_by(PatientModel.id)
            )
        )
        events = list(
            self.db.scalars(
                select(PatientClinicalTimelineEventModel)
                .where(
                    PatientClinicalTimelineEventModel.institution_id
                    == actor.institution_id
                )
                .order_by(
                    PatientClinicalTimelineEventModel.patient_id,
                    PatientClinicalTimelineEventModel.event_date,
                    PatientClinicalTimelineEventModel.id,
                )
                .limit(MAX_SOURCE_EVENTS + 1)
            )
        )
        if len(events) > MAX_SOURCE_EVENTS:
            raise OmopAdapterError("Dataset excede limite synthetic/demo do adapter.")
        if any(
            item.source_type != "synthetic_fixture"
            or not (item.provenance or {}).get("demo_only")
            for item in events
        ):
            raise OmopAdapterError("OMOP export bloqueado: source não é synthetic-only.")
        tables, metrics, mapping_hashes, warnings = self._transform(
            patients, events, release_ids, snapshot.snapshot_hash
        )
        files = {
            f"{table.lower()}.csv": self._csv(TABLE_COLUMNS[table], rows)
            for table, rows in tables.items()
        }
        compatibility = self.compatibility()
        file_hashes = {name: canonical_sha256(content) for name, content in files.items()}
        manifest = {
            "schema_version": "prescripta-omop-export-v1",
            "description": "OMOP CDM 5.4 partial export",
            "claim_level": "omop_v5_4_partial_adapter",
            "cdm_version": CDM_VERSION,
            "adapter_version": ADAPTER_VERSION,
            "source_snapshot_marker": cohort.data_snapshot_marker,
            "source_snapshot_hash": snapshot.snapshot_hash,
            "synthetic_only": True,
            "terminology_release_ids": release_ids,
            "mapping_hashes": sorted(mapping_hashes),
            "files": file_hashes,
            "compatibility_hash": compatibility["content_hash"],
        }
        export_hash = canonical_sha256({"manifest": manifest, "files": files})
        run = OmopEtlRunModel(
            institution_id=actor.institution_id,
            study_id=study.id,
            cohort_run_id=cohort.id,
            source_classification=study.data_source_classification,
            synthetic_only=True,
            source_snapshot_marker=cohort.data_snapshot_marker,
            source_snapshot_hash=snapshot.snapshot_hash,
            source_schema_version=SOURCE_SCHEMA_VERSION,
            adapter_version=ADAPTER_VERSION,
            cdm_version=CDM_VERSION,
            terminology_release_ids=release_ids,
            mapping_hashes=sorted(mapping_hashes),
            status="exported_partial" if persist_export else "preview_partial",
            metrics=metrics,
            warnings=warnings,
            errors=[],
            manifest=manifest,
            export_files=files if persist_export else {},
            export_hash=export_hash,
            executed_by_user_id=actor.id,
            started_at=started,
            completed_at=datetime.now(UTC),
        )
        self.db.add(run)
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="omop.etl.export" if persist_export else "omop.validation.preview",
            resource_type="omop_etl_run",
            resource_id=run.id,
            status=run.status,
            details={
                "cdm_version": CDM_VERSION,
                "claim_level": "omop_v5_4_partial_adapter",
                "export_hash": export_hash,
                "synthetic_only": True,
            },
        )
        return run

    def list_runs(self, actor: UserModel) -> list[OmopEtlRunModel]:
        return list(
            self.db.scalars(
                select(OmopEtlRunModel)
                .where(OmopEtlRunModel.institution_id == actor.institution_id)
                .order_by(OmopEtlRunModel.started_at.desc(), OmopEtlRunModel.id)
            )
        )

    def run(self, run_id: str, actor: UserModel) -> OmopEtlRunModel:
        run = self.db.get(OmopEtlRunModel, run_id)
        if run is None or run.institution_id != actor.institution_id:
            raise OmopAdapterError("ETL run não encontrado.")
        return run

    @staticmethod
    def compatibility() -> dict:
        targets = [
            {
                "target": "OMOP CDM 5.4 schema semantics",
                "level": "partial",
                "proven": "seven domain CSV contracts and deterministic validation",
                "missing": "support tables and official DDL load validation",
                "claim_allowed": "omop_v5_4_partial_adapter",
            },
            {
                "target": "OMOP Vocabulary conventions",
                "level": "partial",
                "proven": "source values, concept 0, reviewed active domain-correct mappings",
                "missing": "complete Standardized Vocabulary tables",
                "claim_allowed": "partial",
            },
            {
                "target": "ATHENA vocabulary bundle loading",
                "level": "partial",
                "proven": "controlled metadata and concepts CSV import",
                "missing": "full ATHENA table-set loader",
                "claim_allowed": "operator-provided subset only",
            },
            {
                "target": "DataQualityDashboard",
                "level": "not_tested",
                "proven": "none",
                "missing": "operational CDM and real DQD execution",
                "claim_allowed": "not validated",
            },
            {
                "target": "Achilles / ATLAS",
                "level": "not_supported",
                "proven": "none",
                "missing": "support/vocabulary tables and tool execution",
                "claim_allowed": "not compatible in v0.9.1",
            },
            {
                "target": "OHDSI network study readiness",
                "level": "not_supported",
                "proven": "none",
                "missing": "full CDM, DQD, governance and external validation",
                "claim_allowed": "not network-ready",
            },
        ]
        basis = {
            "cdm_version": CDM_VERSION,
            "claim_level": "omop_v5_4_partial_adapter",
            "targets": targets,
            "synthetic_only": True,
            "ohdsi_tool_validated": False,
        }
        return {**basis, "content_hash": canonical_sha256(basis)}

    def _transform(
        self,
        patients: list[PatientModel],
        events: list[PatientClinicalTimelineEventModel],
        release_ids: list[str],
        snapshot_hash: str,
    ) -> tuple[dict[str, list[dict]], dict, set[str], list[str]]:
        tables: dict[str, list[dict]] = {name: [] for name in TABLE_COLUMNS}
        mapping_hashes: set[str] = set()
        warnings: list[str] = []
        person_ids = {item.id: index for index, item in enumerate(patients, start=1)}
        patient_by_id = {item.id: item for item in patients}
        for patient in patients:
            birth = patient.birth_date
            tables["PERSON"].append(
                self._row(
                    "PERSON",
                    person_id=person_ids[patient.id],
                    gender_concept_id=0,
                    year_of_birth=birth.year if birth else None,
                    month_of_birth=birth.month if birth else None,
                    day_of_birth=birth.day if birth else None,
                    birth_datetime=None,
                    race_concept_id=0,
                    ethnicity_concept_id=0,
                    location_id=None,
                    provider_id=None,
                    care_site_id=None,
                    person_source_value=(
                        "SYN-"
                        + canonical_sha256(
                            {"snapshot": snapshot_hash, "patient": patient.id}
                        )[:16]
                    ),
                    gender_source_value=patient.sex_for_dosing_calculation,
                    gender_source_concept_id=0,
                    race_source_value=None,
                    race_source_concept_id=0,
                    ethnicity_source_value=None,
                    ethnicity_source_concept_id=0,
                )
            )
        visit_events = [
            item
            for item in events
            if item.event_type in {"encounter", "hospitalization"}
        ]
        visit_ids = {item.id: index for index, item in enumerate(visit_events, start=1)}
        visit_by_person_date: dict[tuple[int, date], int] = {}
        for event in visit_events:
            occurred = self._occurred(event)
            payload = event.payload or {}
            end = self._parse_datetime(payload.get("end")) or occurred
            resolved = self._resolve_concept(event, "Visit", release_ids)
            mapping_hashes.update(resolved["mapping_hashes"])
            visit_by_person_date[(event.patient_id, occurred.date())] = visit_ids[event.id]
            tables["VISIT_OCCURRENCE"].append(
                self._row(
                    "VISIT_OCCURRENCE",
                    visit_occurrence_id=visit_ids[event.id],
                    person_id=person_ids.get(event.patient_id),
                    visit_concept_id=resolved["standard_concept_id"],
                    visit_start_date=occurred.date(),
                    visit_start_datetime=occurred,
                    visit_end_date=end.date(),
                    visit_end_datetime=end,
                    visit_type_concept_id=0,
                    visit_source_value=event.concept_code or event.event_type,
                    visit_source_concept_id=resolved["source_concept_id"],
                )
            )
        counters: dict[str, int] = defaultdict(int)
        rejected: dict[str, int] = defaultdict(int)
        unmapped: dict[str, int] = defaultdict(int)
        mapped: dict[str, int] = defaultdict(int)
        source_rows: dict[str, int] = defaultdict(int)
        for event in events:
            target = EVENT_TABLE.get(event.event_type)
            if target is None:
                continue
            table, domain = target
            source_rows[table] += 1
            if event.patient_id not in patient_by_id:
                rejected[table] += 1
                continue
            occurred = self._occurred(event)
            resolved = self._resolve_concept(event, domain, release_ids)
            mapping_hashes.update(resolved["mapping_hashes"])
            if resolved["standard_concept_id"]:
                mapped[table] += 1
            else:
                unmapped[table] += 1
                warnings.append(
                    f"{table}:{event.id}:{resolved['unmapped_reason']}"
                )
            counters[table] += 1
            row_id = counters[table]
            visit_id = visit_by_person_date.get((event.patient_id, occurred.date()))
            row = self._event_row(
                table,
                row_id,
                event,
                occurred,
                visit_id,
                resolved,
                person_ids[event.patient_id],
            )
            if row is None:
                rejected[table] += 1
            else:
                tables[table].append(row)
        metrics = {}
        for table in TABLE_COLUMNS:
            total = len(patients) if table == "PERSON" else source_rows[table]
            metrics[table] = {
                "total_source_rows": total,
                "exported_rows": len(tables[table]),
                "rejected_rows": rejected[table],
                "source_concepts_resolved": sum(
                    1
                    for row in tables[table]
                    if any(
                        key.endswith("_source_concept_id") and row.get(key)
                        for key in row
                    )
                ),
                "standard_concepts_resolved": mapped[table],
                "unmapped_source_codes": unmapped[table],
                "invalid_or_deprecated_mappings": 0,
                "domain_mismatches": 0,
                "ambiguous_mappings": sum(
                    1
                    for value in warnings
                    if value.startswith(f"{table}:") and "ambiguous" in value
                ),
                "required_field_failures": rejected[table],
                "orphan_fk_count": 0,
                "duplicate_pk_count": 0,
            }
        return tables, metrics, mapping_hashes, sorted(set(warnings))

    def _event_row(
        self,
        table: str,
        row_id: int,
        event: PatientClinicalTimelineEventModel,
        occurred: datetime,
        visit_id: int | None,
        resolved: dict,
        person_id: int,
    ) -> dict | None:
        payload = event.payload or {}
        common = {
            "person_id": person_id,
            "visit_occurrence_id": visit_id,
            "visit_detail_id": None,
        }
        concept_id = resolved["standard_concept_id"]
        source_id = resolved["source_concept_id"]
        source_value = event.concept_code or event.concept_label or event.event_type
        if table == "CONDITION_OCCURRENCE":
            return self._row(
                table,
                condition_occurrence_id=row_id,
                condition_concept_id=concept_id,
                condition_start_date=occurred.date(),
                condition_start_datetime=occurred,
                condition_end_date=self._payload_date(payload, "end"),
                condition_end_datetime=self._parse_datetime(payload.get("end")),
                condition_type_concept_id=0,
                condition_status_concept_id=0,
                condition_source_value=source_value,
                condition_source_concept_id=source_id,
                **common,
            )
        if table == "DRUG_EXPOSURE":
            end = self._parse_datetime(payload.get("end")) or occurred
            return self._row(
                table,
                drug_exposure_id=row_id,
                drug_concept_id=concept_id,
                drug_exposure_start_date=occurred.date(),
                drug_exposure_start_datetime=occurred,
                drug_exposure_end_date=end.date(),
                drug_exposure_end_datetime=end,
                drug_type_concept_id=0,
                quantity=self._decimal(payload.get("quantity")),
                days_supply=payload.get("days_supply"),
                route_concept_id=0,
                drug_source_value=source_value,
                drug_source_concept_id=source_id,
                route_source_value=payload.get("route"),
                dose_unit_source_value=payload.get("unit"),
                **common,
            )
        if table == "MEASUREMENT":
            numeric = self._decimal(payload.get("value"))
            return self._row(
                table,
                measurement_id=row_id,
                measurement_concept_id=concept_id,
                measurement_date=occurred.date(),
                measurement_datetime=occurred,
                measurement_time=occurred.time(),
                measurement_type_concept_id=0,
                operator_concept_id=0,
                value_as_number=numeric,
                value_as_concept_id=0,
                unit_concept_id=0,
                measurement_source_value=source_value,
                measurement_source_concept_id=source_id,
                unit_source_value=payload.get("unit"),
                value_source_value=str(payload.get("value", "")),
                **common,
            )
        if table == "PROCEDURE_OCCURRENCE":
            return self._row(
                table,
                procedure_occurrence_id=row_id,
                procedure_concept_id=concept_id,
                procedure_date=occurred.date(),
                procedure_datetime=occurred,
                procedure_end_date=self._payload_date(payload, "end"),
                procedure_end_datetime=self._parse_datetime(payload.get("end")),
                procedure_type_concept_id=0,
                modifier_concept_id=0,
                quantity=self._decimal(payload.get("quantity")),
                procedure_source_value=source_value,
                procedure_source_concept_id=source_id,
                **common,
            )
        if table == "OBSERVATION":
            numeric = self._decimal(payload.get("value"))
            return self._row(
                table,
                observation_id=row_id,
                observation_concept_id=concept_id,
                observation_date=occurred.date(),
                observation_datetime=occurred,
                observation_type_concept_id=0,
                value_as_number=numeric,
                value_as_string=None if numeric is not None else payload.get("value"),
                value_as_concept_id=0,
                qualifier_concept_id=0,
                unit_concept_id=0,
                observation_source_value=source_value,
                observation_source_concept_id=source_id,
                unit_source_value=payload.get("unit"),
                value_source_value=str(payload.get("value", "")),
                **common,
            )
        return None

    def _resolve_concept(
        self,
        event: PatientClinicalTimelineEventModel,
        expected_domain: str,
        release_ids: list[str],
    ) -> dict:
        base = {
            "source_concept_id": 0,
            "standard_concept_id": 0,
            "mapping_hashes": [],
            "unmapped_reason": "source_concept_not_found",
        }
        if not event.concept_code or not event.concept_system or not release_ids:
            return base
        concepts = list(
            self.db.scalars(
                select(TerminologyConceptModel).where(
                    TerminologyConceptModel.release_id.in_(release_ids),
                    TerminologyConceptModel.source_system == event.concept_system,
                    TerminologyConceptModel.source_code == event.concept_code,
                )
            )
        )
        if len(concepts) != 1:
            if concepts:
                base["unmapped_reason"] = "ambiguous_source_release"
            return base
        source = concepts[0]
        base["source_concept_id"] = source.omop_concept_id or 0
        if source.invalid_reason:
            base["unmapped_reason"] = "source_concept_invalid"
            return base
        if source.standard_status == "standard":
            if source.domain != expected_domain or not source.omop_concept_id:
                base["unmapped_reason"] = "domain_mismatch_or_missing_omop_id"
                return base
            base["standard_concept_id"] = source.omop_concept_id
            base["unmapped_reason"] = None
            return base
        mappings = list(
            self.db.scalars(
                select(TerminologyMappingModel).where(
                    TerminologyMappingModel.source_concept_id == source.id,
                    TerminologyMappingModel.institution_id == event.institution_id,
                    TerminologyMappingModel.status == "approved_for_demo",
                    TerminologyMappingModel.relationship_type == "Maps to",
                )
            )
        )
        valid = []
        for mapping in mappings:
            target = self.db.get(TerminologyConceptModel, mapping.target_concept_id)
            if (
                target
                and target.release_id in release_ids
                and target.standard_status == "standard"
                and target.domain == expected_domain
                and not target.invalid_reason
                and target.omop_concept_id
            ):
                valid.append((mapping, target))
        if len(valid) != 1:
            base["unmapped_reason"] = "ambiguous_mapping" if len(valid) > 1 else "unmapped"
            return base
        mapping, target = valid[0]
        base["standard_concept_id"] = target.omop_concept_id
        base["mapping_hashes"] = [mapping.mapping_hash]
        base["unmapped_reason"] = None
        return base

    def _study(self, study_id: str, actor: UserModel) -> ResearchStudyModel:
        study = self.db.get(ResearchStudyModel, study_id)
        if study is None or study.institution_id != actor.institution_id:
            raise OmopAdapterError("Estudo não encontrado.")
        if not study.demo_only or study.data_source_classification != "synthetic":
            raise OmopAdapterError("OMOP v0.9.1 aceita somente estudo synthetic-only.")
        return study

    def _cohort(
        self, cohort_id: str, study: ResearchStudyModel, actor: UserModel
    ) -> CohortRunModel:
        cohort = self.db.get(CohortRunModel, cohort_id)
        if (
            cohort is None
            or cohort.institution_id != actor.institution_id
            or cohort.study_id != study.id
            or cohort.status != "completed_demo"
        ):
            raise OmopAdapterError("Cohort run incompatível com o estudo/tenant.")
        return cohort

    @staticmethod
    def _row(table: str, **values) -> dict:
        return {column: values.get(column) for column in TABLE_COLUMNS[table]}

    @staticmethod
    def _csv(columns: list[str], rows: list[dict]) -> str:
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: value.isoformat() if isinstance(value, (date, datetime)) else value
                    for key, value in row.items()
                }
            )
        return buffer.getvalue()

    @staticmethod
    def _occurred(event: PatientClinicalTimelineEventModel) -> datetime:
        value = event.event_date or event.created_at
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @staticmethod
    def _parse_datetime(value) -> datetime | None:
        if not value:
            return None
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)

    @classmethod
    def _payload_date(cls, payload: dict, key: str) -> date | None:
        parsed = cls._parse_datetime(payload.get(key))
        return parsed.date() if parsed else None

    @staticmethod
    def _decimal(value) -> Decimal | None:
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
