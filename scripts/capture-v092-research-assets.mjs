import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = process.cwd();
const apiUrl = "http://127.0.0.1:8017/api";
const frontendUrl = "http://127.0.0.1:5181";
const outputDir = path.join(root, "docs", "assets", "v0.9.2");
const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "prescripta-v092-assets-"));
const python = process.env.PRESCRIPTA_PYTHON ?? path.join(root, ".venv", "Scripts", "python.exe");
const playwrightModule = path.join(root, "frontend", "node_modules", "playwright", "index.mjs");
const viteEntry = path.join(root, "frontend", "node_modules", "vite", "bin", "vite.js");
const { chromium } = await import(pathToFileURL(playwrightModule).href);
const children = [];
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function start(command, args, options) {
  const child = spawn(command, args, { ...options, stdio: "ignore" });
  children.push(child);
}

async function waitFor(url) {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try { if ((await fetch(url)).ok) return; } catch { /* starting */ }
    await wait(250);
  }
  throw new Error(`Readiness timeout: ${url}`);
}

async function shot(page, files, tab, file) {
  await page.getByRole("tab", { name: tab }).click();
  await page.waitForTimeout(150);
  await page.screenshot({ path: path.join(outputDir, file), animations: "disabled", caret: "hide", fullPage: true });
  files.push(file);
}

await fs.mkdir(outputDir, { recursive: true });
const databasePath = path.join(tempDir, "research-assets.db").replaceAll("\\", "/");
start(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8017"], {
  cwd: path.join(root, "backend"),
  env: { ...process.env, PRESCRIPTA_DATABASE_URL: `sqlite:///${databasePath}`, PRESCRIPTA_CORS_ORIGINS: frontendUrl, PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS: "false" },
});
start(process.execPath, [viteEntry, "--host", "127.0.0.1", "--port", "5181"], {
  cwd: path.join(root, "frontend"), env: { ...process.env, VITE_API_URL: apiUrl },
});

let browser;
try {
  await waitFor(`${apiUrl}/health`);
  await waitFor(frontendUrl);
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, colorScheme: "light", locale: "pt-BR", reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto(`${frontendUrl}/login`);
  await page.getByLabel(/e-mail/i).fill("pesquisa@prescripta.local");
  await page.getByLabel(/senha/i).fill("Pesquisa@12345");
  await page.getByRole("button", { name: /^Entrar$/ }).click();
  await page.getByRole("heading", { name: /^Olá,/ }).waitFor();

  const prepared = await page.evaluate(async ({ api }) => {
    const request = async (url, init) => {
      const response = await fetch(`${api}${url}`, { credentials: "include", headers: { "Content-Type": "application/json" }, ...init });
      if (!response.ok) throw new Error(`${url}: ${response.status} ${await response.text()}`);
      return response.json();
    };
    const studies = await request("/research/studies");
    const workspace = await request(`/research/studies/${studies[0].id}/workspace`);
    if (workspace.runs.length < 2) {
      const version = workspace.cohort_versions.find((item) => item.status === "reviewed_demo");
      const run = await request(`/research/cohort-versions/${version.id}/runs`, { method: "POST", body: JSON.stringify({ data_snapshot_marker: workspace.runs[0].data_snapshot_marker }) });
      await request("/data-quality/runs", { method: "POST", body: JSON.stringify({ study_id: studies[0].id, cohort_run_id: run.id }) });
    }
    return studies[0].id;
  }, { api: apiUrl });

  await page.goto(`${frontendUrl}/research?study=${prepared}`);
  await page.getByRole("heading", { name: "Pesquisa e RWE" }).waitFor();
  await page.getByRole("tab", { name: "RWE comparativa" }).click();
  const files = [];
  await page.screenshot({ path: path.join(outputDir, "signal-explorer-v0.9.2.png"), animations: "disabled", caret: "hide", fullPage: true });
  files.push("signal-explorer-v0.9.2.png");
  await page.getByRole("button", { name: /Executar comparação/ }).click();
  await page.getByRole("heading", { name: "Table 1 e balance" }).waitFor({ timeout: 30_000 });
  await page.screenshot({ path: path.join(outputDir, "comparative-table-one-v0.9.2.png"), animations: "disabled", caret: "hide", fullPage: true });
  files.push("comparative-table-one-v0.9.2.png");
  await shot(page, files, "Métodos causais", "psm-iptw-diagnostics-v0.9.2.png");
  await shot(page, files, "Literatura", "literature-workspace-v0.9.2.png");
  await shot(page, files, "Research Copilot", "research-copilot-v2-v0.9.2.png");
  await shot(page, files, "Preview NL→SQL", "nl-to-sql-default-off-v0.9.2.png");
  await page.getByLabel("Selecionar idioma").selectOption("en-US");
  await page.getByRole("heading", { name: /Research Query Assistant/ }).waitFor();
  await page.screenshot({ path: path.join(outputDir, "research-comparative-en-US-v0.9.2.png"), animations: "disabled", caret: "hide", fullPage: true });
  files.push("research-comparative-en-US-v0.9.2.png");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(outputDir, "research-comparative-mobile-v0.9.2.png"), animations: "disabled", caret: "hide", fullPage: true });
  files.push("research-comparative-mobile-v0.9.2.png");

  const assets = [];
  for (const file of files) {
    const buffer = await fs.readFile(path.join(outputDir, file));
    assets.push({ file, bytes: buffer.length, width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20), sha256: crypto.createHash("sha256").update(buffer).digest("hex") });
  }
  await fs.writeFile(path.join(outputDir, "manifest.json"), `${JSON.stringify({ version: "0.9.2", generator: "scripts/capture-v092-research-assets.mjs", synthetic_fixture: true, assets }, null, 2)}\n`);
} finally {
  if (browser) await browser.close().catch(() => undefined);
  for (const child of children.reverse()) child.kill();
  await wait(500);
  await fs.rm(tempDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
}
