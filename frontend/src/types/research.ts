export type ResearchStudy = {
  id: string;
  institution_id: string;
  title: string;
  slug: string;
  description: string;
  research_question: string;
  objective: string;
  design: "retrospective_cohort" | "cross_sectional" | "descriptive";
  status: string;
  owner_user_id: number;
  current_protocol_version_id: string | null;
  demo_only: boolean;
  data_source_classification: "synthetic" | "internal_demo";
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ResearchStudyPayload = Pick<
  ResearchStudy,
  | "title"
  | "slug"
  | "description"
  | "research_question"
  | "objective"
  | "design"
  | "data_source_classification"
>;

export type StudyProtocolVersion = {
  id: string;
  study_id: string;
  institution_id: string;
  version: number;
  population: Record<string, unknown>;
  exposure: Record<string, unknown>;
  comparator: Record<string, unknown>;
  outcome: Record<string, unknown>;
  index_date: Record<string, unknown>;
  washout: Record<string, unknown>;
  follow_up: Record<string, unknown>;
  censoring: Record<string, unknown>;
  inclusion: Array<Record<string, unknown>>;
  exclusion: Array<Record<string, unknown>>;
  covariates: Array<Record<string, unknown>>;
  missing_data_strategy: Record<string, unknown>;
  statistical_plan: Record<string, unknown>;
  limitations: string[];
  source_refs: string[];
  status: string;
  definition_hash: string;
  authored_by_user_id: number;
  reviewed_by_user_id: number | null;
  reviewed_at: string | null;
  created_at: string;
};

export type ConceptSetVersion = {
  id: string;
  concept_set_id: string;
  institution_id: string;
  version: number;
  status: string;
  terminology_versions: Record<string, string>;
  include_descendants: boolean;
  source_refs: string[];
  license_metadata: Record<string, unknown>;
  provenance: Record<string, unknown>;
  definition_hash: string;
  authored_by_user_id: number;
  reviewed_by_user_id: number | null;
  reviewed_at: string | null;
  created_at: string;
};

export type ConceptSet = {
  id: string;
  institution_id: string;
  name: string;
  domain: string;
  status: string;
  owner_user_id: number;
  reviewer_user_id: number | null;
  current_version_id: string | null;
  created_at: string;
  version: ConceptSetVersion | null;
  members: Array<Record<string, unknown>>;
};

export type CohortVersion = {
  id: string;
  cohort_definition_id: string;
  study_id: string;
  institution_id: string;
  version: number;
  definition: CohortDefinition;
  definition_hash: string;
  status: string;
  query_cost: number;
  authored_by_user_id: number;
  reviewed_by_user_id: number | null;
  reviewed_at: string | null;
  created_at: string;
};

export type CohortCriterion = {
  criterion: "age" | "sex" | "medication_exposure" | "condition" | "measurement_exists" | "procedure" | "date" | "demographic";
  operator: string;
  value?: string | number | string[] | number[] | null;
  field?: string | null;
  concept_set_version_id?: string | null;
  window?: { before_index_days?: number; after_index_days?: number };
  label?: string;
};

export type CohortDefinition = {
  all: CohortCriterion[];
  exclude: CohortCriterion[];
};

export type OutcomeDefinition = {
  id: string;
  study_id: string;
  institution_id: string;
  name: string;
  domain: string;
  concept_set_version_ids: string[];
  event_qualification: Record<string, unknown>;
  observation_window: Record<string, unknown>;
  temporal_relationship: string;
  source_refs: string[];
  limitations: string[];
  version: number;
  review_status: string;
  definition_hash: string;
  authored_by_user_id: number;
  reviewed_by_user_id: number | null;
  created_at: string;
};

export type AttritionStep = {
  sequence: number;
  criterion: CohortCriterion;
  label: string;
  before_count: number;
  excluded_count: number;
  after_count: number;
  criterion_hash: string;
};

export type CohortRun = {
  id: string;
  study_id: string;
  cohort_version_id: string;
  protocol_version_id: string | null;
  institution_id: string;
  data_snapshot_marker: string;
  executed_at: string;
  executed_by_user_id: number;
  definition_hash: string;
  source_version_refs: string[];
  result_count: number;
  attrition: AttritionStep[];
  analytics: Record<string, unknown>;
  engine_version: string;
  prescripta_version: string;
  status: string;
  warnings: string[];
  run_hash: string;
  synthetic_demo_notice: string;
};

export type ResearchWorkspace = {
  studies: number;
  concept_sets: number;
  cohort_runs: number;
  open_data_quality_findings: number;
  recent_runs: CohortRun[];
  synthetic_demo_notice: string;
};

export type StudyWorkspace = {
  study: ResearchStudy;
  protocol_versions: StudyProtocolVersion[];
  cohort_versions: CohortVersion[];
  outcomes: OutcomeDefinition[];
  runs: CohortRun[];
  concept_set_version_ids: string[];
};

export type DataQualityFinding = {
  id: string;
  institution_id: string;
  rule: string;
  severity: string;
  resource_type: string;
  resource_id: string;
  field: string;
  message: string;
  source: string;
  detected_at: string;
  status: string;
  resolution: string | null;
};

export type AIInteraction = {
  id: string;
  provider: string;
  model: string | null;
  task_type: string;
  source_ids: string[];
  study_id: string | null;
  input_hash: string;
  output_hash: string;
  generated_at: string;
  latency_ms: number;
  status: string;
  fallback_used: boolean;
  data_classification: string;
  human_review_status: string;
  output_payload: Record<string, unknown>;
};

export type EvidenceSource = {
  id: string;
  institution_id: string;
  source_type: string;
  title: string;
  identifier: string;
  url: string | null;
  publisher: string | null;
  jurisdiction: string | null;
  publication_date: string | null;
  access_date: string | null;
  source_version: string | null;
  review_status: string;
  reviewer_user_id: number | null;
  license_metadata: Record<string, unknown>;
  content_hash: string | null;
  provenance: Record<string, unknown>;
  created_by_user_id: number;
  created_at: string;
};

export type EvidenceLink = {
  id: string;
  institution_id: string;
  source_id: string;
  target_type: string;
  target_id: string;
  relationship: string;
  locator: string;
  review_status: string;
  created_by_user_id: number;
  created_at: string;
};
