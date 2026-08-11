from __future__ import annotations

import base64
import hashlib
import io
import zipfile
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    CohortDefinitionModel,
    CohortDefinitionVersionModel,
    CohortRunModel,
    PatientClinicalTimelineEventModel,
    PatientModel,
    ResearchSnapshotModel,
    ResearchStudyModel,
    TerminologyConceptModel,
)
from app.domain.user import UserRole
from app.schemas.omop_schema import OmopPreviewRequest
from app.schemas.terminology_schema import (
    TerminologyImportRequest,
    TerminologyMappingCreate,
    TerminologyMappingReview,
    TerminologyReleaseCreate,
    TerminologySourceCreate,
)
from app.services.canonical_json import canonical_sha256
from app.services.omop_adapter_service import OmopAdapterError, OmopAdapterService
from app.services.terminology_registry_service import (
    TerminologyError,
    TerminologyRegistryService,
)


def _encoded(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _release_payload(raw: bytes, version: str, **overrides) -> TerminologyReleaseCreate:
    values = {
        "version": version,
        "source_checksum": hashlib.sha256(raw).hexdigest(),
        "source_artifact_name": f"synthetic-{version}.csv",
        "license_identifier": "synthetic-test-only",
        "license_name": "Synthetic fixture metadata",
        "license_reference": "https://example.test/synthetic-terminology",
        "redistributable": False,
        "requires_license": False,
        "requires_login": False,
        "requires_attribution": False,
        "license_status": "not_applicable",
        "provenance": {
            "synthetic_fixture": True,
            "not_official_vocabulary_content": True,
        },
    }
    values.update(overrides)
    return TerminologyReleaseCreate.model_validate(values)


def _import_csv(service, source, raw, version, actor):
    release = service.create_release(
        source.id, _release_payload(raw, version), actor
    )
    run = service.import_bundle(
        release.id,
        TerminologyImportRequest(
            artifact_name=f"synthetic-{version}.csv",
            format="csv",
            content_base64=_encoded(raw),
        ),
        actor,
    )
    return release, run


def test_governed_terminology_import_mapping_review_and_drift(
    create_test_user, db_session: Session
) -> None:
    author = create_test_user(email="term-author@example.test", role=UserRole.ADMIN)
    reviewer = create_test_user(email="term-reviewer@example.test", role=UserRole.ADMIN)
    service = TerminologyRegistryService(db_session)
    source = service.create_source(
        TerminologySourceCreate(
            canonical_system="SYN-SOURCE",
            public_name="Synthetic source terminology fixture",
            steward="Prescripta tests",
            family="synthetic",
            source_reference="https://example.test/synthetic-source",
            jurisdiction="TEST",
            locale="en-US",
        ),
        author,
    )
    raw_v1 = (
        b"source_code,display,domain,standard_status,aliases,invalid_reason\n"
        b"C1,Synthetic condition alpha,Condition,source,alpha alias,\n"
        b"D1,Synthetic drug alpha,Drug,source,,\n"
    )
    release_v1, first_import = _import_csv(service, source, raw_v1, "fixture-v1", author)
    repeated = service.import_bundle(
        release_v1.id,
        TerminologyImportRequest(
            artifact_name="synthetic-fixture-v1.csv",
            format="csv",
            content_base64=_encoded(raw_v1),
        ),
        author,
    )
    assert repeated.id == first_import.id
    assert first_import.inserted_count == 2
    raw_v2 = (
        b"source_code,display,domain,standard_status,aliases,invalid_reason\n"
        b"C1,Synthetic condition beta,Condition,source,beta alias,\n"
        b"D1,Synthetic drug alpha,Drug,source,,deprecated\n"
    )
    release_v2, _ = _import_csv(service, source, raw_v2, "fixture-v2", author)
    codes = list(
        db_session.scalars(
            select(TerminologyConceptModel).where(
                TerminologyConceptModel.source_code == "C1"
            )
        )
    )
    assert len(codes) == 2
    assert {item.release_id for item in codes} == {release_v1.id, release_v2.id}
    assert service.search(author, query="C1")["suggestion_only"] is True
    suggested = service.search(
        author,
        query="Sy",
        release_id=release_v1.id,
        domain="Condition",
        standard_status="source",
        active_only=True,
    )
    assert suggested["suggestion_only"] is True
    assert suggested["total"] == 1
    with pytest.raises(TerminologyError, match="Paginação"):
        service.search(author, limit=101)
    drift = service.drift(release_v1.id, release_v2.id, author)
    assert drift["summary"]["target_changed"] == 1
    assert drift["summary"]["source_concept_deprecated"] == 1

    target_source = service.create_source(
        TerminologySourceCreate(
            canonical_system="OMOP-SYNTHETIC-SCHEMA-FIXTURE",
            public_name="Synthetic OMOP-shaped test fixture",
            steward="Prescripta tests",
            family="omop",
            source_reference="https://example.test/omop-schema-fixture",
            jurisdiction="TEST",
            locale="en-US",
        ),
        author,
    )
    target_raw = (
        b"source_code,display,domain,standard_status,omop_concept_id\n"
        b"STD-C,Synthetic standard condition fixture,Condition,standard,900000001\n"
    )
    target_release, _ = _import_csv(
        service, target_source, target_raw, "fixture-standard-v1", author
    )
    assert service.search(author, query="STD-C")["suggestion_only"] is False
    source_concept = db_session.scalar(
        select(TerminologyConceptModel).where(
            TerminologyConceptModel.release_id == release_v1.id,
            TerminologyConceptModel.source_code == "C1",
        )
    )
    target_concept = db_session.scalar(
        select(TerminologyConceptModel).where(
            TerminologyConceptModel.release_id == target_release.id,
            TerminologyConceptModel.source_code == "STD-C",
        )
    )
    mapping = service.propose_mapping(
        TerminologyMappingCreate(
            source_concept_id=source_concept.id,
            target_concept_id=target_concept.id,
            relationship_type="Maps to",
            mapping_method="explicit_fixture",
            domain_expectation="Condition",
            rationale="Synthetic governance and domain validation fixture.",
            provenance={"synthetic_fixture": True},
        ),
        author,
    )
    with pytest.raises(TerminologyError, match="independente"):
        service.review_mapping(
            mapping.id,
            TerminologyMappingReview(
                decision="approved_for_demo",
                note="Author must not approve this proposed synthetic mapping.",
            ),
            author,
        )
    approved = service.review_mapping(
        mapping.id,
        TerminologyMappingReview(
            decision="approved_for_demo",
            note="Independent review of the synthetic mapping and expected domain.",
        ),
        reviewer,
    )
    assert approved.reviewed_by_user_id == reviewer.id
    assert approved.status == "approved_for_demo"
    assert service.list_mappings(author, status="approved_for_demo") == [approved]
    with pytest.raises(TerminologyError, match="Somente mapping proposed"):
        service.review_mapping(
            approved.id,
            TerminologyMappingReview(
                decision="rejected",
                note="Already reviewed mapping cannot transition a second time.",
            ),
            reviewer,
        )
    with pytest.raises(TerminologyError, match="distintos"):
        service.propose_mapping(
            TerminologyMappingCreate(
                source_concept_id=source_concept.id,
                target_concept_id=source_concept.id,
                relationship_type="Maps to",
                mapping_method="explicit_fixture",
                domain_expectation="Condition",
                rationale="Self mapping must be rejected by governance.",
                provenance={"synthetic_fixture": True},
            ),
            author,
        )
    superseding = service.propose_mapping(
        TerminologyMappingCreate(
            source_concept_id=source_concept.id,
            target_concept_id=target_concept.id,
            relationship_type="Maps to",
            mapping_method="manual",
            domain_expectation="Condition",
            rationale="Versioned replacement proposal for branch coverage.",
            provenance={"synthetic_fixture": True},
            supersedes_mapping_id=approved.id,
        ),
        author,
    )
    assert superseding.version == 2
    assert superseding.mapping_family_id == approved.mapping_family_id
    rejected = service.review_mapping(
        superseding.id,
        TerminologyMappingReview(
            decision="rejected",
            note="Independent reviewer rejects this replacement proposal.",
        ),
        reviewer,
    )
    assert rejected.status == "rejected"
    assert service.drift(release_v1.id, release_v1.id, author)["summary"] == {
        "unchanged": 2
    }

    bad_buffer = io.BytesIO()
    with zipfile.ZipFile(bad_buffer, "w") as archive:
        archive.writestr("../concepts.csv", raw_v1)
    bad_raw = bad_buffer.getvalue()
    bad_release = service.create_release(
        source.id, _release_payload(bad_raw, "bad-archive"), author
    )
    with pytest.raises(TerminologyError, match="path traversal"):
        service.import_bundle(
            bad_release.id,
            TerminologyImportRequest(
                artifact_name="bad.zip",
                format="zip_csv",
                content_base64=_encoded(bad_raw),
            ),
            author,
        )

    restricted_release = service.create_release(
        source.id,
        _release_payload(
            raw_v1,
            "license-required",
            requires_license=True,
            requires_login=True,
            license_status="license_required",
        ),
        author,
    )
    with pytest.raises(TerminologyError, match="License required"):
        service.import_bundle(
            restricted_release.id,
            TerminologyImportRequest(
                artifact_name="restricted.csv",
                format="csv",
                content_base64=_encoded(raw_v1),
            ),
            author,
        )


def test_omop_partial_adapter_exports_seven_tables_with_lineage_and_tenant_guard(
    create_test_user, db_session: Session
) -> None:
    author = create_test_user(email="omop-author@example.test", role=UserRole.ADMIN)
    reviewer = create_test_user(email="omop-reviewer@example.test", role=UserRole.ADMIN)
    other = create_test_user(
        email="omop-other@example.test", role=UserRole.ADMIN, institution_id="other"
    )
    terminology = TerminologyRegistryService(db_session)
    source = terminology.create_source(
        TerminologySourceCreate(
            canonical_system="SYN-SOURCE",
            public_name="Synthetic event source fixture",
            steward="Prescripta tests",
            family="synthetic",
            source_reference="https://example.test/source-events",
        ),
        author,
    )
    source_raw = (
        b"source_code,display,domain,standard_status\n"
        b"C1,Synthetic condition,Condition,source\n"
        b"D1,Synthetic drug,Drug,source\n"
        b"M1,Synthetic measurement,Measurement,source\n"
        b"P1,Synthetic procedure,Procedure,source\n"
        b"O1,Synthetic observation,Observation,source\n"
    )
    source_release, _ = _import_csv(
        terminology, source, source_raw, "events-v1", author
    )
    target_source = terminology.create_source(
        TerminologySourceCreate(
            canonical_system="OMOP-SYNTHETIC-SCHEMA-FIXTURE",
            public_name="Synthetic OMOP-shaped test fixture",
            steward="Prescripta tests",
            family="omop",
            source_reference="https://example.test/omop-fixture",
        ),
        author,
    )
    target_raw = (
        b"source_code,display,domain,standard_status,omop_concept_id\n"
        b"STD-C,Synthetic standard condition fixture,Condition,standard,900000001\n"
    )
    target_release, _ = _import_csv(
        terminology, target_source, target_raw, "standard-v1", author
    )
    source_condition = db_session.scalar(
        select(TerminologyConceptModel).where(
            TerminologyConceptModel.release_id == source_release.id,
            TerminologyConceptModel.source_code == "C1",
        )
    )
    target_condition = db_session.scalar(
        select(TerminologyConceptModel).where(
            TerminologyConceptModel.release_id == target_release.id
        )
    )
    mapping = terminology.propose_mapping(
        TerminologyMappingCreate(
            source_concept_id=source_condition.id,
            target_concept_id=target_condition.id,
            relationship_type="Maps to",
            mapping_method="explicit_fixture",
            domain_expectation="Condition",
            rationale="Synthetic OMOP adapter mapping fixture.",
            provenance={"synthetic_fixture": True},
        ),
        author,
    )
    terminology.review_mapping(
        mapping.id,
        TerminologyMappingReview(
            decision="approved_for_demo",
            note="Independent review for the synthetic adapter fixture.",
        ),
        reviewer,
    )

    patient = PatientModel(
        institution_id=author.institution_id,
        created_by_user_id=author.id,
        name="Synthetic OMOP Patient",
        age=40,
        weight_kg=70,
        sex_for_dosing_calculation="female",
    )
    db_session.add(patient)
    db_session.flush()
    event_specs = [
        ("encounter", "V1", {}),
        ("diagnosis", "C1", {}),
        ("medication_start", "D1", {"quantity": "2", "unit": "tablet"}),
        ("measurement", "M1", {"value": "72.5", "unit": "kg"}),
        ("procedure", "P1", {"quantity": "1"}),
        ("observation", "O1", {"value": "synthetic qualitative value"}),
    ]
    occurred = datetime(2026, 8, 1, 12, 30, tzinfo=UTC)
    for index, (event_type, code, payload) in enumerate(event_specs, start=1):
        db_session.add(
            PatientClinicalTimelineEventModel(
                patient_id=patient.id,
                institution_id=author.institution_id,
                event_type=event_type,
                title=f"Synthetic {event_type}",
                summary="Synthetic-only OMOP adapter fixture.",
                source_type="synthetic_fixture",
                source_system="Prescripta tests",
                source_ref=f"omop-v091:{index}",
                concept_system="SYN-SOURCE",
                concept_code=code,
                concept_label=f"Synthetic {event_type}",
                event_date=occurred,
                payload=payload,
                provenance={"demo_only": True, "fixture": "v091"},
                validation_status="pending_review",
                created_by=author.id,
            )
        )
    study = ResearchStudyModel(
        institution_id=author.institution_id,
        title="Synthetic OMOP adapter study",
        slug="synthetic-omop-adapter-v091",
        research_question="Can synthetic canonical events be transformed deterministically?",
        objective="Validate the partial adapter without clinical claims.",
        design="descriptive",
        status="active_demo",
        owner_user_id=author.id,
        demo_only=True,
        data_source_classification="synthetic",
    )
    db_session.add(study)
    db_session.flush()
    definition = CohortDefinitionModel(
        study_id=study.id,
        institution_id=author.institution_id,
        name="Synthetic OMOP cohort",
        status="reviewed_demo",
        created_by_user_id=author.id,
    )
    db_session.add(definition)
    db_session.flush()
    version = CohortDefinitionVersionModel(
        cohort_definition_id=definition.id,
        study_id=study.id,
        institution_id=author.institution_id,
        version=1,
        definition={"schema_version": "2", "inclusion": {"items": []}},
        definition_hash=canonical_sha256({"synthetic": "cohort"}),
        status="reviewed_demo",
        query_cost=1,
        authored_by_user_id=author.id,
        reviewed_by_user_id=reviewer.id,
        reviewed_at=datetime.now(UTC),
    )
    db_session.add(version)
    db_session.flush()
    run_basis = {"study": study.id, "snapshot": "synthetic-omop-v091"}
    cohort = CohortRunModel(
        study_id=study.id,
        cohort_version_id=version.id,
        institution_id=author.institution_id,
        data_snapshot_marker="synthetic-omop-v091",
        executed_at=datetime.now(UTC),
        executed_by_user_id=author.id,
        definition_hash=version.definition_hash,
        source_version_refs=[source_release.id, target_release.id],
        result_count=1,
        attrition=[],
        analytics={"aggregate_only": True},
        engine_version="test-fixture",
        prescripta_version="0.9.1",
        status="completed_demo",
        warnings=[],
        run_hash=canonical_sha256(run_basis),
    )
    db_session.add(cohort)
    db_session.flush()
    snapshot_payload = {"run_basis": run_basis, "aggregate_only": True}
    db_session.add(
        ResearchSnapshotModel(
            cohort_run_id=cohort.id,
            snapshot_type="cohort_run_v1",
            payload=snapshot_payload,
            snapshot_hash=canonical_sha256(snapshot_payload),
        )
    )
    db_session.flush()

    payload = OmopPreviewRequest(
        study_id=study.id,
        cohort_run_id=cohort.id,
        terminology_release_ids=[source_release.id, target_release.id],
    )
    adapter = OmopAdapterService(db_session)
    first = adapter.execute(payload, author, persist_export=True)
    second = adapter.execute(payload, author, persist_export=True)
    assert first.export_hash == second.export_hash
    assert first.cdm_version == "5.4"
    assert first.manifest["claim_level"] == "omop_v5_4_partial_adapter"
    assert len(first.export_files) == 7
    assert first.metrics["CONDITION_OCCURRENCE"]["standard_concepts_resolved"] == 1
    assert "900000001" in first.export_files["condition_occurrence.csv"]
    assert "C1" in first.export_files["condition_occurrence.csv"]
    assert first.metrics["DRUG_EXPOSURE"]["unmapped_source_codes"] == 1
    assert adapter.compatibility()["ohdsi_tool_validated"] is False
    with pytest.raises(OmopAdapterError, match="não encontrado"):
        adapter.run(first.id, other)
