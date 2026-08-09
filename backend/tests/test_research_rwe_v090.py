from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.database.models import PatientClinicalTimelineEventModel, PatientModel
from app.domain.user import UserRole
from app.schemas.ai_task_schema import AIInteractionReviewRequest, AIRequestSchema
from app.schemas.research_schema import (
    AnalysisPlanCreate,
    CohortDefinitionCreate,
    CohortReviewRequest,
    CohortRunRequest,
    ConceptSetCreate,
    ConceptSetReviewRequest,
    OutcomeDefinitionCreate,
    OutcomeReviewRequest,
    ResearchReviewRequest,
    ResearchStudyCreate,
    StudyProtocolVersionCreate,
)
from app.services.ai_task_router import AITaskRouter
from app.services.cohort_dsl import (
    CohortDSLValidationError,
    CohortDSLValidator,
    DeterministicCohortEngine,
)
from app.services.data_quality_service import DataQualityService
from app.services.research_analysis_service import ResearchAnalysisService
from app.services.research_service import ResearchError, ResearchService


def test_v090_deterministic_analysis_package_and_synthetic_journey(
    create_test_user,
    db_session: Session,
) -> None:
    author = create_test_user(email="v090-author@example.test", role=UserRole.PESQUISADOR)
    reviewer = create_test_user(email="v090-reviewer@example.test", role=UserRole.PESQUISADOR)
    patient = PatientModel(
        institution_id=author.institution_id,
        created_by_user_id=author.id,
        name="Synthetic RWE Patient",
        age=48,
        weight_kg=70,
        sex_for_dosing_calculation="female",
        comorbidities=["Synthetic condition"],
        current_medications=["Synthetic drug"],
    )
    db_session.add(patient)
    db_session.flush()
    db_session.add(
        PatientClinicalTimelineEventModel(
            patient_id=patient.id,
            institution_id=author.institution_id,
            event_type="diagnosis",
            title="Synthetic diagnosis",
            summary="Synthetic event for the v0.9.0 fixture.",
            source_type="synthetic_fixture",
            source_system="Prescripta test",
            source_ref="v090-test:diagnosis:001",
            concept_system="CID-10",
            concept_code="E11-DEMO",
            concept_label="Synthetic condition",
            event_date=datetime(2026, 1, 1, tzinfo=UTC),
            provenance={"demo_only": True, "fixture_version": "v090"},
            validation_status="pending_review",
            created_by=author.id,
        )
    )
    db_session.flush()

    research = ResearchService(db_session)
    study = research.create_study(
        ResearchStudyCreate(
            title="Synthetic Research and RWE MVP",
            slug="synthetic-rwe-mvp-v090",
            description="Synthetic vertical slice.",
            research_question="What is the aggregate profile of the eligible synthetic cohort?",
            objective="Describe reproducible aggregate characteristics for the synthetic cohort.",
            design="retrospective_cohort",
            data_source_classification="synthetic",
        ),
        author,
    )
    protocol = research.create_protocol_version(
        study.id,
        StudyProtocolVersionCreate(
            population={"description": "Synthetic adults"},
            exposure={"description": "Synthetic condition"},
            comparator={"description": "No causal comparator"},
            outcome={"description": "Synthetic outcome"},
            index_date={"event": "snapshot"},
            washout={"days": 0},
            follow_up={"days": 90},
            censoring={"strategy": "none_demo"},
            inclusion=[{"criterion": "age_gte_18"}],
            exclusion=[],
            covariates=[],
            missing_data_strategy={"strategy": "report_only"},
            statistical_plan={"methods": ["descriptive_only"]},
            limitations=["Synthetic fixture without external validity."],
            source_refs=["synthetic-dataset:v090"],
        ),
        author,
    )
    research.review_protocol(
        protocol.id,
        ResearchReviewRequest(
            decision="reviewed_demo",
            note="Independent human methodological review for demonstration.",
        ),
        reviewer,
    )
    concept = research.create_concept_set(
        ConceptSetCreate.model_validate(
            {
                "name": "Synthetic condition v090",
                "domain": "condition",
                "terminology_versions": {"CID-10": "2026-demo"},
                "source_refs": ["terminology-fixture:v090"],
                "license_metadata": {"fixture": True},
                "provenance": {"demo_only": True},
                "members": [
                    {
                        "terminology_system": "CID-10",
                        "terminology_version": "2026-demo",
                        "concept_code": "E11-DEMO",
                        "label": "Synthetic condition",
                    }
                ],
            }
        ),
        author,
    )
    concept_version_id = concept["version"]["id"]
    for decision in ("human_reviewed", "approved_for_demo_study"):
        research.review_concept_set(
            concept_version_id,
            ConceptSetReviewRequest(
                decision=decision,
                note="Independent terminology review for the synthetic fixture.",
            ),
            reviewer,
        )
    cohort = research.create_cohort_version(
        study.id,
        CohortDefinitionCreate(
            name="Nested synthetic adults",
            definition={
                "schema_version": "2",
                "inclusion": {
                    "operator": "all",
                    "items": [
                        {"criterion": "age", "operator": "gte", "value": 18},
                        {
                            "operator": "any",
                            "items": [
                                {
                                    "criterion": "condition",
                                    "operator": "exists",
                                    "concept_set_version_id": concept_version_id,
                                    "temporal_relationship": "during_window",
                                }
                            ],
                        },
                    ],
                },
                "exclusion": {"operator": "any", "items": []},
            },
        ),
        author,
    )
    assert cohort.definition["schema_version"] == "2"
    research.review_cohort(
        cohort.id,
        CohortReviewRequest(
            decision="reviewed_demo",
            note="Independent review of the bounded cohort DSL.",
        ),
        reviewer,
    )
    outcome = research.create_outcome(
        study.id,
        OutcomeDefinitionCreate(
            name="Synthetic outcome in 90 days",
            domain="condition",
            concept_set_version_ids=[concept_version_id],
            event_qualification={"minimum_events": 1},
            observation_window={"after_index_days": 90},
            temporal_relationship="after_index",
            source_refs=["synthetic-dataset:v090"],
            limitations=["Synthetic outcome without clinical validation."],
        ),
        author,
    )
    research.review_outcome(
        outcome.id,
        OutcomeReviewRequest(
            decision="reviewed_demo",
            note="Independent human review of the synthetic outcome.",
        ),
        reviewer,
    )
    cohort_run = research.execute_cohort(
        cohort.id,
        CohortRunRequest(data_snapshot_marker="synthetic-v090-snapshot"),
        author,
    )
    assert cohort_run.result_count == 1
    assert cohort_run.analytics["numeric"]["age_years"]["mean"] == "48"
    assert cohort_run.analytics["incidence"]["status"] == "deferred"
    assert cohort_run.analytics["aggregate_only"] is True

    dq_run = DataQualityService(db_session).run(author, study.id)
    assert dq_run["status"] == "completed"
    assert dq_run["summary"]["analysis_blocked"] is False

    analysis = ResearchAnalysisService(db_session)
    plan = analysis.create_plan(
        study.id,
        AnalysisPlanCreate(
            cohort_run_id=cohort_run.id,
            objectives=["Describe the synthetic population."],
            variables=[{"name": "age_years", "type": "numeric"}],
            steps=[{"method": "numeric_summary"}],
            descriptive_metrics=["n", "mean", "sd", "median", "q1", "q3"],
            subgroup_definitions=[],
            missing_data_approach="report_only",
            methods=["population_count", "numeric_summary", "baseline_table_1"],
            planned_outputs=["summary_cards", "table_1", "research_package"],
            output_specification={"aggregate_only": True},
            source_refs=["synthetic-dataset:v090"],
            limitations=["Descriptive synthetic analysis only."],
        ),
        author,
    )
    with pytest.raises(ResearchError, match="independente"):
        analysis.review_plan(
            plan.id,
            ResearchReviewRequest(
                decision="reviewed_demo",
                note="The author cannot review their own plan.",
            ),
            author,
        )
    analysis.review_plan(
        plan.id,
        ResearchReviewRequest(
            decision="reviewed_demo",
            note="Independent human review of the descriptive plan.",
        ),
        reviewer,
    )
    first_run = analysis.execute(plan.id, author)
    second_run = analysis.execute(plan.id, author)
    assert first_run.content_hash == second_run.content_hash
    assert first_run.results["aggregate_only"] is True
    assert "patient" not in str(first_run.results).casefold()
    package = analysis.export_package(first_run.id, author)
    assert package.aggregate_only is True
    assert set(package.manifest["files"]) == set(package.files)
    assert "patient" not in str(package.files["results.json"]).casefold()

    journey = analysis.patient_journey(study.id, patient.id, author)
    assert journey["synthetic_only"] is True
    assert journey["patient_ref"].startswith("SYN-")
    assert "Synthetic RWE Patient" not in str(journey)

    other_study = research.create_study(
        ResearchStudyCreate(
            title="Internal demonstration study",
            slug="internal-demo-v090",
            research_question="Can a non-synthetic study expose a patient journey?",
            objective="Verify the patient journey fail-closed boundary.",
            design="descriptive",
            data_source_classification="internal_demo",
        ),
        author,
    )
    with pytest.raises(ResearchError, match="falhou fechado"):
        analysis.patient_journey(other_study.id, patient.id, author)


