export type Patient = {
  id: number;
  name: string;
  birth_date: string | null;
  age: number | null;
  weight_kg: number;
  height_cm: number | null;
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
  adverse_reactions: string[];
  clinical_notes: string | null;
  clinical_profile_reviewed_at: string | null;
  clinical_profile_completeness_score: number;
  clinical_profile_badge: string;
};

export type PatientPayload = Omit<
  Patient,
  | "id"
  | "clinical_profile_reviewed_at"
  | "clinical_profile_completeness_score"
  | "clinical_profile_badge"
>;

export type QuickTriagePayload = {
  renal_condition?: boolean | null;
  hepatic_condition?: boolean | null;
  cardiac_condition?: boolean | null;
  gastrointestinal_history?: boolean | null;
  hypertension?: boolean | null;
  diabetes?: boolean | null;
  pregnancy_or_lactation?: boolean | null;
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
