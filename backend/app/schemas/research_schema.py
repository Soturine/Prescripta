from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResearchStudyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=5, max_length=240)
    slug: str = Field(min_length=3, max_length=160, pattern=r"^[a-z0-9][a-z0-9-]+$")
    description: str = Field(default="", max_length=4000)
    research_question: str = Field(min_length=10, max_length=4000)
    objective: str = Field(min_length=10, max_length=4000)
    design: Literal["retrospective_cohort", "cross_sectional", "descriptive"]
    data_source_classification: Literal["synthetic", "internal_demo"] = "synthetic"


class ResearchStudyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    title: str
    slug: str
    description: str
    research_question: str
    objective: str
    design: str
    status: str
    owner_user_id: int
    current_protocol_version_id: str | None
    demo_only: bool
    data_source_classification: str
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StudyProtocolVersionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    population: dict = Field(min_length=1)
    exposure: dict = Field(default_factory=dict)
    comparator: dict = Field(default_factory=dict)
    outcome: dict = Field(min_length=1)
    index_date: dict = Field(min_length=1)
    washout: dict = Field(default_factory=dict)
    follow_up: dict = Field(min_length=1)
    censoring: dict = Field(default_factory=dict)
    inclusion: list[dict] = Field(default_factory=list, max_length=50)
    exclusion: list[dict] = Field(default_factory=list, max_length=50)
    covariates: list[dict] = Field(default_factory=list, max_length=50)
    missing_data_strategy: dict = Field(min_length=1)
    statistical_plan: dict = Field(min_length=1)
    limitations: list[str] = Field(min_length=1, max_length=30)
    source_refs: list[str] = Field(min_length=1, max_length=30)


class ResearchReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["in_review", "reviewed_demo", "superseded", "archived"]
    note: str = Field(min_length=8, max_length=1000)


class StudyProtocolVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: str
    institution_id: str
    version: int
    population: dict
    exposure: dict
    comparator: dict
    outcome: dict
    index_date: dict
    washout: dict
    follow_up: dict
    censoring: dict
    inclusion: list[dict]
    exclusion: list[dict]
    covariates: list[dict]
    missing_data_strategy: dict
    statistical_plan: dict
    limitations: list[str]
    source_refs: list[str]
    status: str
    definition_hash: str
    authored_by_user_id: int
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class ConceptSetMemberInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    terminology_system: Literal["CID-10", "ICD-10", "SNOMED CT", "LOINC", "RxNorm", "ATC", "OMOP"]
    terminology_version: str = Field(min_length=1, max_length=80)
    concept_id: str | None = Field(default=None, max_length=80)
    concept_code: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=2, max_length=240)
    excluded: bool = False


class ConceptSetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=220)
    domain: Literal["condition", "medication", "measurement", "procedure", "demographic"]
    terminology_versions: dict[str, str] = Field(min_length=1, max_length=10)
    terminology_release_ids: list[str] = Field(default_factory=list, max_length=10)
    include_descendants: bool = False
    source_refs: list[str] = Field(min_length=1, max_length=30)
    license_metadata: dict = Field(min_length=1)
    provenance: dict = Field(min_length=1)
    members: list[ConceptSetMemberInput] = Field(min_length=1, max_length=500)


class ConceptSetReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal[
        "terminology_matched",
        "human_reviewed",
        "approved_for_demo_study",
        "rejected",
    ]
    note: str = Field(min_length=8, max_length=1000)


class ConceptSetVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    concept_set_id: str
    institution_id: str
    version: int
    status: str
    terminology_versions: dict
    terminology_release_refs: list[dict] = Field(default_factory=list)
    include_descendants: bool
    source_refs: list[str]
    license_metadata: dict
    provenance: dict
    definition_hash: str
    authored_by_user_id: int
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class ConceptSetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    name: str
    domain: str
    status: str
    owner_user_id: int
    reviewer_user_id: int | None
    current_version_id: str | None
    created_at: datetime
    version: ConceptSetVersionRead | None = None
    members: list[dict] = Field(default_factory=list)


class CohortDefinitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=220)
    definition: dict


class CohortReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["reviewed_demo", "rejected", "superseded"]
    note: str = Field(min_length=8, max_length=1000)


class CohortVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cohort_definition_id: str
    study_id: str
    institution_id: str
    version: int
    definition: dict
    definition_hash: str
    status: str
    query_cost: int
    authored_by_user_id: int
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class OutcomeDefinitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=220)
    domain: Literal["condition", "medication", "measurement", "procedure", "event"]
    concept_set_version_ids: list[str] = Field(default_factory=list, max_length=20)
    event_qualification: dict = Field(min_length=1)
    observation_window: dict = Field(min_length=1)
    temporal_relationship: str = Field(min_length=2, max_length=80)
    source_refs: list[str] = Field(min_length=1, max_length=30)
    limitations: list[str] = Field(min_length=1, max_length=30)


class OutcomeDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: str
    institution_id: str
    name: str
    domain: str
    concept_set_version_ids: list[str]
    event_qualification: dict
    observation_window: dict
    temporal_relationship: str
    source_refs: list[str]
    limitations: list[str]
    version: int
    review_status: str
    definition_hash: str
    authored_by_user_id: int
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class OutcomeReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["reviewed_demo", "rejected", "superseded"]
    note: str = Field(min_length=8, max_length=1000)


class CohortRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_snapshot_marker: str = Field(min_length=3, max_length=160)


class CohortRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: str
    cohort_version_id: str
    protocol_version_id: str | None
    institution_id: str
    data_snapshot_marker: str
    executed_at: datetime
    executed_by_user_id: int
    definition_hash: str
    source_version_refs: list[str]
    result_count: int
    attrition: list[dict]
    analytics: dict
    engine_version: str
    prescripta_version: str
    status: str
    warnings: list[str]
    run_hash: str
    synthetic_demo_notice: str = (
        "Dados sintéticos/demonstrativos. Métricas não representam população real "
        "e não devem ser usadas para inferência clínica."
    )


class ResearchSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cohort_run_id: str
    snapshot_type: str
    payload: dict
    snapshot_hash: str
    created_at: datetime


class TimelineEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int = Field(gt=0)
    event_type: Literal[
        "medication_start",
        "medication_stop",
        "dose_change",
        "diagnosis",
        "measurement",
        "procedure",
        "adverse_event",
        "hospitalization",
        "encounter",
        "pharmacy_intervention",
    ]
    occurred_at: datetime
    source: str = Field(min_length=2, max_length=100)
    source_ref: str = Field(min_length=3, max_length=220)
    concept_system: str | None = Field(default=None, max_length=40)
    concept_code: str | None = Field(default=None, max_length=120)
    concept_label: str | None = Field(default=None, max_length=240)
    summary: str = Field(min_length=3, max_length=500)
    structured_payload: dict = Field(default_factory=dict)
    provenance: dict = Field(default_factory=dict)
    visibility_classification: Literal["clinical", "restricted"] = "clinical"


