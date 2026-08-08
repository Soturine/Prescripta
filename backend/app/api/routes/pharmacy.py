from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.pharmacy_schema import (
    MedicationFormulationReviewCreate,
    MedicationFormulationReviewRead,
    MedicationReconciliationCreate,
    MedicationReconciliationItemRead,
    MedicationReconciliationRead,
    PharmacyInterventionCreate,
    PharmacyInterventionDecision,
    PharmacyInterventionEventRead,
    PharmacyInterventionRead,
    PharmacyInterventionResolve,
    ReconciliationItemDecision,
)
from app.services.pharmacy_workflow_service import (
    PharmacyWorkflowConflict,
    PharmacyWorkflowError,
    PharmacyWorkflowService,
)

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])
DbSession = Annotated[Session, Depends(get_db)]
PharmacyReader = Annotated[
    UserModel,
    Depends(
        require_any_capability(
            Capability.PHARMACY_INTERVENTION_READ,
            Capability.PHARMACY_INTERVENTION_WRITE,
            Capability.PHARMACY_INTERVENTION_DECIDE,
        )
    ),
]
Pharmacist = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.PHARMACY_INTERVENTION_WRITE)),
]
DecisionActor = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.PHARMACY_INTERVENTION_DECIDE)),
]
ReconciliationActor = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.PHARMACY_RECONCILIATION_WRITE)),
]
FormulationReviewer = Annotated[
    UserModel,
    Depends(require_any_capability(Capability.PHARMACY_FORMULATION_REVIEW)),
]


def _workflow_http_error(exc: PharmacyWorkflowError) -> HTTPException:
    code = (
        status.HTTP_409_CONFLICT
        if isinstance(exc, PharmacyWorkflowConflict)
        else status.HTTP_422_UNPROCESSABLE_CONTENT
    )
    return HTTPException(status_code=code, detail=str(exc))


@router.post(
    "/interventions",
    response_model=PharmacyInterventionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_intervention(
    payload: PharmacyInterventionCreate,
    db: DbSession,
    current_user: Pharmacist,
) -> PharmacyInterventionRead:
    try:
        return PharmacyWorkflowService(db).create_intervention(payload, current_user)
    except PharmacyWorkflowError as exc:
        raise _workflow_http_error(exc) from exc


@router.get("/interventions", response_model=list[PharmacyInterventionRead])
def list_interventions(
    db: DbSession,
    current_user: PharmacyReader,
    workflow_status: Annotated[str | None, Query(alias="status")] = None,
    priority: str | None = None,
) -> list[PharmacyInterventionRead]:
    return PharmacyWorkflowService(db).list_interventions(
        current_user,
        status=workflow_status,
        priority=priority,
    )


@router.get(
    "/interventions/{intervention_id}/events",
    response_model=list[PharmacyInterventionEventRead],
)
def intervention_events(
    intervention_id: int,
    db: DbSession,
    current_user: PharmacyReader,
) -> list[PharmacyInterventionEventRead]:
    try:
        return PharmacyWorkflowService(db).events(intervention_id, current_user)
    except PharmacyWorkflowError as exc:
        raise _workflow_http_error(exc) from exc


@router.post(
    "/interventions/{intervention_id}/cosign",
    response_model=PharmacyInterventionRead,
)
def cosign_intervention(
    intervention_id: int,
    expected_version: int,
    db: DbSession,
    current_user: Pharmacist,
) -> PharmacyInterventionRead:
    try:
        return PharmacyWorkflowService(db).cosign(
            intervention_id,
            current_user,
            expected_version=expected_version,
        )
    except PharmacyWorkflowError as exc:
        raise _workflow_http_error(exc) from exc


@router.post(
    "/interventions/{intervention_id}/decision",
    response_model=PharmacyInterventionRead,
)
def decide_intervention(
    intervention_id: int,
    payload: PharmacyInterventionDecision,
    db: DbSession,
    current_user: DecisionActor,
) -> PharmacyInterventionRead:
    try:
        return PharmacyWorkflowService(db).decide(
            intervention_id,
            payload,
            current_user,
        )
    except PharmacyWorkflowError as exc:
        raise _workflow_http_error(exc) from exc


@router.post(
    "/interventions/{intervention_id}/resolve",
    response_model=PharmacyInterventionRead,
)
def resolve_intervention(
    intervention_id: int,
    payload: PharmacyInterventionResolve,
    db: DbSession,
    current_user: Pharmacist,
) -> PharmacyInterventionRead:
    try:
        return PharmacyWorkflowService(db).resolve(
            intervention_id,
            payload,
            current_user,
        )
    except PharmacyWorkflowError as exc:
        raise _workflow_http_error(exc) from exc


@router.post(
    "/reconciliations",
    response_model=MedicationReconciliationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_reconciliation(
    payload: MedicationReconciliationCreate,
    db: DbSession,
    current_user: ReconciliationActor,
) -> MedicationReconciliationRead:
    try:
        reconciliation = PharmacyWorkflowService(db).create_reconciliation(
            payload,
            current_user,
        )
        return MedicationReconciliationRead.model_validate(
            PharmacyWorkflowService(db).reconciliation(
                reconciliation.id,
                current_user,
            )
        )
    except PharmacyWorkflowError as exc:
        raise _workflow_http_error(exc) from exc


@router.get(
    "/reconciliations/{reconciliation_id}",
    response_model=MedicationReconciliationRead,
)
def reconciliation_detail(
    reconciliation_id: int,
    db: DbSession,
    current_user: PharmacyReader,
) -> MedicationReconciliationRead:
    try:
        detail = PharmacyWorkflowService(db).reconciliation(
            reconciliation_id,
            current_user,
        )
        return MedicationReconciliationRead.model_validate(detail)
    except PharmacyWorkflowError as exc:
        raise _workflow_http_error(exc) from exc


@router.post(
    "/reconciliation-items/{item_id}/decision",
    response_model=MedicationReconciliationItemRead,
)
def decide_reconciliation_item(
    item_id: int,
    payload: ReconciliationItemDecision,
    db: DbSession,
    current_user: ReconciliationActor,
) -> MedicationReconciliationItemRead:
    try:
        return PharmacyWorkflowService(db).decide_reconciliation_item(
            item_id,
            payload,
            current_user,
        )
    except PharmacyWorkflowError as exc:
        raise _workflow_http_error(exc) from exc


@router.post(
    "/formulation-reviews",
    response_model=MedicationFormulationReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_formulation_review(
    payload: MedicationFormulationReviewCreate,
    db: DbSession,
    current_user: FormulationReviewer,
) -> MedicationFormulationReviewRead:
    try:
        return PharmacyWorkflowService(db).create_formulation_review(
            payload,
            current_user,
        )
    except PharmacyWorkflowError as exc:
        raise _workflow_http_error(exc) from exc
