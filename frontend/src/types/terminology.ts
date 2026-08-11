export type TerminologySource = {
  id: string;
  canonical_system: string;
  public_name: string;
  steward: string;
  family: string;
  source_reference: string;
  jurisdiction: string | null;
  locale: string | null;
  active: boolean;
};

export type TerminologyRelease = {
  id: string;
  source_id: string;
  edition: string;
  version: string;
  release_date: string | null;
  source_checksum: string;
  source_artifact_name: string;
  license_identifier: string;
  license_name: string;
  license_reference: string;
  redistributable: boolean;
  requires_license: boolean;
  requires_login: boolean;
  requires_attribution: boolean;
  license_status: string;
  license_note: string;
  status: string;
  content_hash: string;
};

export type TerminologyConcept = {
  id: string;
  release_id: string;
  source_system: string;
  source_code: string;
  display: string;
  aliases: string[];
  domain: string;
  standard_status: string;
  omop_concept_id: number | null;
  invalid_reason: string | null;
  content_hash: string;
};

export type TerminologyConceptPage = {
  items: TerminologyConcept[];
  offset: number;
  limit: number;
  total: number;
  suggestion_only: boolean;
};

export type TerminologyMapping = {
  id: string;
  mapping_family_id: string;
  source_concept_id: string;
  target_concept_id: string;
  relationship_type: string;
  mapping_method: string;
  domain_expectation: string;
  rationale: string;
  version: number;
  mapping_hash: string;
  status: string;
  authored_by_user_id: number;
  reviewed_by_user_id: number | null;
  review_note: string | null;
};

export type OmopEtlRun = {
  id: string;
  study_id: string;
  cohort_run_id: string;
  synthetic_only: boolean;
  source_snapshot_marker: string;
  source_snapshot_hash: string;
  adapter_version: string;
  cdm_version: "5.4";
  terminology_release_ids: string[];
  mapping_hashes: string[];
  status: string;
  metrics: Record<string, Record<string, number>>;
  warnings: string[];
  errors: string[];
  manifest: Record<string, unknown>;
  export_hash: string;
};

export type OmopCompatibility = {
  cdm_version: "5.4";
  claim_level: "omop_v5_4_partial_adapter";
  targets: Array<{
    target: string;
    level: string;
    proven: string;
    missing: string;
    claim_allowed: string;
  }>;
  synthetic_only: boolean;
  ohdsi_tool_validated: boolean;
  content_hash: string;
};