class TimelineEventRead(TimelineEventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    created_at: datetime


class DataQualityFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str | None
    institution_id: str
    rule: str
    severity: str
    resource_type: str
    resource_id: str
    field: str
    message: str
    source: str
    detected_at: datetime
    status: str
    resolution: str | None


class DataQualityRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    study_id: str | None
    cohort_run_id: str | None
    data_snapshot_marker: str | None
    data_snapshot_hash: str | None
    terminology_snapshot: dict
    ruleset_version: str
    scope_status: str
    status: str
    summary: dict
    content_hash: str
    executed_by_user_id: int
    executed_at: datetime
    findings_created: int
    findings_open: int
    by_rule: dict[str, int]


class DataQualityRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_id: str | None = None
    cohort_run_id: str | None = None


class DataQualityAcknowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolution: str = Field(min_length=8, max_length=500)


class AnalysisPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohort_run_id: str
    data_quality_run_id: str | None = None
    outcome_version_ids: list[str] = Field(default_factory=list, max_length=20)
    objectives: list[str] = Field(min_length=1, max_length=20)
    variables: list[dict] = Field(default_factory=list, max_length=30)
    steps: list[dict] = Field(min_length=1, max_length=20)
    descriptive_metrics: list[str] = Field(min_length=1, max_length=20)
    subgroup_definitions: list[dict] = Field(default_factory=list, max_length=10)
    missing_data_approach: Literal["report_only", "complete_case_descriptive"]
    methods: list[
        Literal[
            "population_count",
            "numeric_summary",
            "categorical_distribution",
            "prevalence",
            "baseline_table_1",
            "resource_utilization",
        ]
    ] = Field(min_length=1, max_length=10)
    planned_outputs: list[
        Literal[
            "summary_cards", "table_1", "distribution_chart", "attrition_table", "research_package"
        ]
    ] = Field(min_length=1, max_length=10)
    output_specification: dict = Field(default_factory=dict)
    source_refs: list[str] = Field(min_length=1, max_length=30)
    limitations: list[str] = Field(min_length=1, max_length=30)


class AnalysisPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: str
    institution_id: str
    version: int
    cohort_run_id: str | None
    data_quality_run_id: str | None
    outcome_version_refs: list[dict] = Field(default_factory=list)
    objectives: list[str]
    variables: list[dict]
    steps: list[dict]
    descriptive_metrics: list[str]
    subgroup_definitions: list[dict]
    missing_data_approach: str
    methods: list[str]
    planned_outputs: list[str]
    output_specification: dict
    source_refs: list[str]
    limitations: list[str]
    definition_hash: str
    status: str
    authored_by_user_id: int
    reviewed_by_user_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class AnalysisRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: str
    analysis_plan_id: str
    cohort_run_id: str
    data_quality_run_id: str | None
    outcome_version_refs: list[dict] = Field(default_factory=list)
    institution_id: str
    data_snapshot_marker: str
    status: str
    results: dict
    provenance: dict
    content_hash: str
    executed_by_user_id: int
    executed_at: datetime


class ResearchPackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    study_id: str
    analysis_run_id: str
    institution_id: str
    manifest: dict
    files: dict
    content_hash: str
    aggregate_only: bool
    exported_by_user_id: int
    created_at: datetime


class PatientJourneyRead(BaseModel):
    study_id: str
    patient_ref: str
    events: list[dict]
    event_count: int
    aggregate_only: bool = False
    synthetic_only: bool = True
    warning: str = "Jornada sintética demonstrativa; sem uso clínico."


class ResearchWorkspaceRead(BaseModel):
    studies: int
    concept_sets: int
    cohort_runs: int
    open_data_quality_findings: int
    recent_runs: list[CohortRunRead]
    synthetic_demo_notice: str


class StudyWorkspaceRead(BaseModel):
    study: ResearchStudyRead
    protocol_versions: list[StudyProtocolVersionRead]
    cohort_versions: list[CohortVersionRead]
    outcomes: list[OutcomeDefinitionRead]
    runs: list[CohortRunRead]
    concept_set_version_ids: list[str]
    analysis_plans: list[AnalysisPlanRead] = Field(default_factory=list)
    analysis_runs: list[AnalysisRunRead] = Field(default_factory=list)
    data_quality: dict = Field(default_factory=dict)
    readiness: list[dict] = Field(default_factory=list)
    research_packages: list[ResearchPackageRead] = Field(default_factory=list)


class StudyProtocolReviewEnvelope(BaseModel):
    protocol: StudyProtocolVersionRead
    study: ResearchStudyRead

    @model_validator(mode="after")
    def same_study(self) -> StudyProtocolReviewEnvelope:
        if self.protocol.study_id != self.study.id:
            raise ValueError("protocol e study divergentes")
        return self
