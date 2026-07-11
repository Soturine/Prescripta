import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const root = process.cwd();
const frontendUrl = process.env.PRESCRIPTA_CAPTURE_FRONTEND_URL ?? "http://127.0.0.1:5175";
const apiUrl = process.env.PRESCRIPTA_CAPTURE_API_URL ?? "http://127.0.0.1:8011/api";
const chromePath =
  process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const debugPort = Number(process.env.PRESCRIPTA_CAPTURE_DEBUG_PORT ?? "9225");
const outDir = path.join(root, "docs", "assets", "v0.8.3");
const data = JSON.parse(await fs.readFile(path.join(root, ".codex-v083-assets-data.json"), "utf8"));

class CdpClient {
  constructor(ws) {
    this.ws = ws;
    this.nextId = 1;
    this.pending = new Map();
    ws.addEventListener("message", (event) => {
      const payload = JSON.parse(event.data);
      if (payload.id && this.pending.has(payload.id)) {
        const { resolve, reject } = this.pending.get(payload.id);
        this.pending.delete(payload.id);
        if (payload.error) {
          reject(new Error(payload.error.message));
        } else {
          resolve(payload.result ?? {});
        }
      }
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error(`CDP timeout: ${method}`));
        }
      }, 15000);
    });
  }
}

async function wait(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForEndpoint(url, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return response;
      }
    } catch {
      // keep waiting
    }
    await wait(300);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function waitForEval(cdp, expression, timeoutMs = 12000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const result = await cdp.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (result.result?.value) {
      return;
    }
    await wait(400);
  }
  const body = await cdp.send("Runtime.evaluate", {
    expression: "document.body.innerText",
    returnByValue: true,
  });
  throw new Error(
    `Timed out waiting for expression: ${expression}\nBody:\n${body.result?.value ?? ""}`,
  );
}

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || "Runtime evaluation failed");
  }
  return result;
}

function js(value) {
  return JSON.stringify(value);
}

let currentLogin = null;

async function ensureLogin(cdp, session) {
  if (currentLogin === session.email) {
    return;
  }
  await cdp.send("Page.navigate", { url: `${frontendUrl}/login` });
  await waitForEval(cdp, "document.readyState === 'complete'");
  await evaluate(cdp, "localStorage.clear(); true;");
  await evaluate(
    cdp,
    `fetch(${js(`${apiUrl}/auth/login`)}, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: ${js(session.email)}, password: ${js(session.password)} })
    }).then((response) => {
      if (!response.ok) throw new Error('login failed ' + response.status);
      return response.json();
    }).then((payload) => {
      localStorage.setItem('prescripta_access_token', payload.access_token);
      localStorage.setItem('prescripta_user', JSON.stringify(payload.user));
      window.location.href = ${js(`${frontendUrl}/`)};
      return true;
    })`,
  );
  await waitForEval(
    cdp,
    "!location.pathname.includes('login') && !document.body.innerText.includes('Validando')",
  );
  currentLogin = session.email;
  await wait(700);
}

async function navigate(cdp, route, session, viewport = { width: 1440, height: 1100, mobile: false }) {
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    deviceScaleFactor: 1,
    mobile: viewport.mobile,
  });
  await ensureLogin(cdp, session);
  await cdp.send("Page.navigate", { url: `${frontendUrl}${route}` });
  await waitForEval(cdp, "document.readyState === 'complete'");
  await waitForEval(
    cdp,
    "!document.body.innerText.includes('Carregando') && !location.pathname.includes('login')",
  );
  await wait(900);
}

async function screenshot(cdp, filename) {
  const shot = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
  });
  await fs.writeFile(path.join(outDir, filename), Buffer.from(shot.data, "base64"));
}

