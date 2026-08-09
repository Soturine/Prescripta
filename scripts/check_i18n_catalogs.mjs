import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const catalogs = {
  "pt-BR": JSON.parse(readFileSync(resolve(root, "frontend/src/i18n/locales/pt-BR.json"), "utf8")),
  "en-US": JSON.parse(readFileSync(resolve(root, "frontend/src/i18n/locales/en-US.json"), "utf8")),
};

function flatten(value, prefix = "", result = new Map()) {
  for (const [key, child] of Object.entries(value)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof child === "string") result.set(path, child);
    else if (child && typeof child === "object" && !Array.isArray(child)) flatten(child, path, result);
    else throw new Error(`Invalid catalog value at ${path}`);
  }
  return result;
}

function placeholders(value) {
  return [...value.matchAll(/{{\s*([\w.]+)\s*}}/g)].map((match) => match[1]).sort();
}

const flat = Object.fromEntries(Object.entries(catalogs).map(([locale, value]) => [locale, flatten(value)]));
const referenceKeys = [...flat["pt-BR"].keys()].sort();
const comparedKeys = [...flat["en-US"].keys()].sort();
if (JSON.stringify(referenceKeys) !== JSON.stringify(comparedKeys)) {
  const missing = referenceKeys.filter((key) => !flat["en-US"].has(key));
  const orphan = comparedKeys.filter((key) => !flat["pt-BR"].has(key));
  throw new Error(`Catalog key mismatch. missing=${missing.join(",")} orphan=${orphan.join(",")}`);
}

for (const key of referenceKeys) {
  const expected = placeholders(flat["pt-BR"].get(key));
  const actual = placeholders(flat["en-US"].get(key));
  if (JSON.stringify(expected) !== JSON.stringify(actual)) {
    throw new Error(`Placeholder mismatch at ${key}: pt-BR=${expected} en-US=${actual}`);
  }
}

const migratedFiles = [
  "frontend/src/components/Layout.tsx",
  "frontend/src/components/Sidebar.tsx",
  "frontend/src/components/LanguageSelector.tsx",
  "frontend/src/components/PageHeader.tsx",
  "frontend/src/pages/Dashboard.tsx",
  "frontend/src/pages/Login.tsx",
  "frontend/src/pages/Help.tsx",
];
const forbiddenResiduals = ["Medication Safety", "Pharmacy workflow", ">Sources<", ">Workspace<"];
for (const file of migratedFiles) {
  const source = readFileSync(resolve(root, file), "utf8");
  if (!source.includes("useTranslation")) throw new Error(`Migrated file does not use i18n: ${file}`);
  for (const residual of forbiddenResiduals) {
    if (source.includes(residual)) throw new Error(`Hardcoded residual '${residual}' in ${file}`);
  }
}

console.log(`i18n catalogs OK: ${referenceKeys.length} aligned keys, placeholders and migrated surfaces checked.`);
