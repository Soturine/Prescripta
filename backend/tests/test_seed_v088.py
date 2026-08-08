from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import (
    CohortRunModel,
    ConceptSetModel,
    DataQualityFindingModel,
    InstitutionalClinicalProtocolVersionModel,
    PatientClinicalTimelineEventModel,
    PharmacyInterventionModel,
    ResearchStudyModel,
    UserModel,
)
from app.database.seed import seed_demo_data


def test_v088_seed_is_idempotent_synthetic_and_verifiable(db_session: Session) -> None:
    seed_demo_data(db_session)
    seed_demo_data(db_session)

    study = db_session.scalar(
        select(ResearchStudyModel).where(
            ResearchStudyModel.slug == "seguranca-medicamentosa-sintetica-v088"
        )
    )
    assert study is not None
    assert study.demo_only is True
    assert study.data_source_classification == "synthetic"
    assert study.status == "protocol_reviewed_demo"
    assert db_session.scalar(
        select(func.count(ResearchStudyModel.id)).where(
            ResearchStudyModel.slug == study.slug
        )
    ) == 1

    run = db_session.scalar(
        select(CohortRunModel).where(CohortRunModel.study_id == study.id)
    )
    assert run is not None
    assert run.status == "completed_demo"
    assert len(run.attrition) == 2
    assert run.attrition[0]["before_count"] >= run.attrition[-1]["after_count"]
    assert db_session.scalar(
        select(func.count(CohortRunModel.id)).where(CohortRunModel.study_id == study.id)
    ) == 1

    concept = db_session.scalar(
        select(ConceptSetModel).where(
            ConceptSetModel.name == "Condição metabólica sintética v0.8.8"
        )
    )
    assert concept is not None
    assert concept.status == "approved_for_demo_study"
    assert db_session.scalar(
        select(func.count(PatientClinicalTimelineEventModel.id)).where(
            PatientClinicalTimelineEventModel.source_system == "Prescripta demo v0.8.8"
        )
    ) == 2
    assert db_session.scalar(
        select(func.count(DataQualityFindingModel.id)).where(
            DataQualityFindingModel.rule == "unknown_unit"
        )
    ) == 1
    assert db_session.scalar(
        select(func.count(PharmacyInterventionModel.id)).where(
            PharmacyInterventionModel.idempotency_key == "seed-v088-pharmacy-dose-001"
        )
    ) == 1

    protocol_version = db_session.scalar(
        select(InstitutionalClinicalProtocolVersionModel).where(
            InstitutionalClinicalProtocolVersionModel.version == "2026.08-demo"
        )
    )
    assert protocol_version is not None
    assert protocol_version.review_status == "reviewed_demo"
    nurse = db_session.scalar(
        select(UserModel).where(UserModel.email == "enfermagem@prescripta.local")
    )
    assert nurse is not None
    assert nurse.credential_type == "coren_demo"
    assert nurse.credential_verification_status == "verified"
    assert str(protocol_version.protocol_id) in nurse.institutional_policy["nursing_protocols"]
