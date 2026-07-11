from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.models import ClinicalImportBatchModel, UserModel
from app.database.session import get_db
from app.domain.user import UserRole
from app.integrations.adapters.csv.csv_importer import CsvImporter
from app.integrations.adapters.fhir.fhir_bundle_importer import FhirBundleImporter
from app.integrations.adapters.json.generic_json_importer import GenericJsonImporter
from app.integrations.services.clinical_reconciliation_service import ClinicalReconciliationService
from app.integrations.services.integration_service import IntegrationService
from app.schemas.integration_schema import (
    ClinicalImportBatchRead,
    ClinicalReconciliationItemRead,
    ClinicalReconciliationRead,
    ClinicalSourceRecordRead,
    CsvImportRequest,
    FhirBundleImportRequest,
    GenericJsonImportRequest,
    ImportReviewRequest,
    ReconciliationDecisionRequest,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])
DbSession = Annotated[Session, Depends(get_db)]
ImportReader = Annotated[
    UserModel,
    Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO, UserRole.ENFERMAGEM, UserRole.AUDITOR)),
]
ImportManager = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.MEDICO))]


@router.post("/fhir/import-bundle", response_model=ClinicalImportBatchRead)
def import_fhir_bundle(
    payload: FhirBundleImportRequest,
    db: DbSession,
    current_user: ImportManager,
) -> ClinicalImportBatchRead:
    records = FhirBundleImporter().import_bundle(payload.bundle)
    batch = _create_import_batch(
        db,
        source_system=payload.source_system,
        source_type="fhir_bundle",
        records=records,
        user=current_user,
        patient_id=payload.patient_id,
        consent_confirmed=payload.consent_confirmed,
        authorized_by=payload.authorized_by,
        purpose=payload.purpose,
    )
    return _batch_response(db, batch)


@router.post("/json/import", response_model=ClinicalImportBatchRead)
def import_json_payload(
    payload: GenericJsonImportRequest,
    db: DbSession,
    current_user: ImportManager,
) -> ClinicalImportBatchRead:
    records = GenericJsonImporter().import_payload(payload.payload)
    batch = _create_import_batch(
        db,
        source_system=payload.source_system,
        source_type="generic_json",
        records=records,
        user=current_user,
        patient_id=payload.patient_id,
        consent_confirmed=payload.consent_confirmed,
        authorized_by=payload.authorized_by,
        purpose=payload.purpose,
    )
    return _batch_response(db, batch)


@router.post("/csv/import", response_model=ClinicalImportBatchRead)
def import_csv_payload(
    payload: CsvImportRequest,
    db: DbSession,
    current_user: ImportManager,
) -> ClinicalImportBatchRead:
    records = CsvImporter().import_text(payload.csv_text)
    batch = _create_import_batch(
        db,
        source_system=payload.source_system,
        source_type="csv",
        records=records,
        user=current_user,
        patient_id=payload.patient_id,
        consent_confirmed=payload.consent_confirmed,
        authorized_by=payload.authorized_by,
        purpose=payload.purpose,
    )
    return _batch_response(db, batch)


@router.get("/imports", response_model=list[ClinicalImportBatchRead])
def list_imports(db: DbSession, _current_user: ImportReader) -> list[ClinicalImportBatchRead]:
    service = IntegrationService(db)
    return [_batch_response(db, batch) for batch in service.list_batches()]


@router.get("/imports/{batch_id}", response_model=ClinicalImportBatchRead)
def get_import(
    batch_id: int,
    db: DbSession,
    _current_user: ImportReader,
) -> ClinicalImportBatchRead:
    batch = _get_batch_or_404(db, batch_id)
    return _batch_response(db, batch)


@router.post("/imports/{batch_id}/accept", response_model=ClinicalImportBatchRead)
def accept_import(
    batch_id: int,
    db: DbSession,
    current_user: ImportManager,
) -> ClinicalImportBatchRead:
    service = IntegrationService(db)
    batch = _get_batch_or_404(db, batch_id)
    updated = service.accept_batch(batch, current_user)
    return _batch_response(db, updated)


@router.post("/imports/{batch_id}/reject", response_model=ClinicalImportBatchRead)
def reject_import(
    batch_id: int,
    payload: ImportReviewRequest,
    db: DbSession,
    current_user: ImportManager,
) -> ClinicalImportBatchRead:
    service = IntegrationService(db)
    batch = _get_batch_or_404(db, batch_id)
    updated = service.reject_batch(batch, current_user, reason=payload.reason)
    return _batch_response(db, updated)


@router.get("/imports/{batch_id}/reconciliation", response_model=ClinicalReconciliationRead)
def get_import_reconciliation(
    batch_id: int,
    db: DbSession,
    _current_user: ImportReader,
) -> ClinicalReconciliationRead:
    batch = _get_batch_or_404(db, batch_id)
    return ClinicalReconciliationService(db).build(batch)


@router.post(
    "/imports/{batch_id}/reconciliation/items/{item_id}/accept",
    response_model=ClinicalReconciliationItemRead,
)
def accept_reconciliation_item(
    batch_id: int,
    item_id: str,
    payload: ReconciliationDecisionRequest,
    db: DbSession,
    current_user: ImportManager,
) -> ClinicalReconciliationItemRead:
    batch = _get_batch_or_404(db, batch_id)
    try:
        return ClinicalReconciliationService(db).accept_item(
            batch,
            item_id,
            current_user,
            justification=payload.justification,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/imports/{batch_id}/reconciliation/items/{item_id}/reject",
    response_model=ClinicalReconciliationItemRead,
)
def reject_reconciliation_item(
    batch_id: int,
    item_id: str,
    payload: ReconciliationDecisionRequest,
    db: DbSession,
    current_user: ImportManager,
) -> ClinicalReconciliationItemRead:
    batch = _get_batch_or_404(db, batch_id)
    try:
        return ClinicalReconciliationService(db).reject_item(
            batch,
            item_id,
            current_user,
            justification=payload.justification,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/imports/{batch_id}/reconciliation/accept-safe",
    response_model=ClinicalReconciliationRead,
)
def accept_reconciliation_items_without_conflict(
    batch_id: int,
    db: DbSession,
    current_user: ImportManager,
) -> ClinicalReconciliationRead:
    batch = _get_batch_or_404(db, batch_id)
    return ClinicalReconciliationService(db).accept_all_without_conflict(batch, current_user)


def _get_batch_or_404(db: Session, batch_id: int) -> ClinicalImportBatchModel:
    batch = IntegrationService(db).get_batch(batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Importa??o clinica n?o encontrada.",
        )
    return batch


def _create_import_batch(db: Session, **kwargs) -> ClinicalImportBatchModel:
    try:
        return IntegrationService(db).create_import_batch(**kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _batch_response(db: Session, batch: ClinicalImportBatchModel) -> ClinicalImportBatchRead:
    records = IntegrationService(db).list_records(batch.id)
    return ClinicalImportBatchRead(
        id=batch.id,
        source_system=batch.source_system,
        source_type=batch.source_type,
        imported_by=batch.imported_by,
        patient_id=batch.patient_id,
        consent_id=batch.consent_id,
        status=batch.status,
        imported_at=batch.imported_at,
        finished_at=batch.finished_at,
        errors=list(batch.errors or []),
        records=[ClinicalSourceRecordRead.model_validate(record) for record in records],
    )
