from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, exists, false, or_, select
from sqlalchemy.orm import Session

from app.database.models import (
    AuditEventModel,
    BreakGlassAccessModel,
    CareEpisodeAssignmentModel,
    CareTeamMembershipModel,
    PatientAccessGrantModel,
    PatientModel,
    UserModel,
)


class ObjectAuthorizationService:
    """Exige capacidade profissional e vínculo assistencial explícito e vigente."""

    VALID_PURPOSES = {"treatment", "care_coordination", "safety_review", "audit"}

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def has_capability(user: UserModel, capability: str) -> bool:
        return capability in set(user.capabilities or [])

    def can_access_patient(
        self,
        user: UserModel,
        patient: PatientModel | int,
        *,
        capability: str = "patient.read",
        purpose: str = "treatment",
        record_break_glass_object: bool = True,
    ) -> bool:
        if purpose not in self.VALID_PURPOSES or not self.has_capability(user, capability):
            return False
        patient_record = (
            self.db.get(PatientModel, patient) if isinstance(patient, int) else patient
        )
        if (
            patient_record is None
            or not user.institution_id
            or patient_record.institution_id != user.institution_id
        ):
            return False
        now = datetime.now(UTC)
        if self._has_grant(user, patient_record.id, capability, purpose, now):
            return True
        if self._has_team_membership(user, patient_record.id, capability, purpose, now):
            return True
        if self._has_episode_assignment(user, patient_record.id, capability, purpose, now):
            return True
        break_glass = self._active_break_glass(
            user, patient_record.id, capability, purpose, now
        )
        if break_glass is None:
            return False
        if record_break_glass_object:
            self._record_break_glass_object(break_glass, patient_record.id, capability, now)
        return True

    def patient_scope(
        self,
        user: UserModel,
        *,
        capability: str = "patient.read",
        purpose: str = "treatment",
    ):
        if purpose not in self.VALID_PURPOSES or not self.has_capability(user, capability):
            return false()
        now = datetime.now(UTC)
        same_institution = PatientModel.institution_id == user.institution_id
        grants = select(PatientAccessGrantModel.patient_id).where(
            PatientAccessGrantModel.user_id == user.id,
            PatientAccessGrantModel.institution_id == user.institution_id,
            PatientAccessGrantModel.capability == capability,
            PatientAccessGrantModel.purpose == purpose,
            PatientAccessGrantModel.active.is_(True),
            PatientAccessGrantModel.status == "active",
            PatientAccessGrantModel.revoked_at.is_(None),
            PatientAccessGrantModel.starts_at <= now,
            or_(
                PatientAccessGrantModel.expires_at.is_(None),
                PatientAccessGrantModel.expires_at > now,
            ),
        )
        teams = select(CareTeamMembershipModel.patient_id).where(
            CareTeamMembershipModel.user_id == user.id,
            CareTeamMembershipModel.institution_id == user.institution_id,
            CareTeamMembershipModel.purpose == purpose,
            CareTeamMembershipModel.capabilities.contains(capability),
            CareTeamMembershipModel.revoked_at.is_(None),
            CareTeamMembershipModel.starts_at <= now,
            or_(
                CareTeamMembershipModel.expires_at.is_(None),
                CareTeamMembershipModel.expires_at > now,
            ),
        )
        episodes = select(CareEpisodeAssignmentModel.patient_id).where(
            CareEpisodeAssignmentModel.user_id == user.id,
            CareEpisodeAssignmentModel.institution_id == user.institution_id,
            CareEpisodeAssignmentModel.purpose == purpose,
            CareEpisodeAssignmentModel.capabilities.contains(capability),
            CareEpisodeAssignmentModel.revoked_at.is_(None),
            CareEpisodeAssignmentModel.starts_at <= now,
            or_(
                CareEpisodeAssignmentModel.expires_at.is_(None),
                CareEpisodeAssignmentModel.expires_at > now,
            ),
        )
        break_glass = select(BreakGlassAccessModel.patient_id).where(
            BreakGlassAccessModel.user_id == user.id,
            BreakGlassAccessModel.institution_id == user.institution_id,
            BreakGlassAccessModel.capability == capability,
            BreakGlassAccessModel.purpose == purpose,
            BreakGlassAccessModel.status == "active",
            BreakGlassAccessModel.ended_at.is_(None),
            BreakGlassAccessModel.started_at <= now,
            BreakGlassAccessModel.expires_at > now,
        )
        return and_(
            same_institution,
            or_(
                PatientModel.id.in_(grants),
                PatientModel.id.in_(teams),
                PatientModel.id.in_(episodes),
                PatientModel.id.in_(break_glass),
            ),
        )

    def record_denied(
        self,
        user: UserModel,
        *,
        resource_type: str,
        resource_id: str,
        capability: str = "patient.read",
        purpose: str = "treatment",
    ) -> None:
        event_key = (resource_type, resource_id, capability, purpose)
        recorded = self.db.info.setdefault("authorization_denials", set())
        if event_key in recorded or len(recorded) >= 20:
            return
        recorded.add(event_key)
        event = AuditEventModel(
            user_id=user.id,
            user_role=user.role,
            action="authorization.denied",
            resource_type=resource_type,
            resource_id=resource_id,
            status="denied",
            details={
                "capability": capability,
                "purpose": purpose,
                "reason": "active_relationship_required",
                "correlation_id": self.db.info.get("correlation_id"),
            },
        )
        self.db.add(event)

    def require_patient(
        self,
        user: UserModel,
        patient_id: int,
        *,
        capability: str = "patient.read",
        purpose: str = "treatment",
    ) -> bool:
        allowed = self.can_access_patient(
            user,
            patient_id,
            capability=capability,
            purpose=purpose,
        )
        if not allowed:
            self.record_denied(
                user,
                resource_type="patient",
                resource_id=str(patient_id),
                capability=capability,
                purpose=purpose,
            )
        return allowed

    def _has_grant(
        self,
        user: UserModel,
        patient_id: int,
        capability: str,
        purpose: str,
        now: datetime,
    ) -> bool:
        return bool(
            self.db.scalar(
                select(
                    exists().where(
                        PatientAccessGrantModel.patient_id == patient_id,
                        PatientAccessGrantModel.user_id == user.id,
                        PatientAccessGrantModel.institution_id == user.institution_id,
                        PatientAccessGrantModel.capability == capability,
                        PatientAccessGrantModel.purpose == purpose,
                        PatientAccessGrantModel.active.is_(True),
                        PatientAccessGrantModel.status == "active",
                        PatientAccessGrantModel.revoked_at.is_(None),
                        PatientAccessGrantModel.starts_at <= now,
                        or_(
                            PatientAccessGrantModel.expires_at.is_(None),
                            PatientAccessGrantModel.expires_at > now,
                        ),
                    )
                )
            )
        )

    def _has_team_membership(
        self,
        user: UserModel,
        patient_id: int,
        capability: str,
        purpose: str,
        now: datetime,
    ) -> bool:
        candidates = self.db.scalars(
            select(CareTeamMembershipModel).where(
                CareTeamMembershipModel.patient_id == patient_id,
                CareTeamMembershipModel.user_id == user.id,
                CareTeamMembershipModel.institution_id == user.institution_id,
                CareTeamMembershipModel.purpose == purpose,
                CareTeamMembershipModel.revoked_at.is_(None),
                CareTeamMembershipModel.starts_at <= now,
                or_(
                    CareTeamMembershipModel.expires_at.is_(None),
                    CareTeamMembershipModel.expires_at > now,
                ),
            )
        )
        return any(capability in set(item.capabilities or []) for item in candidates)

    def _has_episode_assignment(
        self,
        user: UserModel,
        patient_id: int,
        capability: str,
        purpose: str,
        now: datetime,
    ) -> bool:
        candidates = self.db.scalars(
            select(CareEpisodeAssignmentModel).where(
                CareEpisodeAssignmentModel.patient_id == patient_id,
                CareEpisodeAssignmentModel.user_id == user.id,
                CareEpisodeAssignmentModel.institution_id == user.institution_id,
                CareEpisodeAssignmentModel.purpose == purpose,
                CareEpisodeAssignmentModel.revoked_at.is_(None),
                CareEpisodeAssignmentModel.starts_at <= now,
                or_(
                    CareEpisodeAssignmentModel.expires_at.is_(None),
                    CareEpisodeAssignmentModel.expires_at > now,
                ),
            )
        )
        return any(capability in set(item.capabilities or []) for item in candidates)

    def _active_break_glass(
        self,
        user: UserModel,
        patient_id: int,
        capability: str,
        purpose: str,
        now: datetime,
    ) -> BreakGlassAccessModel | None:
        return self.db.scalar(
            select(BreakGlassAccessModel).where(
                BreakGlassAccessModel.patient_id == patient_id,
                BreakGlassAccessModel.user_id == user.id,
                BreakGlassAccessModel.institution_id == user.institution_id,
                BreakGlassAccessModel.capability == capability,
                BreakGlassAccessModel.purpose == purpose,
                BreakGlassAccessModel.status == "active",
                BreakGlassAccessModel.ended_at.is_(None),
                BreakGlassAccessModel.started_at <= now,
                BreakGlassAccessModel.expires_at > now,
            )
        )

    def _record_break_glass_object(
        self,
        access: BreakGlassAccessModel,
        patient_id: int,
        capability: str,
        now: datetime,
    ) -> None:
        accessed = list(access.objects_accessed or [])
        marker = {"type": "patient", "id": str(patient_id), "capability": capability}
        if not any(
            item.get("type") == marker["type"]
            and item.get("id") == marker["id"]
            and item.get("capability") == marker["capability"]
            for item in accessed
        ):
            accessed.append(marker | {"first_accessed_at": now.isoformat()})
            access.objects_accessed = accessed
            self.db.flush()
