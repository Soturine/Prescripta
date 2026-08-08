from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import (
    InstitutionalClinicalProtocolModel,
    InstitutionalClinicalProtocolVersionModel,
    MedicationModel,
    ProtocolConditionScopeModel,
    ProtocolCredentialRequirementModel,
    ProtocolMedicationScopeModel,
    ProtocolPrescribingScopeModel,
    UserModel,
)
from app.schemas.clinical_protocol_schema import (
    InstitutionalClinicalProtocolCreate,
    InstitutionalClinicalProtocolVersionCreate,
    ProtocolVersionReviewRequest,
)
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256, json_compatible


class InstitutionalProtocolError(ValueError):
    pass


class InstitutionalClinicalProtocolService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_protocol(
        self,
        payload: InstitutionalClinicalProtocolCreate,
        actor: UserModel,
    ) -> InstitutionalClinicalProtocolModel:
        protocol = InstitutionalClinicalProtocolModel(
            institution_id=actor.institution_id,
            code=payload.code,
            name=payload.name,
            program=payload.program,
            status="active",
            created_by_user_id=actor.id,
        )
        self.db.add(protocol)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise InstitutionalProtocolError(
                "Já existe protocolo com esse código na instituição."
            ) from exc
        AuditService(self.db).record_action(
            user=actor,
            action="clinical_protocol.create",
            resource_type="institutional_clinical_protocol",
            resource_id=str(protocol.id),
            status="active",
            details={"code": protocol.code, "program": protocol.program},
        )
        return protocol

    def create_version(
        self,
        protocol_id: int,
        payload: InstitutionalClinicalProtocolVersionCreate,
        actor: UserModel,
    ) -> InstitutionalClinicalProtocolVersionModel:
        protocol = self._protocol(protocol_id, actor)
        medication_ids = sorted({item.medication_id for item in payload.medications})
        known = set(
            self.db.scalars(
                select(MedicationModel.id).where(MedicationModel.id.in_(medication_ids))
            )
        )
        if known != set(medication_ids):
            raise InstitutionalProtocolError("Scope contém medicamento inexistente.")
        definition = payload.model_dump(mode="json")
        version = InstitutionalClinicalProtocolVersionModel(
            protocol_id=protocol.id,
            institution_id=protocol.institution_id,
            version=payload.version,
            status="draft",
            review_status="pending_review",
            effective_from=self._aware(payload.effective_from),
            effective_until=self._aware(payload.effective_until),
            source_refs=payload.source_refs,
            clinical_context=json_compatible(payload.clinical_context),
            eligible_professions=sorted(set(payload.eligible_professions)),
            required_capability=payload.required_capability,
            required_parameters=sorted(set(payload.required_parameters)),
            contraindications=sorted(set(payload.contraindications)),
            requires_second_review=payload.requires_second_review,
            second_reviewer_role=payload.second_reviewer_role,
            override_policy=json_compatible(payload.override_policy),
            definition_hash=canonical_sha256(definition),
            created_by_user_id=actor.id,
        )
        self.db.add(version)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise InstitutionalProtocolError(
                "A versão já existe para este protocolo."
            ) from exc
        scope = payload.prescribing_scope
        self.db.add(
            ProtocolPrescribingScopeModel(
                protocol_version_id=version.id,
                allowed_routes=sorted(set(scope.allowed_routes)),
                dose_min=scope.dose_min,
                dose_max=scope.dose_max,
                dose_unit=scope.dose_unit,
                frequency_min_per_day=scope.frequency_min_per_day,
                frequency_max_per_day=scope.frequency_max_per_day,
                max_duration_days=scope.max_duration_days,
                min_age_years=scope.min_age_years,
                max_age_years=scope.max_age_years,
                min_weight_kg=scope.min_weight_kg,
                max_weight_kg=scope.max_weight_kg,
                constraints=json_compatible(scope.constraints),
            )
        )
        for item in payload.medications:
            self.db.add(
                ProtocolMedicationScopeModel(
                    protocol_version_id=version.id,
                    medication_id=item.medication_id,
                    concept_set_ref=item.concept_set_ref,
                )
            )
        for item in payload.conditions:
            self.db.add(
                ProtocolConditionScopeModel(
                    protocol_version_id=version.id,
                    terminology_system=item.terminology_system,
                    terminology_version=item.terminology_version,
                    condition_code=item.condition_code.casefold(),
                    label=item.label,
                )
            )
        for item in payload.credentials:
            self.db.add(
                ProtocolCredentialRequirementModel(
                    protocol_version_id=version.id,
                    credential_type=item.credential_type,
                    credential_region=item.credential_region,
                    verification_required=item.verification_required,
                    unexpired_required=item.unexpired_required,
                )
            )
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="protocol.version.create",
            resource_type="institutional_clinical_protocol_version",
            resource_id=str(version.id),
            status="draft",
            details={
                "protocol_id": protocol.id,
                "version": version.version,
                "definition_hash": version.definition_hash,
            },
        )
        return version

    def review_version(
        self,
        version_id: int,
        payload: ProtocolVersionReviewRequest,
        actor: UserModel,
    ) -> InstitutionalClinicalProtocolVersionModel:
        version = self.version(version_id, actor)
        if version.created_by_user_id == actor.id:
            raise InstitutionalProtocolError("A revisão deve ser independente do autor.")
        version.review_status = payload.decision
        version.status = "active" if payload.decision == "reviewed_demo" else payload.decision
        version.reviewed_by_user_id = actor.id
        version.reviewed_at = datetime.now(UTC)
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="protocol.review",
            resource_type="institutional_clinical_protocol_version",
            resource_id=str(version.id),
            status=payload.decision,
            details={"version": version.version, "note": payload.note},
        )
        return version

    def list_protocols(self, actor: UserModel) -> list[InstitutionalClinicalProtocolModel]:
        return list(
            self.db.scalars(
                select(InstitutionalClinicalProtocolModel)
                .where(
                    InstitutionalClinicalProtocolModel.institution_id
                    == actor.institution_id
                )
                .order_by(InstitutionalClinicalProtocolModel.name)
            )
        )

    def version(
        self, version_id: int, actor: UserModel
    ) -> InstitutionalClinicalProtocolVersionModel:
        version = self.db.get(InstitutionalClinicalProtocolVersionModel, version_id)
        if version is None or version.institution_id != actor.institution_id:
            raise InstitutionalProtocolError("Versão de protocolo não encontrada.")
        return version

    def version_detail(self, version_id: int, actor: UserModel) -> dict:
        version = self.version(version_id, actor)
        scope = self.db.scalar(
            select(ProtocolPrescribingScopeModel).where(
                ProtocolPrescribingScopeModel.protocol_version_id == version.id
            )
        )
        medications = list(
            self.db.scalars(
                select(ProtocolMedicationScopeModel).where(
                    ProtocolMedicationScopeModel.protocol_version_id == version.id
                )
            )
        )
        conditions = list(
            self.db.scalars(
                select(ProtocolConditionScopeModel).where(
                    ProtocolConditionScopeModel.protocol_version_id == version.id
                )
            )
        )
        credentials = list(
            self.db.scalars(
                select(ProtocolCredentialRequirementModel).where(
                    ProtocolCredentialRequirementModel.protocol_version_id == version.id
                )
            )
        )
        return {
            **self._model_dict(version),
            "prescribing_scope": self._model_dict(scope) if scope else {},
            "medications": [self._model_dict(item) for item in medications],
            "conditions": [self._model_dict(item) for item in conditions],
            "credentials": [self._model_dict(item) for item in credentials],
        }

    def _protocol(
        self, protocol_id: int, actor: UserModel
    ) -> InstitutionalClinicalProtocolModel:
        protocol = self.db.get(InstitutionalClinicalProtocolModel, protocol_id)
        if protocol is None or protocol.institution_id != actor.institution_id:
            raise InstitutionalProtocolError("Protocolo não encontrado.")
        return protocol

    @staticmethod
    def _model_dict(model) -> dict:
        return {
            column.name: getattr(model, column.name) for column in model.__table__.columns
        }

    @staticmethod
    def _aware(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
