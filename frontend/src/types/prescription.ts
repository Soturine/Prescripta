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
  dose_mg: number;
  frequency_per_day: number;
  route: string;
  duration_days: number | null;
  indication: string | null;
  professional_notes: string | null;
};

export type DoseSummary = {
  daily_total_mg: number;
  duration_days: number | null;
  estimated_cumulative_dose_mg: number | null;
  max_daily_dose_mg: number;
  max_duration_days: number | null;
  max_cumulative_dose_mg: number | null;
  continuous_use: boolean;
  monitoring_required: boolean;
  monitoring_notes: string | null;
  exposure_plan: {
    dose_per_administration_mg: number;
    administrations_per_day: number;
    calculated_daily_dose_mg: number;
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

export type PrescriptionCheckResult = {
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
};

export type PrescriptionExplanationPayload = PrescriptionCheckResult & {
  patient: {
    id: number;
    name: string;
    birth_date: string | null;
    age: number | null;
    weight_kg: number;
    height_cm: number | null;
    allergies: string[];
    comorbidities: string[];
    current_medications: string[];
  };
  medication: {
    id: number;
    active_ingredient_id?: number | null;
    brand_name: string;
    active_ingredient: string;
    commercial_aliases?: string[];
    therapeutic_class: string;
    therapeutic_classes?: string[];
    source_jurisdiction?: string;
    evidence_source_type?: string;
    validation_status?: string;
    concentration?: string | null;
    pharmaceutical_form?: string | null;
    evidence_source_url?: string | null;
    max_daily_dose_mg: number;
    allowed_routes: string[];
    contraindications: string[];
    notes: string | null;
  };
  dose_mg: number;
  frequency_per_day: number;
  route: string;
  duration_days: number | null;
  indication: string | null;
  professional_notes: string | null;
  user_profile: string;
  dose_summary: DoseSummary;
  compatibility: Compatibility;
  patient_factors_considered: string[];
  medication_factors_considered: string[];
  rag_evidence: RagEvidence[];
  clinical_context_graph: ClinicalContextGraph;
  alternatives: AlternativeMedication[];
};

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
};
