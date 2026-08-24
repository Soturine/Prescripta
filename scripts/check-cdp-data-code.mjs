import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const scripts = await fs.readdir(path.join(root, "scripts"));
const violations = [];
for (const name of scripts.filter((item) => item.endsWith(".mjs"))) {
  const file = path.join(root, "scripts", name);
  const source = await fs.readFile(file, "utf8");
  const calls = source.matchAll(/evaluate\s*\(\s*cdp\s*,\s*`([\s\S]*?)`\s*,?\s*\)/g);
  for (const match of calls) {
    if (match[1].includes("${")) {
      violations.push(`${name}: interpolated Runtime.evaluate expression`);
    }
  }
}
if (violations.length) {
  throw new Error(violations.join("\n"));
}
console.log("CDP audit OK: dynamic values use Runtime.callFunctionOn arguments.");
