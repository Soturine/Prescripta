import { spawn, spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = process.cwd();
const version = (await fs.readFile(path.join(root, "VERSION"), "utf8")).trim();
const apiUrl = "http://127.0.0.1:8014/api";
const frontendUrl = "http://127.0.0.1:5178";
const currentDir = path.join(root, "docs", "assets", "current");
const stageDir = path.join(root, "docs", "assets", `.current-${version}-stage`);
const backupDir = path.join(root, "docs", "assets", ".current-backup");
const releaseDir = path.join(root, "docs", "assets", `v${version}`);
const releaseStageDir = path.join(root, "docs", "assets", `.release-${version}-stage`);
const releaseBackupDir = path.join(root, "docs", "assets", `.release-${version}-backup`);
const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), `prescripta-${version}-assets-`));
const python = process.env.PRESCRIPTA_PYTHON
  ?? (process.platform === "win32"
    ? path.join(root, ".venv", "Scripts", "python.exe")
    : path.join(root, ".venv", "bin", "python"));
const playwrightModule = path.join(root, "frontend", "node_modules", "playwright", "index.mjs");
const viteEntry = path.join(root, "frontend", "node_modules", "vite", "bin", "vite.js");
const { chromium } = await import(pathToFileURL(playwrightModule).href);
const children = [];

const names = {
  overview: "overview.gif",
  dashboard: "dashboard.png",
  dashboardEnglish: "dashboard-en-US.png",
  patient: "patient-workspace.png",
  check: "clinical-check.png",
  decision: "clinical-result.png",
  pharmacy: "pharmacy.png",
  research: "research-workspace.png",
  analysis: "research-analysis.png",
  audit: "audit.png",
  mobile: "mobile-navigation.png",
};

const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function waitFor(url, timeout = 60_000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // O processo ainda está iniciando.
    }
    await wait(300);
  }
  throw new Error(`Timeout aguardando readiness de ${url}`);
}

function start(command, args, options) {
  const child = spawn(command, args, { ...options, stdio: "ignore" });
  children.push(child);
  return child;
}

async function settle(page) {
  await page.waitForLoadState("domcontentloaded");
  await page.locator(".page-enter").waitFor({ state: "visible" });
  await page.waitForFunction(() => {
    const element = document.querySelector(".page-enter");
    return element && getComputedStyle(element).opacity === "1";
  });
  await page.evaluate(() => document.fonts.ready);
}

async function login(page, email, password) {
  await page.context().clearCookies();
  await page.goto(`${frontendUrl}/login`);
  await page.getByLabel(/e-mail/i).fill(email);
  await page.getByLabel(/senha/i).fill(password);
  await page.getByRole("button", { name: /^Entrar$/ }).click();
  await page.getByRole("heading", { name: /^Olá,/ }).waitFor();
  await settle(page);
}

async function navigate(page, route) {
  await page.goto(`${frontendUrl}${route}`);
  await settle(page);
}

async function screenshot(page, name) {
  await page.screenshot({
    path: path.join(stageDir, name),
    animations: "disabled",
    caret: "hide",
    fullPage: false,
  });
}

