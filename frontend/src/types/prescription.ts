import type { MedicationCounselingSummary } from "./medication";
import type { PatientKnowledgeBundle } from "./patient";

export type RiskLevel = "baixo" | "moderado" | "alto" | "critico";
export type PrescriptionStatus = "liberado" | "atencao" | "bloqueado";

export type Alert = {
  code: string;
  title: string;
  description: string;
  severity: RiskLevel;
  recommendation: string;
};

export type PrescriptionCheckPayload = {
  patient_id: number;
  medication_id: number;
  dose_mg?: number | null;
  frequency_per_day?: number | null;
  route?: string | null;
  dose?: StructuredDoseInput | null;
  duration_days: number | null;
  indication: string | null;
  professional_notes: string | null;
  contextual_activity_answer?: string | null;
};

export type StructuredDoseInput = {
  amount: number;
  amount_unit: string;
  administration_kind: "bolus" | "intermittent" | "continuous" | "prn";
  concentration_value?: number | null;
  concentration_unit?: string | null;
  volume?: number | null;
  volume_unit?: string | null;
  rate_value?: number | null;
  rate_unit?: string | null;
  frequency_per_day?: number | null;
  interval_value?: number | null;
  interval_unit?: string | null;
  duration_value?: number | null;
  duration_unit?: string | null;
  route?: string | null;
  site?: string | null;
  procedure_context?: string | null;
  prn: boolean;
  max_administrations_per_day?: number | null;
  source_id?: string | null;
  source_version?: string | null;
  precision: string;
  rounding_policy: string;
};

export type DecisionOverride = {
  id: number;
  prescription_audit_id: number;
  requested_by_user_id: number;
  reason: string;
  status: string;
  reviewed_by_user_id: number | null;
  review_decision: string | null;
  review_note: string | null;
  requested_at: string;
  reviewed_at: string | null;
};

export type DoseSummary = {
  daily_total_mg: number | null;
  duration_days: number | null;
  estimated_cumulative_dose_mg: number | null;
  max_daily_dose_mg: number;
  max_duration_days: number | null;
  max_cumulative_dose_mg: number | null;
  continuous_use: boolean;
  monitoring_required: boolean;
  monitoring_notes: string | null;
  exposure_plan: {
    dose_per_administration_mg: number | null;
    administrations_per_day: number;
    calculated_daily_dose_mg: number | null;
    calculated_cumulative_dose_mg: number | null;
    has_missing_duration_for_cumulative_dose: boolean;
  };
  mechanism_profile: {
    mechanism_of_action: string | null;
    absorption_notes: string | null;
    distribution_notes: string | null;
    metabolism_organs: string[];
    elimination_organs: string[];
    renal_elimination_level: string;
    hepatic_metabolism_level: string;
    cyp_interactions: string[];
    pharmacodynamic_notes: string | null;
    pharmacokinetic_notes: string | null;
    clinical_interpretation: string | null;
  };
  condition_specific_limits: Record<string, number>;
  weight_based_rule?: {
    enabled: boolean;
    dose_mg_per_kg: number | null;
    patient_weight_kg: number | null;
    calculated_limit_mg_per_day: number | null;
    calculated_daily_dose_mg: number;
    was_considered: boolean;
  };
  anthropometrics?: {
    age: number | null;
    age_group: string;
    weight_kg: number;
    height_cm: number | null;
    bmi: number | null;
    bmi_considered: boolean;
  };
  patient_data_considered?: Array<{ label: string; value: string }>;
};

export type Compatibility = {
  level: "alta" | "moderada" | "baixa";
  score: number;
  patient_factors_considered: string[];
  medication_factors_considered: string[];
  reasons: string[];
  review_required: boolean;
  educational_notice: string;
};

export type RagEvidence = {
  source: string;
  excerpt: string;
  score: number;
  matched_terms: string[];
  educational_notice: string;
  jurisdiction: string;
  source_name: string;
  source_url: string | null;
  evidence_type: string;
  validation_status: string;
  active_ingredient: string | null;
  commercial_names: string[];
  extracted_sections: string[];
  retrieved_at: string | null;
  version: string;
};

export type AlternativeMedication = {
  medication_id: number;
  name: string;
  active_ingredient: string;
  therapeutic_class: string;
  similarity_reason: string;
  status: PrescriptionStatus;
  risk_level: RiskLevel;
  top_alerts: Alert[];
  observation: string;
};

export type ClinicalContextGraph = {
  nodes: Array<{ id: string; label: string; type: string }>;
  edges: Array<{ from: string; to: string; label: string }>;
  patient_factors: string[];
  medication_factors: string[];
};

