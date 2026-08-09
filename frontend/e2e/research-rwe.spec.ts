import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test.describe("Research, RWE e workflows profissionais", () => {
  test("pesquisador percorre coorte, análise, resultados e evidências agregadas", async ({ page }) => {
    await login(page, "pesquisador");
    await expect(page.getByRole("link", { name: "Pesquisa e RWE", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Pacientes", exact: true })).toHaveCount(0);
    await page.getByRole("link", { name: "Pesquisa e RWE", exact: true }).click();

    await expect(page.getByRole("heading", { name: "Pesquisa e RWE" })).toBeVisible();
    await expect(
      page.getByRole("heading", {
        name: "Estudo sintético de segurança medicamentosa v0.9.0",
      }),
    ).toBeVisible();
    await expect(page.getByText(/exclusivamente sobre dados sintéticos/)).toBeVisible();
    await page.getByRole("tab", { name: "Coorte" }).click();
    await expect(page.getByRole("heading", { name: "Construtor de coorte" })).toBeVisible();
    await expect(page.getByText(/JSON avançado/)).toBeVisible();

    await page.getByRole("tab", { name: "Resultados" }).click();
    await expect(page.getByText(/^N = \d+$/)).toBeVisible();
    await expect(page.getByText(/Removidos:/).first()).toBeVisible();

    await page.getByRole("tab", { name: "Plano de análise" }).click();
    await expect(page.getByRole("heading", { name: "Qualidade dos dados" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Plano de análise" })).toBeVisible();

    await page.getByRole("tab", { name: "Evidências" }).click();
    await expect(page.getByRole("heading", { name: "Pacote de pesquisa" })).toBeVisible();
    await expect(page.getByText(/Pacote agregado pronto/).first()).toBeVisible();
  });

  test("farmacêutico visualiza intervenção explícita sem alteração automática", async ({ page }) => {
    await login(page, "farmaceutico");
    await page.getByRole("link", { name: "Farmácia clínica", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Farmácia clínica" })).toBeVisible();
    await expect(page.getByText(/Dose sintética requer conferência humana/)).toBeVisible();
    await expect(page.getByText(/Nenhuma prescrição é alterada automaticamente/)).toBeVisible();
  });
});
