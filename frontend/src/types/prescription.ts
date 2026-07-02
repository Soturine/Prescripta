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
