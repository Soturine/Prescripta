import { expect, test } from "@playwright/test";

import { login, loginWith, logout } from "./helpers";

test.describe("sessão, perfis e autorização", () => {
  test("login, logout e expiração por 401", async ({ page }) => {
    await login(page, "admin");
    await expect(page.getByRole("link", { name: "Acessos e perfis" })).toBeVisible();
    await logout(page);

    await login(page, "medico");
    await page.route("**/api/dashboard", async (route) => route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "Sessão expirada" }) }));
    await page.reload();
    await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();
  });

  test("cada perfil recebe somente a navegação de suas capacidades", async ({ page }) => {
    const cases = [
      ["admin", "Acessos e perfis", "Pacientes"],
      ["medico", "Checagem", "Acessos e perfis"],
      ["enfermagem", "Pacientes", "Checagem"],
      ["auditor", "Auditoria", "Pacientes"],
      ["farmaceutico", "Reconciliação", "Acessos e perfis"],
      ["psicologo", "Pacientes", "Medicamentos"],
      ["safety", "Auditoria", "Pacientes"],
    ] as const;
    for (const [role, visible, hidden] of cases) {
      await login(page, role);
      await expect(page.getByRole("link", { name: visible, exact: true })).toBeVisible();
      await expect(page.getByRole("link", { name: hidden, exact: true })).toHaveCount(0);
      await logout(page);
    }
  });

  test("médico navega por paciente autorizado, protocolos e atalho de teclado", async ({ page }) => {
    await login(page, "medico");
    const skipLink = page.getByRole("link", { name: "Pular para o conteúdo" });
    await skipLink.focus();
    await expect(skipLink).toBeVisible();
    await page.keyboard.press("Enter");
    await expect(page.locator("#main-content")).toBeFocused();

    await page.getByRole("link", { name: "Pacientes", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Pacientes", exact: true })).toBeVisible();
    await page.getByRole("link", { name: /Abrir workspace de/ }).first().click();
    await expect(page.getByRole("navigation", { name: "Seções do paciente" })).toBeVisible();
    await expect(page.getByText(/vínculo, finalidade e capacidade explícitos/i)).toBeVisible();

    await page.getByRole("link", { name: "Protocolos", exact: true }).click();
    await expect(page.getByRole("heading", { name: /Apoio emergencial estruturado/ })).toBeVisible();
    await expect(page.getByText(/sem decisão automática/i).first()).toBeVisible();
  });

  test("mesmo tenant e cross-tenant sem relação não concedem acesso; break-glass é explícito", async ({ page }) => {
    await login(page, "admin");
    const baseUser = {
      name: "Médico E2E sem vínculo", password: "SemGrant@12345", role: "medico", profession: "medicine",
      capabilities: ["dashboard.view", "patient.read", "break_glass.invoke"], is_active: true,
      specialty_codes: ["general_practice"], institution_id: "demo",
    };
    const sameTenant = await page.request.post("http://127.0.0.1:8013/api/users", { data: { ...baseUser, email: "sem-grant-e2e@prescripta.local" } });
    expect([201, 409]).toContain(sameTenant.status());
    const otherTenant = await page.request.post("http://127.0.0.1:8013/api/users", { data: { ...baseUser, email: "cross-tenant-e2e@prescripta.local", institution_id: "outra-instituicao-demo" } });
    expect([201, 409]).toContain(otherTenant.status());

    await loginWith(page, "sem-grant-e2e@prescripta.local", "SemGrant@12345");
    const sameList = await page.request.get("http://127.0.0.1:8013/api/patients");
    expect(await sameList.json()).toEqual([]);
    const denied = await page.request.get("http://127.0.0.1:8013/api/patients/1");
    expect([403, 404]).toContain(denied.status());
    const emergency = await page.request.post("http://127.0.0.1:8013/api/access/patients/1/break-glass", { data: { capability: "patient.read", purpose: "treatment", reason: "Emergência demonstrativa auditável para teste E2E", duration_minutes: 5, idempotency_key: "e2e-break-glass-001" } });
    expect(emergency.status()).toBe(201);
    expect((await page.request.get("http://127.0.0.1:8013/api/patients/1")).status()).toBe(200);
    await expect(page.request.post(`http://127.0.0.1:8013/api/access/break-glass/${(await emergency.json()).id}/end`)).resolves.toMatchObject({ ok: expect.anything() });

    await loginWith(page, "cross-tenant-e2e@prescripta.local", "SemGrant@12345");
    const crossList = await page.request.get("http://127.0.0.1:8013/api/patients");
    expect(await crossList.json()).toEqual([]);
    expect([403, 404]).toContain((await page.request.get("http://127.0.0.1:8013/api/patients/1")).status());
  });
});

test.describe("estados resilientes", () => {
  test("erro de API oferece retry e vazio não vira dado clínico", async ({ page }) => {
    await login(page, "medico");
    let returnEmpty = false;
    await page.route("**/api/patients", async (route) => {
      if (!returnEmpty) await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "offline demo" }) });
      else await route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
    });
    await page.getByRole("link", { name: "Pacientes", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Falha ao carregar pacientes" })).toBeVisible();
    returnEmpty = true;
    await page.getByRole("button", { name: "Tentar novamente" }).click();
    await expect(page.getByRole("heading", { name: "Nenhum paciente autorizado" })).toBeVisible();
    await expect(page.getByText(/mesma instituição não é suficiente/)).toBeVisible();
  });
});
