import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const root = process.cwd();
const frontendUrl = "http://127.0.0.1:5176";
const apiUrl = "http://127.0.0.1:8012/api";
const chromePath = process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const outDir = path.join(root, "docs", "assets", "v0.8.5");
const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "prescripta-v085-capture-"));

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function waitFor(url, timeout = 30000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    try { const response = await fetch(url); if (response.ok) return; } catch { /* retry */ }
    await wait(300);
  }
  throw new Error(`Timeout aguardando ${url}`);
}

class Cdp {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.pending = new Map();
    ws.addEventListener("message", ({ data }) => {
      const message = JSON.parse(data);
      const pending = this.pending.get(message.id);
      if (pending) { this.pending.delete(message.id); message.error ? pending.reject(new Error(message.error.message)) : pending.resolve(message.result ?? {}); }
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => { this.pending.set(id, { resolve, reject }); setTimeout(() => reject(new Error(`CDP ${method}`)), 20000); });
  }
}

async function evaluate(cdp, expression) {
  const response = await cdp.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.text);
  return response.result?.value;
}
async function waitText(cdp, text, timeout = 15000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if (await evaluate(cdp, `document.body.innerText.includes(${JSON.stringify(text)})`)) return;
    await wait(350);
  }
  const body = await evaluate(cdp, "JSON.stringify({href:location.href,ready:document.readyState,body:document.body?.innerText,html:document.documentElement?.outerHTML?.slice(0,300)})");
  throw new Error(`Texto não encontrado: ${text}\n${body}`);
}
async function shot(cdp, name) {
  const result = await cdp.send("Page.captureScreenshot", { format: "png", fromSurface: true });
  await fs.writeFile(path.join(outDir, name), Buffer.from(result.data, "base64"));
}
async function shotSection(cdp, name, heading) {
  const rect = await evaluate(cdp, `(() => { const needle=${JSON.stringify(heading)}; const h=[...document.querySelectorAll('h2')].find(x=>(x.textContent||'').includes(needle)); if(!h)return null; const r=h.closest('section').getBoundingClientRect(); return {x:Math.max(0,r.x-12),y:Math.max(0,r.y+scrollY-12),width:Math.min(document.documentElement.scrollWidth,r.width+24),height:r.height+24}; })()`);
  if (!rect) throw new Error(`Seção não encontrada: ${heading}`);
  const result = await cdp.send("Page.captureScreenshot", { format: "png", fromSurface: true, captureBeyondViewport: true, clip: { ...rect, scale: 1 } });
  await fs.writeFile(path.join(outDir, name), Buffer.from(result.data, "base64"));
}
async function viewport(cdp, width, height, mobile = false) {
  await cdp.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile });
}
async function navigate(cdp, route, width = 1440, height = 1000, mobile = false) {
  await viewport(cdp, width, height, mobile);
  await cdp.send("Page.navigate", { url: `${frontendUrl}${route}` });
  await wait(1300);
  await waitText(cdp, "Prescripta");
}
async function scrollText(cdp, text) {
  await evaluate(cdp, `(() => { const needle=${JSON.stringify(text.toLowerCase())}; const el=[...document.querySelectorAll('h1,h2,h3,p,span')].find(x=>(x.textContent||'').toLowerCase().includes(needle)); if(el) el.scrollIntoView({block:'start'}); return !!el; })()`);
  await wait(500);
}
async function makeGif(name, frames) {
  const listPath = path.join(tempDir, `${name}.txt`);
  const body = frames.flatMap((frame) => [`file '${path.join(outDir, frame).replaceAll("'", "'\\''")}'`, "duration 5"]).join("\n") + `\nfile '${path.join(outDir, frames.at(-1))}'\n`;
  await fs.writeFile(listPath, body, "utf8");
  const output = path.join(outDir, name);
  const command = spawnSync("ffmpeg", ["-y", "-f", "concat", "-safe", "0", "-i", listPath, "-vf", "fps=5,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer", output], { stdio: "inherit" });
  if (command.status !== 0) throw new Error(`ffmpeg falhou: ${name}`);
}

