import type { Alert, PrescriptionStatus, RiskLevel } from "./prescription";

export type AuditRecord = {
  id: number;
  patient_id: number | null;
  medication_id: number | null;
  patient_name: string;
  medication_name: string;
  dose_mg: number;
  frequency_per_day: number;
  route: string;
  status: PrescriptionStatus;
  risk_level: RiskLevel;
  checked_at: string;
  alerts: Alert[];
};

export type DashboardSummary = {
  patient_count: number;
  medication_count: number;
  prescription_checks: number;
  alerts_by_severity: Record<RiskLevel, number>;
};
