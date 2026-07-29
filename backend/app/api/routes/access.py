from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_capabilities
from app.database.models import CareEpisodeAssignmentModel, CareTeamMembershipModel, UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.access_schema import (
    AccessRevokeRequest,
    BreakGlassCreate,
    BreakGlassRead,
    BreakGlassReview,
    CareEpisodeAssignmentCreate,
    CareEpisodeAssignmentRead,
    CareTeamMembershipCreate,
    CareTeamMembershipRead,
    PatientAccessGrantCreate,
    PatientAccessGrantRead,
)
from app.services.audit_service import AuditService
from app.services.clinical_access_service import ClinicalAccessError, ClinicalAccessService

router = APIRouter(prefix="/access", tags=["clinical-access"])
DbSession = Annotated[Session, Depends(get_db)]
AccessManager = Annotated[
    UserModel, Depends(require_capabilities(Capability.ACCESS_MANAGE))
]
BreakGlassUser = Annotated[
    UserModel, Depends(require_capabilities(Capability.BREAK_GLASS_INVOKE))
]
SafetyReviewer = Annotated[
    UserModel, Depends(require_capabilities(Capability.SAFETY_REVIEW))
]


def _unprocessable(exc: ClinicalAccessError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))


@router.post(
    "/patients/{patient_id}/grants",
    response_model=PatientAccessGrantRead,
    status_code=status.HTTP_201_CREATED,
)
def create_grant(
    patient_id: int,
    payload: PatientAccessGrantCreate,
    db: DbSession,
    current_user: AccessManager,
) -> PatientAccessGrantRead:
    try:
        grant = ClinicalAccessService(db).create_grant(patient_id, payload, current_user)
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc
    AuditService(db).record_action(
        user=current_user,
        action="patient_access.grant",
        resource_type="patient_access_grant",
        resource_id=str(grant.id),
        details={"capability": grant.capability, "purpose": grant.purpose},
    )
    return grant


@router.get(
    "/patients/{patient_id}/grants",
    response_model=list[PatientAccessGrantRead],
)
def list_grants(
    patient_id: int,
    db: DbSession,
    current_user: AccessManager,
) -> list[PatientAccessGrantRead]:
    try:
        return ClinicalAccessService(db).list_grants(patient_id, current_user)
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc


@router.post("/grants/{grant_id}/revoke", response_model=PatientAccessGrantRead)
def revoke_grant(
    grant_id: int,
    payload: AccessRevokeRequest,
    db: DbSession,
    current_user: AccessManager,
) -> PatientAccessGrantRead:
    try:
        grant = ClinicalAccessService(db).revoke_grant(
            grant_id, reason=payload.reason, actor=current_user
        )
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc
    AuditService(db).record_action(
        user=current_user,
        action="patient_access.revoke",
        resource_type="patient_access_grant",
        resource_id=str(grant.id),
        details={"capability": grant.capability, "purpose": grant.purpose},
    )
    return grant


@router.post(
    "/patients/{patient_id}/care-team",
    response_model=CareTeamMembershipRead,
    status_code=status.HTTP_201_CREATED,
)
def create_care_team_membership(
    patient_id: int,
    payload: CareTeamMembershipCreate,
    db: DbSession,
    current_user: AccessManager,
) -> CareTeamMembershipRead:
    try:
        membership = ClinicalAccessService(db).create_team_membership(
            patient_id, payload, current_user
        )
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc
    AuditService(db).record_action(
        user=current_user,
        action="care_team.assign",
        resource_type="care_team_membership",
        resource_id=str(membership.id),
        details={"purpose": membership.purpose, "capabilities": membership.capabilities},
    )
    return membership


@router.get(
    "/patients/{patient_id}/care-team",
    response_model=list[CareTeamMembershipRead],
)
def list_care_team(
    patient_id: int,
    db: DbSession,
    current_user: AccessManager,
) -> list[CareTeamMembershipRead]:
    try:
        return ClinicalAccessService(db).list_team(patient_id, current_user)
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc


