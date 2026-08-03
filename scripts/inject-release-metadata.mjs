import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { origin, base } from "./generate-sitemap.mjs";

const here = fileURLToPath(import.meta.url);
const root = path.resolve(path.dirname(here), "..");
const argument = (name) => { const index = process.argv.indexOf(name); return index < 0 ? undefined : process.argv[index + 1]; };
const escapeHtml = (value) => value.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
const metaValue = (html, name) => html.match(new RegExp(`<meta[^>]+name=["']${name}["'][^>]+content=["']([^"']*)`, "i"))?.[1] || html.match(new RegExp(`<meta[^>]+content=["']([^"']*)["'][^>]+name=["']${name}["']`, "i"))?.[1] || "";
const put = (html, pattern, tag) => pattern.test(html) ? html.replace(pattern, tag) : html.replace(/<\/head>/i, `  ${tag}\n</head>`);

export function inject({ directory, siteOrigin, basePath, manifest }) {
  const normalizedOrigin = origin(siteOrigin);
  const normalizedBase = base(basePath);
  const socialImage = manifest.socialImage;
  if (!socialImage || !fs.existsSync(path.join(directory, socialImage))) throw new Error(`Missing social image: ${socialImage}`);
  for (const entry of manifest.pagePairs) {
    const eligible = entry.indexable && entry.page !== "destination.html";
    if (!eligible) continue;
    for (const language of ["en", "ar"]) {
      const rel = language === "ar" ? `ar/${entry.page}` : entry.page;
      const file = path.join(directory, rel);
      let html = fs.readFileSync(file, "utf8");
      const pageUrl = `${normalizedOrigin}${normalizedBase}${rel === "index.html" ? "" : rel}`;
      const enUrl = `${normalizedOrigin}${normalizedBase}${entry.page === "index.html" ? "" : entry.page}`;
      const arUrl = `${normalizedOrigin}${normalizedBase}ar/${entry.page}`;
      const imageUrl = `${normalizedOrigin}${normalizedBase}${socialImage}`;
      const title = html.match(/<title>([\s\S]*?)<\/title>/i)?.[1].trim() || "Visit Libya";
      const description = metaValue(html, "description");
      html = put(html, /<link[^>]+rel=["']canonical["'][^>]*>/i, `<link rel="canonical" href="${escapeHtml(pageUrl)}">`);
      html = html.replace(/\s*<link[^>]+rel=["']alternate["'][^>]+hreflang=["'](?:en|ar|x-default)["'][^>]*>\s*/gi, "\n");
      html = html.replace(/<\/head>/i, `  <link rel="alternate" hreflang="en" href="${escapeHtml(enUrl)}">\n  <link rel="alternate" hreflang="ar" href="${escapeHtml(arUrl)}">\n  <link rel="alternate" hreflang="x-default" href="${escapeHtml(enUrl)}">\n</head>`);
      for (const [property, value] of [["og:title", title], ["og:description", description], ["og:type", "website"], ["og:url", pageUrl], ["og:image", imageUrl], ["og:locale", language === "ar" ? "ar_LY" : "en_US"], ["og:locale:alternate", language === "ar" ? "en_US" : "ar_LY"]]) html = put(html, new RegExp(`<meta[^>]+property=["']${property}["'][^>]*>`, "i"), `<meta property="${property}" content="${escapeHtml(value)}">`);
      for (const [name, value] of [["twitter:card", "summary_large_image"], ["twitter:title", title], ["twitter:description", description], ["twitter:image", imageUrl]]) html = put(html, new RegExp(`<meta[^>]+name=["']${name}["'][^>]*>`, "i"), `<meta name="${name}" content="${escapeHtml(value)}">`);
      fs.writeFileSync(file, html);
    }
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === here) {
  try {
    const directory = path.resolve(argument("--directory") || path.join(root, ".pages-artifact"));
    const manifest = JSON.parse(fs.readFileSync(path.join(directory, "config/frontend-pages.json"), "utf8"));
    const siteOrigin = argument("--site-origin") || process.env.SITE_ORIGIN;
    if (!siteOrigin) throw new Error("SITE_ORIGIN or --site-origin is required");
    inject({ directory, siteOrigin, basePath: argument("--base-path") || manifest.projectBasePath, manifest });
    console.log(`Injected release metadata into ${directory}`);
  } catch (error) {
    console.error(`Metadata injection failed: ${error.message}`);
    process.exitCode = 1;
  }
}