import fs from "node:fs/promises";
import path from "node:path";

const baseUrl = (process.env.TEMPLATE_API_BASE_URL || "http://127.0.0.1:3000").replace(/\/+$/, "");
const groups = (process.env.TEMPLATE_GROUPS || "general,modern,standard,swift,neo-general,neo-modern,neo-standard,neo-swift")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const outputDir = path.resolve(process.cwd(), "../fastapi/templates");

async function exportGroup(group) {
  const url = `${baseUrl}/api/template?group=${encodeURIComponent(group)}`;
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to fetch ${group} from ${url}: ${response.status} ${text}`);
  }
  const data = await response.json();
  const payload = {
    version: "v1",
    ...data,
  };
  const outputFile = path.join(outputDir, `${group}.json`);
  await fs.writeFile(outputFile, `${JSON.stringify(payload, null, 2)}\n`, "utf-8");
  console.log(`exported ${group} -> ${outputFile}`);
}

async function main() {
  await fs.mkdir(outputDir, { recursive: true });
  for (const group of groups) {
    await exportGroup(group);
  }
  console.log(`done. exported ${groups.length} template groups`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

