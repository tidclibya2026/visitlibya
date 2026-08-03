import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const sourceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argument = (name) => { const index = process.argv.indexOf(name); return index < 0 ? undefined : process.argv[index + 1]; };
const directory = path.resolve(argument("--directory") || path.join(sourceRoot, ".pages-artifact"));
const preManifest = process.argv.includes("--pre-manifest");
const errors = [];
const manifest = JSON.parse(fs.readFileSync(path.join(directory, "config/frontend-pages.json"), "utf8"));
const allowlist = JSON.parse(fs.readFileSync(path.join(sourceRoot, "config/pages-artifact-allowlist.json"), "utf8"));
const allowedExtensions = new Set(["", ".html", ".css", ".js", ".json", ".jpg", ".jpeg", ".png", ".webp", ".avif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".txt", ".xml"]);
const textExtensions = new Set([".html", ".css", ".js", ".json", ".txt", ".xml"]);
const forbiddenTop = new Set(allowlist.forbiddenTopLevel);
const files = [];
const relative = (target) => path.relative(directory, target).replaceAll("\\", "/");

function exactPath(target) {
  const rel = path.relative(directory, target);
  if (rel.startsWith("..") || path.isAbsolute(rel) && rel === target) return false;
  let current = directory;
  for (const segment of rel.split(path.sep).filter(Boolean)) {
    if (!fs.existsSync(current) || !fs.readdirSync(current).includes(segment)) return false;
    current = path.join(current, segment);
  }
  return fs.existsSync(current);
}

function resolveReference(file, reference) {
  const clean = reference.split(/[?#]/, 1)[0];
  if (!clean || clean.startsWith("#") || /^(?:https?:|mailto:|tel:|data:|\/\/)/i.test(clean)) return;
  if (clean.startsWith("/") || clean.includes("\\") || /^[A-Za-z]:/.test(clean)) { errors.push(`unsafe reference in ${relative(file)}: ${reference}`); return; }
  let decoded;
  try { decoded = decodeURIComponent(clean); } catch { errors.push(`invalid encoding in ${relative(file)}: ${reference}`); return; }
  const target = path.resolve(path.dirname(file), decoded);
  if (!exactPath(target)) errors.push(`missing or case-mismatched reference in ${relative(file)}: ${reference}`);
}

function walk(current) {
  for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
    const target = path.join(current, entry.name);
    const rel = relative(target);
    if (entry.isSymbolicLink()) errors.push(`symlink: ${rel}`);
    else if (entry.isDirectory()) {
      if (!rel.includes("/") && forbiddenTop.has(rel)) errors.push(`forbidden directory: ${rel}`);
      walk(target);
    } else {
      files.push(target);
      if (/(?:^|\/)\.env(?:\.|$)|\.(?:map|log|zip|docx?|xlsx?|pptx?|tiff?)$/i.test(rel)) errors.push(`forbidden file: ${rel}`);
      if (!allowedExtensions.has(path.extname(rel).toLowerCase()) && rel !== ".nojekyll") errors.push(`unsupported extension: ${rel}`);
      if (textExtensions.has(path.extname(rel).toLowerCase())) {
        const content = fs.readFileSync(target, "utf8");
        if (/^(?:<{7}|={7}|>{7})/m.test(content)) errors.push(`merge marker: ${rel}`);
        if (/sourceMappingURL\s*=/.test(content)) errors.push(`source map reference: ${rel}`);
        if (/(?:[A-Za-z]:\\|Users\\)/.test(content)) errors.push(`workstation path: ${rel}`);
        if (/\b(?:DATABASE_URL|POSTGRES_PASSWORD|JWT_SECRET_KEY|BEGIN [A-Z ]*PRIVATE KEY)\b/i.test(content)) errors.push(`secret-like value: ${rel}`);
      }
    }
  }
}

walk(directory);
for (const rel of [".nojekyll", "404.html", "robots.txt", ...manifest.pagePairs.flatMap((entry) => [entry.page, `ar/${entry.page}`])]) if (!exactPath(path.join(directory, rel))) errors.push(`missing required file: ${rel}`);
for (const top of fs.readdirSync(directory)) {
  const allowed = new Set([...allowlist.rootFiles.map((item) => item.split("/")[0]), ...Object.keys(allowlist.publicTrees).map((item) => item.split("/")[0]), ...allowlist.publicMedia.map((item) => item.split("/")[0]), ...manifest.pagePairs.map((entry) => entry.page), "ar", ...allowlist.generatedFiles]);
  if (!allowed.has(top)) errors.push(`not allowlisted at artifact root: ${top}`);
}

for (const file of files) {
  const extension = path.extname(file).toLowerCase();
  if (!textExtensions.has(extension)) continue;
  const content = fs.readFileSync(file, "utf8");
  if (extension === ".html") {
    for (const match of content.matchAll(/\b(?:href|src)=["']([^"']+)["']/gi)) resolveReference(file, match[1]);
    for (const match of content.matchAll(/url\(\s*["']?([^)"']+)["']?\s*\)/gi)) resolveReference(file, match[1].trim());
  } else if (extension === ".css") {
    for (const match of content.matchAll(/url\(\s*["']?([^)"']+)["']?\s*\)/gi)) resolveReference(file, match[1].trim());
  } else if (extension === ".js") {
    for (const match of content.matchAll(/(?:from\s+|import\s*)["']([^"']+)["']/g)) if (match[1].startsWith(".")) resolveReference(file, match[1]);
  }
}

const config = fs.readFileSync(path.join(directory, "config/frontend-config.js"), "utf8");
if (!/apiEnabled:\s*false/.test(config) || !/apiBaseUrl:\s*["']{2}/.test(config) || !/deploymentEnvironment:\s*["']static["']/.test(config)) errors.push("public runtime configuration is not static-safe");
if (/https?:\/\/(?:localhost|127\.0\.0\.1|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)/i.test(config)) errors.push("private runtime URL");
const hasSitemap = fs.existsSync(path.join(directory, "sitemap.xml"));
for (const entry of manifest.pagePairs) for (const rel of [entry.page, `ar/${entry.page}`]) {
  const html = fs.readFileSync(path.join(directory, rel), "utf8");
  const expectedRobots = entry.indexable ? "index,follow" : "noindex,follow";
  if (!new RegExp(`<meta[^>]+(?:name=["']robots["'][^>]+content|content=["']${expectedRobots}["'][^>]+name)=["']?${expectedRobots.replace(",", ",?")}["']?`, "i").test(html) && !html.includes(`content="${expectedRobots}"`)) errors.push(`robots policy: ${rel}`);
  const eligible = entry.indexable && entry.page !== "destination.html";
  const canonicalCount = [...html.matchAll(/rel=["']canonical["']/gi)].length;
  if (hasSitemap && eligible && canonicalCount !== 1) errors.push(`canonical count ${canonicalCount}: ${rel}`);
  if ((!hasSitemap || !eligible) && canonicalCount !== 0) errors.push(`unexpected canonical: ${rel}`);
  if (!hasSitemap && /property=["']og:url["']/i.test(html)) errors.push(`origin metadata in preview: ${rel}`);
  if (entry.page === "destination.html" && /property=["']og:url["']/i.test(html)) errors.push(`generic destination og:url forbidden: ${rel}`);
}
const notFound = fs.readFileSync(path.join(directory, "404.html"), "utf8");
if (!/noindex,follow/i.test(notFound) || !/\/visitlibya\//.test(notFound)) errors.push("404 policy or project base recovery is invalid");

if (!preManifest) {
  const manifestPath = path.join(directory, "release-manifest.json");
  if (!fs.existsSync(manifestPath)) errors.push("release-manifest.json missing");
  else {
    const release = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    if (release.schemaVersion !== 1 || !/^\d{4}-\d{2}-\d{2}T/.test(release.buildTimestampUtc) || !/^[0-9a-f]{40}$/i.test(release.sourceCommit) || release.projectBasePath !== manifest.projectBasePath || !["supplied", "not-supplied"].includes(release.releaseOriginStatus) || !Array.isArray(release.files)) errors.push("release manifest schema invalid");
    const payload = files.filter((file) => relative(file) !== "release-manifest.json").sort((a, b) => relative(a).localeCompare(relative(b), "en"));
    if (release.fileCount !== payload.length || release.files.length !== payload.length) errors.push("release manifest file count mismatch");
    const total = payload.reduce((sum, file) => sum + fs.statSync(file).size, 0);
    if (release.totalBytes !== total) errors.push("release manifest total byte mismatch");
    for (let index = 0; index < payload.length; index += 1) {
      const file = payload[index];
      const expected = { path: relative(file), bytes: fs.statSync(file).size, sha256: crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex") };
      const actual = release.files[index];
      if (!actual || actual.path !== expected.path || actual.bytes !== expected.bytes || actual.sha256 !== expected.sha256) errors.push(`release manifest entry mismatch: ${expected.path}`);
    }
    if (JSON.stringify(release).includes(sourceRoot) || /[A-Za-z]:\\|Users\\/.test(JSON.stringify(release))) errors.push("release manifest contains workstation path");
    if ((release.releaseOriginStatus === "supplied") !== hasSitemap) errors.push("release origin status does not match sitemap state");
  }
}

if (errors.length) { for (const error of errors) console.error(`FAIL ${error}`); console.error(`Pages artifact validation failed: ${errors.length} issue(s).`); process.exitCode = 1; }
else console.log(`Pages artifact validation passed: ${files.length} files, ${files.reduce((sum, file) => sum + fs.statSync(file).size, 0)} bytes, sitemap ${hasSitemap ? "present" : "absent"}.`);