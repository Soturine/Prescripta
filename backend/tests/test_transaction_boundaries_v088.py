from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.database.models import (
    AuditEventModel,
    BreakGlassAccessModel,
    PatientAccessGrantModel,
    PatientModel,
)
from app.domain.user import Capability, UserRole
from app.schemas.access_schema import BreakGlassCreate, PatientAccessGrantCreate
from app.services.audit_service import AuditService
from app.services.clinical_access_service import ClinicalAccessService


def test_services_and_repositories_do_not_own_commits():
    app_root = Path(__file__).parents[1] / "app"
    checked_roots = (
        app_root / "services",
        app_root / "repositories",
        app_root / "integrations",
        app_root / "reports",
    )
    offenders = []
    for root in checked_roots:
        for path in root.rglob("*.py"):
            if ".commit()" in path.read_text(encoding="utf-8"):
                offenders.append(path.relative_to(app_root).as_posix())
    assert offenders == []


def test_grant_and_audit_are_rolled_back_as_one_operation(
    create_test_user,
    db_session: Session,
):
    admin = create_test_user(email="admin@uow-v088.local", role=UserRole.ADMIN)
    doctor = create_test_user(
        email="doctor@uow-v088.local",
        password="Doctor@12345",
        role=UserRole.MEDICO,
    )
    doctor.credential_expires_at = datetime.now(UTC) + timedelta(days=30)
    patient = PatientModel(
        institution_id="demo",
        created_by_user_id=admin.id,
        name="Paciente transacional demo",
        age=41,
        weight_kg=70,
    )
    db_session.add(patient)
    db_session.commit()

    try:
        grant = ClinicalAccessService(db_session).create_grant(
            patient.id,
            PatientAccessGrantCreate(
                user_id=doctor.id,
                capability=Capability.PATIENT_READ.value,
                purpose="treatment",
                reason="Vínculo transacional demonstrativo para rollback.",
            ),
            admin,
        )
        AuditService(db_session).record_action(
            user=admin,
            action="patient_access.grant",
            resource_type="patient_access_grant",
            resource_id=str(grant.id),
            status="created",
            details={"capability": grant.capability},
        )
        raise RuntimeError("falha posterior simulada")
    except RuntimeError:
        db_session.rollback()

    assert db_session.query(PatientAccessGrantModel).count() == 0
    assert db_session.query(AuditEventModel).filter_by(
        action="patient_access.grant"
    ).count() == 0


def test_break_glass_flush_does_not_survive_caller_rollback(
    create_test_user,
    db_session: Session,
):
    admin = create_test_user(email="admin@break-uow.local", role=UserRole.ADMIN)
    doctor = create_test_user(
        email="doctor@break-uow.local",
        password="Doctor@12345",
        role=UserRole.MEDICO,
    )
    patient = PatientModel(
        institution_id="demo",
        created_by_user_id=admin.id,
        name="Paciente break-glass transacional",
        age=58,
        weight_kg=80,
    )
    db_session.add(patient)
    db_session.commit()

    access = ClinicalAccessService(db_session).invoke_break_glass(
        patient.id,
        BreakGlassCreate(
            capability=Capability.PATIENT_READ.value,
            purpose="treatment",
            reason="Emergência demonstrativa para validar rollback integral.",
            duration_minutes=15,
            idempotency_key="break-uow-v088",
        ),
        doctor,
    )
    assert access.id is not None
    db_session.rollback()
    assert db_session.query(BreakGlassAccessModel).count() == 0


def test_service_changes_persist_only_after_the_application_boundary_commits(
    create_test_user,
    db_session: Session,
):
    admin = create_test_user(email="admin@commit-uow.local", role=UserRole.ADMIN)
    doctor = create_test_user(
        email="doctor@commit-uow.local",
        password="Doctor@12345",
        role=UserRole.MEDICO,
    )
    patient = PatientModel(
        institution_id="demo",
        created_by_user_id=admin.id,
        name="Paciente commit único",
        age=39,
        weight_kg=68,
    )
    db_session.add(patient)
    db_session.commit()

    grant = ClinicalAccessService(db_session).create_grant(
        patient.id,
        PatientAccessGrantCreate(
            user_id=doctor.id,
            capability=Capability.PATIENT_READ.value,
            purpose="treatment",
            reason="Vínculo demonstrativo confirmado pelo command boundary.",
        ),
        admin,
    )
    AuditService(db_session).record_action(
        user=admin,
        action="patient_access.grant",
        resource_type="patient_access_grant",
        resource_id=str(grant.id),
        status="created",
        details={"capability": grant.capability},
    )
    db_session.commit()
    db_session.expire_all()

    assert db_session.get(PatientAccessGrantModel, grant.id) is not None
    assert db_session.query(AuditEventModel).filter_by(
        action="patient_access.grant"
    ).count() == 1
