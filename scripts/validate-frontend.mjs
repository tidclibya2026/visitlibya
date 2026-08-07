import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifestPath = path.join(root, "config/frontend-pages.json");
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
const sections = new Map();
const warnings = [];
const approvedLocalReferences = new Set([
  "config/frontend-config.example.js",
  "assets/js/app/config/runtime-config.js",
  "docs/frontend-architecture.md",
  "docs/frontend-runtime-configuration.md",
  "docs/frontend-deployment-smoke-tests.md",
  "docs/public-release-readiness.md",
  "backend/.env.example",
  "backend/app/core/config.py",
  ".github/workflows/backend-production-validation.yml",
  "docker-compose.production.example.yml",
  "docs/backend-cors-and-frontend-integration.md",
  "docs/frontend-release-checklist.md",
  "scripts/validate-pages-artifact.mjs",
  "scripts/build-pages-artifact.mjs",
  "scripts/generate-sitemap.mjs",
  "docs/release-artifact-guide.md",
]);
const allowedExternalHttp = new Set();
const ignoredDirectories = new Set([".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".pages-artifact"]);
const localReferencePattern = /^(?![a-z][a-z0-9+.-]*:|\/\/)(.*)$/i;
const unsupportedBrowserImage = /\.tiff?(?:$|[?#])/i;

function issue(section, message) {
  if (!sections.has(section)) sections.set(section, []);
  sections.get(section).push(message);
}

function warn(message) { warnings.push(message); }
function sha256(file) { return createHash("sha256").update(fs.readFileSync(file)).digest("hex"); }
function relative(file) { return path.relative(root, file).replaceAll("\\", "/"); }
function sourceLine(content, index) { return content.slice(0, index).split(/\r?\n/).length; }
function at(file, content, index, message) { return `${relative(file)}:${sourceLine(content, index)}: ${message}`; }
function stripQueryAndFragment(reference) { return reference.split(/[?#]/, 1)[0]; }
function decodePath(reference) {
  try { return decodeURIComponent(reference); } catch { return null; }
}
function walk(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    if (ignoredDirectories.has(entry.name)) return [];
    const target = path.join(directory, entry.name);
    return entry.isDirectory() ? walk(target) : [target];
  });
}

function exactPathStatus(target) {
  const absolute = path.resolve(target);
  const rel = path.relative(root, absolute);
  if (rel.startsWith("..") || path.isAbsolute(rel) && rel === absolute) return "outside repository";
  let current = root;
  for (const segment of rel.split(path.sep).filter(Boolean)) {
    let entries;
    try { entries = fs.readdirSync(current); } catch { return "missing"; }
    if (!entries.includes(segment)) {
      if (entries.some((entry) => entry.toLowerCase() === segment.toLowerCase())) return "filename case mismatch";
      return "missing";
    }
    current = path.join(current, segment);
  }
  return fs.existsSync(absolute) ? "ok" : "missing";
}

function webpDimensions(file) {
  const buffer = fs.readFileSync(file);
  if (buffer.length < 30 || buffer.toString("ascii", 0, 4) !== "RIFF" || buffer.toString("ascii", 8, 12) !== "WEBP") return null;
  for (let offset = 12; offset + 8 <= buffer.length;) {
    const type = buffer.toString("ascii", offset, offset + 4);
    const size = buffer.readUInt32LE(offset + 4);
    const data = offset + 8;
    if (type === "VP8X" && data + 10 <= buffer.length) {
      return { width: 1 + buffer.readUIntLE(data + 4, 3), height: 1 + buffer.readUIntLE(data + 7, 3) };
    }
    if (type === "VP8 " && data + 10 <= buffer.length && buffer[data + 3] === 0x9d && buffer[data + 4] === 0x01 && buffer[data + 5] === 0x2a) {
      return { width: buffer.readUInt16LE(data + 6) & 0x3fff, height: buffer.readUInt16LE(data + 8) & 0x3fff };
    }
    if (type === "VP8L" && data + 5 <= buffer.length && buffer[data] === 0x2f) {
      const bits = buffer.readUInt32LE(data + 1);
      return { width: (bits & 0x3fff) + 1, height: ((bits >> 14) & 0x3fff) + 1 };
    }
    offset = data + size + (size % 2);
  }
  return null;
}
function localTarget(sourceFile, reference) {
  const clean = stripQueryAndFragment(reference);
  const decoded = decodePath(clean);
  if (decoded === null) return { error: "invalid URL encoding" };
  if (decoded.includes("\\")) return { error: "Windows backslash in browser URL" };
  if (/^[A-Za-z]:[\\/]/.test(decoded) || decoded.startsWith("file://")) return { error: "local absolute filesystem URL" };
  if (decoded.startsWith("/")) return { error: "root-relative path breaks GitHub Pages project hosting" };
  const target = path.resolve(path.dirname(sourceFile), decoded || path.basename(sourceFile));
  if (path.relative(root, target).startsWith("..")) return { error: "path escapes repository" };
  return { target };
}

const gitFilesResult = spawnSync("git", ["ls-files", "-z"], { cwd: root, encoding: "utf8" });
if (gitFilesResult.status !== 0) issue("Git tracking", "git ls-files failed; tracked dependency status cannot be verified");
const tracked = new Set((gitFilesResult.stdout ?? "").split("\0").filter(Boolean).map((item) => item.replaceAll("\\", "/")));
const ignoredCache = new Map();

function isIgnored(rel) {
  if (!ignoredCache.has(rel)) {
    const result = spawnSync("git", ["check-ignore", "--no-index", "--quiet", "--", rel], { cwd: root });
    ignoredCache.set(rel, result.status === 0);
  }
  return ignoredCache.get(rel);
}

function validateLocalReference(section, sourceFile, content, reference, index, { fragment = true } = {}) {
  if (!reference || reference.startsWith("#")) {
    if (fragment && reference.startsWith("#")) validateFragment(section, sourceFile, sourceFile, reference.slice(1), content, index);
    return null;
  }
  if (/^https:\/\//i.test(reference)) return null;
  if (/^http:\/\//i.test(reference)) {
    if (!allowedExternalHttp.has(reference)) issue(section, at(sourceFile, content, index, `unsafe external HTTP reference ${reference}`));
    return null;
  }
  if (/^(?:mailto:|tel:|data:|javascript:|\/\/)/i.test(reference)) return null;
  if (!localReferencePattern.test(reference)) return null;
  if (unsupportedBrowserImage.test(reference)) issue(section, at(sourceFile, content, index, `direct TIFF/TIF browser reference ${reference}`));
  const resolved = localTarget(sourceFile, reference);
  if (resolved.error) {
    issue(section, at(sourceFile, content, index, `${resolved.error}: ${reference}`));
    return null;
  }
  const status = exactPathStatus(resolved.target);
  if (status !== "ok") {
    issue(section, at(sourceFile, content, index, `${status}: ${reference}`));
    return null;
  }
  const rel = relative(resolved.target);
  if (!tracked.has(rel) && !["scripts/generate-sitemap.mjs", "favicon.png"].includes(rel)) issue("Git tracking", at(sourceFile, content, index, `referenced dependency is not tracked by Git: ${reference}`));
  if (isIgnored(rel)) issue("Git tracking", at(sourceFile, content, index, `referenced dependency is ignored by Git: ${reference}`));
  if (fragment) {
    const hashIndex = reference.indexOf("#");
    if (hashIndex >= 0) validateFragment(section, sourceFile, resolved.target, reference.slice(hashIndex + 1), content, index);
  }
  return resolved.target;
}

function validateFragment(section, sourceFile, targetFile, rawFragment, sourceContent, index) {
  if (!rawFragment) return;
  const fragment = decodePath(rawFragment);
  if (fragment === null || !fs.existsSync(targetFile) || path.extname(targetFile).toLowerCase() !== ".html") return;
  const targetContent = fs.readFileSync(targetFile, "utf8");
  const ids = new Set([...targetContent.matchAll(/\bid=["']([^"']+)["']/gi)].map((match) => match[1]));
  if (!ids.has(fragment)) issue(section, at(sourceFile, sourceContent, index, `fragment #${fragment} is missing in ${relative(targetFile)}`));
}

const files = walk(root);
const htmlFiles = files.filter((file) => path.extname(file).toLowerCase() === ".html" && !relative(file).startsWith("backend/") && relative(file) !== "404.html");
const cssFiles = files.filter((file) => path.extname(file).toLowerCase() === ".css");
const jsFiles = files.filter((file) => /\.(?:js|mjs)$/i.test(file) && !relative(file).startsWith("backend/"));
const textFiles = files.filter((file) => /\.(?:html|css|js|mjs|md|yml|yaml|example|py)$/i.test(file));
const expectedPages = manifest.pagePairs.flatMap(({ page }) => [page, `ar/${page}`]).sort();
const actualPages = htmlFiles.map(relative).sort();

for (const page of expectedPages.filter((item) => !actualPages.includes(item))) issue("HTML and parity", `${page}: expected bilingual page is missing`);
for (const page of actualPages.filter((item) => !expectedPages.includes(item))) issue("HTML and parity", `${page}: HTML page is absent from config/frontend-pages.json`);

const htmlByRelative = new Map(htmlFiles.map((file) => [relative(file), fs.readFileSync(file, "utf8")]));
for (const file of htmlFiles) {
  const rel = relative(file);
  const content = htmlByRelative.get(rel);
  const stylesheetHrefs = [...content.matchAll(/<link\b[^>]*\brel=["'][^"']*stylesheet[^"']*["'][^>]*\bhref=["']([^"']+)["'][^>]*>/gi)].map((match) => match[1]);
  const scriptSources = [...content.matchAll(/<script\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/gi)].map((match) => match[1]);
  for (const [kind, values] of [["stylesheet", stylesheetHrefs], ["script", scriptSources]]) {
    const normalized = values.map(stripQueryAndFragment);
    for (const value of new Set(normalized)) if (normalized.filter((item) => item === value).length > 1) issue(kind === "stylesheet" ? "CSS references" : "JavaScript modules", `${rel}: duplicate ${kind} dependency ${value}`);
  }
  const normalizedAiScript = scriptSources.map((source) => stripQueryAndFragment(source).replace(/^\.\.\//, "")).includes("assets/js/pages/ai.js");
  if (/^(?:ar\/)?ai\.html$/.test(rel) ? !normalizedAiScript : normalizedAiScript) issue("JavaScript modules", `${rel}: AI controller scope is incorrect`);
  const head = content.match(/<head\b[^>]*>([\s\S]*?)<\/head>/i)?.[1] ?? "";
  for (const match of head.matchAll(/<script\b([^>]*)\bsrc=["']([^"']+)["'][^>]*>/gi)) if (!/\b(?:defer|async)\b|\btype=["']module["']/i.test(match[1])) issue("JavaScript modules", `${rel}: blocking classic script in document head: ${match[2]}`);
  const arabic = rel.startsWith("ar/");
  const expectedLang = arabic ? "ar" : "en";
  const expectedDir = arabic ? "rtl" : "ltr";
  if (!new RegExp(`<html[^>]*\\blang=["']${expectedLang}["']`, "i").test(content)) issue("HTML and parity", `${rel}: expected lang=${expectedLang}`);
  if (!new RegExp(`<html[^>]*\\bdir=["']${expectedDir}["']`, "i").test(content)) issue("HTML and parity", `${rel}: expected dir=${expectedDir}`);
  const ids = [...content.matchAll(/\bid=["']([^"']+)["']/gi)].map((match) => match[1]);
  for (const [id, count] of [...new Set(ids)].map((id) => [id, ids.filter((item) => item === id).length])) {
    if (count > 1) issue("HTML and parity", `${rel}: duplicate id=${id}`);
  }
  for (const match of content.matchAll(/\b(?:href|src)=["']([^"']+)["']/gi)) {
    validateLocalReference("HTML references", file, content, match[1], match.index);
  }
  for (const match of content.matchAll(/url\(\s*["']?([^)'"']+)["']?\s*\)/gi)) {
    validateLocalReference("HTML references", file, content, match[1].trim(), match.index, { fragment: false });
  }
  for (const match of content.matchAll(/<a\b[^>]*target=["']_blank["'][^>]*>/gi)) {
    if (!/\brel=["'][^"']*(?:noopener|noreferrer)/i.test(match[0])) issue("Navigation", at(file, content, match.index, "target=_blank link lacks rel=noopener or noreferrer"));
  }
  for (const match of content.matchAll(/(?:href|src)=["']([^"']*\\[^"']*)["']/gi)) issue("HTML references", at(file, content, match.index, `Windows backslash in browser URL ${match[1]}`));
  for (const match of content.matchAll(/href=["']([^"']*destination\.html\?slug=([^&#"']+)[^"']*)["']/gi)) {
    const slug = decodePath(match[2]);
    if (!slug || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) issue("Navigation", at(file, content, match.index, `invalid destination slug ${match[2]}`));
  }
}

for (const pair of manifest.pagePairs) {
  const enContent = htmlByRelative.get(pair.page);
  const arContent = htmlByRelative.get(`ar/${pair.page}`);
  if (!enContent || !arContent) continue;
  const normalizeScripts = (content) => [...content.matchAll(/<script[^>]+src=["']([^"']+)["']/gi)]
    .map((match) => stripQueryAndFragment(match[1]).replace(/^\.\.\//, "")).sort();
  if (JSON.stringify(normalizeScripts(enContent)) !== JSON.stringify(normalizeScripts(arContent))) issue("HTML and parity", `${pair.page}: English and Arabic script sets differ`);
  const expectedEn = `ar/${pair.page}`;
  const expectedAr = `../${pair.page}`;
  if (!new RegExp(`class=["'][^"']*(?:vl-language|language)[^"']*["'][^>]*href=["']${expectedEn.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["']`, "i").test(enContent)) issue("Navigation", `${pair.page}: language switch does not resolve to ${expectedEn}`);
  if (!new RegExp(`class=["'][^"']*(?:vl-language|language)[^"']*["'][^>]*href=["']${expectedAr.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["']`, "i").test(arContent)) issue("Navigation", `ar/${pair.page}: language switch does not resolve to ${expectedAr}`);
}

for (const page of manifest.apiDependentPages.flatMap((item) => [item, `ar/${item}`])) {
  const content = htmlByRelative.get(page);
  if (!content) continue;
  const pair = manifest.pagePairs.find(({ page: candidate }) => candidate === page.replace(/^ar\//, ""));
  const configIndex = content.indexOf("config/frontend-config.js");
  const controller = pair?.controller;
  const controllerIndex = controller ? content.indexOf(controller) : -1;
  if (configIndex < 0) issue("Runtime configuration", `${page}: missing frontend runtime configuration script`);
  if (controllerIndex < 0) issue("Runtime configuration", `${page}: missing required page controller ${controller ?? "unknown"}`);
  if (configIndex >= 0 && controllerIndex >= 0 && configIndex > controllerIndex) issue("Runtime configuration", `${page}: configuration loads after its page controller`);
}

for (const file of cssFiles) {
  const content = fs.readFileSync(file, "utf8");
  for (const match of content.matchAll(/url\(\s*["']?([^)'"']+)["']?\s*\)/gi)) {
    const reference = match[1].trim();
    if (/^https:\/\/fonts\.googleapis\.com\//i.test(reference)) warn(`${relative(file)}:${sourceLine(content, match.index)}: external Google Fonts import is an availability/privacy dependency`);
    else validateLocalReference("CSS references", file, content, reference, match.index, { fragment: false });
  }
  for (const match of content.matchAll(/@import\s+(?:url\(\s*)?["']([^"']+)["']/gi)) {
    const reference = match[1];
    if (/^https:\/\/fonts\.googleapis\.com\//i.test(reference)) continue;
    validateLocalReference("CSS references", file, content, reference, match.index, { fragment: false });
  }
}

for (const file of jsFiles) {
  const content = fs.readFileSync(file, "utf8");
  for (const match of content.matchAll(/(?:from\s+|import\s*)["']([^"']+)["']/g)) {
    if (!match[1].startsWith(".")) continue;
    const target = validateLocalReference("JavaScript modules", file, content, match[1], match.index, { fragment: false });
    if (target && !/\.(?:js|mjs|json)$/i.test(target)) issue("JavaScript modules", at(file, content, match.index, `unsupported module extension ${match[1]}`));
    if (relative(file).startsWith("assets/js/pages/") && /\/pages\//.test(relative(target ?? ""))) {
      const imported = relative(target);
      if (imported !== relative(file) && /(?:data|curated)/i.test(content.slice(match.index, match.index + match[0].length + 80))) issue("JavaScript modules", at(file, content, match.index, "page controller imports another page controller for shared data"));
    }
  }
}

const curatedFile = path.join(root, "assets/js/data/curated-destinations.js");
const curatedSource = fs.readFileSync(curatedFile, "utf8");
if (/\b(?:document|window)\b|addEventListener\s*\(|initialize\w*\s*\(/.test(curatedSource)) issue("JavaScript modules", "assets/js/data/curated-destinations.js: shared data module contains page initialization side effects");

for (const file of textFiles) {
  const rel = relative(file);
  const content = fs.readFileSync(file, "utf8");
  if (/\b(?:localhost|127\.0\.0\.1)\b/i.test(content) && !approvedLocalReferences.has(rel) && !rel.startsWith("backend/tests/") && rel !== "scripts/validate-frontend.mjs" && rel !== "scripts/smoke-test-static-site.mjs") issue("Deployment safety", `${rel}: local host reference is not in an approved development example`);
  if (/^(?:<{7}|={7}|>{7})/m.test(content)) issue("Release readiness", `${rel}: unresolved merge marker`);
  if (/\b(?:src|href)=["']\/(?!\/)|url\(\s*["']?\/(?!\/)/i.test(content)) issue("Deployment safety", `${rel}: root-relative frontend path can break project-subpath hosting`);
  const browserSource = /^(?:ar\/.*\.html|[^/]+\.html|style\.css|assets\/.*\.(?:css|js)|config\/frontend-config(?:\.example)?\.js)$/i.test(rel);
  if (/file:\/\//i.test(content) && browserSource) issue("Deployment safety", `${rel}: file:// browser reference is forbidden`);
}

for (const file of files) {
  const rel = relative(file);
  if (/(?:^|\/)(?:\.qa-review|coverage|contact-sheets?|screenshots?|browser-profiles?|runtime-performance-qa)(?:\/|$)/i.test(rel)) issue("Release readiness", `${rel}: temporary QA output must remain outside the repository`);
}
const publicConfigFile = path.join(root, "config/frontend-config.js");
const publicConfig = fs.readFileSync(publicConfigFile, "utf8");
if (!/apiEnabled:\s*false\b/.test(publicConfig)) issue("Runtime configuration", "config/frontend-config.js: committed apiEnabled must be false");
if (!/apiBaseUrl:\s*["']\s*["']/.test(publicConfig)) issue("Runtime configuration", "config/frontend-config.js: committed apiBaseUrl must be empty");
if (!/deploymentEnvironment:\s*["']static["']/.test(publicConfig)) issue("Runtime configuration", "config/frontend-config.js: committed environment must be static");
if (/apiEnabled:\s*true\b/.test(publicConfig) && !/apiBaseUrl:\s*["']https:\/\//.test(publicConfig)) issue("Runtime configuration", "config/frontend-config.js: enabled non-local configuration must use HTTPS");
if (/\b(?:token|secret|password|apiKey|authorization)\s*:/i.test(publicConfig)) issue("Runtime configuration", "config/frontend-config.js: token-like or secret-like configuration field is forbidden");
if (/https?:\/\/[^\s"']+/i.test(publicConfig)) issue("Runtime configuration", "config/frontend-config.js: production/API hostname must not be committed in static mode");

const configAssignments = jsFiles.filter((file) => /VISIT_LIBYA_CONFIG\s*=/.test(fs.readFileSync(file, "utf8"))).map(relative);
for (const assignment of configAssignments) {
  if (!["config/frontend-config.js", "config/frontend-config.example.js"].includes(assignment)) issue("Runtime configuration", `${assignment}: duplicates the public runtime configuration`);
}

const { curatedDestinations } = await import(pathToFileURL(curatedFile));
const responsiveManifestFile = path.join(root, "assets/js/data/responsive-images.js");
const responsiveImages = fs.existsSync(responsiveManifestFile)
  ? (await import(pathToFileURL(responsiveManifestFile))).responsiveImages
  : {};
const requiredCuratedFields = ["name_en", "name_ar", "description_en", "description_ar", "region_en", "region_ar", "category_en", "category_ar", "slug", "image"];
const slugs = new Set();
for (const destination of curatedDestinations) {
  for (const field of requiredCuratedFields) if (typeof destination[field] !== "string" || !destination[field].trim()) issue("Curated destinations", `${destination.slug ?? "unknown"}: missing bilingual field ${field}`);
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(destination.slug)) issue("Curated destinations", `${destination.slug}: invalid slug pattern`);
  if (slugs.has(destination.slug)) issue("Curated destinations", `${destination.slug}: duplicate slug`);
  slugs.add(destination.slug);
  validateLocalReference("Curated destinations", curatedFile, curatedSource, `../../../${destination.image}`, curatedSource.indexOf(`slug: "${destination.slug}"`), { fragment: false });
}
if (!slugs.has("leptis-magna")) issue("Curated destinations", "leptis-magna is missing from curated data");

const destinationController = fs.readFileSync(path.join(root, "assets/js/pages/destination-details.js"), "utf8");
if (!/destination\.html\?slug=\$\{encodeURIComponent\(slug\)\}/.test(destinationController)) issue("Navigation", "destination-details.js: language switching does not preserve the destination slug");
if (!/if \(!slug\)[\s\S]{0,200}view:\s*["']not-found["']/.test(destinationController)) issue("Curated destinations", "destination-details.js: invalid/unknown slug lacks a terminal state");
if (!/if \(!runtimeConfig\.apiEnabled\)[\s\S]{0,150}view:\s*["']error["']/.test(destinationController)) issue("Curated destinations", "destination-details.js: unknown slug can remain loading when API is disabled");
for (const [page, content] of [
  ["destination.html", htmlByRelative.get("destination.html") ?? ""],
  ["ar/destination.html", htmlByRelative.get("ar/destination.html") ?? ""],
]) {
  if (!/<button[^>]+id=["']destinationAddToTrip["'][^>]+type=["']button["']/i.test(content)) {
    issue("Trip integration", `${page}: missing semantic Add to Trip button`);
  }
  if (!content.includes('id="destinationTripAvailability"')) {
    issue("Trip integration", `${page}: missing curated destination availability status`);
  }
}
for (const requirement of [
  /listTrips\(\{ limit: 100 \}\)/,
  /getTrip\(tripId\)/,
  /expected_version:\s*latestTrip\.version/,
  /destination_id:\s*currentDestination\.id/,
  /day_number:\s*dayNumber/,
  /Number\.isSafeInteger\(payload\.id\)/,
  /TRIP_VERSION_CONFLICT/,
]) {
  if (!requirement.test(destinationController)) {
    issue("Trip integration", `destination-details.js: missing contract guard ${requirement}`);
  }
}
if (/\b(?:innerHTML|outerHTML|insertAdjacentHTML|eval|document\.write)\b/.test(destinationController)) {
  issue("Trip integration", "destination-details.js: unsafe dynamic DOM API found");
}

const en = (await import(pathToFileURL(path.join(root, "assets/js/app/i18n/en.js")))).en;
const ar = (await import(pathToFileURL(path.join(root, "assets/js/app/i18n/ar.js")))).ar;
function dictionaryKeys(value, prefix = "") {
  return Object.entries(value).flatMap(([key, child]) => child && typeof child === "object" ? dictionaryKeys(child, `${prefix}${key}.`) : [`${prefix}${key}`]).sort();
}
if (JSON.stringify(dictionaryKeys(en)) !== JSON.stringify(dictionaryKeys(ar))) issue("HTML and parity", "English and Arabic dynamic dictionaries are not structurally equivalent");
for (const key of ["registrationUnavailable", "signInUnavailable"]) if (!en.auth[key] || !ar.auth[key]) issue("HTML and parity", `missing bilingual auth.${key}`);
if (!en.trips.plannerUnavailable || !ar.trips.plannerUnavailable) issue("HTML and parity", "missing bilingual trips.plannerUnavailable");
for (const key of ["addToTrip", "signInRequired", "success", "duplicate", "conflict", "unavailableForCurated"]) {
  if (!en.tripIntegration[key] || !ar.tripIntegration[key]) {
    issue("Trip integration", `missing bilingual tripIntegration.${key}`);
  }
}

const staticHooks = {
  "register.html": ["data-register-form", "data-register-error", "data-register-submit"],
  "trips.html": ["data-login-form", "data-login-error", "data-login-submit"],
  "trip.html": ["data-trip-error", "data-trip-editor", "data-trip-loading"],
};
for (const [page, hooks] of Object.entries(staticHooks)) {
  for (const rel of [page, `ar/${page}`]) {
    const content = htmlByRelative.get(rel) ?? "";
    for (const hook of hooks) if (!content.includes(hook)) issue("Static unavailable states", `${rel}: missing ${hook} hook`);
  }
}

if (!fs.existsSync(path.join(root, ".github/workflows/frontend-validation.yml"))) warn("frontend validation workflow is missing");

const releaseFiles = [".nojekyll", "404.html", "robots.txt", "docs/public-release-readiness.md", "docs/release-checklist.md", "docs/release-artifact-guide.md", "docs/measured-runtime-performance.md", "config/pages-artifact-allowlist.json", ".github/workflows/pages-release.yml", ".github/workflows/release-artifact-validation.yml", "scripts/build-pages-artifact.mjs", "scripts/inject-release-metadata.mjs", "scripts/generate-sitemap.mjs", "scripts/validate-pages-artifact.mjs"];
for (const rel of releaseFiles) if (!fs.existsSync(path.join(root, rel))) issue("Release readiness", `missing ${rel}`);
if (fs.existsSync(path.join(root, "sitemap.xml"))) issue("Release readiness", "sitemap.xml must be generated only in a release artifact");
const titles = new Map(), descriptions = new Map();
for (const [rel, content] of htmlByRelative) {
  const title = content.match(/<title>([\s\S]*?)<\/title>/i)?.[1].trim();
  const description = content.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)/i)?.[1] ?? content.match(/<meta[^>]+content=["']([^"']+)["'][^>]+name=["']description["']/i)?.[1];
  if (!title) issue("Release readiness", `${rel}: title missing`); else if (titles.has(title)) issue("Release readiness", `${rel}: duplicate title with ${titles.get(title)}`); else titles.set(title, rel);
  if (!description) issue("Release readiness", `${rel}: description missing`); else if (descriptions.has(description)) issue("Release readiness", `${rel}: duplicate description with ${descriptions.get(description)}`); else descriptions.set(description, rel);
  if (!/name=["']theme-color["']/i.test(content)) issue("Release readiness", `${rel}: theme-color missing`);
  const entry = manifest.pagePairs.find((item) => item.page === rel.replace(/^ar\//, ""));
  const expected = entry?.indexable ? "index,follow" : "noindex,follow";
  if (!new RegExp(`<meta[^>]+(?:name=["']robots["'][^>]+content|content=["']${expected}["'][^>]+name)=["']?${expected.replace(",", ",?")}["']?`, "i").test(content) && !content.includes(`content="${expected}"`)) issue("Release readiness", `${rel}: expected robots ${expected}`);
  if (/(?:example\.invalid|rel=["']canonical["']|property=["']og:url["'])/i.test(content)) issue("Release readiness", `${rel}: source contains release-only origin metadata`);
}
const robotsSource = fs.existsSync(path.join(root, "robots.txt")) ? fs.readFileSync(path.join(root, "robots.txt"), "utf8") : "";
if (/^\s*Sitemap:/im.test(robotsSource)) issue("Release readiness", "source robots.txt must not contain a sitemap without a confirmed origin");
if (/Disallow:\s*\/(?:assets|ar|imges|panel)/i.test(robotsSource)) issue("Release readiness", "robots.txt blocks public content or assets");
if (fs.existsSync(path.join(root, "404.html"))) { const notFound = fs.readFileSync(path.join(root, "404.html"), "utf8"); if (!/noindex,follow/i.test(notFound) || !/[\u0600-\u06ff]/.test(notFound) || !/destinations\.html/.test(notFound)) issue("Release readiness", "404 page policy or bilingual recovery links are incomplete"); }
if (fs.existsSync(path.join(root, ".github/workflows/pages-release.yml"))) { const workflow = fs.readFileSync(path.join(root, ".github/workflows/pages-release.yml"), "utf8"); if (!/workflow_dispatch:/.test(workflow) || /\bpush:|pull_request:/.test(workflow)) issue("Release readiness", "Pages workflow must remain manual-only"); for (const action of workflow.matchAll(/uses:\s*([^\s]+)/g)) if (!/^actions\/(?:checkout|setup-node|configure-pages|upload-pages-artifact|deploy-pages)@/.test(action[1])) issue("Release readiness", `unapproved action ${action[1]}`); if (!/path:\s*\.pages-artifact/.test(workflow)) issue("Release readiness", "workflow does not upload the sanitized artifact"); }
if (fs.existsSync(path.join(root, ".github/workflows/pages-release.yml"))) {
  const workflow = fs.readFileSync(path.join(root, ".github/workflows/pages-release.yml"), "utf8");
  if (!/\bbuild:\s*[\s\S]*\bdeploy:\s*/.test(workflow) || !/\bneeds:\s*build/.test(workflow)) issue("Release readiness", "Pages build and deploy jobs are not separated");
  if (!/github\.ref == 'refs\/heads\/main'/.test(workflow)) issue("Release readiness", "Pages deployment is not restricted to main");
  if (!/smoke-test-static-site\.mjs --root \.pages-artifact/.test(workflow)) issue("Release readiness", "Pages workflow does not smoke test the artifact");
  if (/\bbackend\//.test(workflow) || /apiEnabled\s*:\s*true/.test(workflow)) issue("Release readiness", "Pages workflow references backend activation");
}
const artifactWorkflowPath = path.join(root, ".github/workflows/release-artifact-validation.yml");
if (fs.existsSync(artifactWorkflowPath)) {
  const workflow = fs.readFileSync(artifactWorkflowPath, "utf8");
  if (/deploy-pages|pages:\s*write|id-token:\s*write/.test(workflow)) issue("Release readiness", "validation-only artifact workflow can deploy");
  if (!/contents:\s*read/.test(workflow) || !/build-pages-artifact\.mjs/.test(workflow) || !/validate-pages-artifact\.mjs/.test(workflow)) issue("Release readiness", "validation-only artifact workflow is incomplete");
}
const allowlistPath = path.join(root, "config/pages-artifact-allowlist.json");
if (fs.existsSync(allowlistPath)) {
  const allowlist = JSON.parse(fs.readFileSync(allowlistPath, "utf8"));
  for (const forbidden of [".git", ".github", "backend", "docs", "node_modules", "scripts", "tests"]) if (!allowlist.forbiddenTopLevel?.includes(forbidden)) issue("Release readiness", `artifact allowlist does not forbid ${forbidden}`);
  if (!allowlist.rootFiles?.includes("config/frontend-config.js") || !allowlist.rootFiles?.includes("404.html") || !allowlist.publicTrees?.["assets/js"] || !Array.isArray(allowlist.publicMedia) || allowlist.publicMedia.length === 0) issue("Release readiness", "artifact allowlist lacks required public scope");
}
const builderSource = fs.existsSync(path.join(root, "scripts/build-pages-artifact.mjs")) ? fs.readFileSync(path.join(root, "scripts/build-pages-artifact.mjs"), "utf8") : "";
for (const requirement of ["assertSafeOutput", "pages-artifact-allowlist.json", "release-manifest.json", "sha256", "sourceCommit", "releaseOriginStatus", "validate-pages-artifact.mjs"]) if (!builderSource.includes(requirement)) issue("Release readiness", `artifact builder lacks ${requirement}`);
const { origin: validateReleaseOrigin } = await import(pathToFileURL(path.join(root, "scripts/generate-sitemap.mjs")).href);
for (const unsafeOrigin of ["http://example.com", "https://localhost", "https://127.0.0.1", "https://10.0.0.1", "https://192.168.1.1", "https://172.16.0.1", "https://user:pass@example.com", "https://example.com/path"]) {
  try { validateReleaseOrigin(unsafeOrigin); issue("Release readiness", `unsafe SITE_ORIGIN accepted: ${unsafeOrigin}`); } catch {}
}
try { if (validateReleaseOrigin("https://example.com/") !== "https://example.com") issue("Release readiness", "safe SITE_ORIGIN normalization failed"); } catch { issue("Release readiness", "safe HTTPS SITE_ORIGIN was rejected"); }

const publicConfigPath = path.join(root, "config/frontend-config.js");
if (fs.existsSync(publicConfigPath)) {
  const publicConfig = fs.readFileSync(publicConfigPath, "utf8");
  if (/https?:\/\/(?:localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|[^/]*\.(?:test|invalid))(?:[:/]|$)/i.test(publicConfig)) issue("Deployment safety", "config/frontend-config.js: localhost, private, or test URL in public runtime configuration");
  if (/\b(?:apiKey|api_key|password|secret|token)\s*[:=]\s*["''][^"'']+["'']/i.test(publicConfig)) issue("Deployment safety", "config/frontend-config.js: possible public secret value");
}
const publicHtml = new Map(htmlByRelative);
const notFoundPath = path.join(root, "404.html");
if (fs.existsSync(notFoundPath)) publicHtml.set("404.html", fs.readFileSync(notFoundPath, "utf8"));
const mediaPerformancePages = new Set([
  "index.html", "ar/index.html", "destinations.html", "ar/destinations.html", "destination.html", "ar/destination.html",
  "culture.html", "ar/culture.html", "experiences.html", "ar/experiences.html", "heritage.html", "ar/heritage.html",
  "atlas.html", "ar/atlas.html", "services.html", "ar/services.html",
]);
for (const [rel, content] of publicHtml) {
  const file = path.join(root, rel);
  const expectedLanguage = rel.startsWith("ar/") ? "ar" : "en";
  const expectedDirection = rel.startsWith("ar/") ? "rtl" : "ltr";
  if (!new RegExp(`<html[^>]*\\blang=["'']${expectedLanguage}["'']`, "i").test(content) || !new RegExp(`<html[^>]*\\bdir=["'']${expectedDirection}["'']`, "i").test(content)) issue("HTML and parity", `${rel}: invalid release language or direction attributes`);
  const pageH1 = [...content.matchAll(/<h1\b[^>]*>/gi)];
  if (pageH1.length !== 1) issue("HTML and parity", `${rel}: expected exactly one h1, found ${pageH1.length}`);
  const publicIds = [...content.matchAll(/\bid=["'']([^"'']+)["'']/gi)].map((match) => match[1]);
  for (const id of new Set(publicIds)) if (publicIds.filter((candidate) => candidate === id).length > 1) issue("HTML and parity", `${rel}: duplicate id=${id}`);
  if (/tabindex=["''][1-9]\d*["'']/i.test(content)) issue("HTML and parity", `${rel}: positive tabindex is forbidden`);
  if (rel !== "404.html" && !/<a\b[^>]*class=["''][^"'']*(?:site-skip-link|trips-skip-link)[^"'']*["''][^>]*href=["'']#[^"'']+["'']/i.test(content)) issue("HTML and parity", `${rel}: skip link is missing`);
  for (const match of content.matchAll(/<a\b[^>]*target=["'']_blank["''][^>]*>/gi)) {
    const relation = match[0].match(/\brel=["'']([^"'']*)["'']/i)?.[1] ?? "";
    if (!/\bnoopener\b/i.test(relation) || !/\bnoreferrer\b/i.test(relation)) issue("Navigation", at(file, content, match.index, "target=_blank link requires rel=noopener noreferrer"));
  }
  for (const match of content.matchAll(/<a\b[^>]*\bhref=["']([^"']*)["'][^>]*>/gi)) {
    const href = match[1].trim();
    if (!href) issue("Navigation", at(file, content, match.index, "public link has an empty href"));
    if (href === "#") issue("Navigation", at(file, content, match.index, "public link uses href=#"));
    if (/^javascript:/i.test(href)) issue("Navigation", at(file, content, match.index, "JavaScript pseudo-link is forbidden"));
    if (/^(?:file:\/\/|https?:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?(?:\/|$))/i.test(href)) issue("Deployment safety", at(file, content, match.index, "public link uses a local URL"));
    if (/\/visitlibya\/visitlibya\//i.test(href)) issue("Navigation", at(file, content, match.index, "duplicated /visitlibya/ project path"));
  }
  const favicon = content.match(/<link[^>]+rel=["']icon["'][^>]+href=["']([^"']+)["']/i)?.[1];
  if (!favicon) issue("Release readiness", `${rel}: favicon missing`);
  else {
    const resolved = localTarget(file, favicon);
    if (resolved.error || exactPathStatus(resolved.target) !== "ok") issue("HTML references", `${rel}: favicon does not resolve: ${favicon}`);
  }
  if (rel !== "404.html") {
    const logoPath = rel.startsWith("ar/") ? "../visitlibyalogo.png" : "visitlibyalogo.png";
    if (!new RegExp(`<a\\b[^>]*class=["''][^"'']*vl-logo[^"'']*["''][^>]*href=["'']index\\.html["''][^>]*>[\\s\\S]*?<img\\b[^>]*class=["''][^"'']*media-logo[^"'']*["''][^>]*src=["'']${logoPath.replaceAll(".", "\\.")}["''][^>]*alt=["'']["'']`, "i").test(content)) issue("Visual system", `${rel}: approved decorative header logo or language-local home link is missing`);
  }  for (const property of ["og:title", "og:description", "og:type"]) if (!new RegExp(`<meta[^>]+property=["']${property}["']`, "i").test(content)) issue("Release readiness", `${rel}: ${property} missing`);
  for (const name of ["twitter:card", "twitter:title", "twitter:description"]) if (!new RegExp(`<meta[^>]+name=["']${name}["']`, "i").test(content)) issue("Release readiness", `${rel}: ${name} missing`);
  for (const hero of content.matchAll(/<span[^>]+class=["'][^"']*page-hero-bg[^"']*["'][^>]*>[\s\S]*?<img\b[^>]*\balt=["']([^"']*)["'][^>]*>/gi)) {
    const alt = hero[1].trim();
    if (!alt || /^(?:Visit Libya page hero|page hero|hero image)$/i.test(alt)) issue("HTML and parity", `${rel}: meaningful hero image has empty or generic alt text`);
  }
  if (/<link[^>]+rel=["']canonical["'][^>]+href=["']https?:\/\/(?:www\.)?visitlibya\.ly/i.test(content)) issue("Release readiness", `${rel}: active visitlibya.ly canonical URL is premature`);
  for (const match of content.matchAll(/destination\.html\?slug=([^&#"']+)/gi)) {
    const slug = decodePath(match[1]);
    if (slug && !slugs.has(slug)) issue("Curated destinations", `${rel}: destination link uses unknown slug ${slug}`);
  }
  const highPriorityImages = [...content.matchAll(/<img\b[^>]*\bfetchpriority=["']high["'][^>]*>/gi)];
  if (highPriorityImages.length > 1) issue("Media delivery", `${rel}: more than one image uses fetchpriority=high`);
  for (const highPriorityImage of highPriorityImages) {
    const tag = highPriorityImage[0];
    if (/\bloading=["']lazy["']/i.test(tag)) issue("Media delivery", at(file, content, highPriorityImage.index, "fetchpriority=high image must not use loading=lazy"));
    const alt = tag.match(/\balt=["']([^"']+)["']/i)?.[1].trim();
    if (!alt) issue("Media delivery", at(file, content, highPriorityImage.index, "fetchpriority=high image requires meaningful alt text"));
  }
  for (const picture of content.matchAll(/<picture\b[^>]*>([\s\S]*?)<\/picture>/gi)) {
    if (!/<img\b[^>]*\bsrc=["'][^"']+["'][^>]*>/i.test(picture[1])) issue("Media delivery", at(file, content, picture.index, "picture element lacks a valid img fallback"));
  }
  for (const candidateSet of content.matchAll(/<(?:img|source)\b[^>]*\bsrcset=["']([^"']+)["'][^>]*>/gi)) {
    const candidates = candidateSet[1].split(",").map((candidate) => candidate.trim()).filter(Boolean);
    const widthDescriptors = candidates.map((candidate) => candidate.match(/\s+(\d+)w$/)?.[1]).filter(Boolean).map(Number);
    if (widthDescriptors.length && !/\bsizes=["'][^"']+["']/i.test(candidateSet[0])) issue("Media delivery", at(file, content, candidateSet.index, "width-descriptor srcset requires sizes"));
    if (widthDescriptors.length !== new Set(widthDescriptors).size || widthDescriptors.some((width, index) => index > 0 && width <= widthDescriptors[index - 1])) issue("Media delivery", at(file, content, candidateSet.index, "srcset widths must be unique and ascending"));
    for (const candidate of candidates) {
      const [reference, descriptor = ""] = candidate.split(/\s+/);
      validateLocalReference("HTML references", file, content, reference, candidateSet.index, { fragment: false });
      const width = Number(descriptor.match(/^(\d+)w$/)?.[1] ?? 0);
      const local = localTarget(file, reference);
      if (width && local.target && fs.existsSync(local.target) && /\.webp$/i.test(local.target)) {
        const dimensions = webpDimensions(local.target);
        if (!dimensions) issue("Media delivery", at(file, content, candidateSet.index, `invalid WebP candidate: ${reference}`));
        else if (dimensions.width !== width) issue("Media delivery", at(file, content, candidateSet.index, `${reference}: ${width}w descriptor does not match ${dimensions.width}px file width`));
      }
    }
  }
  for (const editorial of content.matchAll(/<(?:section)\b[^>]*class=["'][^"']*(?:discover-detail|ar-detail)[^"']*["'][^>]*>[\s\S]*?<img\b([^>]*)>/gi)) {
    const attributes = editorial[1];
    if (/\bsrc=["'](?:\.\.\/)?imges\/curated\//i.test(attributes) && !/\bloading=["']lazy["']/i.test(attributes)) issue("Media delivery", `${rel}: below-the-fold curated editorial image must use loading=lazy`);
    if (/\bsrc=["'](?:\.\.\/)?imges\/curated\//i.test(attributes) && !/\bdecoding=["']async["']/i.test(attributes)) issue("Media delivery", `${rel}: curated editorial image must use decoding=async`);
    const alt = attributes.match(/\balt=["']([^"']+)["']/i)?.[1].trim();
    if (!alt) issue("Media delivery", `${rel}: editorial image lacks meaningful alt text`);
  }
  if (mediaPerformancePages.has(rel)) for (const image of content.matchAll(/<img\b[^>]*>/gi)) {
    const tag = image[0];
    if (!/\bdecoding=["']async["']/i.test(tag)) issue("Media delivery", at(file, content, image.index, "audited image must use decoding=async"));
    const primary = /\b(?:loading=["']eager["']|fetchpriority=["']high["'])/i.test(tag);
    if (!primary && !/\bloading=["']lazy["']/i.test(tag)) issue("Media delivery", at(file, content, image.index, "below-the-fold image must use loading=lazy"));
    const source = tag.match(/\bsrc=["']([^"']+)["']/i)?.[1] ?? "";
    if (!/\.webp(?:[?#]|$)/i.test(source) && (!/\bwidth=["']?\d+/i.test(tag) || !/\bheight=["']?\d+/i.test(tag))) issue("Media delivery", at(file, content, image.index, "audited image with known dimensions must declare width and height"));
  }
}
for (const pair of manifest.pagePairs) {
  const enContent = htmlByRelative.get(pair.page) ?? "";
  const arContent = htmlByRelative.get(`ar/${pair.page}`) ?? "";
  for (const [rel, content, expected] of [
    [pair.page, enContent, { en: pair.page, ar: `ar/${pair.page}`, "x-default": pair.page }],
    [`ar/${pair.page}`, arContent, { ar: pair.page, en: `../${pair.page}`, "x-default": `../${pair.page}` }],
  ]) for (const [language, href] of Object.entries(expected)) {
    const escaped = href.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (!new RegExp(`<link[^>]+rel=["']alternate["'][^>]+hreflang=["']${language}["'][^>]+href=["']${escaped}["']`, "i").test(content)) issue("HTML and parity", `${rel}: missing origin-neutral hreflang=${language} for ${href}`);
  }
}

const layoutCss = fs.readFileSync(path.join(root, "style.css"), "utf8");
const heritageImagePaths = [
  "imges/Leptis Magna3.jpeg",
  "imges/Cyrene.jpg",
  "imges/Sabratha.jpg",
  "imges/curated/acacus-rock-art-chariot.jpg",
  "imges/Ghadames2.JPG",
];
const heritageSemanticOrder = Object.freeze({
  "heritage.html": ["Leptis Magna", "Cyrene / Shahhat", "Sabratha", "Rock-Art Sites of Tadrart Acacus", "Old Town of Ghadames"],
  "ar/heritage.html": ["لبدة الكبرى", "شحات / قورينا", "صبراتة", "الفن الصخري في أكاكوس", "مدينة غدامس القديمة"],
});
const voidElements = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]);
function directChildElements(source, expectedTag) {
  const elements = [];
  const tags = /<\/?([a-z][a-z0-9-]*)\b[^>]*>/gi;
  let depth = 0;
  let current = null;
  for (const tag of source.matchAll(tags)) {
    const name = tag[1].toLowerCase();
    const closing = tag[0].startsWith("</");
    if (closing) {
      if (!voidElements.has(name)) depth -= 1;
      if (depth === 0 && current && name === expectedTag) {
        elements.push({
          opening: current.opening,
          inner: source.slice(current.innerStart, tag.index),
          outer: source.slice(current.start, tag.index + tag[0].length),
        });
        current = null;
      }
      continue;
    }
    if (depth === 0 && name === expectedTag) current = { start: tag.index, innerStart: tag.index + tag[0].length, opening: tag[0] };
    if (!voidElements.has(name) && !tag[0].endsWith("/>") ) depth += 1;
  }
  return elements;
}
function elementById(source, tagName, id) {
  const opening = new RegExp(`<${tagName}\\b[^>]*\\bid=["']${id}["'][^>]*>`, "i").exec(source);
  if (!opening) return null;
  const tags = new RegExp(`<\\/?${tagName}\\b[^>]*>`, "gi");
  tags.lastIndex = opening.index;
  let depth = 0;
  for (const tag of source.matchAll(tags)) {
    if (tag[0].startsWith("</")) depth -= 1;
    else depth += 1;
    if (depth === 0) return {
      opening: opening[0],
      inner: source.slice(opening.index + opening[0].length, tag.index),
      outer: source.slice(opening.index, tag.index + tag[0].length),
    };
  }
  return null;
}
for (const rel of ["heritage.html", "ar/heritage.html"]) {
  const content = htmlByRelative.get(rel) ?? "";
  const section = elementById(content, "section", "world-heritage");
  const grids = section ? directChildElements(section.inner, "div").filter((element) => /\bclass=["'][^"']*\b(?:heritage-card-grid|destination-grid)\b[^"']*["']/i.test(element.opening)) : [];
  if (grids.length !== 1) issue("Editorial layout", `${rel}: World Heritage section must contain exactly one direct heritage grid`);
  const grid = grids[0] ?? { opening: "", inner: "" };
  if (!/\bclass=["'][^"']*\bdestination-grid\b[^"']*\bheritage-card-grid\b[^"']*["']/i.test(grid.opening)) issue("Editorial layout", `${rel}: World Heritage grid must use destination-grid heritage-card-grid`);
  const cards = directChildElements(grid.inner, "article").filter((element) => /\bclass=["'][^"']*\bdestination-card\b[^"']*["']/i.test(element.opening));
  if (cards.length !== 5) issue("Editorial layout", `${rel}: World Heritage grid must contain exactly five cards`);
  const paths = cards.map((card) => card.inner.match(/<img\b[^>]*\bsrc=["'](?:\.\.\/)?([^"']+)["']/i)?.[1] ?? "");
  if (JSON.stringify(paths) !== JSON.stringify(heritageImagePaths)) issue("Editorial layout", `${rel}: World Heritage image paths or semantic order changed`);
  const headings = cards.map((card) => card.inner.match(/<h3\b[^>]*>([\s\S]*?)<\/h3>/i)?.[1].replace(/<[^>]+>/g, "").trim() ?? "");
  if (JSON.stringify(headings) !== JSON.stringify(heritageSemanticOrder[rel])) issue("HTML and parity", `${rel}: World Heritage destination order changed`);
  for (const card of cards) {
    const alt = card.inner.match(/<img\b[^>]*\balt=["']([^"']+)["']/i)?.[1].trim();
    if (!alt) issue("HTML and parity", `${rel}: World Heritage card lacks meaningful alt text`);
  }
}
for (const rel of ["culture.html", "ar/culture.html", "ar/experiences.html", "ar/heritage.html"]) {
  const content = htmlByRelative.get(rel) ?? "";
  for (const match of content.matchAll(/<(?:section)\b[^>]*class=["'][^"']*(?:discover-detail|ar-detail)[^"']*["'][^>]*>[\s\S]*?<img\b([^>]*)>/gi)) {
    const attributes = match[1];
    if (/\bstyle=["'][^"']*(?:height|max-height|object-fit)\s*:/i.test(attributes)) issue("Editorial layout", `${rel}: editorial image uses an inline crop constraint`);
    const alt = attributes.match(/\balt=["']([^"']+)["']/i)?.[1]?.trim();
    if (!alt) issue("Editorial layout", `${rel}: editorial image lacks meaningful alt text`);
  }
}
for (const required of [
  /\.ar-detail img\s*\{[\s\S]*?height:\s*auto;[\s\S]*?object-fit:\s*contain;/,
  /#world-heritage[^\{]*\{[\s\S]*?grid-template-columns:\s*repeat\(6,/,
  /@media \(max-width:\s*1050px\)[\s\S]*?#world-heritage[\s\S]*?repeat\(2,/,
  /@media \(max-width:\s*640px\)[\s\S]*?#world-heritage[\s\S]*?minmax\(0,\s*1fr\)/,
]) if (!required.test(layoutCss)) issue("Editorial layout", "style.css: responsive editorial or heritage-grid rule is missing");

const imageReferences = new Map();
function recordImage(target, label) {
  if (!fs.existsSync(target) || !fs.statSync(target).isFile()) return;
  const rel = relative(target);
  if (!imageReferences.has(rel)) imageReferences.set(rel, new Set());
  imageReferences.get(rel).add(label);
}
for (const [rel, content] of publicHtml) {
  for (const match of content.matchAll(/(?:src=["']|url\(\s*["']?)([^"')]+)(?:["']|\))/gi)) {
    const decoded = decodePath(stripQueryAndFragment(match[1]));
    if (!decoded || !/(?:^|\/)imges\//i.test(decoded)) continue;
    recordImage(path.resolve(path.dirname(path.join(root, rel)), decoded), rel);
  }
}
for (const destination of curatedDestinations) recordImage(path.join(root, destination.image), `curated destination: ${destination.slug}`);
for (const match of destinationController.matchAll(/["'](imges\/[^"']+)["']/gi)) recordImage(path.join(root, match[1]), "destination gallery data");
const responsiveOptimizedReferences = new Set();
for (const [fallback, delivery] of Object.entries(responsiveImages)) {
  const fallbackStatus = exactPathStatus(path.join(root, fallback));
  if (fallbackStatus !== "ok") issue("Media delivery", `${fallback}: responsive manifest fallback is ${fallbackStatus}`);
  const base = path.join(root, delivery.webp);
  const baseDimensions = fs.existsSync(base) ? webpDimensions(base) : null;
  if (!baseDimensions) issue("Media delivery", `${delivery.webp}: responsive manifest base is missing or invalid WebP`);
  responsiveOptimizedReferences.add(delivery.webp);
  let priorWidth = 0;
  const seen = new Set();
  for (const candidate of delivery.candidates) {
    responsiveOptimizedReferences.add(candidate.src);
    if (seen.has(candidate.width) || candidate.width <= priorWidth) issue("Media delivery", `${fallback}: responsive candidate widths must be unique and ascending`);
    seen.add(candidate.width);
    priorWidth = candidate.width;
    const target = path.join(root, candidate.src);
    const dimensions = fs.existsSync(target) ? webpDimensions(target) : null;
    if (!dimensions) issue("Media delivery", `${candidate.src}: missing or invalid WebP derivative`);
    else {
      if (dimensions.width !== candidate.width) issue("Media delivery", `${candidate.src}: filename/manifest width ${candidate.width} does not match ${dimensions.width}px`);
      if (baseDimensions && dimensions.width > baseDimensions.width) issue("Media delivery", `${candidate.src}: derivative is upscaled beyond approved base width`);
    }
  }
}
const allowlistedMedia = fs.existsSync(allowlistPath)
  ? new Set(JSON.parse(fs.readFileSync(allowlistPath, "utf8")).publicMedia ?? [])
  : new Set();
for (const optimized of responsiveOptimizedReferences) if (!allowlistedMedia.has(optimized)) issue("Media delivery", `${optimized}: responsive asset is missing from artifact allowlist`);
for (const optimized of [...allowlistedMedia].filter((item) => item.startsWith("imges/optimized/"))) if (!responsiveOptimizedReferences.has(optimized)) issue("Media delivery", `${optimized}: allowlisted optimized asset is absent from responsive image manifest`);

const temporaryManifestPath = path.join(root, "config/temporary-destination-media.json");
if (!fs.existsSync(temporaryManifestPath)) issue("Media delivery", "config/temporary-destination-media.json: temporary media manifest is missing");
else {
  let temporaryManifest;
  const source = fs.readFileSync(temporaryManifestPath, "utf8");
  try { temporaryManifest = JSON.parse(source); } catch (error) { issue("Media delivery", `temporary media manifest is malformed: ${error.message}`); }
  if (/[A-Za-z]:[\\/]|(?:^|["'])file:\/\//i.test(source)) issue("Deployment safety", "temporary media manifest contains a private absolute path");
  if (temporaryManifest) {
    if (temporaryManifest.approvalDate !== "2026-08-03" || temporaryManifest.approvalStatus !== "temporary-owner-approved" || temporaryManifest.provenanceStatus !== "temporary-owner-supplied" || temporaryManifest.permanentRightsStatus !== "pending") issue("Media delivery", "temporary media manifest approval/provenance status is invalid");
    const manifestFallbacks = new Set();
    const manifestOptimized = new Set();
    for (const entry of temporaryManifest.files ?? []) {
      const fallback = entry.repositorySourcePath;
      if (manifestFallbacks.has(fallback)) issue("Media delivery", `${fallback}: duplicate temporary manifest entry`);
      manifestFallbacks.add(fallback);
      const status = exactPathStatus(path.join(root, fallback));
      if (status !== "ok") issue("Media delivery", `${fallback}: temporary fallback is ${status}`);
      else if (sha256(path.join(root, fallback)) !== entry.sourceSha256) issue("Media delivery", `${fallback}: approved source SHA-256 mismatch`);
      for (const optimized of entry.optimizedWebpPaths ?? []) {
        if (manifestOptimized.has(optimized)) issue("Media delivery", `${optimized}: duplicate temporary derivative manifest entry`);
        manifestOptimized.add(optimized);
        if (exactPathStatus(path.join(root, optimized)) !== "ok") issue("Media delivery", `${optimized}: temporary derivative is missing or case-mismatched`);
        if (!allowlistedMedia.has(optimized)) issue("Media delivery", `${optimized}: temporary derivative is not allowlisted`);
      }
      if (entry.approvalStatus !== "temporary-owner-approved" || entry.ownerApprovalDate !== "2026-08-03" || entry.provenanceStatus !== "temporary-owner-supplied" || entry.permanentRightsStatus !== "pending") issue("Media delivery", `${fallback}: incomplete temporary approval metadata`);
    }
    for (const item of [...allowlistedMedia].filter((value) => value.startsWith("imges/destinations/temporary/"))) if (!manifestFallbacks.has(item)) issue("Media delivery", `${item}: allowlisted temporary fallback is absent from the manifest`);
    for (const item of [...allowlistedMedia].filter((value) => value.startsWith("imges/optimized/destinations/"))) if (!manifestOptimized.has(item)) issue("Media delivery", `${item}: unused temporary derivative is allowlisted`);
    const destinations = temporaryManifest.destinations ?? {};
    const awjila = curatedDestinations.find((item) => item.slug === "awjila");
    const nafusa = curatedDestinations.find((item) => item.slug === "nafusa");
    const bomba = curatedDestinations.find((item) => item.slug === "bomba-bay");
    const villa = curatedDestinations.find((item) => item.slug === "villa-sileen");
    if (awjila?.image !== destinations.awjila?.hero || destinations.awjila?.card !== destinations.awjila?.hero) issue("Media delivery", "Awjila hero/card does not use the approved master");
    if (nafusa?.image !== destinations.nafusa?.hero || destinations.nafusa?.card !== destinations.nafusa?.hero) issue("Media delivery", "Nafusa hero/card does not use the approved landscape");
    if (bomba?.image !== destinations["bomba-bay"]?.hero || destinations["bomba-bay"]?.card !== destinations["bomba-bay"]?.hero) issue("Media delivery", "Bomba Bay hero/card does not use the approved coast image");
    if (villa?.image === destinations["villa-sileen"]?.gallery?.[0]) issue("Media delivery", "Villa Sileen columns must not be used as hero/card");
    if (new Set(destinations.awjila?.gallery ?? []).size !== (destinations.awjila?.gallery ?? []).length) issue("Media delivery", "Awjila gallery contains duplicate entries");
    const forbiddenRelationships = [
      [/awjila:\s*\[[^\]]*natural lakes1\.jpg/i, "Awjila still references natural lakes1.jpg"],
      [/nafusa:\s*\[[^\]]*traditional industries\.jpg/i, "Nafusa gallery still uses traditional industries.jpg"],
      [/"bomba-bay":\s*\[[^\]]*beaches18\.JPG/i, "Bomba Bay still references beaches18.JPG"],
      [/sabratha:\s*\[[^\]]*Leptis Magna3\.jpeg/i, "Sabratha still references Leptis Magna3.jpeg"],
      [/"villa-sileen":\s*\[[^\]]*villa-sileen-(?:aerial|coast|theatre)\.jpg/i, "Villa Sileen gallery still presents modern-compound media"],
    ];
    for (const [pattern, message] of forbiddenRelationships) if (pattern.test(destinationController)) issue("Media delivery", message);
    const villaRoles = temporaryManifest.files.find((item) => item.repositorySourcePath.endsWith("villa-sileen-columns.jpg"))?.selectedRoles ?? [];
    if (villaRoles.length !== 1 || villaRoles[0] !== "gallery") issue("Media delivery", "Villa Sileen columns approval must remain gallery-only");
  }
}
const strictImageSize = process.env.VISIT_LIBYA_STRICT_IMAGE_SIZE === "1";
for (const [imagePath, references] of [...imageReferences].sort(([a], [b]) => a.localeCompare(b))) {
  const bytes = fs.statSync(path.join(root, imagePath)).size;
  const category = bytes > 15 * 1024 * 1024 ? "publication blocker (>15 MB)" : bytes > 5 * 1024 * 1024 ? "high-priority warning (>5 MB)" : bytes > 2 * 1024 * 1024 ? "warning (>2 MB)" : null;
  if (!category) continue;
  const message = `${imagePath} | ${category} | referenced by ${[...references].sort().join(", ")}`;
  if (strictImageSize) issue("Image size audit", message); else warn(message);
}
for (const [imagePath, references] of [...imageReferences].filter(([imagePath]) => imagePath.startsWith("imges/optimized/"))) {
  const bytes = fs.statSync(path.join(root, imagePath)).size;
  if (bytes > 2 * 1024 * 1024) warn(`${imagePath} | optimized asset remains above 2 MB | referenced by ${[...references].sort().join(", ")}`);
}
const visualCssFiles = [layoutCss, fs.readFileSync(path.join(root, "assets/css/design-system.css"), "utf8"), fs.readFileSync(path.join(root, "assets/css/base.css"), "utf8")];
const visualCss = visualCssFiles.join("\n");
if (!fs.existsSync(path.join(root, "visitlibyalogo.png"))) issue("Visual system", "approved visitlibyalogo.png is missing");
if (!fs.existsSync(path.join(root, "favicon.png"))) issue("Visual system", "approved favicon.png is missing");
if (!/--font-latin:[^;]+Inter[^;]+system-ui/i.test(visualCss) || !/--font-arabic:[^;]+Cairo[^;]+Noto Sans Arabic[^;]+Tahoma/i.test(visualCss)) issue("Visual system", "English and Arabic fallback font stacks are incomplete");
const fontImports = [...layoutCss.matchAll(/@import\s+url\([^)]*fonts\.googleapis\.com[^)]*\)/gi)];
if (fontImports.length !== 1) issue("Visual system", `expected one Google Fonts import, found ${fontImports.length}`);
else {
  const fontImport = fontImports[0][0];
  if (!/display=swap/i.test(fontImport)) issue("Visual system", "external font import must use display=swap");
  if (!/family=Cairo:wght@400;700;800;900&family=Inter:wght@400;600;700;800;900/i.test(fontImport)) issue("Visual system", "external font import uses unapproved families or weights");
}
if (!/\.media-natural,\.media-editorial,[^{]+\{width:100%;height:auto;max-height:none;object-fit:contain\}/i.test(layoutCss)) issue("Visual system", "editorial media must preserve natural ratio with contain");
if (/\.media-(?:editorial|natural)[^{]*\{[^}]*(?:height:\s*\d|object-fit:\s*cover)/i.test(layoutCss)) issue("Visual system", "editorial media contains a fixed-height crop rule");
if (!/\.media-(?:card|hero)[^{]*[\s\S]{0,220}object-fit:cover/i.test(layoutCss)) issue("Visual system", "controlled card and hero cover behavior is missing");if (!/\.vl-nav\{[^}]*min-width:0;[^}]*max-width:100%/i.test(layoutCss)) issue("Visual system", "legacy navigation must permit shrinking without overflow");
if (/\.vl-language\{[^}]*position:\s*absolute/i.test(layoutCss)) issue("Visual system", "language switch must remain in normal flow");
if (/(?:html|body)[^{]*\{[^}]*overflow-x:\s*hidden/i.test(layoutCss)) issue("Visual system", "global html/body overflow hiding is forbidden as a layout workaround");
if (!/\.chat-form\{[^}]*grid-template-columns:minmax\(0,1fr\) auto/i.test(layoutCss) || !/\.chat-form input\{[^}]*min-width:0;[^}]*width:100%/i.test(layoutCss)) issue("Visual system", "AI form grid lacks mobile min-content width safety");
if (!/\.vl-logo img\{[^}]*width:clamp\([^}]*height:auto;[^}]*object-fit:contain/i.test(layoutCss)) issue("Visual system", "legacy header logo must preserve responsive contained sizing");
if (!fs.existsSync(path.join(root, "docs/visual-qa-report.md"))) issue("Visual system", "visual QA report is missing");
if (fs.existsSync(allowlistPath)) {
  const iconAllowlist = JSON.parse(fs.readFileSync(allowlistPath, "utf8")).rootFiles ?? [];
  for (const asset of ["visitlibyalogo.png", "favicon.png"]) if (!iconAllowlist.includes(asset)) issue("Visual system", `artifact allowlist omits ${asset}`);
}const failures = [...sections.values()].reduce((count, items) => count + items.length, 0);
const orderedSections = ["HTML and parity", "HTML references", "Navigation", "CSS references", "JavaScript modules", "Git tracking", "Runtime configuration", "Curated destinations", "Static unavailable states", "Deployment safety", "Release readiness", "Editorial layout", "Media delivery", "Visual system", "Image size audit"];
for (const name of orderedSections) {
  const items = sections.get(name) ?? [];
  if (items.length) {
    console.error(`FAIL ${name} (${items.length})`);
    for (const item of items) console.error(`  - ${item}`);
  } else console.log(`PASS ${name}`);
}
for (const warning of warnings) console.warn(`WARN ${warning}`);
if (failures) {
  console.error(`Frontend validation failed: ${failures} violation(s), ${warnings.length} warning(s).`);
  process.exitCode = 1;
} else {
  console.log(`Frontend validation passed: ${orderedSections.length} sections, ${actualPages.length} pages, ${warnings.length} warning(s).`);
}
