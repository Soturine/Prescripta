import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test.describe("Research, RWE e workflows profissionais", () => {
  test("pesquisador vê somente agregados, attrition, provenance e DQ sintéticos", async ({ page }) => {
    await login(page, "pesquisador");
    await expect(page.getByRole("link", { name: "Pesquisa e RWE", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Pacientes", exact: true })).toHaveCount(0);
    await page.getByRole("link", { name: "Pesquisa e RWE", exact: true }).click();

    await expect(page.getByRole("heading", { name: "Pesquisa e RWE" })).toBeVisible();
    await expect(
      page.getByRole("heading", {
        name: "Estudo sintético de segurança medicamentosa v0.8.8",
      }),
    ).toBeVisible();
    await expect(page.getByText(/exclusivamente sobre dados sintéticos/)).toBeVisible();
    await expect(page.getByText("Unidade não reconhecida").first()).toBeVisible();
    await expect(page.getByText("unknown_unit")).toBeHidden();
    await page.getByText("Detalhes técnicos").click();
    await expect(page.getByText("unknown_unit")).toBeVisible();

    await page.getByRole("tab", { name: "Cohort" }).click();
    await expect(page.getByRole("heading", { name: "Cohort Builder" })).toBeVisible();
    await expect(page.getByText(/JSON avançado/)).toBeVisible();

    await page.getByRole("tab", { name: "Runs" }).click();
    await expect(page.getByText(/^N = \d+$/)).toBeVisible();
    await expect(page.getByText(/Removidos:/).first()).toBeVisible();

    await page.getByRole("tab", { name: "Provenance" }).click();
    await expect(page.getByRole("heading", { name: "Provenance" })).toBeVisible();
    await expect(page.getByText(/prescripta-cohort-deterministic-v1/)).toBeVisible();
  });

  test("farmacêutico visualiza intervenção explícita sem alteração automática", async ({ page }) => {
    await login(page, "farmaceutico");
    await page.getByRole("link", { name: "Farmácia clínica", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Farmácia clínica" })).toBeVisible();
    await expect(page.getByText(/Dose sintética requer conferência humana/)).toBeVisible();
    await expect(page.getByText(/Nenhuma prescrição é alterada automaticamente/)).toBeVisible();
  });
});
