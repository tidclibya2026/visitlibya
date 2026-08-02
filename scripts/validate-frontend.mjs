import fs from "node:fs";
import path from "node:path";
import process from "node:process";
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
  "backend/.env.example",
  "backend/app/core/config.py",
  ".github/workflows/backend-production-validation.yml",
  "docker-compose.production.example.yml",
  "docs/backend-cors-and-frontend-integration.md",
  "docs/frontend-release-checklist.md",
  "scripts/validate-pages-artifact.mjs",
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
  if (/\b(?:src|href)=["']\/(?!\/)|url\(\s*["']?\/(?!\/)/i.test(content)) issue("Deployment safety", `${rel}: root-relative frontend path can break project-subpath hosting`);
  const browserSource = /^(?:ar\/.*\.html|[^/]+\.html|style\.css|assets\/.*\.(?:css|js)|config\/frontend-config(?:\.example)?\.js)$/i.test(rel);
  if (/file:\/\//i.test(content) && browserSource) issue("Deployment safety", `${rel}: file:// browser reference is forbidden`);
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

const en = (await import(pathToFileURL(path.join(root, "assets/js/app/i18n/en.js")))).en;
const ar = (await import(pathToFileURL(path.join(root, "assets/js/app/i18n/ar.js")))).ar;
function dictionaryKeys(value, prefix = "") {
  return Object.entries(value).flatMap(([key, child]) => child && typeof child === "object" ? dictionaryKeys(child, `${prefix}${key}.`) : [`${prefix}${key}`]).sort();
}
if (JSON.stringify(dictionaryKeys(en)) !== JSON.stringify(dictionaryKeys(ar))) issue("HTML and parity", "English and Arabic dynamic dictionaries are not structurally equivalent");
for (const key of ["registrationUnavailable", "signInUnavailable"]) if (!en.auth[key] || !ar.auth[key]) issue("HTML and parity", `missing bilingual auth.${key}`);
if (!en.trips.plannerUnavailable || !ar.trips.plannerUnavailable) issue("HTML and parity", "missing bilingual trips.plannerUnavailable");

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

const releaseFiles = [".nojekyll", "404.html", "robots.txt", ".github/workflows/pages-release.yml", "scripts/build-pages-artifact.mjs", "scripts/inject-release-metadata.mjs", "scripts/generate-sitemap.mjs", "scripts/validate-pages-artifact.mjs"];
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

const publicHtml = new Map(htmlByRelative);
const notFoundPath = path.join(root, "404.html");
if (fs.existsSync(notFoundPath)) publicHtml.set("404.html", fs.readFileSync(notFoundPath, "utf8"));
for (const [rel, content] of publicHtml) {
  const file = path.join(root, rel);
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
  for (const property of ["og:title", "og:description", "og:type"]) if (!new RegExp(`<meta[^>]+property=["']${property}["']`, "i").test(content)) issue("Release readiness", `${rel}: ${property} missing`);
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
const heritageImagePaths = new Set([
  "imges/Leptis Magna3.jpeg",
  "imges/Cyrene.jpg",
  "imges/Sabratha.jpg",
<<<<<<< HEAD
  "imges/curated/acacus-rock-art-chariot.jpg",
=======
  "imges/Acacus.jpg",
>>>>>>> origin/main
  "imges/Ghadames2.JPG",
]);
for (const rel of ["heritage.html", "ar/heritage.html"]) {
  const content = htmlByRelative.get(rel) ?? "";
  const section = content.match(/<section\b[^>]*\bid=["']world-heritage["'][^>]*>([\s\S]*?)<\/section>/i)?.[1] ?? "";
  const cards = [...section.matchAll(/<article\b[^>]*class=["'][^"']*destination-card[^"']*["'][^>]*>[\s\S]*?<\/article>/gi)];
  if (cards.length !== 5) issue("Editorial layout", `${rel}: World Heritage grid must contain exactly five cards`);
  if (!/class=["'][^"']*destination-grid[^"']*["']/i.test(section)) issue("Editorial layout", `${rel}: World Heritage desktop grid class is missing`);
  const paths = new Set([...section.matchAll(/<img\b[^>]*\bsrc=["'](?:\.\.\/)?([^"']+)["']/gi)].map((match) => match[1]));
  if (paths.size !== heritageImagePaths.size || [...heritageImagePaths].some((image) => !paths.has(image))) issue("Editorial layout", `${rel}: World Heritage image paths changed`);
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
const strictImageSize = process.env.VISIT_LIBYA_STRICT_IMAGE_SIZE === "1";
for (const [imagePath, references] of [...imageReferences].sort(([a], [b]) => a.localeCompare(b))) {
  const bytes = fs.statSync(path.join(root, imagePath)).size;
  const category = bytes > 15 * 1024 * 1024 ? "publication blocker (>15 MB)" : bytes > 5 * 1024 * 1024 ? "high-priority warning (>5 MB)" : bytes > 2 * 1024 * 1024 ? "warning (>2 MB)" : null;
  if (!category) continue;
  const message = `${imagePath} | ${category} | referenced by ${[...references].sort().join(", ")}`;
  if (strictImageSize) issue("Image size audit", message); else warn(message);
}
const failures = [...sections.values()].reduce((count, items) => count + items.length, 0);
const orderedSections = ["HTML and parity", "HTML references", "Navigation", "CSS references", "JavaScript modules", "Git tracking", "Runtime configuration", "Curated destinations", "Static unavailable states", "Deployment safety", "Release readiness", "Editorial layout", "Image size audit"];
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
