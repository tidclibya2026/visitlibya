import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const violations = [];
const warnings = [];
const apiPages = [
  "destinations.html", "destination.html", "register.html", "trips.html", "trip.html",
  "ar/destinations.html", "ar/destination.html", "ar/register.html", "ar/trips.html", "ar/trip.html",
];
const approvedLocalReferences = new Set([
  "config/frontend-config.example.js",
  "assets/js/app/config/runtime-config.js",
  "docs/frontend-architecture.md",
  "docs/frontend-runtime-configuration.md",
  "backend/.env.example",
  "backend/app/core/config.py",
]);

function fail(message) { violations.push(message); }
function relative(file) { return path.relative(root, file).replaceAll("\\", "/"); }
function exists(relativePath) { return fs.existsSync(path.join(root, relativePath)); }
function walk(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(directory, entry.name);
    if (entry.name === ".git" || entry.name === ".venv" || entry.name === "node_modules") return [];
    return entry.isDirectory() ? walk(target) : [target];
  });
}

const files = walk(root);
const textFiles = files.filter((file) => /\.(?:html|css|js|mjs|md|yml|yaml|example|py)$/.test(file));

for (const file of textFiles) {
  const rel = relative(file);
  const content = fs.readFileSync(file, "utf8");
  if (/\b(?:localhost|127\.0\.0\.1)\b/i.test(content) &&
      !approvedLocalReferences.has(rel) &&
      !rel.startsWith("backend/tests/") &&
      rel !== "scripts/validate-frontend.mjs") {
    fail(`${rel}: local host reference is not in an approved development example`);
  }
  if (/\b(?:src|href)=["']\/(?!\/)|url\(["']?\/(?!\/)/i.test(content)) {
    fail(`${rel}: root-relative frontend path can break project-subpath hosting`);
  }
}

for (const page of apiPages) {
  const content = fs.readFileSync(path.join(root, page), "utf8");
  const configIndex = content.indexOf("config/frontend-config.js");
  const controllerMatch = content.match(/<script\s+type=["']module["']\s+src=["']([^"']*assets\/js\/pages\/[^"']+)["']/i);
  if (configIndex < 0) fail(`${page}: missing frontend runtime configuration script`);
  if (!controllerMatch) fail(`${page}: missing API page controller module`);
  else if (configIndex > content.indexOf(controllerMatch[0])) fail(`${page}: configuration loads after its page controller`);
}

const publicConfig = fs.readFileSync(path.join(root, "config/frontend-config.js"), "utf8");
if (!/apiEnabled:\s*false\b/.test(publicConfig)) fail("config/frontend-config.js: committed apiEnabled must be false");
if (!/apiBaseUrl:\s*["']\s*["']/.test(publicConfig)) fail("config/frontend-config.js: committed apiBaseUrl must be empty");
if (!/deploymentEnvironment:\s*["']static["']/.test(publicConfig)) fail("config/frontend-config.js: committed environment must be static");
if (/apiEnabled:\s*true\b/.test(publicConfig) && /apiBaseUrl:\s*["']http:\/\//.test(publicConfig)) {
  fail("config/frontend-config.js: enabled production configuration must not use HTTP");
}

const configAssignments = textFiles.filter((file) => {
  const rel = relative(file);
  return rel.endsWith(".js") && /VISIT_LIBYA_CONFIG\s*=/.test(fs.readFileSync(file, "utf8"));
}).map(relative);
const allowedAssignments = new Set(["config/frontend-config.js", "config/frontend-config.example.js"]);
for (const assignment of configAssignments) {
  if (!allowedAssignments.has(assignment)) fail(`${assignment}: duplicates the public runtime configuration`);
}

for (const file of files.filter((item) => item.endsWith(".html"))) {
  const content = fs.readFileSync(file, "utf8");
  for (const match of content.matchAll(/<script[^>]+src=["']([^"']+)["']/gi)) {
    const reference = match[1].split(/[?#]/, 1)[0];
    if (/^(?:https?:)?\/\//i.test(reference)) continue;
    const target = path.resolve(path.dirname(file), reference);
    if (!fs.existsSync(target)) fail(`${relative(file)}: missing script ${reference}`);
  }
}

for (const file of files.filter((item) => /\.(?:js|mjs)$/.test(item))) {
  const content = fs.readFileSync(file, "utf8");
  for (const match of content.matchAll(/(?:from\s+|import\s*)["']([^"']+)["']/g)) {
    const reference = match[1];
    if (!reference.startsWith(".")) continue;
    const target = path.resolve(path.dirname(file), reference);
    if (!fs.existsSync(target)) fail(`${relative(file)}: missing module ${reference}`);
  }
}

const en = fs.readFileSync(path.join(root, "assets/js/app/i18n/en.js"), "utf8");
const ar = fs.readFileSync(path.join(root, "assets/js/app/i18n/ar.js"), "utf8");
const keys = (source) => [...source.matchAll(/^\s{4}([A-Za-z][A-Za-z0-9]*):/gm)].map((match) => match[1]).sort();
if (JSON.stringify(keys(en)) !== JSON.stringify(keys(ar))) fail("English and Arabic dynamic dictionaries are not structurally equivalent");

if (!exists(".github/workflows/frontend-validation.yml")) warnings.push("frontend validation workflow is missing");

for (const warning of warnings) console.warn(`WARN: ${warning}`);
if (violations.length) {
  for (const violation of violations) console.error(`FAIL: ${violation}`);
  console.error(`Frontend validation failed with ${violations.length} violation(s).`);
  process.exitCode = 1;
} else {
  console.log(`Frontend validation passed (${apiPages.length} API pages checked).`);
}