function trackBrowserErrors(page, browserErrors, prefix = "") {
  page.on("pageerror", (error) => browserErrors.push(`${prefix}pageerror: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    const location = message.location().url;
    const expectedAnonymousProbe = location.endsWith("/api/auth/me") && message.text().includes("Failed to load resource");
    if (!expectedAnonymousProbe) browserErrors.push(`${prefix}console: ${message.text()} (${location || "sem URL"})`);
  });
}

function makeGif(outputName, frameNames) {
  const listPath = path.join(tempDir, "overview-frames.txt");
  const lines = frameNames.flatMap((frame) => [
    `file '${path.join(stageDir, frame).replaceAll("\\", "/").replaceAll("'", "'\\''")}'`,
    "duration 2.5",
  ]);
  lines.push(`file '${path.join(stageDir, frameNames.at(-1)).replaceAll("\\", "/").replaceAll("'", "'\\''")}'`);
  return fs.writeFile(listPath, `${lines.join("\n")}\n`, "utf8").then(() => {
    const result = spawnSync("ffmpeg", [
      "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", listPath,
      "-vf", "fps=4,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=64[p];[s1][p]paletteuse=dither=bayer",
      "-loop", "0", path.join(stageDir, outputName),
    ], { stdio: "inherit" });
    if (result.status !== 0) throw new Error("ffmpeg falhou ao gerar o GIF de apresentação.");
  });
}

function imageDimensions(buffer, extension) {
  if (extension === ".png") {
    return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
  }
  if (extension === ".gif") {
    return { width: buffer.readUInt16LE(6), height: buffer.readUInt16LE(8) };
  }
  throw new Error(`Formato não suportado no manifesto: ${extension}`);
}

async function writeManifest(directory, files) {
  const assets = [];
  for (const file of files) {
    const buffer = await fs.readFile(path.join(directory, file));
    assets.push({
      file,
      bytes: buffer.length,
      ...imageDimensions(buffer, path.extname(file).toLowerCase()),
      sha256: crypto.createHash("sha256").update(buffer).digest("hex"),
    });
  }
  await fs.writeFile(path.join(directory, "manifest.json"), `${JSON.stringify({ version, generator: "scripts/capture-current-assets.mjs", assets }, null, 2)}\n`, "utf8");
}

async function replaceDirectoryAtomically(target, stage, backup) {
  await fs.rm(backup, { recursive: true, force: true });
  try {
    await fs.rename(target, backup);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  try {
    await fs.rename(stage, target);
    await fs.rm(backup, { recursive: true, force: true });
  } catch (error) {
    try { await fs.rename(backup, target); } catch { /* preserve the original error */ }
    throw error;
  }
}

async function stageReleaseArchive() {
  await fs.rm(releaseStageDir, { recursive: true, force: true });
  await fs.mkdir(releaseStageDir, { recursive: true });
  const releaseFiles = [];
  for (const file of Object.values(names)) {
    const extension = path.extname(file);
    const archived = `${path.basename(file, extension)}-v${version}${extension}`;
    await fs.copyFile(path.join(stageDir, file), path.join(releaseStageDir, archived));
    releaseFiles.push(archived);
  }
  await writeManifest(releaseStageDir, releaseFiles.sort());
}

await fs.rm(stageDir, { recursive: true, force: true });
await fs.mkdir(stageDir, { recursive: true });
const databasePath = path.join(tempDir, "capture.db").replaceAll("\\", "/");
start(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8014"], {
  cwd: path.join(root, "backend"),
  env: {
    ...process.env,
    PRESCRIPTA_DATABASE_URL: `sqlite:///${databasePath}`,
    PRESCRIPTA_CORS_ORIGINS: frontendUrl,
    PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS: "false",
  },
});
start(process.execPath, [viteEntry, "--host", "127.0.0.1", "--port", "5178"], {
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
  trackBrowserErrors(page, browserErrors);

  await login(page, "medico@prescripta.local", "Medico@12345");
  await screenshot(page, names.dashboard);
  await page.getByLabel("Selecionar idioma").selectOption("en-US");
  await page.getByRole("heading", { name: /^Hello,/ }).waitFor();
  await screenshot(page, names.dashboardEnglish);
  await page.getByLabel("Select language").selectOption("pt-BR");
  await page.getByRole("heading", { name: /^Olá,/ }).waitFor();

  await navigate(page, "/patients/1");
  await page.getByRole("navigation", { name: "Seções do paciente" }).waitFor();
  await screenshot(page, names.patient);

  await navigate(page, "/prescription-check");
  await screenshot(page, names.check);
  await page.locator('[name="amount"]').fill("2");
  await page.locator('[name="amount_unit"]').selectOption("mL");
  await page.locator('[name="concentration_value"]').fill("50");
  await page.locator('[name="concentration_unit"]').selectOption("mg/mL");
  await page.getByRole("button", { name: "Executar checagem" }).click();
  const decisionHeading = page.getByRole("heading", { name: /Dados insuficientes|Cobertura insuficiente|Revisão necessária|Avaliado: nenhum achado acionável|Prescrição bloqueada/i });
  await decisionHeading.waitFor();
  await decisionHeading.scrollIntoViewIfNeeded();
  await screenshot(page, names.decision);

  await login(page, "farmacia@prescripta.local", "Farmacia@12345");
  await navigate(page, "/pharmacy");
  await page.getByRole("heading", { name: "Farmácia clínica" }).waitFor();
  await screenshot(page, names.pharmacy);

  await login(page, "pesquisa@prescripta.local", "Pesquisa@12345");
  await navigate(page, "/research");
  await page.getByRole("heading", { name: "Pesquisa e RWE" }).waitFor();
  await page.getByRole("heading", { name: /Estudo sintético de segurança medicamentosa/ }).waitFor();
  await screenshot(page, names.research);
  await page.getByRole("tab", { name: "Análise" }).click();
  await page.getByRole("tab", { name: "Comparação e métodos" }).waitFor();
  await screenshot(page, names.analysis);

  await login(page, "auditor@prescripta.local", "Auditor@12345");
  await navigate(page, "/audit");
  await page.getByRole("heading", { name: "Auditoria", exact: true }).waitFor();
  await screenshot(page, names.audit);

  const mobilePage = await context.newPage();
  await mobilePage.setViewportSize({ width: 390, height: 844 });
  trackBrowserErrors(mobilePage, browserErrors, "mobile ");
  await login(mobilePage, "medico@prescripta.local", "Medico@12345");
  await mobilePage.getByRole("button", { name: "Abrir navegação" }).click();
  await screenshot(mobilePage, names.mobile);
  await mobilePage.close();

  if (browserErrors.length) {
    throw new Error(`Captura recusada por erros no navegador:\n${browserErrors.join("\n")}`);
  }
  await context.close();
  await makeGif(names.overview, [names.dashboard, names.patient, names.decision, names.research]);
  await writeManifest(stageDir, Object.values(names).sort());
  await stageReleaseArchive();
  await replaceDirectoryAtomically(releaseDir, releaseStageDir, releaseBackupDir);
  await replaceDirectoryAtomically(currentDir, stageDir, backupDir);
  console.log(`Assets v${version} captured in current/ and v${version}/.`);
} finally {
  if (browser) await browser.close().catch(() => undefined);
  for (const child of children.reverse()) child.kill();
  await Promise.race([
    Promise.all(children.map((child) => child.exitCode === null
      ? new Promise((resolve) => child.once("exit", resolve))
      : Promise.resolve())),
    wait(3_000),
  ]);
  await fs.rm(stageDir, { recursive: true, force: true });
  await fs.rm(releaseStageDir, { recursive: true, force: true });
  await fs.rm(tempDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
}
