import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const assetRoot = join(root, "frontend", "src", "assets", "third-party");
const manifest = JSON.parse(await readFile(join(assetRoot, "manifest.json"), "utf8"));
const forbidden = [/<script\b/i, /<foreignObject\b/i, /\son[a-z]+\s*=/i, /javascript:/i, /(?:href|src)\s*=\s*["']https?:/i];

for (const asset of manifest.assets) {
  const content = await readFile(join(assetRoot, asset.path));
  const text = content.toString("utf8");
  const digest = createHash("sha256").update(content).digest("hex");
  if (digest !== asset.sha256) throw new Error(`Hash mismatch: ${asset.path}`);
  if (!asset.source || !asset.license || !asset.source_commit || !asset.purpose) throw new Error(`Incomplete provenance: ${asset.path}`);
  for (const pattern of forbidden) if (pattern.test(text)) throw new Error(`Unsafe SVG pattern ${pattern}: ${asset.path}`);
}

console.log(`Frontend assets OK: ${manifest.assets.length} governed SVGs`);
