from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_any_capability
from app.database.models import UserModel
from app.database.session import get_db
from app.domain.user import Capability
from app.schemas.omop_schema import (
    OmopCompatibilityRead,
    OmopEtlRunRead,
    OmopPreviewRequest,
)
from app.services.omop_adapter_service import OmopAdapterError, OmopAdapterService

router = APIRouter(prefix="/omop", tags=["omop"])
DbSession = Annotated[Session, Depends(get_db)]
Previewer = Annotated[
    UserModel, Depends(require_any_capability(Capability.OMOP_PREVIEW))
]
Exporter = Annotated[
    UserModel, Depends(require_any_capability(Capability.OMOP_EXPORT))
]


def _error(exc: OmopAdapterError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))


@router.post("/preview", response_model=OmopEtlRunRead, status_code=201)
def preview(
    payload: OmopPreviewRequest, db: DbSession, current_user: Previewer
) -> OmopEtlRunRead:
    try:
        return OmopAdapterService(db).execute(
            payload, current_user, persist_export=False
        )
    except OmopAdapterError as exc:
        raise _error(exc) from exc


@router.post("/exports", response_model=OmopEtlRunRead, status_code=201)
def export(
    payload: OmopPreviewRequest, db: DbSession, current_user: Exporter
) -> OmopEtlRunRead:
    try:
        return OmopAdapterService(db).execute(
            payload, current_user, persist_export=True
        )
    except OmopAdapterError as exc:
        raise _error(exc) from exc


@router.get("/runs", response_model=list[OmopEtlRunRead])
def list_runs(db: DbSession, current_user: Previewer) -> list[OmopEtlRunRead]:
    return OmopAdapterService(db).list_runs(current_user)


@router.get("/runs/{run_id}", response_model=OmopEtlRunRead)
def run_detail(
    run_id: str, db: DbSession, current_user: Previewer
) -> OmopEtlRunRead:
    try:
        return OmopAdapterService(db).run(run_id, current_user)
    except OmopAdapterError as exc:
        raise _error(exc) from exc


@router.get("/runs/{run_id}/download")
def download_export(run_id: str, db: DbSession, current_user: Exporter) -> dict:
    try:
        run = OmopAdapterService(db).run(run_id, current_user)
    except OmopAdapterError as exc:
        raise _error(exc) from exc
    if not run.synthetic_only or not run.export_files:
        raise HTTPException(status_code=409, detail="Export sintético não está disponível.")
    return {
        "manifest": run.manifest,
        "files": run.export_files,
        "export_hash": run.export_hash,
        "synthetic_only": True,
    }


@router.get("/compatibility", response_model=OmopCompatibilityRead)
def compatibility(current_user: Previewer) -> OmopCompatibilityRead:
    del current_user
    return OmopCompatibilityRead.model_validate(OmopAdapterService.compatibility())