def test_research_copilot_acceptance_creates_an_unreviewed_draft(
    create_test_user,
    db_session: Session,
) -> None:
    author = create_test_user(email="copilot-author@example.test", role=UserRole.PESQUISADOR)
    reviewer = create_test_user(email="copilot-reviewer@example.test", role=UserRole.PESQUISADOR)
    study = ResearchService(db_session).create_study(
        ResearchStudyCreate(
            title="Synthetic Copilot Proposal Study",
            slug="synthetic-copilot-v090",
            research_question="Which synthetic adults meet the proposed bounded cohort criteria?",
            objective="Verify proposal-only Copilot behavior with explicit human acceptance.",
            design="descriptive",
            data_source_classification="synthetic",
        ),
        author,
    )
    router = AITaskRouter(db_session)
    interaction = router.execute(
        AIRequestSchema(
            task_type="cohort_drafting",
            data_classification="synthetic",
            study_id=study.id,
            preferred_provider="fallback",
            allowed_providers=["fallback"],
            purpose="bounded_cohort_proposal",
            input={
                "definition": {
                    "schema_version": "2",
                    "inclusion": {
                        "operator": "all",
                        "items": [{"criterion": "age", "operator": "gte", "value": 18}],
                    },
                    "exclusion": {"operator": "any", "items": []},
                }
            },
        ),
        author,
    )
    assert interaction.human_review_status == "needs_review"
    assert interaction.output_payload["status"] == "proposal_only_not_executed"
    reviewed = router.review(
        interaction.id,
        AIInteractionReviewRequest(
            decision="accepted_as_draft",
            note="Human accepted the bounded proposal as an unreviewed draft.",
        ),
        reviewer,
    )
    created = reviewed.usage_metadata["accepted_draft"]
    assert created["resource_type"] == "cohort_definition_version"
    assert created["status"] == "draft"