await fs.mkdir(outDir, { recursive: true });
const env = { ...process.env, PRESCRIPTA_DATABASE_URL: `sqlite:///${path.join(tempDir, "capture.db").replaceAll("\\", "/")}`, PRESCRIPTA_CORS_ORIGINS: frontendUrl, PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS: "false" };
const backend = spawn(path.join(root, ".venv", "Scripts", "python.exe"), ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8012"], { cwd: path.join(root, "backend"), env, stdio: "ignore" });
const frontend = spawn(process.env.ComSpec ?? "cmd.exe", ["/d", "/s", "/c", "npm run dev -- --host 127.0.0.1 --port 5176"], { cwd: path.join(root, "frontend"), env: { ...process.env, VITE_API_URL: apiUrl }, stdio: "ignore" });
const chrome = spawn(chromePath, ["--headless=new", "--remote-debugging-port=9226", `--user-data-dir=${path.join(tempDir, "chrome")}`, "--disable-gpu", "--no-first-run", "about:blank"], { stdio: "ignore" });

try {
  await waitFor(`${apiUrl}/health`); await waitFor(frontendUrl); await waitFor("http://127.0.0.1:9226/json/list");
  const targets = await (await fetch("http://127.0.0.1:9226/json/list")).json();
  const ws = new WebSocket(targets.find((item) => item.type === "page").webSocketDebuggerUrl);
  await new Promise((resolve) => ws.addEventListener("open", resolve, { once: true }));
  const cdp = new Cdp(ws); await cdp.send("Page.enable"); await cdp.send("Runtime.enable");
  await navigate(cdp, "/login");
  await evaluate(cdp, `fetch('${apiUrl}/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'admin@prescripta.local',password:'Admin@12345'})}).then(r=>r.json()).then(x=>{localStorage.setItem('prescripta_access_token',x.access_token);return true})`);
  await cdp.send("Page.navigate", { url: `${frontendUrl}/` });
  await wait(1200);
  await waitText(cdp, "Dashboard");

  await shot(cdp, "dashboard-admin-v0.8.5.png");
  await evaluate(cdp, `fetch('${apiUrl}/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'medico@prescripta.local',password:'Medico@12345'})}).then(r=>r.json()).then(x=>{localStorage.setItem('prescripta_access_token',x.access_token);return true})`);
  await cdp.send("Page.navigate", { url: `${frontendUrl}/` });
  await wait(1200);
  await waitText(cdp, "Dashboard");
  await shot(cdp, "dashboard-clinical-v0.8.5.png");
  await evaluate(cdp, `fetch('${apiUrl}/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'admin@prescripta.local',password:'Admin@12345'})}).then(r=>r.json()).then(x=>{localStorage.setItem('prescripta_access_token',x.access_token);return true})`);
  await navigate(cdp, "/patients"); await shot(cdp, "patients-v0.8.5.png");
  await navigate(cdp, "/patients/1"); await shot(cdp, "patient-history-v0.8.5.png"); await viewport(cdp, 1440, 620); await scrollText(cdp, "Laudos e documentos"); await shot(cdp, "patient-document-review-v0.8.5.png");
  await navigate(cdp, "/medications"); await shot(cdp, "medications-catalog-v0.8.5.png"); await scrollText(cdp, "Fila de curadoria"); await shot(cdp, "medication-curation-v0.8.5.png");
  await navigate(cdp, "/prescription-check");
  await evaluate(cdp, `(() => { const set=(n,v)=>{const e=document.querySelector('[name="'+n+'"]'); if(!e)return; const p=e.tagName==='SELECT'?HTMLSelectElement.prototype:HTMLInputElement.prototype; Object.getOwnPropertyDescriptor(p,'value').set.call(e,String(v)); e.dispatchEvent(new Event('change',{bubbles:true})); e.dispatchEvent(new Event('input',{bubbles:true}));}; const ps=document.querySelector('[name="patient_id"]'); const ms=document.querySelector('[name="medication_id"]'); set('patient_id',ps?.options?.[1]?.value); set('medication_id',ms?.options?.[1]?.value); set('dose_mg',50);set('frequency_per_day',2);set('route','oral');set('duration_days',7);document.querySelector('button[type="submit"]')?.click();return true})()`);
  await waitText(cdp, "Resultado", 20000); await shot(cdp, "prescription-clinical-v0.8.5.png");
  await viewport(cdp, 1440, 620);
  await shotSection(cdp, "dose-intelligence-v0.8.5.png", "Dose Intelligence");
  await shotSection(cdp, "psychotropic-safety-v0.8.5.png", "Segurança psicotrópica");
  await shotSection(cdp, "prescribing-policy-v0.8.5.png", "Política de prescrição");
  await evaluate(cdp, `[...document.querySelectorAll('button')].find(x=>(x.textContent||'').includes('Modo técnico'))?.click();true`); await wait(600); await shot(cdp, "prescription-technical-v0.8.5.png");
  await navigate(cdp, "/protocols"); await shot(cdp, "protocols-v0.8.5.png");
  await navigate(cdp, "/reports"); await shot(cdp, "reports-v0.8.5.png");
  await navigate(cdp, "/audit"); await shot(cdp, "audit-v0.8.5.png");
  await navigate(cdp, "/settings/ai"); await shot(cdp, "ai-settings-v0.8.5.png");
  await navigate(cdp, "/", 390, 844, true); await shot(cdp, "mobile-v0.8.5.png");
  await navigate(cdp, "/", 768, 1024, true); await shot(cdp, "tablet-v0.8.5.png");
  ws.close();

  await makeGif("prescripta-v0.8.5-main-demo.gif", ["dashboard-admin-v0.8.5.png", "patients-v0.8.5.png", "prescription-clinical-v0.8.5.png", "reports-v0.8.5.png"]);
  await makeGif("prescripta-v0.8.5-clinical-workflow.gif", ["patient-history-v0.8.5.png", "prescription-clinical-v0.8.5.png", "dose-intelligence-v0.8.5.png", "psychotropic-safety-v0.8.5.png"]);
  await makeGif("prescripta-v0.8.5-admin-audit.gif", ["dashboard-admin-v0.8.5.png", "medications-catalog-v0.8.5.png", "reports-v0.8.5.png", "audit-v0.8.5.png"]);
  await makeGif("prescripta-v0.8.5-ai-assisted-flow.gif", ["ai-settings-v0.8.5.png", "prescription-technical-v0.8.5.png", "reports-v0.8.5.png", "audit-v0.8.5.png"]);
} finally {
  backend.kill(); frontend.kill(); chrome.kill();
}
