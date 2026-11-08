import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { allowConsoleMessage, credentials, login, type DemoRole } from "./helpers";

// Auditoria 2026-11: os gates de axe cobriam só o perfil médico. Aqui cada perfil demo percorre as
// páginas do próprio menu; a estrutura que um leitor de tela usa (um h1, um landmark main) é
// verificada junto com o axe, e nenhuma página do menu pode receber 403 da API (menu oferecendo o que
// o backend nega). Não substitui um teste com leitor de tela real.
const roles = Object.keys(credentials) as DemoRole[];
// Regras "moderate" para o axe, mas é por elas que um leitor de tela navega (cabeçalhos e landmarks).
const STRUCTURE_RULES = new Set(["heading-order", "landmark-no-duplicate-main", "landmark-main-is-top-level"]);

for (const role of roles) {
  test(`perfil ${role}: páginas do menu sem violação séria de axe e com estrutura navegável`, async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop-chromium");
    test.setTimeout(180_000);
    allowConsoleMessage(page, /status of 403 \(Forbidden\)/);
    let current = "/";
    const forbidden: string[] = [];
    page.on("response", (response) => {
      if (response.status() === 403) forbidden.push(`${current} -> ${new URL(response.url()).pathname}`);
    });
    await login(page, role);
    const nav = page.getByRole("navigation").first();
    await expect(nav).toBeVisible();
    const links = await nav.getByRole("link").evaluateAll((items) =>
      items.map((item) => ({ name: (item.textContent ?? "").trim(), href: item.getAttribute("href") ?? "" })),
    );
    const report: Array<Record<string, unknown>> = [];
    try {
      for (const link of links.filter((item) => item.href.startsWith("/"))) {
        current = link.href;
        await page.goto(link.href);
        await expect(page.locator(".page-enter")).toHaveCSS("opacity", "1");
        await page.waitForLoadState("networkidle");
        const results = await new AxeBuilder({ page }).analyze();
        const serious = results.violations.filter(
          (v) => v.impact === "serious" || v.impact === "critical" || STRUCTURE_RULES.has(v.id),
        );
        const h1 = await page.locator("h1").allTextContents();
        const mains = await page.getByRole("main").count();
        report.push({
          page: link.href,
          link: link.name,
          h1,
          mains,
          violations: results.violations.map((v) => ({
            id: v.id,
            impact: v.impact,
            targets: v.nodes.slice(0, 5).map((node) => ({ target: node.target.join(" "), summary: node.failureSummary })),
          })),
        });
        expect.soft(serious.map((v) => `${link.href} ${v.id}: ${v.help}`)).toEqual([]);
        expect.soft(h1.length, `${link.href}: exatamente um h1`).toBe(1);
        expect.soft(mains, `${link.href}: um landmark main`).toBe(1);
      }
      expect(report.length, "o menu do perfil tem páginas").toBeGreaterThan(0);
      expect.soft(forbidden, "páginas do menu não recebem 403").toEqual([]);
    } finally {
      await testInfo.attach(`profile-${role}.json`, {
        body: JSON.stringify({ role, links, forbidden, pages: report }, null, 2),
        contentType: "application/json",
      });
    }
  });
}
