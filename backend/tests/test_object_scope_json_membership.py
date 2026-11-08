"""PRE-06: o escopo em lista e a checagem por objeto devem autorizar exatamente os mesmos pacientes.

Roda sempre em SQLite e também em PostgreSQL quando PRESCRIPTA_DATABASE_URL aponta para um
banco migrado (job `postgres` do CI). Antes da correção, o PostgreSQL falhava com
`operator does not exist: json ~~ text` e o SQLite fazia correspondência por substring.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database.models import (
    CareEpisodeAssignmentModel,
    CareTeamMembershipModel,
    PatientModel,
    UserModel,
)
from app.database.session import Base
from app.services.object_authorization import ObjectAuthorizationService

INSTITUTION = "scope-json-test"


@pytest.fixture(params=["sqlite", "postgresql"])
def scoped_session(request: pytest.FixtureRequest) -> Generator[Session, None, None]:
    if request.param == "sqlite":
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
    else:
        url = os.getenv("PRESCRIPTA_DATABASE_URL", "")
        if not url.startswith("postgresql"):
            pytest.skip("PostgreSQL integration test")
        engine = create_engine(url)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def _user(db: Session, email: str, capabilities: list[str]) -> UserModel:
    user = UserModel(
        name="Scope Test",
        email=email,
        hashed_password="not-a-real-hash",
        role="medico",
        profession="medicina",
        capabilities=capabilities,
        institution_id=INSTITUTION,
    )
    db.add(user)
    db.flush()
    return user


def _patient(db: Session, name: str) -> PatientModel:
    patient = PatientModel(name=name, weight_kg=70, institution_id=INSTITUTION)
    db.add(patient)
    db.flush()
    return patient


def _team(db, patient, user, granter, capabilities, *, revoked: bool = False) -> None:
    now = datetime.now(UTC)
    db.add(
        CareTeamMembershipModel(
            patient_id=patient.id,
            user_id=user.id,
            institution_id=INSTITUTION,
            team_code="team",
            care_role="assistente",
            capabilities=capabilities,
            purpose="treatment",
            starts_at=now - timedelta(days=1),
            revoked_at=now if revoked else None,
            granted_by_user_id=granter.id,
        )
    )


def test_patient_scope_matches_object_check_exactly(scoped_session: Session) -> None:
    db = scoped_session
    granter = _user(db, "scope-granter@example.test", [])
    user = _user(db, "scope-user@example.test", ["patient.read"])
    exact = _patient(db, "Sintético exato")
    superstring = _patient(db, "Sintético superstring")
    prefixed = _patient(db, "Sintético prefixado")
    scalar = _patient(db, "Sintético escalar")
    empty = _patient(db, "Sintético vazio")
    revoked = _patient(db, "Sintético revogado")
    episode = _patient(db, "Sintético episódio")

    _team(db, exact, user, granter, ["patient.read"])
    _team(db, superstring, user, granter, ["patient.read.extra"])
    _team(db, prefixed, user, granter, ["xpatient.read"])
    _team(db, scalar, user, granter, "patient.read")  # JSON escalar, não array
    _team(db, empty, user, granter, [])
    _team(db, revoked, user, granter, ["patient.read"], revoked=True)
    db.add(
        CareEpisodeAssignmentModel(
            episode_id="episode-1",
            patient_id=episode.id,
            user_id=user.id,
            institution_id=INSTITUTION,
            capabilities=["patient.read"],
            purpose="treatment",
            starts_at=datetime.now(UTC) - timedelta(days=1),
            granted_by_user_id=granter.id,
        )
    )
    db.flush()

    service = ObjectAuthorizationService(db)
    candidates = [exact, superstring, prefixed, scalar, empty, revoked, episode]
    listed = set(
        db.scalars(
            select(PatientModel.id).where(
                PatientModel.institution_id == INSTITUTION,
                service.patient_scope(user),
            )
        )
    )
    by_object = {
        patient.id
        for patient in candidates
        if service.can_access_patient(user, patient, record_break_glass_object=False)
    }

    assert listed == by_object == {exact.id, episode.id}
