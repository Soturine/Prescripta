import pytest

from app.database.models import PrescriptionAuditModel
from app.domain.user import UserRole
from app.services.decision_override_service import (
    DecisionOverrideError,
    DecisionOverrideService,
)


def _audit(db_session, *, user_id: int, severity: str = "moderado"):
    audit = PrescriptionAuditModel(
        user_id=user_id,
        patient_name="Paciente pseudonimizado",
        medication_name="Medicamento demo",
        route="oral",
        status="revisao_necessaria",
        risk_level=severity,
        clinical_decision={
            "highest_severity": severity,
            "findings": [],
            "override_policy": {
                "allowed": True,
                "reason_required": True,
                "second_reviewer_role": "medico",
            },
        },
    )
    db_session.add(audit)
    db_session.commit()
    return audit


def test_override_requires_independent_second_review(
    db_session, create_test_user
) -> None:
    requester = create_test_user(
        email="requester@override.local", role=UserRole.MEDICO
    )
    reviewer = create_test_user(email="reviewer@override.local", role=UserRole.MEDICO)
    audit = _audit(db_session, user_id=requester.id)
    service = DecisionOverrideService(db_session)

    override = service.request(
        audit=audit,
        requester=requester,
        reason="Justificativa clínica documentada para segunda revisão.",
    )
    with pytest.raises(DecisionOverrideError, match="segundo revisor"):
        service.review(
            override=override,
            reviewer=requester,
            decision="approved",
            note="Revisão independente documentada.",
            required_role="medico",
        )
    reviewed = service.review(
        override=override,
        reviewer=reviewer,
        decision="approved",
        note="Revisão independente documentada.",
        required_role="medico",
    )
    db_session.commit()

    assert reviewed.status == "approved"
    assert reviewed.reviewed_by_user_id == reviewer.id
    assert audit.clinical_decision["highest_severity"] == "moderado"


def test_critical_decision_cannot_be_overridden(db_session, create_test_user) -> None:
    requester = create_test_user(
        email="critical@override.local", role=UserRole.MEDICO
    )
    audit = _audit(db_session, user_id=requester.id, severity="critico")

    with pytest.raises(DecisionOverrideError, match="não admite override"):
        DecisionOverrideService(db_session).request(
            audit=audit,
            requester=requester,
            reason="Justificativa que nunca deve reduzir severidade crítica.",
        )
