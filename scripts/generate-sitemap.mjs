import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argument = (name) => { const index = process.argv.indexOf(name); return index < 0 ? undefined : process.argv[index + 1]; };
const privateIpv4 = /^(?:127\.|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|169\.254\.|0\.)/;

export function origin(value) {
  let url;
  try { url = new URL(value); } catch { throw new Error("SITE_ORIGIN must be an absolute HTTPS origin"); }
  const host = url.hostname.toLowerCase().replace(/^\[|\]$/g, "");
  if (url.protocol !== "https:" || url.username || url.password || url.pathname !== "/" || url.search || url.hash) throw new Error("SITE_ORIGIN must be a credential-free HTTPS origin without a path");
  if (host === "localhost" || host.endsWith(".localhost") || host === "::1" || privateIpv4.test(host) || host.endsWith(".test") || host.endsWith(".invalid")) throw new Error("SITE_ORIGIN must not use a local, private, or test host");
  return url.origin;
}

export function base(value) {
  const normalized = String(value || "/");
  if (!normalized.startsWith("/") || normalized.includes("\\") || normalized.split("/").includes("..")) throw new Error("Invalid SITE_BASE_PATH");
  return `${normalized.replace(/\/+$/, "")}/`;
}

const xml = (value) => value.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

export function sitemapEntries(manifest) {
  return manifest.pagePairs.filter((entry) => entry.indexable && entry.sitemap !== false && entry.page !== "destination.html");
}

export function render({ siteOrigin, basePath, manifest }) {
  const normalizedOrigin = origin(siteOrigin);
  const normalizedBase = base(basePath);
  const url = (page) => `${normalizedOrigin}${normalizedBase}${page === "index.html" ? "" : page}`;
  const entries = sitemapEntries(manifest).flatMap((entry) => [[entry.page, entry.page, `ar/${entry.page}`], [`ar/${entry.page}`, entry.page, `ar/${entry.page}`]]);
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n${entries.map(([page, en, ar]) => `  <url>\n    <loc>${xml(url(page))}</loc>\n    <xhtml:link rel="alternate" hreflang="en" href="${xml(url(en))}" />\n    <xhtml:link rel="alternate" hreflang="ar" href="${xml(url(ar))}" />\n    <xhtml:link rel="alternate" hreflang="x-default" href="${xml(url(en))}" />\n  </url>`).join("\n")}\n</urlset>\n`;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const manifest = JSON.parse(fs.readFileSync(path.resolve(argument("--manifest") || path.join(root, "config/frontend-pages.json")), "utf8"));
    const siteOrigin = argument("--site-origin") || process.env.SITE_ORIGIN;
    if (!siteOrigin) throw new Error("SITE_ORIGIN or --site-origin is required");
    const output = path.resolve(argument("--output") || path.join(root, "sitemap.xml"));
    fs.mkdirSync(path.dirname(output), { recursive: true });
    fs.writeFileSync(output, render({ siteOrigin, basePath: argument("--base-path") || manifest.projectBasePath, manifest }));
    console.log(`Generated ${output}`);
  } catch (error) {
    console.error(`Sitemap generation failed: ${error.message}`);
    process.exitCode = 1;
  }
}