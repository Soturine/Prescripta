export type Medication = {
  id: number;
  active_ingredient_id: number | null;
  brand_name: string;
  active_ingredient: string;
  commercial_aliases: string[];
  therapeutic_class: string;
  therapeutic_classes: string[];
  source_jurisdiction: string;
  evidence_source_type: string;
  validation_status: string;
  concentration: string | null;
  pharmaceutical_form: string | null;
  evidence_source_url: string | null;
  max_daily_dose_mg: number;
  dose_mg_per_kg: number | null;
  dose_by_weight_enabled: boolean;
  max_duration_days: number | null;
  max_cumulative_dose_mg: number | null;
  continuous_use: boolean;
  monitoring_required: boolean;
  monitoring_notes: string | null;
  condition_specific_limits: Record<string, number>;
  allowed_routes: string[];
  contraindications: string[];
  renal_caution: boolean;
  hepatic_caution: boolean;
  cardiac_caution: boolean;
  gastrointestinal_caution: boolean;
  elderly_caution: boolean;
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
  neuropsychiatric_cautions: string[];
  reproductive_cautions: string[];
  organs_involved: string[];
  relevant_adverse_effects: string[];
  structured_contraindications: string[];
  therapeutic_action: string | null;
  alternative_group: string | null;
  related_medications: string[];
  knowledge_source: string | null;
  notes: string | null;
};

export type MedicationPayload = Omit<Medication, "id">;

export type CounselingEvidence = {
  source_id: string;
  source_name: string;
  jurisdiction: string;
  excerpt: string;
  source_url: string | null;
  validation_status: string;
};

export type MedicationCounselingSummary = {
  id: number;
  active_ingredient_id: number | null;
  medication_id: number | null;
  source_id: string;
  jurisdiction: string;
  source_name: string;
  source_url: string | null;
  source_version: string | null;
  validation_status: string;
  generated_by: string;
  provider_name: string | null;
  confidence: string;
  requires_review: boolean;
  main_adverse_effects: string[];
  patient_relevant_effects: string[];
  activity_warnings: string[];
  driving_warning: boolean;
  machine_operation_warning: boolean;
  work_at_height_warning: boolean;
  fall_risk_warning: boolean;
  sedation_attention_warning: boolean;
  sleep_effects: string[];
  appetite_weight_effects: string[];
  mood_behavior_effects: string[];
  libido_sexual_effects: string[];
  neurologic_effects: string[];
  tremor_warning: boolean;
  headache_warning: boolean;
  temperature_regulation_effects: string[];
  blood_pressure_warning: boolean;
  gastrointestinal_effects: string[];
  renal_effects: string[];
  hepatic_effects: string[];
  reproductive_contraceptive_effects: string[];
  red_flags: string[];
  monitoring_required: string[];
  patient_friendly_summary: string;
  professional_summary: string;
  extracted_evidence: CounselingEvidence[];
  created_at: string;
  updated_at: string;
};

export type MedicationCounselingGeneratePayload = {
  provider_name?: string | null;
  source_text?: string | null;
  force_regenerate?: boolean;
};

export type MedicationCounselingReviewPayload = {
  validation_status: "curated" | "validated" | "rejected" | "obsolete";
  patient_friendly_summary?: string | null;
  professional_summary?: string | null;
  main_adverse_effects?: string[] | null;
  patient_relevant_effects?: string[] | null;
  activity_warnings?: string[] | null;
  red_flags?: string[] | null;
  justification?: string | null;
};

export type AdverseEffectTaxonomyEntry = {
  category: string;
  code: string;
  label: string;
};

export type MedicationKnowledgeLookupPayload = {
  query: string;
  source_name: string;
  source_url?: string | null;
  source_text?: string | null;
};

export type MedicationBulkImportPayload = {
  source_name: string;
  source_url?: string | null;
  dry_run?: boolean;
  items: Array<Record<string, unknown>>;
};

export type MedicationKnowledgeReviewPayload = {
  decision: "approve" | "reject";
  justification?: string | null;
  edited_payload?: Record<string, unknown> | null;
};

export type MedicationKnowledgeCurationItem = {
  id: number;
  query: string;
  source_name: string;
  source_url: string | null;
  source_text_excerpt: string;
  extracted_payload: Record<string, unknown>;
  provider: string;
  model: string | null;
  validation_status: string;
  review_status: string;
  reviewed_by: number | null;
  created_by: number | null;
};
