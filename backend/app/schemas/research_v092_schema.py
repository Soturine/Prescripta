from __future__ import annotations

import math
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SyntheticResearchRecord(BaseModel):
    """Bounded synthetic input. Record-level values are never persisted or returned."""

    model_config = ConfigDict(extra="forbid")

    record_key: str = Field(min_length=1, max_length=80)
    group: Literal["exposed", "comparator"]
    outcome: bool
    follow_up_days: float = Field(ge=0, le=36525)
    event_day: float | None = Field(default=None, ge=0, le=36525)
    covariates: dict[str, float | str | bool | None] = Field(default_factory=dict)

    @field_validator("covariates")
    @classmethod
    def finite_numeric_covariates(
        cls, value: dict[str, float | str | bool | None]
    ) -> dict[str, float | str | bool | None]:
        if len(value) > 30:
            raise ValueError("No máximo 30 covariáveis são permitidas.")
        for item in value.values():
            if isinstance(item, float) and not math.isfinite(item):
                raise ValueError("Covariáveis NaN/inf não são aceitas.")
        return value

    @model_validator(mode="after")
    def valid_event_time(self) -> SyntheticResearchRecord:
        if self.outcome and self.event_day is None:
            raise ValueError("Outcome positivo exige event_day.")
        if self.event_day is not None and self.event_day > self.follow_up_days:
            raise ValueError("event_day não pode exceder follow_up_days.")
        return self


class PSMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    estimand: Literal["ATT"] = "ATT"
    covariates: list[str] = Field(default_factory=list, max_length=30)
    ratio: int = Field(default=1, ge=1, le=5)
    caliper: float = Field(default=0.2, gt=0, le=2)
    replacement: Literal[False] = False
    seed: int = Field(default=902, ge=0, le=2_147_483_647)
    missing_data_policy: Literal["complete_case"] = "complete_case"
    normalization: Literal["standardize"] = "standardize"

    @model_validator(mode="after")
    def covariates_when_enabled(self) -> PSMConfig:
        if self.enabled and not self.covariates:
            raise ValueError("PSM exige covariáveis explícitas.")
        return self


class IPTWConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    estimand: Literal["ATE", "ATT"] = "ATE"
    covariates: list[str] = Field(default_factory=list, max_length=30)
    stabilized: bool = True
    truncation_percentiles: tuple[float, float] | None = None
    seed: int = Field(default=902, ge=0, le=2_147_483_647)
    missing_data_policy: Literal["complete_case"] = "complete_case"

    @model_validator(mode="after")
    def validate_config(self) -> IPTWConfig:
        if self.enabled and not self.covariates:
            raise ValueError("IPTW exige covariáveis explícitas.")
        if self.truncation_percentiles:
            low, high = self.truncation_percentiles
            if not 0 <= low < high <= 100:
                raise ValueError("Percentis de truncation são inválidos.")
        return self


class CausalAssumptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consistency: Literal["acknowledged", "needs_review"]
    exchangeability: Literal["acknowledged", "needs_review"]
    positivity: Literal["acknowledged", "needs_review"]
    interference: Literal["acknowledged", "not_applicable", "needs_review"]
    residual_confounding: str = Field(min_length=8, max_length=1000)
    covariate_roles: dict[
        str,
        Literal[
            "confounder",
            "prognostic",
            "instrument_candidate",
            "mediator",
            "collider_risk",
            "unknown",
        ],
    ] = Field(default_factory=dict)


class SensitivityAnalysisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    psm_calipers: list[float] = Field(default_factory=lambda: [0.1, 0.2, 0.3], max_length=4)
    psm_ratios: list[int] = Field(default_factory=lambda: [1, 2], max_length=3)
    iptw_truncations: list[tuple[float, float] | None] = Field(
        default_factory=lambda: [None, (1, 99), (2.5, 97.5), (5, 95)],
        max_length=4,
    )
    iptw_stabilized: list[bool] = Field(default_factory=lambda: [True, False], max_length=2)

    @model_validator(mode="after")
    def bounded_grid(self) -> SensitivityAnalysisConfig:
        if any(not 0 < value <= 2 for value in self.psm_calipers):
            raise ValueError("Sensitivity PSM caliper inválido.")
        if any(not 1 <= value <= 5 for value in self.psm_ratios):
            raise ValueError("Sensitivity PSM ratio inválido.")
        for item in self.iptw_truncations:
            if item is not None and not 0 <= item[0] < item[1] <= 100:
                raise ValueError("Sensitivity IPTW truncation inválida.")
        if self.enabled and (
            len(self.psm_calipers) * len(self.psm_ratios) > 8
            or len(self.iptw_truncations) * len(self.iptw_stabilized) > 8
        ):
            raise ValueError("Sensitivity grid excede o budget.")
        return self


class ComparativeAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_plan_id: str | None = Field(default=None, max_length=36)
    exposed_cohort_run_id: str = Field(min_length=36, max_length=36)
    comparator_cohort_run_id: str = Field(min_length=36, max_length=36)
    data_quality_run_id: str = Field(min_length=36, max_length=36)
    outcome_version_ids: list[str] = Field(min_length=1, max_length=20)
    dataset_snapshot_marker: str = Field(min_length=3, max_length=160)
    dataset_snapshot_hash: str = Field(min_length=64, max_length=64)
    terminology_release_ids: list[str] = Field(default_factory=list, max_length=30)
    mapping_ids: list[str] = Field(default_factory=list, max_length=50)
    covariates: list[str] = Field(default_factory=list, max_length=30)
    records: list[SyntheticResearchRecord] = Field(min_length=2, max_length=5000)
    denominator_unit: Literal["person_days", "person_years"] = "person_years"
    continuity_correction: float | None = Field(default=None, gt=0, le=1)
    small_cell_threshold: int = Field(default=5, ge=1, le=20)
    psm: PSMConfig = Field(default_factory=PSMConfig)
    iptw: IPTWConfig = Field(default_factory=IPTWConfig)
    sensitivity: SensitivityAnalysisConfig = Field(default_factory=SensitivityAnalysisConfig)
    causal_assumptions: CausalAssumptions | None = None
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def validate_groups_and_methods(self) -> ComparativeAnalysisRequest:
        groups = {item.group for item in self.records}
        if groups != {"exposed", "comparator"}:
            raise ValueError("Inputs exigem grupos exposed e comparator.")
        if len({item.record_key for item in self.records}) != len(self.records):
            raise ValueError("record_key deve ser único no input sintético.")
        method_covariates = set(self.psm.covariates) | set(self.iptw.covariates)
        if method_covariates - set(self.covariates):
            raise ValueError("PSM/IPTW referenciam covariável não declarada.")
        if (self.psm.enabled or self.iptw.enabled) and self.causal_assumptions is None:
            raise ValueError("Métodos experimentais exigem checklist de assumptions.")
        return self


class ComparativeAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: str
    institution_id: str
    analysis_plan_id: str | None
    exposed_cohort_run_id: str
    comparator_cohort_run_id: str
    data_quality_run_id: str
    exact_references: dict
    configuration: dict
    results: dict
    diagnostics: dict
    provenance: dict
    input_hash: str
    content_hash: str
    status: str
    synthetic_only: bool
    executed_by_user_id: int
    executed_at: datetime


class MedicationSafetyResearchDraftCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_finding_id: str = Field(min_length=1, max_length=100)
    medication_candidate: str = Field(min_length=2, max_length=220)
    outcome_candidate: str = Field(min_length=2, max_length=220)
    suggested_question: str = Field(min_length=10, max_length=1200)
    source_evidence_ids: list[str] = Field(default_factory=list, max_length=30)
    limitations: list[str] = Field(min_length=1, max_length=20)
    synthetic_only: Literal[True] = True


class MedicationSafetyResearchDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: str
    institution_id: str
    source_finding_id: str
    medication_candidate: str
    outcome_candidate: str
    suggested_question: str
    source_evidence_ids: list[str]
    limitations: list[str]
    status: str
    synthetic_only: bool
    created_by_user_id: int
    created_at: datetime


class EvidenceFieldCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: Literal[
        "study_design",
        "population",
        "sample_size",
        "exposure",
        "comparator",
        "outcomes",
        "follow_up",
        "methods",
        "adjustment",
        "effect_measures",
        "limitations",
        "funding_conflicts",
    ]
    value: str = Field(min_length=1, max_length=2000)
    locator: str = Field(min_length=1, max_length=220)
    supporting_text: str = Field(min_length=1, max_length=4000)


class EvidenceExtractionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=36, max_length=36)
    content: str = Field(min_length=1, max_length=200_000)
    candidates: list[EvidenceFieldCandidate] = Field(default_factory=list, max_length=50)
    schema_version: Literal["literature-extraction-v2"] = "literature-extraction-v2"


class EvidenceExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    institution_id: str
    schema_version: str
    content_hash: str
    extracted_fields: dict
    claims: list[dict]
    prompt_injection_detected: bool
    status: str
    created_by_user_id: int
    created_at: datetime


class ResearchQueryPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(min_length=36, max_length=36)
    dataset_snapshot_marker: str = Field(min_length=3, max_length=160)
    natural_language_question: str = Field(min_length=4, max_length=1000)
    proposed_sql: str = Field(min_length=8, max_length=20_000)
    row_limit: int = Field(default=100, ge=1, le=1000)
    timeout_ms: int = Field(default=3000, ge=100, le=10_000)
    lock_timeout_ms: int = Field(default=500, ge=50, le=5000)
    cost_budget: int = Field(default=10_000, ge=1, le=1_000_000)
    max_ast_nodes: int = Field(default=200, ge=20, le=500)
    max_ast_depth: int = Field(default=12, ge=3, le=30)
    max_total_cost: float = Field(default=5000, gt=0, le=1_000_000)
    max_plan_rows: int = Field(default=10_000, ge=1, le=1_000_000)
    max_plan_nodes: int = Field(default=40, ge=1, le=200)
    max_output_bytes: int = Field(default=200_000, ge=1000, le=1_000_000)
    purpose: str = Field(min_length=3, max_length=120)


class ResearchQueryPreviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: str
    institution_id: str
    dataset_snapshot_marker: str
    natural_language_question_hash: str
    normalized_query: str
    structured_interpretation: dict
    policy: dict
    estimated_cost: int
    status: str
    enabled: bool
    executed: bool
    result: dict
    created_by_user_id: int
    created_at: datetime


class ResearchQueryExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_preview: Literal[True]
