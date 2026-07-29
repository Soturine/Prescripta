export type UserRole =
  | "admin"
  | "medico"
  | "enfermagem"
  | "farmaceutico"
  | "psicologo"
  | "auditor"
  | "clinical_safety_officer";

export type Profession =
  | "administration"
  | "medicine"
  | "nursing"
  | "pharmacy"
  | "psychology"
  | "audit"
  | "clinical_safety";

export type Capability =
  | "dashboard.view"
  | "patient.create"
  | "patient.read"
  | "patient.write"
  | "patient.sensitive_psychology.read"
  | "prescription.check"
  | "prescription.override"
  | "medication.read"
  | "medication.manage"
  | "reconciliation.review"
  | "administration.review"
  | "nursing.protocol_prescribe"
  | "psychology.context.write"
  | "report.read"
  | "report.create"
  | "patient_guidance.create"
  | "audit.read"
  | "safety.review"
  | "ruleset.review"
  | "access.manage"
  | "break_glass.invoke"
  | "user.manage"
  | "ai.status.view"
  | "ai.settings.manage"
  | "system.health.view";

export type User = {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  profession: Profession;
  capabilities: Capability[];
  capability_policy_version: string;
  is_active: boolean;
  created_at: string;
  specialty_code: string | null;
  specialty_codes: string[];
  credential_type: string | null;
  credential_code_demo: string | null;
  credential_region: string | null;
  credential_expires_at: string | null;
  institutional_policy: Record<string, unknown>;
  sensitive_data_segments: string[];
  crm_demo: string | null;
  crm_uf: string | null;
  rqe_demo: string | null;
  credential_verification_status: string;
  institution_id: string;
  mfa_enabled: boolean;
};

export type UserCreatePayload = {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  profession?: Profession;
  capabilities?: Capability[];
  is_active: boolean;
  specialty_code?: string | null;
  specialty_codes?: string[];
  credential_type?: string | null;
  credential_code_demo?: string | null;
  credential_region?: string | null;
  credential_expires_at?: string | null;
  institutional_policy?: Record<string, unknown>;
  sensitive_data_segments?: string[];
  crm_demo?: string | null;
  crm_uf?: string | null;
  rqe_demo?: string | null;
  credential_verification_status?: string;
  institution_id?: string;
};

export type UserClinicalProfilePayload = Partial<
  Pick<
    User,
    | "profession"
    | "capabilities"
    | "specialty_code"
    | "specialty_codes"
    | "credential_type"
    | "credential_code_demo"
    | "credential_region"
    | "credential_expires_at"
    | "institutional_policy"
    | "sensitive_data_segments"
    | "crm_demo"
    | "crm_uf"
    | "rqe_demo"
    | "credential_verification_status"
  >
>;