async function scrollToText(cdp, text) {
  await evaluate(
    cdp,
    `(() => {
      const normalize = (value) => value.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();
      const needle = normalize(${js(text)});
      const nodes = [...document.querySelectorAll('h1,h2,h3,p,span,label,button,article,section')];
      const node = nodes.find((item) => normalize(item.textContent || '').includes(needle));
      if (node) node.scrollIntoView({ block: 'start', inline: 'nearest' });
      return Boolean(node);
    })();`,
  );
  await wait(600);
}

async function fillPrescription(cdp) {
  await evaluate(
    cdp,
    `(() => {
      const patientId = ${Number(data.patient_id)};
      const medicationId = ${Number(data.medication_id)};
      const setValue = (el, value) => {
        if (!el) return;
        const proto = el.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setter.call(el, String(value));
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      };
      setValue(document.querySelector('[name="patient_id"]'), patientId);
      setValue(document.querySelector('[name="medication_id"]'), medicationId);
      setValue(document.querySelector('[name="dose_mg"]'), 50);
      setValue(document.querySelector('[name="frequency_per_day"]'), 2);
      setValue(document.querySelector('[name="route"]'), 'oral');
      setValue(document.querySelector('[name="duration_days"]'), 7);
      const button = document.querySelector('button[type="submit"]');
      button?.click();
      return true;
    })();`,
  );
  await waitForEval(cdp, "document.body.innerText.includes('Resultado')");
  await scrollToText(cdp, "Resultado");
}

async function explainPrescription(cdp) {
  await evaluate(
    cdp,
    `(() => {
      const button = [...document.querySelectorAll('button')]
        .find((item) => (item.textContent || '').includes('Explicar com IA'));
      button?.click();
      return Boolean(button);
    })();`,
  );
  await waitForEval(cdp, "document.body.innerText.includes('Provider configurado') || document.body.innerText.includes('Fallback determin')");
  await wait(900);
}

async function fillProtocol(cdp) {
  await evaluate(
    cdp,
    `(() => {
      const patientId = ${Number(data.patient_id)};
      const setSelect = (select, value) => {
        const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
        setter.call(select, String(value));
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
      };
      const patientSelect = [...document.querySelectorAll('label')]
        .find((label) => (label.textContent || '').includes('Selecionar paciente'))
        ?.querySelector('select');
      if (patientSelect) setSelect(patientSelect, patientId);
      const textInput = [...document.querySelectorAll('input')]
        .find((input) => input.type === 'text' && !input.placeholder);
      if (textInput) {
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(textInput, 'medicamento informado');
        textInput.dispatchEvent(new Event('input', { bubbles: true }));
        textInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
      const boolSelect = [...document.querySelectorAll('select')].find((select) =>
        [...select.options].some((option) => option.value === 'true')
      );
      if (boolSelect) setSelect(boolSelect, 'true');
      return true;
    })();`,
  );
  await wait(500);
}

async function runProtocol(cdp) {
  await fillProtocol(cdp);
  await evaluate(
    cdp,
    `(() => {
      const button = [...document.querySelectorAll('button')]
        .find((item) => (item.textContent || '').includes('Executar fluxo'));
      button?.click();
      return Boolean(button);
    })();`,
  );
  await waitForEval(cdp, "document.body.innerText.includes('Execu')");
  await wait(1000);
  await evaluate(
    cdp,
    `(() => {
      const button = [...document.querySelectorAll('button')]
        .find((item) => (item.textContent || '').includes('Preview'));
      button?.click();
      return true;
    })();`,
  );
  await wait(1000);
}

async function runMedicationLookup(cdp) {
  await scrollToText(cdp, "Busca assistida por fonte");
  await evaluate(
    cdp,
    `(() => {
      const textarea = [...document.querySelectorAll('textarea')][0];
      if (textarea) {
        const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
        setter.call(textarea, 'amoxicilina; sinonimos: amoxicilina tri-hidratada; fonte demonstrativa');
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        textarea.dispatchEvent(new Event('change', { bubbles: true }));
      }
      const button = [...document.querySelectorAll('button')]
        .find((item) => (item.textContent || '').includes('Estruturar fonte'));
      button?.click();
      return true;
    })();`,
  );
  await waitForEval(cdp, "document.body.innerText.includes('enviado para curadoria') || document.body.innerText.includes('Fila de curadoria')");
  await wait(900);
}

