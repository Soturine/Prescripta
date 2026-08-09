from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AuditEventModel,
    MedicationFormulationReviewModel,
    MedicationReconciliationItemModel,
    MedicationReconciliationModel,
    PatientModel,
    PharmacyInterventionEventModel,
    PharmacyInterventionModel,
    UserModel,
)
from app.domain.dose import MedicationDoseInput
from app.schemas.pharmacy_schema import (
    MedicationFormulationReviewCreate,
    MedicationReconciliationCreate,
    PharmacyInterventionCreate,
    PharmacyInterventionDecision,
    PharmacyInterventionResolve,
    ReconciliationItemDecision,
)
from app.services.audit_service import AuditService
from app.services.object_authorization import ObjectAuthorizationService


class PharmacyWorkflowError(ValueError):
    pass


class PharmacyWorkflowConflict(PharmacyWorkflowError):
    pass


class PharmacyWorkflowService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_intervention(
        self,
        payload: PharmacyInterventionCreate,
        pharmacist: UserModel,
    ) -> PharmacyInterventionModel:
        self._require_patient(pharmacist, payload.patient_id)
        existing = self.db.scalar(
            select(PharmacyInterventionModel).where(
                PharmacyInterventionModel.institution_id == pharmacist.institution_id,
                PharmacyInterventionModel.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is not None:
            if (
                existing.patient_id != payload.patient_id
                or existing.intervention_type != payload.intervention_type
                or existing.problem != payload.problem
            ):
                raise PharmacyWorkflowConflict(
                    "Chave idempotente reutilizada com outro conteúdo."
                )
            return existing
        intervention = PharmacyInterventionModel(
            institution_id=pharmacist.institution_id,
            patient_id=payload.patient_id,
            prescription_audit_id=payload.prescription_audit_id,
            medication_id=payload.medication_id,
            pharmacist_user_id=pharmacist.id,
            intervention_type=payload.intervention_type,
            severity=payload.severity,
            priority=payload.priority,
            problem=payload.problem,
            recommendation=payload.recommendation,
            source_refs=payload.source_refs,
            dose_snapshot=payload.dose_snapshot,
            status="open",
            idempotency_key=payload.idempotency_key,
            version=1,
            cosignature_required=payload.cosignature_required,
        )
        self.db.add(intervention)
        self.db.flush()
        self._event(
            intervention,
            pharmacist,
            event_type="created",
            from_status=None,
            to_status="open",
            reason=None,
        )
        self._audit(
            pharmacist,
            "pharmacy.intervention.create",
            intervention,
            "open",
        )
        return intervention

    def cosign(
        self,
        intervention_id: int,
        actor: UserModel,
        *,
        expected_version: int,
    ) -> PharmacyInterventionModel:
        intervention = self._intervention(intervention_id, actor)
        self._require_patient(actor, intervention.patient_id)
        self._expected_version(intervention.version, expected_version)
        if not intervention.cosignature_required:
            raise PharmacyWorkflowError("A intervenção não exige coassinatura.")
        if intervention.pharmacist_user_id == actor.id:
            raise PharmacyWorkflowError("A coassinatura deve ser independente do autor.")
        if intervention.cosigned_by_user_id is not None:
            return intervention
        intervention.cosigned_by_user_id = actor.id
        intervention.cosigned_at = datetime.now(UTC)
        intervention.version += 1
        self._event(
            intervention,
            actor,
            event_type="cosigned",
            from_status=intervention.status,
            to_status=intervention.status,
            reason="Coassinatura independente registrada.",
        )
        self.db.flush()
        return intervention

    def decide(
        self,
        intervention_id: int,
        payload: PharmacyInterventionDecision,
        actor: UserModel,
    ) -> PharmacyInterventionModel:
        intervention = self._intervention(intervention_id, actor)
        self._require_patient(actor, intervention.patient_id)
        self._expected_version(intervention.version, payload.expected_version)
        if intervention.status != "open":
            raise PharmacyWorkflowConflict("A intervenção não está aberta para decisão.")
        if intervention.cosignature_required and intervention.cosigned_by_user_id is None:
            raise PharmacyWorkflowError("Coassinatura farmacêutica independente pendente.")
        old_status = intervention.status
        intervention.status = payload.decision
        intervention.accepted = payload.decision == "accepted"
        intervention.decision_actor_user_id = actor.id
        intervention.reviewed_at = datetime.now(UTC)
        intervention.rejection_reason = (
            payload.reason if payload.decision == "rejected" else None
        )
        intervention.version += 1
        self._event(
            intervention,
            actor,
            event_type="decision",
            from_status=old_status,
            to_status=intervention.status,
            reason=payload.reason,
        )
        self._audit(
            actor,
            "pharmacy.intervention.decision",
            intervention,
            intervention.status,
        )
        self.db.flush()
        return intervention

    def resolve(
        self,
        intervention_id: int,
        payload: PharmacyInterventionResolve,
        actor: UserModel,
    ) -> PharmacyInterventionModel:
        intervention = self._intervention(intervention_id, actor)
        self._require_patient(actor, intervention.patient_id)
        self._expected_version(intervention.version, payload.expected_version)
        if intervention.status not in {"accepted", "rejected"}:
            raise PharmacyWorkflowConflict("A decisão deve ocorrer antes da resolução.")
        old_status = intervention.status
        intervention.status = "resolved"
        intervention.resolution = payload.resolution
        intervention.resolved_at = datetime.now(UTC)
        intervention.version += 1
        self._event(
            intervention,
            actor,
            event_type="resolved",
            from_status=old_status,
            to_status="resolved",
            reason=payload.resolution,
        )
        self._audit(
            actor,
            "pharmacy.intervention.resolve",
            intervention,
            "resolved",
        )
        self.db.flush()
        return intervention

    def list_interventions(
        self,
        actor: UserModel,
        *,
        status: str | None = None,
        priority: str | None = None,
    ) -> list[PharmacyInterventionModel]:
        statement = select(PharmacyInterventionModel).where(
            PharmacyInterventionModel.institution_id == actor.institution_id
        )
        if status:
            statement = statement.where(PharmacyInterventionModel.status == status)
        if priority:
            statement = statement.where(PharmacyInterventionModel.priority == priority)
        statement = statement.order_by(PharmacyInterventionModel.created_at.desc())
        rows = list(self.db.scalars(statement))
        return [
            row
            for row in rows
            if self._can_access_patient(actor, row.patient_id)
        ]

    def events(
        self, intervention_id: int, actor: UserModel
    ) -> list[PharmacyInterventionEventModel]:
        intervention = self._intervention(intervention_id, actor)
        self._require_patient(actor, intervention.patient_id)
        return list(
            self.db.scalars(
                select(PharmacyInterventionEventModel)
                .where(PharmacyInterventionEventModel.intervention_id == intervention_id)
                .order_by(PharmacyInterventionEventModel.version)
            )
        )

    def create_reconciliation(
        self,
        payload: MedicationReconciliationCreate,
        pharmacist: UserModel,
    ) -> MedicationReconciliationModel:
        self._require_patient(pharmacist, payload.patient_id)
        existing = self.db.scalar(
            select(MedicationReconciliationModel).where(
                MedicationReconciliationModel.institution_id == pharmacist.institution_id,
                MedicationReconciliationModel.idempotency_key == payload.idempotency_key,
            )
        )
        if existing is not None:
            if existing.patient_id != payload.patient_id:
                raise PharmacyWorkflowConflict(
                    "Chave idempotente reutilizada com outro paciente."
                )
            return existing
        reconciliation = MedicationReconciliationModel(
            institution_id=pharmacist.institution_id,
            patient_id=payload.patient_id,
            pharmacist_user_id=pharmacist.id,
            status="in_review",
            source_refs=payload.source_refs,
            idempotency_key=payload.idempotency_key,
            version=1,
        )
        self.db.add(reconciliation)
        self.db.flush()
        for item in payload.items:
            self.db.add(
                MedicationReconciliationItemModel(
                    reconciliation_id=reconciliation.id,
                    medication_id=item.medication_id,
                    medication_name=item.medication_name,
                    source_ref=item.source_ref,
                    discrepancy=item.discrepancy,
                    status="needs_review",
                    formulation=item.formulation,
                    concentration=item.concentration,
                    history=[],
                    version=1,
                )
            )
        self.db.flush()
        self._audit_reconciliation(pharmacist, reconciliation, "created")
        return reconciliation

    def reconciliation(self, reconciliation_id: int, actor: UserModel) -> dict:
        reconciliation = self.db.get(MedicationReconciliationModel, reconciliation_id)
        if (
            reconciliation is None
            or reconciliation.institution_id != actor.institution_id
        ):
            raise PharmacyWorkflowError("Reconciliação não encontrada.")
        self._require_patient(actor, reconciliation.patient_id)
        items = list(
            self.db.scalars(
                select(MedicationReconciliationItemModel).where(
                    MedicationReconciliationItemModel.reconciliation_id
                    == reconciliation.id
                )
            )
        )
        payload = {
            column.name: getattr(reconciliation, column.name)
            for column in reconciliation.__table__.columns
        }
        payload["items"] = items
        return payload

    def decide_reconciliation_item(
        self,
        item_id: int,
        payload: ReconciliationItemDecision,
        actor: UserModel,
    ) -> MedicationReconciliationItemModel:
        item = self.db.get(MedicationReconciliationItemModel, item_id)
        reconciliation = (
            self.db.get(MedicationReconciliationModel, item.reconciliation_id)
            if item is not None
            else None
        )
        if (
            item is None
            or reconciliation is None
            or reconciliation.institution_id != actor.institution_id
        ):
            raise PharmacyWorkflowError("Item de reconciliação não encontrado.")
        self._require_patient(actor, reconciliation.patient_id)
        self._expected_version(item.version, payload.expected_version)
        previous = item.status
        item.status = payload.status
        item.action = payload.action
        item.justification = payload.justification
        item.author_user_id = actor.id
        item.version += 1
        item.updated_at = datetime.now(UTC)
        item.history = list(item.history or []) + [
            {
                "version": item.version,
                "from": previous,
                "to": payload.status,
                "action": payload.action,
                "author_user_id": actor.id,
                "at": item.updated_at.isoformat(),
            }
        ]
        self.db.flush()
        remaining = self.db.scalar(
            select(MedicationReconciliationItemModel.id).where(
                MedicationReconciliationItemModel.reconciliation_id == reconciliation.id,
                MedicationReconciliationItemModel.status.in_(["needs_review", "unresolved"]),
            )
        )
        if remaining is None:
            reconciliation.status = "completed"
            reconciliation.completed_at = datetime.now(UTC)
            reconciliation.version += 1
        self._audit_reconciliation(actor, reconciliation, "item_decided")
        self.db.flush()
        return item

    def create_formulation_review(
        self,
        payload: MedicationFormulationReviewCreate,
        actor: UserModel,
    ) -> MedicationFormulationReviewModel:
        patient_id: int | None = None
        if payload.intervention_id is not None:
            intervention = self._intervention(payload.intervention_id, actor)
            patient_id = intervention.patient_id
        else:
            item = self.db.get(
                MedicationReconciliationItemModel, payload.reconciliation_item_id
            )
            reconciliation = (
                self.db.get(MedicationReconciliationModel, item.reconciliation_id)
                if item is not None
                else None
            )
            if (
                item is None
                or reconciliation is None
                or reconciliation.institution_id != actor.institution_id
            ):
                raise PharmacyWorkflowError("Item de reconciliação não encontrado.")
            patient_id = reconciliation.patient_id
        self._require_patient(actor, patient_id)
        dose = MedicationDoseInput(**payload.dose.model_dump())
        mass = dose.administration_mass
        result = {
            "dimension": dose.dimension.value,
            "administration_mass_mg": str(mass.value) if mass else None,
            "daily_mass_mg": str(dose.daily_mass_mg) if dose.daily_mass_mg else None,
            "cumulative_mass_mg": (
                str(dose.cumulative_mass_mg) if dose.cumulative_mass_mg else None
            ),
            "consistent": mass is not None,
            "requires_human_review": True,
            "educational_notice": (
                "Revisão farmacêutica demonstrativa; não representa dispensação real."
            ),
        }
        review = MedicationFormulationReviewModel(
            institution_id=actor.institution_id,
            intervention_id=payload.intervention_id,
            reconciliation_item_id=payload.reconciliation_item_id,
            reviewer_user_id=actor.id,
            dose_input=dose.to_dict(),
            formulation=payload.formulation,
            concentration=payload.concentration,
            rounding_policy=dose.rounding_policy,
            result=result,
            status="reviewed_demo" if mass is not None else "needs_review",
        )
        self.db.add(review)
        self.db.flush()
        return review

    def _intervention(
        self, intervention_id: int, actor: UserModel
    ) -> PharmacyInterventionModel:
        intervention = self.db.get(PharmacyInterventionModel, intervention_id)
        if intervention is None or intervention.institution_id != actor.institution_id:
            raise PharmacyWorkflowError("Intervenção não encontrada.")
        return intervention

    def _require_patient(self, actor: UserModel, patient_id: int | None) -> PatientModel:
        if patient_id is None:
            raise PharmacyWorkflowError("Paciente não encontrado.")
        patient = self.db.get(PatientModel, patient_id)
        if patient is None or patient.institution_id != actor.institution_id:
            raise PharmacyWorkflowError("Paciente não encontrado.")
        if not self._can_access_patient(actor, patient.id):
            raise PharmacyWorkflowError("Vínculo assistencial ativo obrigatório.")
        return patient

    def _can_access_patient(self, actor: UserModel, patient_id: int) -> bool:
        return ObjectAuthorizationService(self.db).can_access_patient(
            actor,
            patient_id,
            capability="patient.read",
            purpose="treatment",
            record_break_glass_object=False,
        )

    @staticmethod
    def _expected_version(actual: int, expected: int) -> None:
        if actual != expected:
            raise PharmacyWorkflowConflict(
                "Versão divergente; recarregue o workflow antes de decidir."
            )

    def _event(
        self,
        intervention: PharmacyInterventionModel,
        actor: UserModel,
        *,
        event_type: str,
        from_status: str | None,
        to_status: str,
        reason: str | None,
    ) -> None:
        self.db.add(
            PharmacyInterventionEventModel(
                intervention_id=intervention.id,
                actor_user_id=actor.id,
                event_type=event_type,
                from_status=from_status,
                to_status=to_status,
                reason=reason,
                details={},
                version=intervention.version,
            )
        )
        self.db.flush()

    def _audit(
        self,
        actor: UserModel,
        action: str,
        intervention: PharmacyInterventionModel,
        status: str,
    ) -> None:
        AuditService(self.db).record_action(
            user=actor,
            action=action,
            resource_type="pharmacy_intervention",
            resource_id=str(intervention.id),
            status=status,
            details={
                "intervention_type": intervention.intervention_type,
                "priority": intervention.priority,
                "version": intervention.version,
            },
        )

    def _audit_reconciliation(
        self,
        actor: UserModel,
        reconciliation: MedicationReconciliationModel,
        status: str,
    ) -> None:
        self.db.add(
            AuditEventModel(
                user_id=actor.id,
                user_role=actor.role,
                action="pharmacy.reconciliation",
                resource_type="medication_reconciliation",
                resource_id=str(reconciliation.id),
                status=status,
                details={"version": reconciliation.version},
            )
        )
