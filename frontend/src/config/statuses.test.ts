import { describe, expect, it } from "vitest";
import { ROLE_LABELS } from "./labels";
import { APP_ROUTES } from "./routes";
import { STATUS_LABELS } from "./statuses";

describe("metadados centrais da interface", () => {
  it("mantém labels de perfis e status em português", () => {
    expect(ROLE_LABELS.medico).toBe("Médico");
    expect(STATUS_LABELS.pending_review).toContain("revisão");
  });

  it("não oferece administração de usuários ao perfil clínico", () => {
    const users = APP_ROUTES.find((route) => route.to === "/users");
    expect(users?.roles).toEqual(["admin"]);
  });
});
