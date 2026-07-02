export type UserRole = "admin" | "medico" | "enfermagem" | "auditor";

export type User = {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
};

export type UserCreatePayload = {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  is_active: boolean;
};