async function main() {
  await fs.mkdir(outDir, { recursive: true });
  const adminToken = { email: "admin@prescripta.local", password: "Admin@12345" };
  const medicoToken = { email: "medico@prescripta.local", password: "Medico@12345" };
  const userDataDir = await fs.mkdtemp(path.join(os.tmpdir(), "prescripta-v083-chrome-"));
  const chrome = spawn(chromePath, [
    "--headless=new",
    `--remote-debugging-port=${debugPort}`,
    `--user-data-dir=${userDataDir}`,
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "about:blank",
  ], { stdio: "ignore" });

  try {
    await waitForEndpoint(`http://127.0.0.1:${debugPort}/json/list`);
    const targets = await (await fetch(`http://127.0.0.1:${debugPort}/json/list`)).json();
    const page = targets.find((target) => target.type === "page");
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((resolve) => ws.addEventListener("open", resolve, { once: true }));
    const cdp = new CdpClient(ws);
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");

    await navigate(cdp, "/", medicoToken);
    await screenshot(cdp, "dashboard-clinical-view-v0.8.3.png");

    await navigate(cdp, "/", adminToken);
    await screenshot(cdp, "dashboard-technical-view-v0.8.3.png");

    await navigate(cdp, `/patients/${data.patient_id}`, adminToken);
    await scrollToText(cdp, "Historico clinico");
    await screenshot(cdp, "patient-history-documents-v0.8.3.png");
    await scrollToText(cdp, "Laudos e documentos");
    await screenshot(cdp, "patient-document-upload-v0.8.3.png");
    await scrollToText(cdp, "Linha do tempo");
    await screenshot(cdp, "patient-timeline-v0.8.3.png");

    await navigate(cdp, "/prescription-check", adminToken);
    await fillPrescription(cdp);
    await screenshot(cdp, "prescription-clinical-view-v0.8.3.png");
    await screenshot(cdp, "psychotropic-alert-v0.8.3.png");
    await screenshot(cdp, "clinician-friendly-ui-v0.8.3.png");
    await explainPrescription(cdp);
    await screenshot(cdp, "ai-module-actions-v0.8.3.png");
    await evaluate(cdp, "[...document.querySelectorAll('button')].find((item) => (item.textContent || '').includes('Modo tecnico'))?.click(); true;");
    await wait(700);
    await screenshot(cdp, "prescription-technical-details-v0.8.3.png");

    await navigate(cdp, "/medications", adminToken);
    await runMedicationLookup(cdp);
    await screenshot(cdp, "medication-knowledge-lookup-v0.8.3.png");
    await scrollToText(cdp, "Fila de curadoria");
    await screenshot(cdp, "medication-curation-queue-v0.8.3.png");

    await navigate(cdp, "/protocols", adminToken);
    await fillProtocol(cdp);
    await screenshot(cdp, "protocol-patient-context-v0.8.3.png");
    await runProtocol(cdp);
    await screenshot(cdp, "protocol-generated-report-v0.8.3.png");

    await navigate(cdp, "/reports", adminToken);
    await scrollToText(cdp, "Relatorio de Protocolo");
    await screenshot(cdp, "reports-protocol-generatedreport-v0.8.3.png");

    await navigate(cdp, "/audit", adminToken);
    await evaluate(cdp, "window.scrollTo(0, 0); true;");
    await wait(500);
    await screenshot(cdp, "audit-protocol-filters-v0.8.3.png");

    await navigate(cdp, "/", medicoToken, { width: 390, height: 844, mobile: true });
    await screenshot(cdp, "responsive-mobile-v0.8.3.png");

    ws.close();
  } finally {
    chrome.kill();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
