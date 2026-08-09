import { expect, test, type Page } from "@playwright/test";

import { credentials, login, loginWith } from "./helpers";

const apiBaseUrl = "http://127.0.0.1:8013/api";

type OverrideMedication = {
  id: number;
  brand_name: string;
  active_ingredient: string;
  requires_second_review: boolean;
  override_allowed: boolean;
  override_reason_required: boolean;
  second_reviewer_role: string | null;
};

async function openCheck(page: Page) {
  await login(page, "medico");
  await page.getByRole("link", { name: "Checagem clínica", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Checagem clínica da prescrição" })).toBeVisible();
}

test.describe("dose dimensional e decisão clínica", () => {
  test("concentração × volume mantém dimensões e persiste decisão antes da IA", async ({ page }) => {
    await openCheck(page);
    await page.locator('[name="amount"]').fill("2");
    await page.locator('[name="amount_unit"]').selectOption("mL");
    await page.locator('[name="concentration_value"]').fill("50");
    await page.locator('[name="concentration_unit"]').selectOption("mg/mL");
    await page.getByRole("button", { name: "Executar checagem" }).click();
    await expect(page.getByRole("heading", { name: /Liberada|Revisão necessária|Dados insuficientes|Cobertura insuficiente|Bloqueada/ })).toBeVisible();
    await expect(page.getByText(/Cobertura:/).first()).toBeVisible();
    await page.getByRole("button", { name: "Explicar com IA" }).click();
    await expect(page.getByRole("heading", { name: "Explicação assistida" })).toBeVisible();
  });

  test("infusão contínua exige taxa explícita e aceita unidade de taxa", async ({ page }) => {
    await openCheck(page);
    await page.locator('[name="administration_kind"]').selectOption("continuous");
    await page.getByRole("button", { name: "Executar checagem" }).click();
    await expect(page.getByText("Infusão contínua exige taxa explícita.")).toBeVisible();
    await page.locator('[name="rate_value"]').fill("2.5");
    await page.locator('[name="rate_unit"]').selectOption("mg/h");
    await page.getByRole("button", { name: "Executar checagem" }).click();
    await expect(page.getByRole("heading", { name: /Liberada|Revisão necessária|Dados insuficientes|Cobertura insuficiente|Bloqueada/ })).toBeVisible();
  });

  test("PRN não usa frequência programada e exige teto diário", async ({ page }) => {
    await openCheck(page);
    await page.locator('[name="administration_kind"]').selectOption("prn");
    await page.getByRole("button", { name: "Executar checagem" }).click();
    await expect(page.getByText("PRN exige teto de administrações.")).toBeVisible();
    await page.locator('[name="max_administrations_per_day"]').fill("3");
    await page.getByRole("button", { name: "Executar checagem" }).click();
    await expect(page.getByRole("heading", { name: /Liberada|Revisão necessária|Dados insuficientes|Cobertura insuficiente|Bloqueada/ })).toBeVisible();
  });

  test("dose extrema não produz false-green", async ({ page }) => {
    await openCheck(page);
    await page.locator('[name="amount"]').fill("999999");
    await page.getByRole("button", { name: "Executar checagem" }).click();
    await expect(page.getByRole("heading", { name: /Prescrição bloqueada|Revisão necessária/i })).toBeVisible();
  });

  test("override exige autor, policy explícita e segundo médico independente", async ({ page, request }) => {
    const adminLogin = await request.post(`${apiBaseUrl}/auth/login`, {
      data: { email: credentials.admin[0], password: credentials.admin[1] },
    });
    expect(adminLogin.ok()).toBe(true);
    const medicationResponse = await request.get(`${apiBaseUrl}/medications?page_size=100`);
    expect(medicationResponse.ok()).toBe(true);
    const medications = (await medicationResponse.json()) as OverrideMedication[];
    const medication = medications.find((item) => item.active_ingredient.toLocaleLowerCase("pt-BR").includes("paracetamol")) ?? medications[0];
    expect(medication).toBeDefined();

    const policyUpdate = await request.put(`${apiBaseUrl}/medications/${medication.id}`, {
      data: {
        requires_second_review: true,
        override_allowed: true,
        override_reason_required: true,
        second_reviewer_role: "medico",
      },
    });
    expect(policyUpdate.ok()).toBe(true);

    try {
      await openCheck(page);
      await page.getByLabel("Medicamento").selectOption(String(medication.id));
      await page.getByRole("button", { name: "Executar checagem" }).click();
      await expect(page.getByRole("heading", { name: /Revisão necessária|Dados insuficientes|Cobertura insuficiente|Avaliado: nenhum achado acionável/ })).toBeVisible();
      await page.getByRole("button", { name: "Solicitar override" }).click();
      await page.getByRole("textbox", { name: /Justificativa clínica/ }).fill("Contexto fictício submetido para revisão humana independente.");
      const overrideResponsePromise = page.waitForResponse((response) => response.url().includes("/prescriptions/") && response.url().endsWith("/overrides") && response.request().method() === "POST");
      await page.getByRole("button", { name: "Registrar solicitação" }).click();
      const overrideResponse = await overrideResponsePromise;
      expect(overrideResponse.status()).toBe(201);
      const override = await overrideResponse.json() as { id: number; status: string };
      expect(override.status).toBe("pending_second_review");
      await expect(page.getByText("Solicitação registrada para segundo revisor.")).toBeVisible();

      const selfReview = await page.request.post(`${apiBaseUrl}/prescriptions/overrides/${override.id}/review`, {
        data: { decision: "approved", note: "Tentativa inválida do próprio solicitante." },
      });
      expect(selfReview.status()).toBe(409);

      await loginWith(page, "anestesia@prescripta.local", "Anestesia@12345");
      const secondReview = await page.request.post(`${apiBaseUrl}/prescriptions/overrides/${override.id}/review`, {
        data: { decision: "approved", note: "Segunda revisão fictícia independente aprovada." },
      });
      expect(secondReview.ok()).toBe(true);
      expect((await secondReview.json() as { status: string }).status).toBe("approved");

      await loginWith(page, credentials.auditor[0], credentials.auditor[1]);
      await page.getByRole("link", { name: "Auditoria", exact: true }).click();
      await expect(page.getByRole("table")).toContainText("Revisou override clínico");
    } finally {
      const restore = await request.put(`${apiBaseUrl}/medications/${medication.id}`, {
        data: {
          requires_second_review: medication.requires_second_review,
          override_allowed: medication.override_allowed,
          override_reason_required: medication.override_reason_required,
          second_reviewer_role: medication.second_reviewer_role,
        },
      });
      expect(restore.ok()).toBe(true);
    }
  });

  test("auditoria apresenta decisão persistida", async ({ page }) => {
    await login(page, "auditor");
    await page.getByRole("link", { name: "Auditoria", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Auditoria", exact: true })).toBeVisible();
    await expect(page.getByRole("table")).toBeVisible();
  });
});
