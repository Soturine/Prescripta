from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import (
    AIInteractionModel,
    CohortDefinitionVersionModel,
    PatientClinicalTimelineEventModel,
    ResearchSnapshotModel,
    StudyProtocolVersionModel,
)
from app.domain.user import UserRole


def _study_payload(slug: str = "synthetic-safety-study") -> dict:
    return {
        "title": "Estudo sintético de segurança medicamentosa",
        "slug": slug,
        "description": "Vertical slice demonstrativo para testes reprodutíveis.",
        "research_question": "Qual a frequência do evento na população sintética elegível?",
        "objective": "Descrever agregados de uma coorte exclusivamente demonstrativa.",
        "design": "retrospective_cohort",
        "data_source_classification": "synthetic",
    }


def _protocol_payload() -> dict:
    return {
        "population": {"description": "Adultos sintéticos"},
        "exposure": {"description": "Exposição demo"},
        "comparator": {"description": "Sem comparador causal"},
        "outcome": {"description": "Condição demo"},
        "index_date": {"event": "snapshot"},
        "washout": {"days": 0},
        "follow_up": {"days": 90},
        "censoring": {"strategy": "none_demo"},
        "inclusion": [{"criterion": "age_gte_18"}],
        "exclusion": [],
        "covariates": [],
        "missing_data_strategy": {"strategy": "report_missingness"},
        "statistical_plan": {"methods": ["descriptive_only"]},
        "limitations": ["Dados sintéticos sem validade externa."],
        "source_refs": ["synthetic-dataset:v088"],
    }


def _concept_payload() -> dict:
    return {
        "name": "Condição metabólica demo",
        "domain": "condition",
        "terminology_versions": {"CID-10": "2026-demo"},
        "include_descendants": False,
        "source_refs": ["terminology-fixture:cid10-demo-v1"],
        "license_metadata": {"fixture": True, "redistribution": "synthetic-only"},
        "provenance": {"origin": "test-fixture", "demo_only": True},
        "members": [
            {
                "terminology_system": "CID-10",
                "terminology_version": "2026-demo",
                "concept_code": "E11-DEMO",
                "label": "diabetes",
                "excluded": False,
            }
        ],
    }


