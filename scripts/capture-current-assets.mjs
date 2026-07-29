import { spawnSync } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const basePath = path.join(root, "scripts", "capture-v085-assets.mjs");
const generatedPath = path.join(root, "scripts", ".capture-current.generated.mjs");
let source = await fs.readFile(basePath, "utf8");
source = source.replaceAll("v0.8.5", "v0.8.6").replaceAll("v085", "v086");
const replacements = new Map([
  ["patients-v0.8.6.png", "patients-list-v0.8.6.png"],
  ["patient-document-review-v0.8.6.png", "patient-documents-v0.8.6.png"],
  ["medications-catalog-v0.8.6.png", "medications-catalog-v0.8.6.png"],
  ["prescripta-v0.8.6-clinical-workflow.gif", "prescripta-v0.8.6-clinical-flow.gif"],
  ["prescripta-v0.8.6-admin-audit.gif", "prescripta-v0.8.6-admin-flow.gif"],
  ["prescripta-v0.8.6-ai-assisted-flow.gif", "prescripta-v0.8.6-audit-flow.gif"],
]);
for (const [from, to] of replacements) source = source.replaceAll(from, to);
source = source.replace(
  'await navigate(cdp, "/login");',
  'await navigate(cdp, "/login"); await shot(cdp, "login-v0.8.6.png");',
);
source = source.replace(
  'await shot(cdp, "dashboard-clinical-v0.8.6.png");',
  `await shot(cdp, "dashboard-clinical-v0.8.6.png");
  await evaluate(cdp, \`fetch('\${apiUrl}/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'auditor@prescripta.local',password:'Auditor@12345'})}).then(r=>r.json()).then(x=>{localStorage.setItem('prescripta_access_token',x.access_token);return true})\`);
  await cdp.send("Page.navigate", { url: \`\${frontendUrl}/\` }); await wait(1200); await shot(cdp, "dashboard-auditor-v0.8.6.png");`,
);
source = source.replace(
  'await navigate(cdp, "/patients/1"); await shot(cdp, "patient-history-v0.8.6.png");',
  'await navigate(cdp, "/patients/1"); await shot(cdp, "patient-details-v0.8.6.png"); await shotSection(cdp, "patient-history-v0.8.6.png", "Linha do tempo do paciente");',
);
source = source.replace(
  'await navigate(cdp, "/medications"); await shot(cdp, "medications-catalog-v0.8.6.png");',
  'await navigate(cdp, "/medications"); await shot(cdp, "medications-catalog-v0.8.6.png"); await shotSection(cdp, "medication-details-v0.8.6.png", "Lista de medicamentos");',
);
source = source.replace(
  'await navigate(cdp, "/protocols"); await shot(cdp, "protocols-v0.8.6.png");',
  'await navigate(cdp, "/protocols"); await shot(cdp, "protocols-list-v0.8.6.png"); await shotSection(cdp, "protocol-run-v0.8.6.png", "Contexto mínimo");',
);
source = source.replace(
  'await navigate(cdp, "/reports");',
  'await navigate(cdp, "/clinical-imports"); await shot(cdp, "imports-v0.8.6.png"); await navigate(cdp, "/users"); await shot(cdp, "users-specialties-v0.8.6.png"); await navigate(cdp, "/reports");',
);
source = source.replace(
  'await makeGif("prescripta-v0.8.6-audit-flow.gif",',
  'await makeGif("prescripta-v0.8.6-mobile-flow.gif", ["mobile-v0.8.6.png", "tablet-v0.8.6.png", "dashboard-clinical-v0.8.6.png", "patients-list-v0.8.6.png"]);\n  await makeGif("prescripta-v0.8.6-audit-flow.gif",',
);
await fs.writeFile(generatedPath, source, "utf8");
try {
  const result = spawnSync(process.execPath, [generatedPath], { cwd: root, stdio: "inherit" });
  if (result.status !== 0) process.exit(result.status ?? 1);
} finally {
  await fs.rm(generatedPath, { force: true });
}
