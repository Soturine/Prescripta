import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { login } from "./helpers";

async function expectNoSeriousAxeViolations(page: Page) {
  await expect(page.locator(".page-enter")).toHaveCSS("opacity", "1");
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical");
  expect(blocking, blocking.map((item) => `${item.id}: ${item.help}`).join("\n")).toEqual([]);
}

test("axe bloqueia violações sérias no dashboard e fluxo clínico", async ({ page }) => {
  await login(page, "medico");
  await expectNoSeriousAxeViolations(page);
  await page.getByRole("link", { name: "Checagem clínica", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Checagem de prescrição" })).toBeVisible();
  await expectNoSeriousAxeViolations(page);
});

test("páginas principais têm snapshots visuais estáveis @visual", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  await login(page, "medico");
  await expect(page.locator(".page-enter")).toHaveCSS("opacity", "1");
  await expect(page).toHaveScreenshot("dashboard-profissional.png", { fullPage: true });
  await page.getByRole("link", { name: "Pacientes", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Pacientes", exact: true })).toBeVisible();
  await expect(page.locator(".page-enter")).toHaveCSS("opacity", "1");
  await expect(page).toHaveScreenshot("pacientes-autorizados.png", { fullPage: true });
  await page.getByRole("link", { name: "Checagem clínica", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Checagem de prescrição" })).toBeVisible();
  await expect(page.locator(".page-enter")).toHaveCSS("opacity", "1");
  await expect(page).toHaveScreenshot("checagem-dimensional.png", { fullPage: true });
});

test("locale EN-US preserva acesso e passa axe no dashboard", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium");
  await login(page, "medico");
  await page.getByLabel("Selecionar idioma").selectOption("en-US");
  await expect(page.locator("html")).toHaveAttribute("lang", "en-US");
  await expect(page.getByRole("heading", { name: /^Hello,/ })).toBeVisible();
  await expect(page.getByRole("link", { name: "Clinical check", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Access and profiles", exact: true })).toHaveCount(0);
  await expectNoSeriousAxeViolations(page);

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("lang", "en-US");
  await expect(page.getByRole("heading", { name: /^Hello,/ })).toBeVisible();
});

test("drawer e reflow funcionam em mobile e tablet @responsive", async ({ page }, testInfo) => {
  test.skip(!["mobile-chromium", "tablet-chromium"].includes(testInfo.project.name));
  await login(page, "medico");
  await page.getByRole("button", { name: "Abrir navegação" }).click();
  await expect(page.getByRole("link", { name: "Pacientes", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator("body")).toHaveCSS("overflow-y", "auto");
  expect(await page.locator("body").evaluate((element) => element.style.overflow)).toBe("");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});

test("reduced motion remove animações não essenciais @reduced", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "reduced-motion");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await login(page, "medico");
  expect(await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches)).toBe(true);
  const duration = await page.locator(".page-enter").evaluate((element) => getComputedStyle(element).animationDuration);
  expect(Number.parseFloat(duration)).toBeLessThanOrEqual(0.001);
});
