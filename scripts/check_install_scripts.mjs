import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptsDirectory = dirname(fileURLToPath(import.meta.url));
const root = resolve(scriptsDirectory, "..");
const lockPath = process.argv[2] ? resolve(process.argv[2]) : resolve(root, "frontend/package-lock.json");
const expected = JSON.parse(readFileSync(resolve(scriptsDirectory, "install-script-policy.json"), "utf8"));
const lock = JSON.parse(readFileSync(lockPath, "utf8"));
const observed = Object.fromEntries(
  Object.entries(lock.packages ?? {})
    .filter(([, metadata]) => metadata.hasInstallScript === true)
    .map(([path, metadata]) => [path, metadata.version])
    .sort(([left], [right]) => left.localeCompare(right)),
);
const normalizedExpected = Object.fromEntries(
  Object.entries(expected).sort(([left], [right]) => left.localeCompare(right)),
);

if (JSON.stringify(observed) !== JSON.stringify(normalizedExpected)) {
  throw new Error(
    `Install-script inventory changed; review before install. expected=${JSON.stringify(normalizedExpected)} observed=${JSON.stringify(observed)}`,
  );
}

console.log("Install-script inventory OK: exact package paths and versions approved.");