export type MissingDataMode = {
  incomplete_history: boolean;
  message: string;
  limitation_summary: string;
  missing_data: string[];
  does_not_block_flow: boolean;
};

export type ContextualQuestion = {
  should_ask: boolean;
  question: string | null;
  options: string[];
  reason: string | null;
};

export type FunctionalContextSummary = {
  profile_known: boolean;
  unknown_fields: string[];
  personalized_warnings: string[];
  generic_warnings: string[];
  question: ContextualQuestion;
};

export type PatientCounselingResponse = {
  summary: MedicationCounselingSummary | null;
  orientation_points: string[];
  red_flags: string[];
  source_label: string | null;
  review_status: string | null;
  generated_by_ai: boolean;
  requires_review: boolean;
  functional_context: FunctionalContextSummary;
  missing_data_mode: MissingDataMode;
  educational_notice: string;
};

export type PrescriptionCheckResult = {
  decision: {
    schema_version: string;
    decision_status:
      | "not_evaluated"
      | "insufficient_data"
      | "insufficient_coverage"
      | "review_required"
      | "blocked"
      | "evaluated_no_issue";
    legacy_status: PrescriptionStatus;
    highest_severity: RiskLevel;
    coverage: {
      status: string;
      sufficient: boolean;
      evaluated: string[];
      not_evaluated: Array<Record<string, string>>;
      reasons: string[];
      source_ids: string[];
    };
    findings: Array<Alert & { module: string; source_ids: string[]; hard_block: boolean }>;
    required_actions: string[];
    missing_data: string[];
    rule_versions: string[];
    source_snapshot: Array<Record<string, unknown>>;
    override_policy: {
      allowed: boolean;
      reason_required: boolean;
      second_reviewer_role: string | null;
      policy_status: string | null;
      note: string;
    };
    human_review_required: boolean;
    evaluated_at: string;
    correlation_id: string;
    recommendation: string;
  };
  coverage_status: string;
  status: PrescriptionStatus;
  risk_level: RiskLevel;
  alerts: Alert[];
  recommendation: string;
  human_review_required: boolean;
  audit_id: number;
  dose_summary: DoseSummary;
  compatibility: Compatibility;
  patient_factors_considered: string[];
  medication_factors_considered: string[];
  rag_evidence: RagEvidence[];
  clinical_context_graph: ClinicalContextGraph;
  alternatives: AlternativeMedication[];
  patient_counseling: PatientCounselingResponse | null;
  missing_data_mode: MissingDataMode | null;
  contextual_question: ContextualQuestion | null;
  patient_knowledge_bundle: PatientKnowledgeBundle;
  clinical_view: {
    status: PrescriptionStatus;
    risk_level: RiskLevel;
    primary_recommendation: string;
    patient_data_considered: Array<{ label: string; value: string }>;
    missing_data: string[];
    relevant_alerts: Array<{
      code: string;
      title: string;
      severity: RiskLevel;
      recommendation: string;
    }>;
    technical_details_available: boolean;
  };
  technical_details: Record<string, unknown>;
  dose_intelligence: {
    status: string;
    calculated_dose: number | null;
    calculated_unit: string;
    calculation_formula: string;
    calculation_basis: string;
    usual_range: { low: number | null; high: number | null };
    max_limits: Record<string, number | null>;
    alerts: Array<Record<string, unknown>>;
    missing_data: string[];
    validation_status: string;
    requires_human_review: boolean;
    educational_notice: string;
  };
  psychotropic_safety: Array<{
    code: string;
    title: string;
    description: string;
    severity: RiskLevel;
    recommendation: string;
    policy_status: string;
    source_ids: string[];
  }>;
  prescribing_policy: {
    status: string;
    prescriber_profile: Record<string, unknown>;
    required_specialties: string[];
    recommended_specialties: string[];
    prescription_form_requirements: string[];
    warnings: string[];
    institutional_notes: string[];
    source_refs: string[];
    requires_human_review: boolean;
    educational_notice: string;
  };
};

export type PrescriptionExplanationPayload = { audit_id: number };

export type PrescriptionExplanationResult = {
  provider: string;
  model: string | null;
  used_fallback: boolean;
  simple_explanation: string;
  technical_summary: string;
  review_questions: string[];
  educational_notice: string;
  prescription_status: PrescriptionStatus;
  risk_level: RiskLevel;
  critical_alert_codes: string[];
  missing_patient_data: string[];
  rag_sources: string[];
  how_to_explain_to_patient: string | null;
};
