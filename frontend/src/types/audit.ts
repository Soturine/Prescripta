import type { RiskLevel } from "./prescription";

export type AuditRecord = {
  id: number;
  user_id: number | null;
  user_name: string | null;
  user_email: string | null;
  user_role: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  created_at: string;
  status: string | null;
  risk_level: RiskLevel | null;
  details: Record<string, unknown>;
};

export type AuditPage = {
  items: AuditRecord[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
};

export type DashboardSummary = {
  patient_count: number;
  medication_count: number;
  prescription_checks: number;
  alerts_by_severity: Record<RiskLevel, number>;
  catalog_quality: Record<string, number>;
};