def test_cohort_dsl_v2_bounded_validation_and_comparators(
    create_test_user,
    db_session: Session,
) -> None:
    actor = create_test_user(email="dsl-v2-boundaries@example.test")
    validator = CohortDSLValidator(db_session, actor.institution_id)

    for invalid_definition, message in (
        ({}, "objeto"),
        ({"schema_version": "3"}, "não suportada"),
        (
            {
                "schema_version": "2",
                "inclusion": {"operator": "all", "items": []},
                "exclusion": {"operator": "any", "items": []},
                "sql": "select *",
            },
            "topo",
        ),
    ):
        with pytest.raises(CohortDSLValidationError, match=message):
            validator.validate(invalid_definition)

    compare = DeterministicCohortEngine._compare
    assert compare("female", "exists", None)
    assert compare("female", "in", ["female", "male"])
    assert compare("FEMALE", "eq", "female")
    assert compare(48, "gte", 18)
    assert compare(48, "lte", 65)
    assert compare(48, "between", [18, 65])
    assert not compare("not-numeric", "gte", 18)
    assert DeterministicCohortEngine._numeric([], 2) == {
        "n": 0,
        "missing": 2,
        "mean": None,
        "sd": None,
        "median": None,
        "q1": None,
        "q3": None,
        "iqr": None,
        "min": None,
        "max": None,
    }

    moment = datetime(2026, 1, 2, tzinfo=UTC)
    assert DeterministicCohortEngine._compare_date(moment, "before", "2026-01-03")
    assert DeterministicCohortEngine._compare_date(moment, "after", "2026-01-01")
    assert DeterministicCohortEngine._compare_date(
        moment,
        "between",
        ["2026-01-01", "2026-01-03"],
    )
