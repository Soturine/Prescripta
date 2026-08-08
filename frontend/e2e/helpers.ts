import { expect, type Page } from "@playwright/test";

export const credentials = {
  admin: ["admin@prescripta.local", "Admin@12345"],
  medico: ["medico@prescripta.local", "Medico@12345"],
  enfermagem: ["enfermagem@prescripta.local", "Enfermagem@12345"],
  auditor: ["auditor@prescripta.local", "Auditor@12345"],
  farmaceutico: ["farmacia@prescripta.local", "Farmacia@12345"],
  psicologo: ["psicologia@prescripta.local", "Psicologia@12345"],
  safety: ["safety@prescripta.local", "Safety@12345"],
  pesquisador: ["pesquisa@prescripta.local", "Pesquisa@12345"],
} as const;

export type DemoRole = keyof typeof credentials;

export async function login(page: Page, role: DemoRole) {
  const [email, password] = credentials[role];
  await page.goto("/login");
  await page.getByLabel(/e-mail/i).fill(email);
  await page.getByLabel(/senha/i).fill(password);
  await page.getByRole("button", { name: /^Entrar$/ }).click();
  await expect(page.getByRole("heading", { name: /^Olá,/ })).toBeVisible();
}

export async function loginWith(page: Page, email: string, password: string) {
  await page.context().clearCookies();
  await page.goto("/login");
  await page.getByLabel(/e-mail/i).fill(email);
  await page.getByLabel(/senha/i).fill(password);
  await page.getByRole("button", { name: /^Entrar$/ }).click();
  await expect(page.getByRole("heading", { name: /^Olá,/ })).toBeVisible();
}

export async function logout(page: Page) {
  await page.locator("details > summary").click();
  await page.getByRole("button", { name: "Encerrar sessão" }).click();
  await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();
}
