export type Patient = {
  id: number;
  name: string;
  birth_date: string | null;
  age: number | null;
  weight_kg: number;
  height_cm: number | null;
  phone: string | null;
  email: string | null;
  mother_name: string | null;
  allergies: string[];
  comorbidities: string[];
  current_medications: string[];
  renal_condition: string | null;
  hepatic_condition: string | null;
  cardiac_condition: string | null;
  gastrointestinal_history: string | null;
  hypertension: boolean;
  diabetes: boolean;
  pregnancy_or_lactation: boolean | null;
  mental_health_factors?: string[];
  reproductive_gynecologic_factors?: string[];
  adverse_reactions: string[];
  clinical_notes: string | null;
  clinical_profile_reviewed_at: string | null;
  clinical_profile_completeness_score: number;
  clinical_profile_badge: string;
  identifiers: PatientIdentifier[];
  possible_duplicate_matches: Array<Record<string, unknown>>;
};

export type PatientPayload = Omit<
  Patient,
  | "id"
  | "clinical_profile_reviewed_at"
  | "clinical_profile_completeness_score"
  | "clinical_profile_badge"
  | "identifiers"
  | "possible_duplicate_matches"
>;

export type PatientIdentifier = {
  id: number;
  patient_id: number;
  identifier_type: string;
  issuing_system: string | null;
  display_masked: string;
  is_primary: boolean;
};

export type PatientIdentifierPayload = {
  identifier_type: string;
  identifier_value: string;
  issuing_system: string | null;
  is_primary: boolean;
};

export type QuickTriagePayload = {
  renal_condition?: boolean | string | null;
  hepatic_condition?: boolean | string | null;
  cardiac_condition?: boolean | string | null;
  gastrointestinal_history?: boolean | string | null;
  hypertension?: boolean | null;
  diabetes?: boolean | null;
  pregnancy_or_lactation?: boolean | null;
  mental_health_factors?: string[];
  reproductive_gynecologic_factors?: string[];
  allergies: string[];
  current_medications: string[];
  adverse_reactions: string[];
  clinical_notes?: string | null;
  condition_to_review?: string | null;
};

export type ClinicalContextGraph = {
  patient_id: number;
  patient_name: string;
  nodes: Array<{ id: string; label: string; type: string }>;
  edges: Array<{ from: string; to: string; label: string }>;
  clinical_profile_completeness_score: number;
  educational_notice: string;
};

export type PatientFunctionalProfile = {
  id: number | null;
  patient_id: number;
  drives_regularly: boolean | null;
  professional_driver: boolean | null;
  operates_machinery: boolean | null;
  works_at_height: boolean | null;
  fall_risk_activity: boolean | null;
  night_shift: boolean | null;
  caregiver_responsibility: boolean | null;
  high_attention_activity: boolean | null;
  frequent_alcohol_use: boolean | null;
  history_of_falls: boolean | null;
  low_tolerance_to_sedation_or_dizziness: boolean | null;
  source: string;
  notes: string | null;
  last_reviewed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  unknown_fields: string[];
  educational_notice: string;
};

export type PatientFunctionalProfilePayload = Omit<
  PatientFunctionalProfile,
  "id" | "patient_id" | "created_at" | "updated_at" | "unknown_fields" | "educational_notice"
>;

export type PatientClinicalDocument = {
  id: number;
  patient_id: number;
  document_type: string;
  title: string;
  summary: string;
  source_type: string;
  source_system: string | null;
  document_date: string | null;
  uploaded_at: string;
  raw_text: string;
  structured_payload: Record<string, unknown>;
  extracted_entities: Record<string, unknown>;
  confidence: number;
  validation_status: string;
  review_status: string;
  file_hash: string | null;
  storage_path: string | null;
};

export type PatientClinicalDocumentPayload = {
  document_type: string;
  title: string;
  summary?: string;
  source_type: string;
  source_system?: string | null;
  document_date?: string | null;
  raw_text?: string;
  structured_payload?: Record<string, unknown>;
};

export type PatientDocumentExtraction = {
  id: number;
  patient_id: number;
  document_id: number;
  provider: string;
  model: string | null;
  extracted_entities: Record<string, unknown>;
  confidence: number;
  validation_status: string;
  review_status: string;
  created_at: string;
};

export type PatientDocumentReviewPayload = {
  decision: "accept" | "reject";
  accepted_entities?: Record<string, unknown> | null;
  justification?: string | null;
};

export type PatientKnowledgeBundle = {
  patient_id: number;
  patient_reference: string;
  generated_at: string;
  send_identifiable_data: boolean;
  structured_profile: Record<string, unknown>;
  documents: Array<Record<string, unknown>>;
  reviewed_documents: Array<Record<string, unknown>>;
  reviewed_entities: Record<string, unknown>;
  reviewed_extractions: Array<Record<string, unknown>>;
  medication_history: Array<Record<string, unknown>>;
  imported_context: Array<Record<string, unknown>>;
  imports: Array<Record<string, unknown>>;
  protocol_context: Array<Record<string, unknown>>;
  protocol_runs: Array<Record<string, unknown>>;
  timeline: Array<Record<string, unknown>>;
  missing_data: string[];
  limitations: string[];
  educational_notice: string;
};
