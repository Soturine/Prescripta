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
};

export type PrescriptionCheckResult = {
  status: PrescriptionStatus;
  risk_level: RiskLevel;
  alerts: Alert[];
  recommendation: string;
  human_review_required: boolean;
  audit_id: number;
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
    brand_name: string;
    active_ingredient: string;
    therapeutic_class: string;
    max_daily_dose_mg: number;
    allowed_routes: string[];
    contraindications: string[];
    notes: string | null;
  };
  dose_mg: number;
  frequency_per_day: number;
  route: string;
  user_profile: string;
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
};
