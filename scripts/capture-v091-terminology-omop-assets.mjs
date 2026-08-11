import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = process.cwd();
const apiUrl = "http://127.0.0.1:8016/api";
const frontendUrl = "http://127.0.0.1:5180";
const outputDir = path.join(root, "docs", "assets", "v0.9.1");
const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "prescripta-v091-assets-"));
const python = process.env.PRESCRIPTA_PYTHON ?? path.join(root, ".venv", "Scripts", "python.exe");
const playwrightModule = path.join(root, "frontend", "node_modules", "playwright", "index.mjs");
const viteEntry = path.join(root, "frontend", "node_modules", "vite", "bin", "vite.js");
const { chromium } = await import(pathToFileURL(playwrightModule).href);
const children = [];
const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function start(command, args, options) {
  const child = spawn(command, args, { ...options, stdio: "ignore" });
  children.push(child);
}

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

async function settle(page) {
  await page.waitForLoadState("domcontentloaded");
  await page.locator(".page-enter").waitFor({ state: "visible" });
  await page.evaluate(() => document.fonts.ready);
}

await fs.mkdir(outputDir, { recursive: true });
const databasePath = path.join(tempDir, "terminology-assets.db").replaceAll("\\", "/");
start(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8016"], {
  cwd: path.join(root, "backend"),
  env: {
    ...process.env,
    PRESCRIPTA_DATABASE_URL: `sqlite:///${databasePath}`,
    PRESCRIPTA_CORS_ORIGINS: frontendUrl,
    PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS: "false",
  },
});
start(process.execPath, [viteEntry, "--host", "127.0.0.1", "--port", "5180"], {
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
    const expectedAnonymousProbe = message.location().url.endsWith("/api/auth/me")
      && message.text().includes("401");
    if (["warning", "error"].includes(message.type()) && !expectedAnonymousProbe) {
      browserErrors.push(`${message.type()}: ${message.text()}`);
    }
  });
  await page.goto(`${frontendUrl}/login`);
  await page.getByLabel(/e-mail/i).fill("pesquisa@prescripta.local");
  await page.getByLabel(/senha/i).fill("Pesquisa@12345");
  await page.getByRole("button", { name: /^Entrar$/ }).click();
  await page.getByRole("heading", { name: /^Olá,/ }).waitFor();
  await page.goto(`${frontendUrl}/research`);
  await settle(page);

  const files = [];
  await page.getByRole("tab", { name: "Terminologias" }).click();
  await page.getByRole("heading", { name: "Registro terminológico governado" }).waitFor();
  const terminologyFile = "research-terminology-governance-v0.9.1.png";
  await page.screenshot({ path: path.join(outputDir, terminologyFile), animations: "disabled", caret: "hide", fullPage: true });
  files.push(terminologyFile);

  await page.getByRole("tab", { name: "OMOP parcial" }).click();
  await page.getByRole("heading", { name: "Matriz de compatibilidade" }).waitFor();
  const omopFile = "research-omop-compatibility-v0.9.1.png";
  await page.screenshot({ path: path.join(outputDir, omopFile), animations: "disabled", caret: "hide", fullPage: true });
  files.push(omopFile);

  await page.getByLabel("Selecionar idioma").selectOption("en-US");
  await page.getByRole("heading", { name: "Compatibility matrix" }).waitFor();
  const englishFile = "research-omop-en-US-v0.9.1.png";
  await page.screenshot({ path: path.join(outputDir, englishFile), animations: "disabled", caret: "hide", fullPage: true });
  files.push(englishFile);

  if (browserErrors.length) throw new Error(browserErrors.join("\n"));
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
    `${JSON.stringify({ version: "0.9.1", generator: "scripts/capture-v091-terminology-omop-assets.mjs", assets }, null, 2)}\n`,
  );
} finally {
  if (browser) await browser.close().catch(() => undefined);
  for (const child of children.reverse()) child.kill();
  await wait(500);
  await fs.rm(tempDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
}