def _create_patient(
    client: TestClient,
    headers: dict[str, str],
    name: str,
    age: int,
    conditions: list[str],
) -> int:
    response = client.post(
        "/api/patients",
        headers=headers,
        json={
            "name": name,
            "age": age,
            "weight_kg": 70,
            "sex_for_dosing_calculation": "female",
            "comorbidities": conditions,
            "current_medications": ["medicamento demo"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_research_vertical_slice_is_aggregate_reproducible_and_tenant_scoped(
    client: TestClient,
    create_test_user,
    auth_headers,
    db_session: Session,
) -> None:
    create_test_user(email="admin@rwe.local", role=UserRole.ADMIN)
    researcher = create_test_user(
        email="author@rwe.local",
        password="Author@12345",
        role=UserRole.PESQUISADOR,
    )
    create_test_user(
        email="reviewer@rwe.local",
        password="Reviewer@12345",
        role=UserRole.PESQUISADOR,
    )
    create_test_user(
        email="outside@rwe.local",
        password="Outside@12345",
        role=UserRole.PESQUISADOR,
        institution_id="other-institution",
    )
    admin_headers = auth_headers("admin@rwe.local", "Admin@12345")
    author_headers = auth_headers("author@rwe.local", "Author@12345")
    reviewer_headers = auth_headers("reviewer@rwe.local", "Reviewer@12345")
    outside_headers = auth_headers("outside@rwe.local", "Outside@12345")

    _create_patient(client, admin_headers, "Synthetic Patient A", 45, ["diabetes"])
    _create_patient(client, admin_headers, "Synthetic Patient B", 16, [])
    _create_patient(client, admin_headers, "Synthetic Patient C", 33, [])

    study = client.post(
        "/api/research/studies",
        headers=author_headers,
        json=_study_payload(),
    )
    assert study.status_code == 201, study.text
    study_id = study.json()["id"]
    assert study.json()["demo_only"] is True
    outside_read = client.get(
        f"/api/research/studies/{study_id}",
        headers=outside_headers,
    )
    assert outside_read.status_code == 404
    assert client.get("/api/patients/1", headers=author_headers).status_code == 403

    protocol = client.post(
        f"/api/research/studies/{study_id}/protocol-versions",
        headers=author_headers,
        json=_protocol_payload(),
    )
    assert protocol.status_code == 201, protocol.text
    same_author_review = client.post(
        f"/api/research/protocol-versions/{protocol.json()['id']}/review",
        headers=author_headers,
        json={"decision": "reviewed_demo", "note": "Tentativa do próprio autor."},
    )
    assert same_author_review.status_code == 422
    reviewed_protocol = client.post(
        f"/api/research/protocol-versions/{protocol.json()['id']}/review",
        headers=reviewer_headers,
        json={
            "decision": "reviewed_demo",
            "note": "Revisão metodológica humana independente para demonstração.",
        },
    )
    assert reviewed_protocol.status_code == 200, reviewed_protocol.text
    reviewed_row = db_session.get(StudyProtocolVersionModel, protocol.json()["id"])
    assert reviewed_row is not None
    reviewed_row.population = {"description": "Tentativa de mutação"}
    with pytest.raises(ValueError, match="imutável"):
        db_session.flush()
    db_session.rollback()

    concept = client.post(
        "/api/research/concept-sets",
        headers=author_headers,
        json=_concept_payload(),
    )
    assert concept.status_code == 201, concept.text
    concept_version_id = concept.json()["version"]["id"]
    for decision in ("human_reviewed", "approved_for_demo_study"):
        reviewed = client.post(
            f"/api/research/concept-set-versions/{concept_version_id}/review",
            headers=reviewer_headers,
            json={
                "decision": decision,
                "note": "Revisão humana da fixture terminológica demonstrativa.",
            },
        )
        assert reviewed.status_code == 200, reviewed.text

    invalid_dsl = client.post(
        f"/api/research/studies/{study_id}/cohorts",
        headers=author_headers,
        json={
            "name": "Coorte inválida",
            "definition": {
                "all": [{"criterion": "age", "operator": "DROP TABLE", "value": 18}]
            },
        },
    )
    assert invalid_dsl.status_code == 422
    cohort = client.post(
        f"/api/research/studies/{study_id}/cohorts",
        headers=author_headers,
        json={
            "name": "Adultos com condição demo",
            "definition": {
                "all": [
                    {
                        "criterion": "age",
                        "operator": "gte",
                        "value": 18,
                        "label": "Adultos",
                    },
                    {
                        "criterion": "condition",
                        "operator": "exists",
                        "concept_set_version_id": concept_version_id,
                        "label": "Condição metabólica demo",
                    },
                ],
                "exclude": [],
            },
        },
    )
    assert cohort.status_code == 201, cohort.text
    cohort_version_id = cohort.json()["id"]
    reviewed_cohort = client.post(
        f"/api/research/cohort-versions/{cohort_version_id}/review",
        headers=reviewer_headers,
        json={
            "decision": "reviewed_demo",
            "note": "DSL e concept set revisados por pessoa independente.",
        },
    )
    assert reviewed_cohort.status_code == 200, reviewed_cohort.text

    outcome = client.post(
        f"/api/research/studies/{study_id}/outcomes",
        headers=author_headers,
        json={
            "name": "Outcome condição demo em 90 dias",
            "domain": "condition",
            "concept_set_version_ids": [concept_version_id],
            "event_qualification": {"minimum_events": 1},
            "observation_window": {"after_index_days": 90},
            "temporal_relationship": "after_index",
            "source_refs": ["synthetic-dataset:v088"],
            "limitations": ["Outcome demonstrativo não validado clinicamente."],
        },
    )
    assert outcome.status_code == 201, outcome.text

    runs = []
    for _ in range(2):
        run = client.post(
            f"/api/research/cohort-versions/{cohort_version_id}/runs",
            headers=author_headers,
            json={"data_snapshot_marker": "synthetic-fixture-v088-001"},
        )
        assert run.status_code == 201, run.text
        runs.append(run.json())
    assert runs[0]["result_count"] == 1
    assert [step["after_count"] for step in runs[0]["attrition"]] == [2, 1]
    assert runs[0]["run_hash"] == runs[1]["run_hash"]
    assert runs[0]["analytics"]["n"] == 1
    assert "sintéticos" in runs[0]["synthetic_demo_notice"]
    assert "patient_ids" not in str(runs[0]).casefold()
    assert db_session.scalar(select(func.count(ResearchSnapshotModel.id))) == 2
    assert db_session.scalar(select(func.count(CohortDefinitionVersionModel.id))) == 1

    workspace = client.get("/api/research/workspace", headers=author_headers)
    assert workspace.status_code == 200
    assert workspace.json()["studies"] == 1
    assert workspace.json()["cohort_runs"] == 2
    study_workspace = client.get(
        f"/api/research/studies/{study_id}/workspace",
        headers=author_headers,
    )
    assert study_workspace.status_code == 200, study_workspace.text
    assert study_workspace.json()["study"]["id"] == study_id
    assert len(study_workspace.json()["protocol_versions"]) == 1
    assert len(study_workspace.json()["cohort_versions"]) == 1
    assert len(study_workspace.json()["outcomes"]) == 1
    assert len(study_workspace.json()["runs"]) == 2
    assert study_workspace.json()["concept_set_version_ids"] == [concept_version_id]
    assert researcher.institution_id == "demo"


def test_evidence_ai_timeline_and_data_quality_boundaries(
    client: TestClient,
    create_test_user,
    auth_headers,
    db_session: Session,
) -> None:
    admin = create_test_user(email="admin@foundation.local", role=UserRole.ADMIN)
    create_test_user(
        email="research@foundation.local",
        password="Research@12345",
        role=UserRole.PESQUISADOR,
    )
    create_test_user(
        email="review@foundation.local",
        password="Review@12345",
        role=UserRole.PESQUISADOR,
    )
    doctor = create_test_user(
        email="doctor@foundation.local",
        password="Doctor@12345",
        role=UserRole.MEDICO,
    )
    admin_headers = auth_headers("admin@foundation.local", "Admin@12345")
    research_headers = auth_headers("research@foundation.local", "Research@12345")
    review_headers = auth_headers("review@foundation.local", "Review@12345")
    doctor_headers = auth_headers("doctor@foundation.local", "Doctor@12345")
    patient_id = _create_patient(client, admin_headers, "Synthetic Timeline", 52, [])
    grant = client.post(
        f"/api/access/patients/{patient_id}/grants",
        headers=admin_headers,
        json={
            "user_id": doctor.id,
            "capability": "patient.read",
            "purpose": "treatment",
            "reason": "Vínculo explícito para leitura da timeline sintética.",
        },
    )
    assert grant.status_code == 201, grant.text
    event = PatientClinicalTimelineEventModel(
        patient_id=patient_id,
        institution_id=admin.institution_id,
        event_type="measurement",
        event_date=datetime.now(UTC) + timedelta(days=30),
        title="Medição demo",
        source_type="synthetic_fixture",
        source_system="Prescripta test",
        source_ref="timeline:future-measurement:001",
        concept_code="DEMO-LOINC",
        concept_system=None,
        concept_label="Medição demo",
        summary="Evento propositalmente inválido para Data Quality.",
        payload={"amount": -1, "unit": "mystery-unit"},
        validation_status="pending_review",
        provenance={"demo_only": True},
        visibility_classification="clinical",
    )
    db_session.add(event)
    db_session.commit()

    timeline = client.get(f"/api/patients/{patient_id}/timeline", headers=doctor_headers)
    assert timeline.status_code == 200
    assert timeline.json()[0]["source_ref"] == "timeline:future-measurement:001"
    unauthorized_timeline = client.get(
        f"/api/patients/{patient_id}/timeline",
        headers=research_headers,
    )
    assert unauthorized_timeline.status_code == 403

    dq = client.post("/api/data-quality/runs", headers=research_headers)
    assert dq.status_code == 200, dq.text
    assert dq.json()["findings_created"] >= 3
    findings = client.get("/api/data-quality/findings", headers=research_headers)
    rules = {item["rule"] for item in findings.json()}
    assert {"impossible_future_date", "non_positive_quantity", "unknown_unit"} <= rules

    source = client.post(
        "/api/evidence/sources",
        headers=research_headers,
        json={
            "source_type": "terminology_source",
            "title": "Fonte terminológica sintética v0.8.8",
            "identifier": "fixture:terminology:v088",
            "jurisdiction": "BR-demo",
            "source_version": "v1",
            "license_metadata": {"fixture": True},
            "provenance": {"created_for": "automated-test"},
        },
    )
    assert source.status_code == 201, source.text
    study = client.post(
        "/api/research/studies",
        headers=research_headers,
        json=_study_payload("ai-draft-study"),
    )
    assert study.status_code == 201
    link = client.post(
        "/api/evidence/links",
        headers=research_headers,
        json={
            "source_id": source.json()["id"],
            "target_type": "study",
            "target_id": study.json()["id"],
            "relationship": "supports_terminology",
            "locator": "fixture section 1",
        },
    )
    assert link.status_code == 201, link.text

    interaction = client.post(
        "/api/ai/tasks",
        headers=research_headers,
        json={
            "task_type": "research_question_structuring",
            "data_classification": "synthetic",
            "study_id": study.json()["id"],
            "source_ids": [source.json()["id"]],
            "preferred_provider": "fallback",
            "allowed_providers": ["fallback"],
            "purpose": "research_protocol_draft",
            "input": {"question": "Descrever a coorte sintética adulta."},
        },
    )
    assert interaction.status_code == 201, interaction.text
    assert interaction.json()["human_review_status"] == "needs_review"
    assert interaction.json()["fallback_used"] is True
    assert interaction.json()["output_payload"]["status"] == "proposal_only_not_executed"
    assert db_session.scalar(select(func.count(CohortDefinitionVersionModel.id))) == 0
    stored = db_session.get(AIInteractionModel, interaction.json()["id"])
    assert stored is not None
    assert stored.input_hash and "question" not in stored.usage_metadata

    reviewed = client.post(
        f"/api/ai/tasks/{interaction.json()['id']}/review",
        headers=review_headers,
        json={
            "decision": "accepted_as_draft",
            "note": "Proposta aceita apenas como draft para edição humana.",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "accepted_as_draft"
