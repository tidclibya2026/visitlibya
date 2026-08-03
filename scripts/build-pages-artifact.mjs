import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { inject } from "./inject-release-metadata.mjs";
import { render, origin } from "./generate-sitemap.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argument = (name) => { const index = process.argv.indexOf(name); return index < 0 ? undefined : process.argv[index + 1]; };
const output = path.resolve(argument("--output") || path.join(root, ".pages-artifact"));
const suppliedOrigin = argument("--site-origin") || process.env.SITE_ORIGIN || "";
const manifest = JSON.parse(fs.readFileSync(path.join(root, "config/frontend-pages.json"), "utf8"));
const allowlist = JSON.parse(fs.readFileSync(path.join(root, "config/pages-artifact-allowlist.json"), "utf8"));
const textExtensions = new Set([".html", ".css", ".js", ".json", ".txt", ".xml"]);
const relative = (target, base = root) => path.relative(base, target).replaceAll("\\", "/");

function assertSafeOutput(target) {
  const parsed = path.parse(target);
  const home = path.resolve(os.homedir());
  const repositoryArtifact = path.join(root, ".pages-artifact");
  if (target === parsed.root || target === root || target === home) throw new Error(`Unsafe output path: ${target}`);
  if (!path.relative(target, root).startsWith("..")) throw new Error("Output may not contain the repository");
  if (!path.relative(root, target).startsWith("..") && target !== repositoryArtifact) throw new Error("Repository output must be the ignored .pages-artifact directory");
  if (fs.existsSync(target) && fs.lstatSync(target).isSymbolicLink()) throw new Error("Output directory may not be a symlink");
  if (target === repositoryArtifact) {
    const ignored = spawnSync("git", ["check-ignore", "--no-index", "--quiet", "--", ".pages-artifact/"], { cwd: root });
    if (ignored.status !== 0) throw new Error(".pages-artifact must remain ignored by Git");
  }
}

function rejectUnsafeText(file, content) {
  const rel = relative(file, output);
  if (/^(?:<{7}|={7}|>{7})/m.test(content)) throw new Error(`Unresolved merge marker in ${rel}`);
  if (rel === "config/frontend-config.js") {
    if (/https?:\/\/(?:localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})(?:[:/]|$)/i.test(content)) throw new Error("Unsafe public runtime URL");
    if (!/apiEnabled:\s*false/.test(content) || !/apiBaseUrl:\s*["']{2}/.test(content) || !/deploymentEnvironment:\s*["']static["']/.test(content)) throw new Error("Public runtime configuration is not static-safe");
    if (/\b(?:apiKey|api_key|password|secret|token)\s*:\s*["'][^"']+["']/i.test(content)) throw new Error("Populated secret-like public runtime value");
  }
}

function copyFile(rel) {
  const source = path.resolve(root, rel);
  if (relative(source).startsWith("../") || !fs.existsSync(source)) throw new Error(`Required public file missing: ${rel}`);
  const stat = fs.lstatSync(source);
  if (stat.isSymbolicLink()) throw new Error(`Public symlink forbidden: ${rel}`);
  if (!stat.isFile()) throw new Error(`Expected public file: ${rel}`);
  const destination = path.resolve(output, rel);
  if (relative(destination, output).startsWith("../")) throw new Error(`Unsafe public path: ${rel}`);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.copyFileSync(source, destination, fs.constants.COPYFILE_EXCL);
  if (textExtensions.has(path.extname(rel).toLowerCase())) rejectUnsafeText(destination, fs.readFileSync(destination, "utf8"));
}

function copyTree(directory, extensions) {
  const sourceDirectory = path.join(root, directory);
  if (!fs.existsSync(sourceDirectory)) throw new Error(`Required public directory missing: ${directory}`);
  const visit = (current) => {
    for (const entry of fs.readdirSync(current, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name, "en"))) {
      const source = path.join(current, entry.name);
      const rel = relative(source);
      if (entry.isSymbolicLink()) throw new Error(`Public symlink forbidden: ${rel}`);
      if (entry.isDirectory()) visit(source);
      else if (extensions.has(path.extname(entry.name).toLowerCase())) copyFile(rel);
    }
  };
  visit(sourceDirectory);
}

function payloadFiles() {
  const files = [];
  const visit = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name, "en"))) {
      const target = path.join(directory, entry.name);
      if (entry.isDirectory()) visit(target);
      else if (relative(target, output) !== "release-manifest.json") files.push(target);
    }
  };
  visit(output);
  return files;
}

const normalizedOrigin = suppliedOrigin ? origin(suppliedOrigin) : null;
assertSafeOutput(output);
fs.rmSync(output, { recursive: true, force: true });
fs.mkdirSync(output, { recursive: true });
const requiredFiles = new Set(allowlist.rootFiles);
for (const entry of manifest.pagePairs) { requiredFiles.add(entry.page); requiredFiles.add(`ar/${entry.page}`); }
for (const rel of [...requiredFiles].sort((a, b) => a.localeCompare(b, "en"))) copyFile(rel);
for (const [directory, extensions] of Object.entries(allowlist.publicTrees).sort(([a], [b]) => a.localeCompare(b, "en"))) copyTree(directory, new Set(extensions));
for (const rel of [...allowlist.publicMedia].sort((a, b) => a.localeCompare(b, "en"))) copyFile(rel);

if (normalizedOrigin) {
  inject({ directory: output, siteOrigin: normalizedOrigin, basePath: manifest.projectBasePath, manifest });
  fs.writeFileSync(path.join(output, "sitemap.xml"), render({ siteOrigin: normalizedOrigin, basePath: manifest.projectBasePath, manifest }));
  fs.appendFileSync(path.join(output, "robots.txt"), `\nSitemap: ${normalizedOrigin}${manifest.projectBasePath}sitemap.xml\n`);
} else console.warn("Preview artifact: SITE_ORIGIN was not supplied; canonical metadata and sitemap.xml are omitted.");

const validation = spawnSync(process.execPath, [path.join(root, "scripts/validate-pages-artifact.mjs"), "--directory", output, "--pre-manifest"], { cwd: root, encoding: "utf8" });
if (validation.status !== 0) throw new Error(`Artifact validation failed before manifest generation:\n${validation.stdout}${validation.stderr}`);
const files = payloadFiles();
const entries = files.map((file) => { const bytes = fs.statSync(file).size; return { path: relative(file, output), bytes, sha256: crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex") }; });
const commitResult = spawnSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" });
if (commitResult.status !== 0 || !/^[0-9a-f]{40}$/i.test(commitResult.stdout.trim())) throw new Error("Unable to determine source commit");
const releaseManifest = { schemaVersion: 1, buildTimestampUtc: new Date().toISOString(), sourceCommit: commitResult.stdout.trim(), projectBasePath: manifest.projectBasePath, releaseOriginStatus: normalizedOrigin ? "supplied" : "not-supplied", fileCount: entries.length, totalBytes: entries.reduce((sum, entry) => sum + entry.bytes, 0), files: entries };
fs.writeFileSync(path.join(output, "release-manifest.json"), `${JSON.stringify(releaseManifest, null, 2)}\n`);
console.log(`Pages artifact: ${releaseManifest.fileCount} payload files, ${releaseManifest.totalBytes} bytes, origin ${releaseManifest.releaseOriginStatus}`);