from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    ClinicalImportBatchModel,
    ClinicalReconciliationDecisionModel,
    ClinicalSourceRecordModel,
    PatientFunctionalProfileModel,
    PatientModel,
    UserModel,
)
from app.integrations.services.clinical_deduplication_service import ClinicalDeduplicationService
from app.integrations.services.integration_audit_service import IntegrationAuditService
from app.schemas.integration_schema import (
    ClinicalReconciliationItemRead,
    ClinicalReconciliationRead,
)
from app.services.audit_service import AuditService
from app.services.controlled_vocabulary import category_for_patient_field
from app.services.normalizer import merge_terms, normalize_text
from app.services.patient_functional_profile import PatientFunctionalProfileService
from app.services.patient_identifier_service import (
    ALLOWED_IDENTIFIER_TYPES,
    PatientIdentifierService,
    normalize_identifier_type,
)

CONDITION_CATEGORY_FIELDS = {
    "renal": "renal_condition",
    "hepatic": "hepatic_condition",
    "cardiac": "cardiac_condition",
    "gastrointestinal": "gastrointestinal_history",
    "mental_health": "mental_health_factors",
    "reproductive_gynecologic": "reproductive_gynecologic_factors",
    "pregnancy_lactation": "reproductive_gynecologic_factors",
}


@dataclass(frozen=True)
class ReconciliationDraftItem:
    item_id: str
    source_record_id: int | None
    record_type: str
    field_path: str
    current_value: dict
    imported_value: dict
    source_system: str
    source_type: str
    confidence: float
    badge: str
    suggestion: str
    conflict: bool


class ClinicalReconciliationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = IntegrationAuditService(db)

    def build(self, batch: ClinicalImportBatchModel) -> ClinicalReconciliationRead:
        items = [self._with_decision(item) for item in self._draft_items(batch)]
        badges = sorted({item.badge for item in items})
        summary = {
            "total": len(items),
            "new": sum(1 for item in items if item.badge == "novo"),
            "duplicates": sum(1 for item in items if item.badge == "duplicado"),
            "conflicts": sum(1 for item in items if item.conflict),
            "accepted": sum(1 for item in items if item.decision == "accepted"),
            "rejected": sum(1 for item in items if item.decision == "rejected"),
            "requires_manual_review": sum(
                1 for item in items if item.badge in {"conflito", "revisao_necessaria"}
            ),
        }
        return ClinicalReconciliationRead(
            batch_id=batch.id,
            patient_id=batch.patient_id,
            status=batch.status,
            summary=summary,
            items=items,
            badges=badges,
        )

    def accept_item(
        self,
        batch: ClinicalImportBatchModel,
        item_id: str,
        user: UserModel,
        *,
        justification: str | None = None,
    ) -> ClinicalReconciliationItemRead:
        item = self._find_item(batch, item_id)
        decision = self._save_decision(batch, item, user, "accepted", justification)
        self._apply_item(batch, item)
        self.audit.record(
            user=user,
            patient_id=batch.patient_id,
            batch_id=batch.id,
            action="clinical_reconciliation.item.accepted",
            source_system=batch.source_system,
            details={
                "item_id": item.item_id,
                "record_type": item.record_type,
                "field_path": item.field_path,
                "old_value": item.current_value,
                "imported_value": item.imported_value,
                "decision": "accepted",
                "justification": justification,
            },
        )
        AuditService(self.db).record_action(
            user=user,
            action="clinical_reconciliation.item.accepted",
            resource_type="clinical_import",
            resource_id=str(batch.id),
            details={
                "item_id": item.item_id,
                "record_type": item.record_type,
                "field_path": item.field_path,
                "old_value": item.current_value,
                "imported_value": item.imported_value,
                "decision": "accepted",
                "justification": justification,
            },
        )
        self.db.commit()
        return self._with_decision(item, decision)

    def reject_item(
        self,
        batch: ClinicalImportBatchModel,
        item_id: str,
        user: UserModel,
        *,
        justification: str | None = None,
    ) -> ClinicalReconciliationItemRead:
        item = self._find_item(batch, item_id)
        decision = self._save_decision(batch, item, user, "rejected", justification)
        self.audit.record(
            user=user,
            patient_id=batch.patient_id,
            batch_id=batch.id,
            action="clinical_reconciliation.item.rejected",
            source_system=batch.source_system,
            details={
                "item_id": item.item_id,
                "record_type": item.record_type,
                "field_path": item.field_path,
                "old_value": item.current_value,
                "imported_value": item.imported_value,
                "decision": "rejected",
                "justification": justification,
            },
        )
        AuditService(self.db).record_action(
            user=user,
            action="clinical_reconciliation.item.rejected",
            resource_type="clinical_import",
            resource_id=str(batch.id),
            details={
                "item_id": item.item_id,
                "record_type": item.record_type,
                "field_path": item.field_path,
                "old_value": item.current_value,
                "imported_value": item.imported_value,
                "decision": "rejected",
                "justification": justification,
            },
        )
        self.db.commit()
        return self._with_decision(item, decision)

    def accept_all_without_conflict(
        self,
        batch: ClinicalImportBatchModel,
        user: UserModel,
    ) -> ClinicalReconciliationRead:
        accepted = 0
        for item in self._draft_items(batch):
            if item.conflict or item.badge in {"duplicado", "revisao_necessaria"}:
                continue
            existing = self._decision_for_item(batch.id, item.item_id)
            if existing and existing.decision:
                continue
            self._save_decision(batch, item, user, "accepted", None)
            self._apply_item(batch, item)
            accepted += 1
        self.audit.record(
            user=user,
            patient_id=batch.patient_id,
            batch_id=batch.id,
            action="clinical_reconciliation.safe_items.accepted",
            source_system=batch.source_system,
            details={"accepted_items": accepted, "conflicts_blocked": True},
        )
        AuditService(self.db).record_action(
            user=user,
            action="clinical_reconciliation.safe_items.accepted",
            resource_type="clinical_import",
            resource_id=str(batch.id),
            details={"accepted_items": accepted, "conflicts_blocked": True},
        )
        self.db.commit()
        return self.build(batch)

    def _draft_items(self, batch: ClinicalImportBatchModel) -> list[ReconciliationDraftItem]:
        patient = self.db.get(PatientModel, batch.patient_id) if batch.patient_id else None
        profile = (
            PatientFunctionalProfileService(self.db).get_for_patient(batch.patient_id)
            if batch.patient_id
            else None
        )
        records = list(
            self.db.scalars(
                select(ClinicalSourceRecordModel)
                .where(ClinicalSourceRecordModel.batch_id == batch.id)
                .order_by(ClinicalSourceRecordModel.id)
            )
        )
        items: list[ReconciliationDraftItem] = []
        for record in records:
            if record.record_type == "patient":
                items.extend(self._patient_items(batch, record, patient))
            elif record.record_type == "allergy":
                items.append(
                    self._list_item(
                        batch,
                        record,
                        patient,
                        field_path="allergies",
                        current_values=list(patient.allergies or []) if patient else [],
                    )
                )
            elif record.record_type == "condition":
                items.append(self._condition_item(batch, record, patient))
            elif record.record_type in {"current_medication", "medication_request"}:
                items.append(
                    self._list_item(
                        batch,
                        record,
                        patient,
                        field_path="current_medications",
                        current_values=list(patient.current_medications or []) if patient else [],
                    )
                )
            elif record.record_type == "functional_profile":
                items.extend(self._functional_profile_items(batch, record, profile))
            else:
                items.append(self._generic_item(batch, record))
        return items

    def _patient_items(
        self,
        batch: ClinicalImportBatchModel,
        record: ClinicalSourceRecordModel,
        patient: PatientModel | None,
    ) -> list[ReconciliationDraftItem]:
        payload = record.mapped_payload or {}
        items: list[ReconciliationDraftItem] = []
        for field in ("name", "birth_date", "phone", "email", "mother_name"):
            if field not in payload or payload.get(field) in {None, ""}:
                continue
            current = getattr(patient, field, None) if patient else None
            imported = payload.get(field)
            badge, suggestion, conflict = self._compare_scalar(current, imported)
            items.append(
                self._item(
                    batch,
                    record,
                    field_path=f"patient.{field}",
                    current=current,
                    imported=imported,
                    badge=badge,
                    suggestion=suggestion,
                    conflict=conflict,
                )
            )
        for index, identifier in enumerate(payload.get("identifiers") or []):
            items.append(
                self._item(
                    batch,
                    record,
                    field_path=f"patient.identifiers[{index}]",
                    current=None,
                    imported=identifier,
                    badge="fonte_externa",
                    suggestion="review_manually",
                    conflict=False,
                )
            )
        return items or [self._generic_item(batch, record)]

    def _list_item(
        self,
        batch: ClinicalImportBatchModel,
        record: ClinicalSourceRecordModel,
        patient: PatientModel | None,
        *,
        field_path: str,
        current_values: list[str],
    ) -> ReconciliationDraftItem:
        payload = record.mapped_payload or {}
        imported = payload.get("normalized_value") or payload.get("original_value")
        if field_path == "current_medications":
            duplicate = self._medication_already_present(payload, current_values)
        else:
            normalized_current = {normalize_text(value) for value in current_values}
            normalized_imported = normalize_text(str(imported))
            duplicate = bool(normalized_imported and normalized_imported in normalized_current)
        if duplicate:
            badge = "duplicado"
            suggestion = "keep_current"
            conflict = False
        elif payload.get("mapped_code") and payload.get("confidence", 0) >= 0.85:
            badge = "possivel_match"
            suggestion = "accept_new_data"
            conflict = False
        elif patient is None:
            badge = "fonte_pendente"
            suggestion = "review_manually"
            conflict = False
        else:
            badge = "novo"
            suggestion = "accept_new_data"
            conflict = False
        return self._item(
            batch,
            record,
            field_path=field_path,
            current=current_values,
            imported=payload,
            badge=badge,
            suggestion=suggestion,
            conflict=conflict,
        )

    def _condition_item(
        self,
        batch: ClinicalImportBatchModel,
        record: ClinicalSourceRecordModel,
        patient: PatientModel | None,
    ) -> ReconciliationDraftItem:
        payload = record.mapped_payload or {}
        imported_code = payload.get("mapped_code")
        mapped_category = payload.get("clinical_category")
        current_field = CONDITION_CATEGORY_FIELDS.get(str(mapped_category), "comorbidities")
        current: Any = self._current_value_for_condition(patient, current_field)
        badge = "novo"
        suggestion = "accept_new_data"
        conflict = False
        if patient and imported_code and current_field in {
            "renal_condition",
            "hepatic_condition",
            "cardiac_condition",
            "gastrointestinal_history",
        }:
            current = getattr(patient, current_field, None)
            if current == imported_code:
                badge = "duplicado"
                suggestion = "keep_current"
            elif current:
                badge = "conflito"
                suggestion = "review_manually"
                conflict = True
            return self._item(
                batch,
                record,
                field_path=current_field,
                current=current,
                imported=payload,
                badge=badge,
                suggestion=suggestion,
                conflict=conflict,
            )
        if patient and imported_code and current_field in {
            "mental_health_factors",
            "reproductive_gynecologic_factors",
            "comorbidities",
        }:
            current_values = list(current or [])
            if imported_code in current_values:
                badge = "duplicado"
                suggestion = "keep_current"
            return self._item(
                batch,
                record,
                field_path=current_field,
                current=current_values,
                imported=payload,
                badge=badge,
                suggestion=suggestion,
                conflict=conflict,
            )
        for field in (
            "renal_condition",
            "hepatic_condition",
            "cardiac_condition",
            "gastrointestinal_history",
        ):
            if not patient:
                break
            category = category_for_patient_field(field)
            if category and imported_code and imported_code == getattr(patient, field, None):
                current_field = field
                current = getattr(patient, field, None)
                badge = "duplicado"
                suggestion = "keep_current"
                break
            if category == "renal" and imported_code and "renal" in normalize_text(
                str(payload.get("normalized_value") or payload.get("original_value"))
            ):
                current_field = field
                current = getattr(patient, field, None)
                if current and current != imported_code:
                    badge = "conflito"
                    suggestion = "review_manually"
                    conflict = True
                break
        return self._item(
            batch,
            record,
            field_path=current_field,
            current=current,
            imported=payload,
            badge=badge,
            suggestion=suggestion,
            conflict=conflict,
        )

    def _functional_profile_items(
        self,
        batch: ClinicalImportBatchModel,
        record: ClinicalSourceRecordModel,
        profile: PatientFunctionalProfileModel | None,
    ) -> list[ReconciliationDraftItem]:
        payload = record.mapped_payload or {}
        items: list[ReconciliationDraftItem] = []
        for field, imported in payload.items():
            if field in {"source", "notes"}:
                continue
            current = getattr(profile, field, None) if profile else None
            badge, suggestion, conflict = self._compare_scalar(current, imported)
            items.append(
                self._item(
                    batch,
                    record,
                    field_path=f"functional_profile.{field}",
                    current=current,
                    imported=imported,
                    badge=badge,
                    suggestion=suggestion,
                    conflict=conflict,
                )
            )
        return items or [self._generic_item(batch, record)]

    def _generic_item(
        self,
        batch: ClinicalImportBatchModel,
        record: ClinicalSourceRecordModel,
    ) -> ReconciliationDraftItem:
        payload = record.mapped_payload or {}
        badge = "revisao_necessaria" if not payload else "novo"
        return self._item(
            batch,
            record,
            field_path=record.record_type,
            current=None,
            imported=payload,
            badge=badge,
            suggestion="review_manually" if badge == "revisao_necessaria" else "accept_new_data",
            conflict=False,
        )

    def _item(
        self,
        batch: ClinicalImportBatchModel,
        record: ClinicalSourceRecordModel,
        *,
        field_path: str,
        current: Any,
        imported: Any,
        badge: str,
        suggestion: str,
        conflict: bool,
    ) -> ReconciliationDraftItem:
        return ReconciliationDraftItem(
            item_id=f"{record.id}:{field_path}",
            source_record_id=record.id,
            record_type=record.record_type,
            field_path=field_path,
            current_value={"value": self._json_value(current)},
            imported_value={"value": self._json_value(imported)},
            source_system=batch.source_system,
            source_type=batch.source_type,
            confidence=float(record.confidence or 0),
            badge=badge,
            suggestion=suggestion,
            conflict=conflict,
        )

    def _compare_scalar(self, current: Any, imported: Any) -> tuple[str, str, bool]:
        if current is None or current == "" or current == []:
            return "novo", "accept_new_data", False
        if normalize_text(str(current)) == normalize_text(str(imported)):
            return "duplicado", "keep_current", False
        return "conflito", "review_manually", True

    def _current_value_for_condition(
        self,
        patient: PatientModel | None,
        field_path: str,
    ) -> Any:
        if patient is None:
            return []
        if hasattr(patient, field_path):
            value = getattr(patient, field_path)
            return list(value or []) if isinstance(value, list) else value
        return list(patient.comorbidities or [])

    def _medication_already_present(self, payload: dict, current_values: list[str]) -> bool:
        imported_keys = self._medication_equivalence_keys(payload)
        if not imported_keys:
            return False
        current_keys: set[str] = set()
        for value in current_values:
            current_keys.update(
                self._medication_equivalence_keys(
                    {
                        "original_value": value,
                        "normalized_value": value,
                    }
                )
            )
        return bool(imported_keys & current_keys)

    def _medication_equivalence_keys(self, payload: dict) -> set[str]:
        keys = {
            str(payload.get("active_ingredient_id") or "").strip(),
            normalize_text(str(payload.get("mapped_code") or "")),
            normalize_text(str(payload.get("normalized_value") or "")),
        }
        raw_value = payload.get("original_value") or payload.get("normalized_value")
        if raw_value:
            result = ClinicalDeduplicationService().deduplicate_medication(str(raw_value))
            keys.add(normalize_text(result.mapped_code))
            keys.add(normalize_text(result.normalized_value))
        return {key for key in keys if key}

    def _with_decision(
        self,
        item: ReconciliationDraftItem,
        decision: ClinicalReconciliationDecisionModel | None = None,
    ) -> ClinicalReconciliationItemRead:
        decision = decision or self._decision_for_item_by_id(item.item_id)
        badge = item.badge
        if decision and decision.decision == "accepted":
            badge = "aceito"
        elif decision and decision.decision == "rejected":
            badge = "rejeitado"
        return ClinicalReconciliationItemRead(
            item_id=item.item_id,
            source_record_id=item.source_record_id,
            record_type=item.record_type,
            field_path=item.field_path,
            current_value=item.current_value,
            imported_value=item.imported_value,
            source_system=item.source_system,
            source_type=item.source_type,
            confidence=item.confidence,
            badge=badge,
            suggestion=item.suggestion,
            conflict=item.conflict,
            decision=decision.decision if decision else None,
            reviewed_by=decision.reviewed_by if decision else None,
            reviewed_at=decision.reviewed_at if decision else None,
            justification=decision.justification if decision else None,
        )

    def _find_item(
        self, batch: ClinicalImportBatchModel, item_id: str
    ) -> ReconciliationDraftItem:
        for item in self._draft_items(batch):
            if item.item_id == item_id:
                return item
        raise ValueError("Item de reconciliacao nao encontrado.")

    def _decision_for_item_by_id(
        self, item_id: str
    ) -> ClinicalReconciliationDecisionModel | None:
        return self.db.scalar(
            select(ClinicalReconciliationDecisionModel).where(
                ClinicalReconciliationDecisionModel.item_id == item_id
            )
        )

    def _decision_for_item(
        self, batch_id: int, item_id: str
    ) -> ClinicalReconciliationDecisionModel | None:
        return self.db.scalar(
            select(ClinicalReconciliationDecisionModel).where(
                ClinicalReconciliationDecisionModel.batch_id == batch_id,
                ClinicalReconciliationDecisionModel.item_id == item_id,
            )
        )

    def _save_decision(
        self,
        batch: ClinicalImportBatchModel,
        item: ReconciliationDraftItem,
        user: UserModel,
        decision_value: str,
        justification: str | None,
    ) -> ClinicalReconciliationDecisionModel:
        decision = self._decision_for_item(batch.id, item.item_id)
        if decision is None:
            decision = ClinicalReconciliationDecisionModel(
                batch_id=batch.id,
                source_record_id=item.source_record_id,
                item_id=item.item_id,
                record_type=item.record_type,
                field_path=item.field_path,
                current_value=item.current_value,
                imported_value=item.imported_value,
                source_system=batch.source_system,
                confidence=item.confidence,
                badge=item.badge,
                suggestion=item.suggestion,
            )
            self.db.add(decision)
        decision.decision = decision_value
        decision.reviewed_by = user.id
        decision.reviewed_at = datetime.now(UTC)
        decision.justification = justification
        return decision

    def _apply_item(
        self,
        batch: ClinicalImportBatchModel,
        item: ReconciliationDraftItem,
    ) -> None:
        if batch.patient_id is None:
            return
        patient = self.db.get(PatientModel, batch.patient_id)
        if patient is None:
            return
        imported = item.imported_value.get("value")
        if item.field_path == "allergies":
            value = self._imported_term(imported)
            patient.allergies = merge_terms(patient.allergies, [value])
        elif item.field_path == "current_medications":
            value = self._imported_term(imported)
            patient.current_medications = merge_terms(patient.current_medications, [value])
        elif item.field_path == "renal_condition":
            code = imported.get("mapped_code") if isinstance(imported, dict) else None
            if code:
                patient.renal_condition = code
        elif item.field_path in {
            "hepatic_condition",
            "cardiac_condition",
            "gastrointestinal_history",
        }:
            code = imported.get("mapped_code") if isinstance(imported, dict) else None
            if code:
                setattr(patient, item.field_path, code)
        elif item.field_path in {
            "mental_health_factors",
            "reproductive_gynecologic_factors",
        }:
            code = imported.get("mapped_code") if isinstance(imported, dict) else None
            value = code or self._imported_term(imported)
            current = getattr(patient, item.field_path, [])
            setattr(patient, item.field_path, merge_terms(current, [value]))
        elif item.field_path == "comorbidities":
            value = self._imported_term(imported)
            patient.comorbidities = merge_terms(patient.comorbidities, [value])
        elif item.field_path.startswith("patient.identifiers"):
            self._apply_identifier(patient, imported)
        elif item.field_path.startswith("patient."):
            field = item.field_path.removeprefix("patient.")
            if hasattr(patient, field) and not field.startswith("identifiers"):
                if field == "birth_date" and isinstance(imported, str):
                    imported = date.fromisoformat(imported)
                setattr(patient, field, imported)
        elif item.field_path.startswith("functional_profile."):
            field = item.field_path.removeprefix("functional_profile.")
            service = PatientFunctionalProfileService(self.db)
            profile = service.get_for_patient(patient.id)
            if profile is None:
                profile = PatientFunctionalProfileModel(
                    patient_id=patient.id,
                    source=f"import:{batch.source_system}",
                    last_reviewed_at=datetime.now(UTC),
                )
                self.db.add(profile)
                self.db.flush()
            if hasattr(profile, field):
                setattr(profile, field, imported)

    def _apply_identifier(self, patient: PatientModel, imported: Any) -> None:
        if not isinstance(imported, dict):
            return
        identifier_value = imported.get("identifier_value") or imported.get("value")
        if not identifier_value:
            return
        identifier_type = str(imported.get("identifier_type") or "external_system_id")
        normalized_type = normalize_identifier_type(identifier_type)
        if normalized_type not in ALLOWED_IDENTIFIER_TYPES:
            normalized_type = "external_system_id"
        PatientIdentifierService(self.db).create(
            patient_id=patient.id,
            identifier_type=normalized_type,
            identifier_value=str(identifier_value),
            issuing_system=imported.get("issuing_system") or imported.get("system"),
            is_primary=False,
        )

    def _imported_term(self, imported: Any) -> str:
        if isinstance(imported, dict):
            return str(
                imported.get("mapped_code")
                or imported.get("normalized_value")
                or imported.get("original_value")
                or imported
            )
        return str(imported)

    def _json_value(self, value: Any) -> Any:
        if isinstance(value, datetime | date):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: self._json_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_value(item) for item in value]
        return value
