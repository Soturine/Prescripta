from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProtocolMedicationScopeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medication_id: int = Field(gt=0)
    concept_set_ref: str | None = Field(default=None, max_length=160)


class ProtocolConditionScopeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    terminology_system: str = Field(min_length=2, max_length=80)
    terminology_version: str = Field(min_length=1, max_length=80)
    condition_code: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=2, max_length=220)


class ProtocolCredentialRequirementInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    credential_type: str = Field(min_length=2, max_length=80)
    credential_region: str | None = Field(default=None, max_length=20)
    verification_required: bool = True
    unexpired_required: bool = True


class ProtocolPrescribingScopeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_routes: list[str] = Field(min_length=1, max_length=12)
    dose_min: Decimal | None = Field(default=None, gt=0)
    dose_max: Decimal | None = Field(default=None, gt=0)
    dose_unit: str | None = Field(default=None, max_length=40)
    frequency_min_per_day: int | None = Field(default=None, gt=0, le=96)
    frequency_max_per_day: int | None = Field(default=None, gt=0, le=96)
    max_duration_days: int | None = Field(default=None, gt=0, le=3650)
    min_age_years: int | None = Field(default=None, ge=0, le=130)
    max_age_years: int | None = Field(default=None, ge=0, le=130)
    min_weight_kg: Decimal | None = Field(default=None, gt=0, le=400)
    max_weight_kg: Decimal | None = Field(default=None, gt=0, le=400)
    constraints: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ranges(self) -> "ProtocolPrescribingScopeInput":
        for low, high, label in (
            (self.dose_min, self.dose_max, "dose"),
            (self.frequency_min_per_day, self.frequency_max_per_day, "frequência"),
            (self.min_age_years, self.max_age_years, "idade"),
            (self.min_weight_kg, self.max_weight_kg, "peso"),
        ):
            if low is not None and high is not None and low > high:
                raise ValueError(f"faixa de {label} invertida")
        if (self.dose_min is not None or self.dose_max is not None) and not self.dose_unit:
            raise ValueError("faixa de dose exige unidade")
        return self


class InstitutionalClinicalProtocolCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9][a-z0-9_.-]+$")
    name: str = Field(min_length=3, max_length=220)
    program: str | None = Field(default=None, max_length=160)


class InstitutionalClinicalProtocolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution_id: str
    code: str
    name: str
    program: str | None
    status: str
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class InstitutionalClinicalProtocolVersionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1, max_length=80)
    effective_from: datetime
    effective_until: datetime | None = None
    source_refs: list[str] = Field(min_length=1, max_length=20)
    clinical_context: dict = Field(default_factory=dict)
    eligible_professions: list[str] = Field(default_factory=lambda: ["nursing"])
    required_capability: str = "nursing.protocol_prescribe"
    required_parameters: list[str] = Field(default_factory=list, max_length=20)
    contraindications: list[str] = Field(default_factory=list, max_length=30)
    requires_second_review: bool = False
    second_reviewer_role: str | None = Field(default=None, max_length=40)
    override_policy: dict = Field(default_factory=lambda: {"allowed": False})
    prescribing_scope: ProtocolPrescribingScopeInput
    medications: list[ProtocolMedicationScopeInput] = Field(min_length=1, max_length=100)
    conditions: list[ProtocolConditionScopeInput] = Field(min_length=1, max_length=100)
    credentials: list[ProtocolCredentialRequirementInput] = Field(
        min_length=1, max_length=20
    )

    @model_validator(mode="after")
    def validate_dates_and_review(self) -> "InstitutionalClinicalProtocolVersionCreate":
        if self.effective_until is not None and self.effective_until <= self.effective_from:
            raise ValueError("effective_until deve ocorrer após effective_from")
        if self.requires_second_review and not self.second_reviewer_role:
            raise ValueError("segunda revisão exige perfil revisor")
        return self


class ProtocolVersionReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["reviewed_demo", "rejected", "revoked"]
    note: str = Field(min_length=8, max_length=500)


class InstitutionalClinicalProtocolVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    protocol_id: int
    institution_id: str
    version: str
    status: str
    review_status: str
    effective_from: datetime
    effective_until: datetime | None
    source_refs: list[str]
    clinical_context: dict
    eligible_professions: list[str]
    required_capability: str
    required_parameters: list[str]
    contraindications: list[str]
    requires_second_review: bool
    second_reviewer_role: str | None
    override_policy: dict
    definition_hash: str
    created_by_user_id: int
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class ProtocolVersionDetailRead(InstitutionalClinicalProtocolVersionRead):
    prescribing_scope: dict
    medications: list[dict]
    conditions: list[dict]
    credentials: list[dict]
