import { expect, test, type Page } from "@playwright/test";

const credentials = {
  admin: ["admin@prescripta.local", "Admin@12345"],
  medico: ["medico@prescripta.local", "Medico@12345"],
  enfermagem: ["enfermagem@prescripta.local", "Enfermagem@12345"],
  auditor: ["auditor@prescripta.local", "Auditor@12345"],
} as const;

async function login(page: Page, role: keyof typeof credentials) {
  const [email, password] = credentials[role];
  await page.goto("/login");
  await page.getByLabel(/e-mail/i).fill(email);
  await page.getByLabel(/senha/i).fill(password);
  await page.getByRole("button", { name: /entrar/i }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

test("login admin e dashboard", async ({ page }) => {
  await login(page, "admin");
  await expect(page.getByRole("heading", { name: "Qualidade do catálogo" })).toBeVisible();
});

test("login médico e navegação clínica", async ({ page }) => {
  await login(page, "medico");
  await expect(page.getByRole("link", { name: "Checagem" })).toBeVisible();
});

test("login enfermagem sem administração de usuários", async ({ page }) => {
  await login(page, "enfermagem");
  await expect(page.getByRole("link", { name: /usuários/i })).toHaveCount(0);
});

test("login auditor e acesso à auditoria", async ({ page }) => {
  await login(page, "auditor");
  await page.getByRole("link", { name: "Auditoria", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Auditoria", exact: true })).toBeVisible();
});

test("pacientes e detalhes", async ({ page }) => {
  await login(page, "medico");
  await page.getByRole("link", { name: "Pacientes" }).click();
  await expect(page.getByRole("heading", { name: "Pacientes", exact: true })).toBeVisible();
  await page.locator('a[href^="/patients/"]').first().click();
  await expect(page.getByText("Histórico clínico e laudos")).toBeVisible();
});

test("catálogo de medicamentos", async ({ page }) => {
  await login(page, "admin");
  await page.getByRole("link", { name: "Medicamentos" }).click();
  await expect(page.getByText("Catálogo de princípios ativos")).toBeVisible();
});

test("checagem completa em fallback determinístico", async ({ page }) => {
  await login(page, "medico");
  await page.getByRole("link", { name: "Checagem" }).click();
  const patient = page.locator('[name="patient_id"]');
  const medication = page.locator('[name="medication_id"]');
  await patient.selectOption({ index: 1 });
  await medication.selectOption({ index: 1 });
  await page.locator('[name="dose_mg"]').fill("50");
  await page.locator('[name="frequency_per_day"]').fill("2");
  await page.locator('[name="route"]').fill("oral");
  await page.locator('button[type="submit"]').click();
  await expect(page.getByText("Dose Intelligence")).toBeVisible();
});

test("protocolos exibem contexto mínimo", async ({ page }) => {
  await login(page, "medico");
  await page.getByRole("link", { name: "Protocolos", exact: true }).click();
  await expect(page.getByText("Contexto mínimo").first()).toBeVisible();
});

test("relatórios e IA fallback", async ({ page }) => {
  await login(page, "admin");
  await page.getByRole("link", { name: "Relatórios", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Relatórios", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "IA assistiva", exact: true }).click();
  await expect(page.getByText(/fallback/i).first()).toBeVisible();
});

test("navegação mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page, "medico");
  await page.getByRole("button", { name: /abrir menu/i }).click();
  await expect(page.getByRole("link", { name: "Pacientes" })).toBeVisible();
});