@router.post("/care-team/{membership_id}/revoke", response_model=CareTeamMembershipRead)
def revoke_care_team_membership(
    membership_id: int,
    payload: AccessRevokeRequest,
    db: DbSession,
    current_user: AccessManager,
) -> CareTeamMembershipRead:
    try:
        membership = ClinicalAccessService(db).revoke_relationship(
            CareTeamMembershipModel, membership_id, actor=current_user
        )
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc
    AuditService(db).record_action(
        user=current_user,
        action="care_team.revoke",
        resource_type="care_team_membership",
        resource_id=str(membership.id),
        details={"reason": payload.reason},
    )
    return membership


@router.post(
    "/patients/{patient_id}/care-episodes",
    response_model=CareEpisodeAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_care_episode_assignment(
    patient_id: int,
    payload: CareEpisodeAssignmentCreate,
    db: DbSession,
    current_user: AccessManager,
) -> CareEpisodeAssignmentRead:
    try:
        assignment = ClinicalAccessService(db).create_episode_assignment(
            patient_id, payload, current_user
        )
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc
    AuditService(db).record_action(
        user=current_user,
        action="care_episode.assign",
        resource_type="care_episode_assignment",
        resource_id=str(assignment.id),
        details={"episode_id": assignment.episode_id, "purpose": assignment.purpose},
    )
    return assignment


@router.post(
    "/care-episodes/{assignment_id}/revoke",
    response_model=CareEpisodeAssignmentRead,
)
def revoke_care_episode_assignment(
    assignment_id: int,
    payload: AccessRevokeRequest,
    db: DbSession,
    current_user: AccessManager,
) -> CareEpisodeAssignmentRead:
    try:
        assignment = ClinicalAccessService(db).revoke_relationship(
            CareEpisodeAssignmentModel, assignment_id, actor=current_user
        )
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc
    AuditService(db).record_action(
        user=current_user,
        action="care_episode.revoke",
        resource_type="care_episode_assignment",
        resource_id=str(assignment.id),
        details={"reason": payload.reason},
    )
    return assignment


@router.post(
    "/patients/{patient_id}/break-glass",
    response_model=BreakGlassRead,
    status_code=status.HTTP_201_CREATED,
)
def invoke_break_glass(
    patient_id: int,
    payload: BreakGlassCreate,
    db: DbSession,
    current_user: BreakGlassUser,
) -> BreakGlassRead:
    try:
        access = ClinicalAccessService(db).invoke_break_glass(
            patient_id, payload, current_user
        )
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc
    AuditService(db).record_action(
        user=current_user,
        action="break_glass.invoke",
        resource_type="break_glass_access",
        resource_id=str(access.id),
        details={
            "capability": access.capability,
            "purpose": access.purpose,
            "expires_at": access.expires_at.isoformat(),
        },
    )
    return access


@router.get("/break-glass", response_model=list[BreakGlassRead])
def list_break_glass(
    db: DbSession,
    current_user: SafetyReviewer,
    review_status: str | None = None,
) -> list[BreakGlassRead]:
    return ClinicalAccessService(db).list_break_glass(current_user, review_status)


@router.post("/break-glass/{access_id}/end", response_model=BreakGlassRead)
def end_break_glass(
    access_id: int,
    db: DbSession,
    current_user: BreakGlassUser,
) -> BreakGlassRead:
    try:
        access = ClinicalAccessService(db).end_break_glass(access_id, current_user)
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc
    AuditService(db).record_action(
        user=current_user,
        action="break_glass.end",
        resource_type="break_glass_access",
        resource_id=str(access.id),
        details={"review_status": access.review_status},
    )
    return access


@router.post("/break-glass/{access_id}/review", response_model=BreakGlassRead)
def review_break_glass(
    access_id: int,
    payload: BreakGlassReview,
    db: DbSession,
    current_user: SafetyReviewer,
) -> BreakGlassRead:
    try:
        access = ClinicalAccessService(db).review_break_glass(
            access_id, payload, current_user
        )
    except ClinicalAccessError as exc:
        raise _unprocessable(exc) from exc
    AuditService(db).record_action(
        user=current_user,
        action="break_glass.review",
        resource_type="break_glass_access",
        resource_id=str(access.id),
        details={"review_status": access.review_status},
    )
    return access
