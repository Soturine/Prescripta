from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    BreakGlassAccessModel,
    CareEpisodeAssignmentModel,
    CareTeamMembershipModel,
    PatientAccessGrantModel,
    PatientModel,
    UserModel,
)
from app.schemas.access_schema import (
    BreakGlassCreate,
    BreakGlassReview,
    CareEpisodeAssignmentCreate,
    CareTeamMembershipCreate,
    PatientAccessGrantCreate,
)
from app.services.object_authorization import ObjectAuthorizationService


class ClinicalAccessError(ValueError):
    pass


class ClinicalAccessService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_grant(
        self,
        patient_id: int,
        payload: PatientAccessGrantCreate,
        grantor: UserModel,
    ) -> PatientAccessGrantModel:
        patient, target = self._patient_and_user(patient_id, payload.user_id, grantor)
        self._validate_capability_and_purpose(target, payload.capability, payload.purpose)
        starts_at = self._aware(payload.starts_at) or datetime.now(UTC)
        expires_at = self._aware(payload.expires_at)
        if expires_at is not None and expires_at <= starts_at:
            raise ClinicalAccessError("A expiração deve ocorrer após o início do grant.")
        grant = self.db.scalar(
            select(PatientAccessGrantModel).where(
                PatientAccessGrantModel.patient_id == patient.id,
                PatientAccessGrantModel.user_id == target.id,
                PatientAccessGrantModel.permission == payload.capability,
            )
        )
        if grant is not None and grant.revoked_at is None and grant.active:
            raise ClinicalAccessError("Já existe grant ativo para essa capacidade.")
        values = dict(
            patient_id=patient.id,
            user_id=target.id,
            institution_id=patient.institution_id,
            permission=payload.capability,
            capability=payload.capability,
            purpose=payload.purpose,
            reason=payload.reason,
            granted_by_user_id=grantor.id,
            starts_at=starts_at,
            expires_at=expires_at,
            care_episode_id=payload.care_episode_id,
            active=True,
            status="active",
        )
        if grant is None:
            grant = PatientAccessGrantModel(**values)
            self.db.add(grant)
        else:
            for field, value in values.items():
                setattr(grant, field, value)
            grant.revoked_at = None
            grant.revoked_by_user_id = None
            grant.revocation_reason = None
        self.db.commit()
        self.db.refresh(grant)
        return grant

    def revoke_grant(
        self,
        grant_id: int,
        *,
        reason: str,
        actor: UserModel,
    ) -> PatientAccessGrantModel:
        grant = self.db.get(PatientAccessGrantModel, grant_id)
        if grant is None or grant.institution_id != actor.institution_id:
            raise ClinicalAccessError("Grant não encontrado.")
        if grant.revoked_at is None:
            grant.revoked_at = datetime.now(UTC)
            grant.revoked_by_user_id = actor.id
            grant.revocation_reason = reason
            grant.active = False
            grant.status = "revoked"
            self.db.commit()
            self.db.refresh(grant)
        return grant

    def create_team_membership(
        self,
        patient_id: int,
        payload: CareTeamMembershipCreate,
        grantor: UserModel,
    ) -> CareTeamMembershipModel:
        patient, target = self._patient_and_user(patient_id, payload.user_id, grantor)
        for capability in payload.capabilities:
            self._validate_capability_and_purpose(target, capability, payload.purpose)
        starts_at = self._aware(payload.starts_at) or datetime.now(UTC)
        expires_at = self._aware(payload.expires_at)
        if expires_at is not None and expires_at <= starts_at:
            raise ClinicalAccessError("A expiração deve ocorrer após o início do vínculo.")
        membership = CareTeamMembershipModel(
            patient_id=patient.id,
            user_id=target.id,
            institution_id=patient.institution_id,
            team_code=payload.team_code,
            care_role=payload.care_role,
            capabilities=sorted(set(payload.capabilities)),
            purpose=payload.purpose,
            starts_at=starts_at,
            expires_at=expires_at,
            granted_by_user_id=grantor.id,
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def create_episode_assignment(
        self,
        patient_id: int,
        payload: CareEpisodeAssignmentCreate,
        grantor: UserModel,
    ) -> CareEpisodeAssignmentModel:
        patient, target = self._patient_and_user(patient_id, payload.user_id, grantor)
        for capability in payload.capabilities:
            self._validate_capability_and_purpose(target, capability, payload.purpose)
        starts_at = self._aware(payload.starts_at) or datetime.now(UTC)
        expires_at = self._aware(payload.expires_at)
        if expires_at is not None and expires_at <= starts_at:
            raise ClinicalAccessError("A expiração deve ocorrer após o início do episódio.")
        assignment = self.db.scalar(
            select(CareEpisodeAssignmentModel).where(
                CareEpisodeAssignmentModel.episode_id == payload.episode_id,
                CareEpisodeAssignmentModel.user_id == target.id,
            )
        )
        if assignment is not None and assignment.revoked_at is None:
            raise ClinicalAccessError("Profissional já atribuído ao episódio.")
        values = dict(
            episode_id=payload.episode_id,
            patient_id=patient.id,
            user_id=target.id,
            institution_id=patient.institution_id,
            capabilities=sorted(set(payload.capabilities)),
            purpose=payload.purpose,
            starts_at=starts_at,
            expires_at=expires_at,
            revoked_at=None,
            granted_by_user_id=grantor.id,
        )
        if assignment is None:
            assignment = CareEpisodeAssignmentModel(**values)
            self.db.add(assignment)
        else:
            for field, value in values.items():
                setattr(assignment, field, value)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def revoke_relationship(
        self,
        model: type[CareTeamMembershipModel] | type[CareEpisodeAssignmentModel],
        relationship_id: int,
        *,
        actor: UserModel,
    ) -> CareTeamMembershipModel | CareEpisodeAssignmentModel:
        relationship = self.db.get(model, relationship_id)
        if relationship is None or relationship.institution_id != actor.institution_id:
            raise ClinicalAccessError("Vínculo assistencial não encontrado.")
        if relationship.revoked_at is None:
            relationship.revoked_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(relationship)
        return relationship

    def list_grants(self, patient_id: int, actor: UserModel) -> list[PatientAccessGrantModel]:
        self._patient_for_manager(patient_id, actor)
        return list(
            self.db.scalars(
                select(PatientAccessGrantModel)
                .where(PatientAccessGrantModel.patient_id == patient_id)
                .order_by(PatientAccessGrantModel.created_at.desc())
            )
        )

    def list_team(
        self, patient_id: int, actor: UserModel
    ) -> list[CareTeamMembershipModel]:
        self._patient_for_manager(patient_id, actor)
        return list(
            self.db.scalars(
                select(CareTeamMembershipModel)
                .where(CareTeamMembershipModel.patient_id == patient_id)
                .order_by(CareTeamMembershipModel.created_at.desc())
            )
        )

    def list_break_glass(
        self, actor: UserModel, review_status: str | None = None
    ) -> list[BreakGlassAccessModel]:
        statement = select(BreakGlassAccessModel).where(
            BreakGlassAccessModel.institution_id == actor.institution_id
        )
        if review_status:
            statement = statement.where(
                BreakGlassAccessModel.review_status == review_status
            )
        return list(self.db.scalars(statement.order_by(BreakGlassAccessModel.created_at.desc())))

    def invoke_break_glass(
        self,
        patient_id: int,
        payload: BreakGlassCreate,
        user: UserModel,
    ) -> BreakGlassAccessModel:
        patient = self.db.get(PatientModel, patient_id)
        if patient is None or patient.institution_id != user.institution_id:
            raise ClinicalAccessError("Paciente não encontrado.")
        if "break_glass.invoke" not in set(user.capabilities or []):
            raise ClinicalAccessError("Profissional sem capacidade de break-glass.")
        self._validate_capability_and_purpose(user, payload.capability, payload.purpose)
        existing = self.db.scalar(
            select(BreakGlassAccessModel).where(
                BreakGlassAccessModel.user_id == user.id,
                BreakGlassAccessModel.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is not None:
            if existing.patient_id != patient_id or existing.capability != payload.capability:
                raise ClinicalAccessError("Chave idempotente reutilizada com outro escopo.")
            return existing
        now = datetime.now(UTC)
        access = BreakGlassAccessModel(
            patient_id=patient.id,
            user_id=user.id,
            institution_id=user.institution_id,
            capability=payload.capability,
            purpose=payload.purpose,
            reason=payload.reason,
            started_at=now,
            expires_at=now + timedelta(minutes=payload.duration_minutes),
            idempotency_key=payload.idempotency_key,
            review_status="pending_review",
            status="active",
        )
        self.db.add(access)
        self.db.commit()
        self.db.refresh(access)
        return access

    def end_break_glass(
        self,
        access_id: int,
        actor: UserModel,
    ) -> BreakGlassAccessModel:
        access = self.db.get(BreakGlassAccessModel, access_id)
        can_manage = "access.manage" in set(actor.capabilities or [])
        if (
            access is None
            or access.institution_id != actor.institution_id
            or (access.user_id != actor.id and not can_manage)
        ):
            raise ClinicalAccessError("Acesso emergencial não encontrado.")
        if access.ended_at is None:
            access.ended_at = datetime.now(UTC)
            access.ended_by_user_id = actor.id
            access.status = "ended"
            self.db.commit()
            self.db.refresh(access)
        return access

    def review_break_glass(
        self,
        access_id: int,
        payload: BreakGlassReview,
        reviewer: UserModel,
    ) -> BreakGlassAccessModel:
        access = self.db.get(BreakGlassAccessModel, access_id)
        if access is None or access.institution_id != reviewer.institution_id:
            raise ClinicalAccessError("Acesso emergencial não encontrado.")
        if access.user_id == reviewer.id:
            raise ClinicalAccessError("A revisão deve ser independente do solicitante.")
        access.review_status = payload.decision
        access.review_notes = payload.notes
        access.reviewed_at = datetime.now(UTC)
        access.reviewed_by_user_id = reviewer.id
        self.db.commit()
        self.db.refresh(access)
        return access

    def _patient_and_user(
        self,
        patient_id: int,
        user_id: int,
        actor: UserModel,
    ) -> tuple[PatientModel, UserModel]:
        patient = self.db.get(PatientModel, patient_id)
        target = self.db.get(UserModel, user_id)
        if (
            patient is None
            or target is None
            or patient.institution_id != actor.institution_id
            or target.institution_id != actor.institution_id
        ):
            raise ClinicalAccessError("Paciente ou profissional não encontrado.")
        return patient, target

    def _patient_for_manager(self, patient_id: int, actor: UserModel) -> PatientModel:
        patient = self.db.get(PatientModel, patient_id)
        if patient is None or patient.institution_id != actor.institution_id:
            raise ClinicalAccessError("Paciente não encontrado.")
        return patient

    @staticmethod
    def _validate_capability_and_purpose(
        user: UserModel,
        capability: str,
        purpose: str,
    ) -> None:
        if purpose not in ObjectAuthorizationService.VALID_PURPOSES:
            raise ClinicalAccessError("Propósito de acesso inválido.")
        if capability not in set(user.capabilities or []):
            raise ClinicalAccessError("O grant não pode ampliar a capacidade profissional.")

    @staticmethod
    def _aware(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
