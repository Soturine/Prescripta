from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.prescription_schema import MedicationDoseInputSchema

INTERVENTION_TYPES = Literal[
    "duplicidade",
    "dose",
    "concentracao",
    "forma",
    "interacao",
    "reconciliacao",
    "administracao",
    "disponibilidade_demo",
    "contraindicacao",
    "informacao_insuficiente",
]
RECONCILIATION_STATES = Literal[
    "confirmed",
    "discontinued",
    "corrected",
    "duplicated",
    "needs_review",
    "unresolved",
]


class PharmacyInterventionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int = Field(gt=0)
    prescription_audit_id: int | None = Field(default=None, gt=0)
    medication_id: int | None = Field(default=None, gt=0)
    intervention_type: INTERVENTION_TYPES
    severity: Literal["low", "moderate", "high", "critical"]
    priority: Literal["routine", "priority", "urgent"]
    problem: str = Field(min_length=8, max_length=2000)
    recommendation: str = Field(min_length=8, max_length=2000)
    source_refs: list[str] = Field(min_length=1, max_length=20)
    dose_snapshot: dict = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=8, max_length=160)
    cosignature_required: bool = False


class PharmacyInterventionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["accepted", "rejected"]
    reason: str = Field(min_length=8, max_length=2000)
    expected_version: int = Field(gt=0)


class PharmacyInterventionResolve(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolution: str = Field(min_length=8, max_length=2000)
    expected_version: int = Field(gt=0)


class PharmacyInterventionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution_id: str
    patient_id: int
    prescription_audit_id: int | None
    medication_id: int | None
    pharmacist_user_id: int
    intervention_type: str
    severity: str
    priority: str
    problem: str
    recommendation: str
    source_refs: list[str]
    dose_snapshot: dict
    status: str
    idempotency_key: str
    version: int
    cosignature_required: bool
    cosigned_by_user_id: int | None
    cosigned_at: datetime | None
    decision_actor_user_id: int | None
    accepted: bool | None
    rejection_reason: str | None
    resolution: str | None
    reviewed_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PharmacyInterventionEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intervention_id: int
    actor_user_id: int
    event_type: str
    from_status: str | None
    to_status: str
    reason: str | None
    details: dict
    version: int
    created_at: datetime


class ReconciliationItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medication_id: int | None = Field(default=None, gt=0)
    medication_name: str = Field(min_length=2, max_length=180)
    source_ref: str = Field(min_length=2, max_length=220)
    discrepancy: str | None = Field(default=None, max_length=2000)
    formulation: str | None = Field(default=None, max_length=160)
    concentration: str | None = Field(default=None, max_length=120)


class MedicationReconciliationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int = Field(gt=0)
    source_refs: list[str] = Field(min_length=1, max_length=20)
    idempotency_key: str = Field(min_length=8, max_length=160)
    items: list[ReconciliationItemCreate] = Field(min_length=1, max_length=200)


class ReconciliationItemDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RECONCILIATION_STATES
    action: str = Field(min_length=2, max_length=80)
    justification: str = Field(min_length=8, max_length=2000)
    expected_version: int = Field(gt=0)


class MedicationReconciliationItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reconciliation_id: int
    medication_id: int | None
    medication_name: str
    source_ref: str
    discrepancy: str | None
    status: str
    action: str | None
    justification: str | None
    author_user_id: int | None
    formulation: str | None
    concentration: str | None
    history: list[dict]
    version: int
    updated_at: datetime


class MedicationReconciliationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution_id: str
    patient_id: int
    pharmacist_user_id: int
    status: str
    source_refs: list[str]
    idempotency_key: str
    version: int
    created_at: datetime
    completed_at: datetime | None
    items: list[MedicationReconciliationItemRead] = Field(default_factory=list)


class MedicationFormulationReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intervention_id: int | None = Field(default=None, gt=0)
    reconciliation_item_id: int | None = Field(default=None, gt=0)
    formulation: str = Field(min_length=2, max_length=160)
    concentration: str = Field(min_length=2, max_length=120)
    dose: MedicationDoseInputSchema

    @model_validator(mode="after")
    def require_target(self) -> "MedicationFormulationReviewCreate":
        if (self.intervention_id is None) == (self.reconciliation_item_id is None):
            raise ValueError("informe exatamente um alvo de revisão")
        return self


class MedicationFormulationReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution_id: str
    intervention_id: int | None
    reconciliation_item_id: int | None
    reviewer_user_id: int
    dose_input: dict
    formulation: str
    concentration: str
    rounding_policy: str
    result: dict
    status: str
    created_at: datetime
