export type UserRole = "admin" | "medico" | "enfermagem" | "auditor";

export type User = {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  specialty_code: string | null;
  crm_demo: string | null;
  crm_uf: string | null;
  rqe_demo: string | null;
  credential_verification_status: string;
};

export type UserCreatePayload = {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  is_active: boolean;
  specialty_code?: string | null;
  crm_demo?: string | null;
  crm_uf?: string | null;
  rqe_demo?: string | null;
};
