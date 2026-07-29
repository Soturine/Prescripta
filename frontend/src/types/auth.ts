import type { User } from "./user";

export type LoginPayload = {
  email: string;
  password: string;
  mfa_code?: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};
