import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = process.cwd();
const apiUrl = "http://127.0.0.1:8015/api";
const frontendUrl = "http://127.0.0.1:5179";
const outputDir = path.join(root, "docs", "assets", "v0.9.0");
const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "prescripta-v090-research-"));
const python = process.env.PRESCRIPTA_PYTHON
  ?? path.join(root, ".venv", "Scripts", "python.exe");
const playwrightModule = path.join(root, "frontend", "node_modules", "playwright", "index.mjs");
const viteEntry = path.join(root, "frontend", "node_modules", "vite", "bin", "vite.js");
const { chromium } = await import(pathToFileURL(playwrightModule).href);
const children = [];

const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function waitFor(url) {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      if ((await fetch(url)).ok) return;
    } catch {
      // Service is still starting.
    }
    await wait(250);
  }
  throw new Error(`Readiness timeout: ${url}`);
}

function start(command, args, options) {
  const child = spawn(command, args, { ...options, stdio: "ignore" });
  children.push(child);
}

async function settle(page) {
  await page.waitForLoadState("domcontentloaded");
  await page.locator(".page-enter").waitFor({ state: "visible" });
  await page.evaluate(() => document.fonts.ready);
}

async function capture(page, file) {
  await page.screenshot({
    path: path.join(outputDir, file),
    animations: "disabled",
    caret: "hide",
    fullPage: false,
  });
}

await fs.mkdir(outputDir, { recursive: true });
const databasePath = path.join(tempDir, "research-assets.db").replaceAll("\\", "/");
start(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8015"], {
  cwd: path.join(root, "backend"),
  env: {
    ...process.env,
    PRESCRIPTA_DATABASE_URL: `sqlite:///${databasePath}`,
    PRESCRIPTA_CORS_ORIGINS: frontendUrl,
    PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS: "false",
  },
});
start(process.execPath, [viteEntry, "--host", "127.0.0.1", "--port", "5179"], {
  cwd: path.join(root, "frontend"),
  env: { ...process.env, VITE_API_URL: apiUrl },
});

let browser;
try {
  await waitFor(`${apiUrl}/health`);
  await waitFor(frontendUrl);
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    colorScheme: "light",
    locale: "pt-BR",
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const browserErrors = [];
  page.on("pageerror", (error) => browserErrors.push(error.message));
  page.on("console", (message) => {
    const location = message.location().url;
    const expectedAnonymousProbe = location.endsWith("/api/auth/me")
      && message.text().includes("401");
    if (message.type() === "error" && !expectedAnonymousProbe) {
      browserErrors.push(message.text());
    }
  });
  await page.goto(`${frontendUrl}/login`);
  await page.getByLabel(/e-mail/i).fill("pesquisa@prescripta.local");
  await page.getByLabel(/senha/i).fill("Pesquisa@12345");
  await page.getByRole("button", { name: /^Entrar$/ }).click();
  await page.getByRole("heading", { name: /^Olá,/ }).waitFor();
  await page.goto(`${frontendUrl}/research`);
  await settle(page);
  await page.getByRole("heading", { name: /Estudo sintético de segurança medicamentosa v0.9.0/ }).waitFor();
  await capture(page, "research-study-workspace-v0.9.0.png");
  await page.getByRole("tab", { name: "Coorte" }).click();
  await page.getByRole("heading", { name: "Construtor de coorte" }).waitFor();
  await capture(page, "research-cohort-builder-v0.9.0.png");
  await page.getByRole("tab", { name: "Plano de análise" }).click();
  await page.getByRole("heading", { name: "Qualidade dos dados" }).waitFor();
  await capture(page, "research-data-quality-analysis-plan-v0.9.0.png");
  await page.getByRole("tab", { name: "Resultados" }).click();
  await page.getByText(/^N = \d+$/).waitFor();
  await page.getByText(/Removidos:/).last().scrollIntoViewIfNeeded();
  await capture(page, "research-results-v0.9.0.png");
  const journeyCard = page
    .getByRole("heading", { name: "Jornada sintética do paciente" })
    .locator("..");
  await journeyCard.getByRole("button", { name: "Carregar jornada" }).click();
  await journeyCard.locator("ol li").first().waitFor();
  await journeyCard.evaluate((element) => element.scrollIntoView({ block: "start" }));
  await capture(page, "research-patient-journey-v0.9.0.png");
  await page.getByRole("tab", { name: "Evidências" }).click();
  await page.getByRole("heading", { name: "Pacote de pesquisa" }).waitFor();
  await capture(page, "research-evidence-package-v0.9.0.png");
  await page.getByLabel("Selecionar idioma").selectOption("en-US");
  await page.getByRole("heading", { name: "Research and RWE" }).waitFor();
  await capture(page, "research-en-US-v0.9.0.png");
  await page.getByLabel("Select language").selectOption("pt-BR");
  const mobilePage = await page.context().newPage();
  await mobilePage.setViewportSize({ width: 390, height: 844 });
  await mobilePage.goto(`${frontendUrl}/research`);
  await settle(mobilePage);
  await mobilePage.getByRole("heading", { name: "Pesquisa e RWE" }).waitFor();
  await capture(mobilePage, "research-mobile-v0.9.0.png");
  await mobilePage.close();
  if (browserErrors.length) throw new Error(browserErrors.join("\n"));
  const files = [
    "research-study-workspace-v0.9.0.png",
    "research-cohort-builder-v0.9.0.png",
    "research-data-quality-analysis-plan-v0.9.0.png",
    "research-results-v0.9.0.png",
    "research-patient-journey-v0.9.0.png",
    "research-evidence-package-v0.9.0.png",
    "research-en-US-v0.9.0.png",
    "research-mobile-v0.9.0.png",
  ];
  const assets = [];
  for (const file of files) {
    const buffer = await fs.readFile(path.join(outputDir, file));
    assets.push({
      file,
      bytes: buffer.length,
      width: buffer.readUInt32BE(16),
      height: buffer.readUInt32BE(20),
      sha256: crypto.createHash("sha256").update(buffer).digest("hex"),
    });
  }
  await fs.writeFile(
    path.join(outputDir, "manifest.json"),
    `${JSON.stringify({ version: "0.9.0", generator: "scripts/capture-v090-research-assets.mjs", assets }, null, 2)}\n`,
  );
} finally {
  if (browser) await browser.close().catch(() => undefined);
  for (const child of children.reverse()) child.kill();
  await wait(500);
  await fs.rm(tempDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
}
