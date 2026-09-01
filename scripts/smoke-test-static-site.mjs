import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import vm from "node:vm";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const sourceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argument = (name) => { const index = process.argv.indexOf(name); return index < 0 ? undefined : process.argv[index + 1]; };
const root = path.resolve(argument("--root") || sourceRoot);
const manifest = JSON.parse(fs.readFileSync(path.join(root, "config/frontend-pages.json"), "utf8"));
const basePath = manifest.projectBasePath;
const failures = [];
let executed = 0;
let passed = 0;

const mimeTypes = new Map(Object.entries({
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".png": "image/png",
  ".webp": "image/webp",
  ".avif": "image/avif",
  ".svg": "image/svg+xml",
  ".kml": "application/vnd.google-earth.kml+xml",
  ".csv": "text/csv; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".otf": "font/otf",
  ".pdf": "application/pdf",
}));

async function test(name, assertion) {
  executed += 1;
  try {
    await assertion();
    passed += 1;
    console.log(`PASS ${name}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    failures.push(`${name}: ${message}`);
    console.error(`FAIL ${name}: ${message}`);
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function decodeRequestPath(rawUrl) {
  const rawPath = String(rawUrl ?? "/").split(/[?#]/, 1)[0];
  let decoded;
  try { decoded = decodeURIComponent(rawPath); } catch { return { status: 400 }; }
  if (decoded.includes("\\") || decoded.split("/").includes("..") || decoded.includes("\0")) return { status: 403 };
  let pathname = decoded;
  if (pathname === "/" || pathname === basePath.slice(0, -1)) pathname = "/index.html";
  else if (pathname === basePath) pathname = `${basePath}index.html`;
  if (pathname.startsWith(basePath)) pathname = `/${pathname.slice(basePath.length)}`;
  const target = path.resolve(root, `.${pathname}`);
  if (path.relative(root, target).startsWith("..")) return { status: 403 };
  return { status: 200, target };
}

function createServer() {
  return http.createServer((request, response) => {
    if (!["GET", "HEAD"].includes(request.method ?? "")) {
      response.writeHead(405, { Allow: "GET, HEAD" }).end();
      return;
    }
    const resolved = decodeRequestPath(request.url);
    if (resolved.status !== 200) {
      response.writeHead(resolved.status).end();
      return;
    }
    let stat;
    try { stat = fs.statSync(resolved.target); } catch { const fallback = path.join(root, "404.html"); const body = fs.readFileSync(fallback); response.writeHead(404, { "Content-Type": "text/html; charset=utf-8", "Content-Length": body.length }).end(request.method === "HEAD" ? undefined : body); return; }
    const target = stat.isDirectory() ? path.join(resolved.target, "index.html") : resolved.target;
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) { response.writeHead(404).end(); return; }
    const mime = mimeTypes.get(path.extname(target).toLowerCase()) ?? "application/octet-stream";
    const size = fs.statSync(target).size;
    response.writeHead(200, { "Content-Type": mime, "Content-Length": size, "X-Content-Type-Options": "nosniff" });
    if (request.method === "HEAD") response.end();
    else fs.createReadStream(target).pipe(response);
  });
}

function listen(server) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve(server.address().port));
  });
}

function close(server) {
  return new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
}

function rawStatus(port, requestPath) {
  return new Promise((resolve, reject) => {
    const request = http.get({ hostname: "127.0.0.1", port, path: requestPath }, (response) => {
      response.resume();
      response.once("end", () => resolve(response.statusCode));
    });
    request.once("error", reject);
  });
}

function pagePaths() {
  return manifest.pagePairs.flatMap(({ page }) => [page, `ar/${page}`]);
}

function htmlAttributes(content) {
  const match = content.match(/<html\b([^>]*)>/i);
  return match?.[1] ?? "";
}

function scripts(content) {
  return [...content.matchAll(/<script[^>]+src=["']([^"']+)["']/gi)].map((match) => match[1]);
}

function localLinks(content) {
  return [...content.matchAll(/href=["']([^"']+)["']/gi)].map((match) => match[1]).filter((link) =>
    link && !link.startsWith("#") && !/^(?:https?:|mailto:|tel:|javascript:|data:|\/\/)/i.test(link));
}

const server = createServer();
let origin;
try {
  const port = await listen(server);
  origin = `http://127.0.0.1:${port}`;
  console.log(`Static smoke server: ${origin}${basePath}`);

  await test("server binds to loopback on an ephemeral port", () => {
    const address = server.address();
    assert(address.address === "127.0.0.1", `bound to ${address.address}`);
    assert(Number.isInteger(address.port) && address.port > 0, "ephemeral port was not assigned");
  });

  for (const page of pagePaths()) {
    await test(`HTTP 200 ${basePath}${page}`, async () => {
      const response = await fetch(`${origin}${basePath}${page}`);
      assert(response.status === 200, `received ${response.status}`);
      assert(response.headers.get("content-type")?.startsWith("text/html"), `unexpected MIME ${response.headers.get("content-type")}`);
      const content = await response.text();
      const arabic = page.startsWith("ar/");
      const attrs = htmlAttributes(content);
      assert(new RegExp(`\\blang=["']${arabic ? "ar" : "en"}["']`, "i").test(attrs), "incorrect lang attribute");
      assert(new RegExp(`\\bdir=["']${arabic ? "rtl" : "ltr"}["']`, "i").test(attrs), "incorrect dir attribute");
    });
  }

  for (const requestPath of ["/", "/index.html", "/ar/index.html"]) {
    await test(`root-style request ${requestPath}`, async () => {
      const response = await fetch(`${origin}${requestPath}`);
      assert(response.status === 200, `received ${response.status}`);
    });
  }

  const criticalAssets = [
    ["config/frontend-config.js", "text/javascript"],
    ["config/frontend-pages.json", "application/json"],
    ["assets/js/app/config/runtime-config.js", "text/javascript"],
    ["assets/js/app/api/client.js", "text/javascript"],
    ["assets/js/data/curated-destinations.js", "text/javascript"],
    ["assets/js/app/map/trip-map.js", "text/javascript"],
    ["style.css", "text/css"],
    ["assets/css/design-system.css", "text/css"],
    ["assets/css/destinations.css", "text/css"],
    ["assets/css/destination-details.css", "text/css"],
    ["imges/Leptis Magna3.jpeg", "image/jpeg"],
    ["imges/Stone inscriptions in antiquities.jpg", "image/jpeg"],
    ["imges/الدبلة.webp", "image/webp"],
  ];
  for (const [asset, expectedMime] of criticalAssets) {
    await test(`asset and MIME ${asset}`, async () => {
      const response = await fetch(`${origin}${basePath}${encodeURI(asset)}`);
      assert(response.status === 200, `received ${response.status}`);
      assert(response.headers.get("content-type")?.startsWith(expectedMime), `expected ${expectedMime}, received ${response.headers.get("content-type")}`);
    });
  }

  await test("query strings and fragments preserve the static pathname", async () => {
    const response = await fetch(`${origin}${basePath}destination.html?slug=leptis-magna#mainContent`);
    assert(response.status === 200, `received ${response.status}`);
    assert((await response.text()).includes("destinationContent"), "destination detail content container is missing");
  });

  await test("directory traversal is rejected", async () => {
    const status = await rawStatus(port, `${basePath}%2e%2e/%2e%2e/config/frontend-config.js`);
    assert(status === 403, `expected 403, received ${status}`);
  });

  for (const page of ["destination.html", "ar/destination.html"]) {
    await test(`${page} detail state containers and config order`, async () => {
      const content = await (await fetch(`${origin}${basePath}${page}?slug=leptis-magna`)).text();
      for (const id of ["destinationLoading", "destinationNotFound", "destinationError", "destinationContent", "destinationLanguageLink"]) assert(content.includes(`id="${id}"`), `missing #${id}`);
      assert(content.indexOf("config/frontend-config.js") < content.indexOf("assets/js/pages/destination-details.js"), "runtime config does not precede controller");
    });
  }

  const unavailableHooks = {
    "register.html": ["data-register-form", "data-register-error", "data-register-submit"],
    "trips.html": ["data-login-form", "data-login-error", "data-login-submit"],
    "trip.html": ["data-trip-error", "data-trip-editor", "data-trip-loading"],
  };
  for (const [page, hooks] of Object.entries(unavailableHooks)) {
    for (const rel of [page, `ar/${page}`]) {
      await test(`${rel} API-disabled structural hooks`, async () => {
        const content = await (await fetch(`${origin}${basePath}${rel}`)).text();
        for (const hook of hooks) assert(content.includes(hook), `missing ${hook}`);
        assert(content.indexOf("config/frontend-config.js") < content.indexOf(manifest.pagePairs.find((entry) => entry.page === page).controller), "runtime config does not precede controller");
      });
    }
  }

  await test("visitor pages do not depend on scripts directory", async () => {
    for (const page of pagePaths()) {
      const content = await (await fetch(`${origin}${basePath}${page}`)).text();
      assert(!scripts(content).some((source) => /(?:^|\/)scripts\//.test(source)), `${page} references a test/operator script`);
    }
  });

  await test("all internal page links return HTTP 200 under project subpath", async () => {
    const checked = new Set();
    for (const page of pagePaths()) {
      const sourceUrl = new URL(`${basePath}${page}`, origin);
      const content = await (await fetch(sourceUrl)).text();
      for (const link of localLinks(content)) {
        const target = new URL(link, sourceUrl);
        if (!target.pathname.endsWith(".html") && !target.pathname.endsWith("/")) continue;
        const key = `${target.pathname}${target.search}`;
        if (checked.has(key)) continue;
        checked.add(key);
        const response = await fetch(target);
        assert(response.status === 200, `${page} -> ${link} returned ${response.status}`);
      }
    }
    assert(checked.size > 20, `only ${checked.size} internal links were checked`);
  });

  const runtimeUrl = pathToFileURL(path.join(root, "assets/js/app/config/runtime-config.js"));
  const clientUrl = pathToFileURL(path.join(root, "assets/js/app/api/client.js"));
  const { loadRuntimeConfig, ATLAS_PRESENTATION_URL, buildAtlasPresentationUrl } = await import(runtimeUrl);
  const { createApiClient } = await import(clientUrl);
  const remoteHttps = { protocol: "https:", hostname: "visit.example" };
  const localHttp = { protocol: "http:", hostname: "127.0.0.1" };
  const policyCases = [
    ["empty enabled URL is disabled", { apiEnabled: true, apiBaseUrl: "" }, remoteHttps, false, "missing-url"],
    ["remote localhost is disabled", { apiEnabled: true, apiBaseUrl: "http://127.0.0.1:8000/api/v1" }, remoteHttps, false, "local-url-on-remote-host"],
    ["HTTP API under HTTPS is disabled", { apiEnabled: true, apiBaseUrl: "http://api.example.test/api/v1" }, remoteHttps, false, "insecure-url"],
    ["illustrative HTTPS API is accepted", { apiEnabled: true, apiBaseUrl: "https://api.example.test/api/v1" }, remoteHttps, true, "available"],
    ["local loopback API is accepted locally", { apiEnabled: true, apiBaseUrl: "http://127.0.0.1:8000/api/v1" }, localHttp, true, "available"],
  ];
  for (const [name, config, location, enabled, status] of policyCases) {
    await test(name, () => {
      const result = loadRuntimeConfig(config, location);
      assert(result.apiEnabled === enabled, `apiEnabled=${result.apiEnabled}`);
      assert(result.apiStatus === status, `apiStatus=${result.apiStatus}`);
    });
  }
  await test("Atlas builder is fixed, HTTPS, and privacy-safe", () => {
    const url = new URL(ATLAS_PRESENTATION_URL);
    assert(url.protocol === "https:" && url.hostname === "tidclibya2026.github.io" && url.pathname === "/Libya_Tourist_Atlas/", "Atlas origin/path mismatch");
    for (const input of [undefined, { destinationName: "Ghadames" }, { destinationName: "غدامس" }, { destinationName: "javascript:alert(1)&token=x" }, { slug: "../invalid" }]) assert(buildAtlasPresentationUrl(input) === ATLAS_PRESENTATION_URL, "Atlas builder accepted unverified deep-link input");
    assert(!/[?&](?:token|user_id|trip_id)=/i.test(ATLAS_PRESENTATION_URL), "Atlas URL leaks private identifiers");
  });
  await test("apiEnabled false returns API_UNAVAILABLE before fetch", async () => {
    const originalFetch = globalThis.fetch;
    let fetchCalls = 0;
    globalThis.fetch = async () => { fetchCalls += 1; throw new Error("fetch must not run"); };
    try {
      const client = createApiClient(loadRuntimeConfig({ apiEnabled: false }, remoteHttps));
      let error;
      try { await client.get("/destinations"); } catch (caught) { error = caught; }
      assert(error?.code === "API_UNAVAILABLE", `received ${error?.code ?? "no error"}`);
      assert(fetchCalls === 0, `fetch called ${fetchCalls} time(s)`);
    } finally { globalThis.fetch = originalFetch; }
  });

  await test("committed runtime config is static-safe and hostname-free", () => {
    const source = fs.readFileSync(path.join(root, "config/frontend-config.js"), "utf8");
    const sandbox = { window: {} };
    vm.runInNewContext(source, sandbox, { filename: "config/frontend-config.js" });
    const config = sandbox.window.VISIT_LIBYA_CONFIG;
    assert(config.apiEnabled === false, "apiEnabled is not false");
    assert(config.apiBaseUrl === "", "apiBaseUrl is not empty");
    assert(config.deploymentEnvironment === "static", "deploymentEnvironment is not static");
    assert(!/https?:\/\/[^\s"']+/.test(source), "a production/API hostname is committed");
  });

  const curatedPath = path.join(root, "assets/js/data/curated-destinations.js");
  const { curatedDestinations } = await import(pathToFileURL(curatedPath));
  await test("curated destination integrity", () => {
    const required = ["name_en", "name_ar", "description_en", "description_ar", "region_en", "region_ar", "category_en", "category_ar", "slug", "image"];
    const slugs = new Set();
    for (const item of curatedDestinations) {
      for (const field of required) assert(typeof item[field] === "string" && item[field].trim(), `${item.slug ?? "unknown"} missing ${field}`);
      assert(/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.slug), `invalid slug ${item.slug}`);
      assert(!slugs.has(item.slug), `duplicate slug ${item.slug}`);
      slugs.add(item.slug);
      assert(fs.existsSync(path.join(root, item.image)), `${item.slug} image is missing: ${item.image}`);
    }
    assert(slugs.has("leptis-magna"), "leptis-magna is missing");
  });

  await test("destination links and language switch preserve valid slugs", () => {
    const listing = fs.readFileSync(path.join(root, "assets/js/pages/destinations.js"), "utf8");
    const detail = fs.readFileSync(path.join(root, "assets/js/pages/destination-details.js"), "utf8");
    assert(/destination\.html\?slug=\$\{encodeURIComponent\(destination\.slug\)\}/.test(listing), "listing does not encode detail slugs");
    assert(/destination\.html\?slug=\$\{encodeURIComponent\(slug\)\}/.test(detail), "language switch does not preserve slug");
    assert(/if \(!runtimeConfig\.apiEnabled\)[\s\S]{0,150}view:\s*["']error["']/.test(detail), "unknown static slug lacks a terminal error state");
  });
  await test("trip map derives only valid authoritative coordinate pairs", async () => {
    const modulePath = path.join(root, "assets/js/app/map/trip-map.js");
    const { validCoordinatePair, buildTripMapStops, mapCoverageSummary } = await import(pathToFileURL(modulePath));
    assert(validCoordinatePair({ latitude: 32.6, longitude: 14.3 }), "valid pair rejected");
    for (const value of [
      { latitude: null, longitude: null },
      { latitude: 32.6, longitude: null },
      { latitude: "32.6", longitude: 14.3 },
      { latitude: 91, longitude: 14.3 },
      { latitude: 32.6, longitude: 181 },
    ]) assert(!validCoordinatePair(value), "invalid pair accepted");
    const items = [
      { id: 3, day_number: 2, sort_order: 0, start_time: null, destination: { id: 3, slug: "third", name_en: "Third", name_ar: "الثالثة", latitude: 25, longitude: 20 } },
      { id: 1, day_number: 1, sort_order: 0, start_time: "09:00:00", destination: { id: 1, slug: "first", name_en: "First", name_ar: "الأولى", latitude: 32, longitude: 13 } },
      { id: 2, day_number: 1, sort_order: 1, start_time: null, destination: { id: 2, slug: "second", name_en: "Second", name_ar: "الثانية", latitude: null, longitude: null } },
    ];
    const mapped = buildTripMapStops(items, "en");
    assert(mapped.length === 2 && mapped[0].itemId === 1 && mapped[0].sequenceNumber === 1, "map order is not deterministic");
    assert(mapped[1].itemId === 3 && mapped[1].sequenceNumber === 3 && mapped[1].dayNumber === 2, "unmapped stop changed itinerary sequence");
    assert(mapCoverageSummary(3, 2, "en").includes("2 of 3"), "partial coverage copy is incorrect");
    assert(/[\u0600-\u06ff]/.test(mapCoverageSummary(3, 2, "ar")), "Arabic coverage copy is missing");
  });
  await test("404 page and unknown-path behavior", async () => {
    const direct = await fetch(`${origin}${basePath}404.html`);
    assert(direct.status === 200, `direct 404 returned ${direct.status}`);
    const missing = await fetch(`${origin}${basePath}missing/deep/path`);
    const content = await missing.text();
    assert(missing.status === 404, `unknown path returned ${missing.status}`);
    assert(/noindex,follow/i.test(content) && /[\u0600-\u06ff]/.test(content), "404 is not bilingual/noindex");
    assert(!/config\/frontend-config|assets\/js\/app\/api/i.test(content), "404 depends on runtime/API code");
  });
  await test("robots is origin-neutral and leaves public paths crawlable", async () => {
    const content = await (await fetch(`${origin}${basePath}robots.txt`)).text();
    const sitemapDirectives = [...content.matchAll(/^\s*Sitemap:\s*(\S+)\s*$/gim)].map((match) => match[1]);
    const sitemapPath = path.join(root, "sitemap.xml");
    if (fs.existsSync(sitemapPath)) {
      const sitemap = fs.readFileSync(sitemapPath, "utf8");
      const firstLocation = sitemap.match(/<loc>([^<]+)<\/loc>/)?.[1];
      assert(firstLocation, "artifact sitemap has no public location");
      const expectedSitemap = `${new URL(firstLocation).origin}${basePath}sitemap.xml`;
      assert(sitemapDirectives.length === 1 && sitemapDirectives[0] === expectedSitemap, `artifact robots sitemap must be ${expectedSitemap}`);
    } else assert(sitemapDirectives.length === 0, "source robots has an unconfirmed sitemap");
    assert(!/Disallow:\s*\/(?:assets|ar|imges|panel)/i.test(content), "robots blocks public paths");
  });
  await test("sitemap generator requires HTTPS and is deterministic", async () => {
    const { render } = await import(pathToFileURL(path.join(sourceRoot, "scripts/generate-sitemap.mjs")));
    let rejected = false; try { render({ siteOrigin: "http://" + "example.com", basePath, manifest }); } catch { rejected = true; }
    assert(rejected, "HTTP origin was accepted");
    const xml = render({ siteOrigin: "https://" + "example.com", basePath, manifest });
    assert(xml.includes("https://" + "example.com/visitlibya/ar/index.html"), "Arabic alternate/base path missing");
    assert(!xml.includes("register.html") && !xml.includes("trips.html") && !xml.includes("trip.html") && !xml.includes("ai.html"), "noindex page entered sitemap");
    assert(!xml.includes("destination.html"), "generic destination template entered sitemap");
    assert(xml === render({ siteOrigin: "https://" + "example.com", basePath, manifest }), "sitemap is not deterministic");
  });
} finally {
  if (server.listening) await close(server);
}

await test("static server shut down cleanly", () => assert(!server.listening, "server is still listening"));
console.log(`Smoke tests executed: ${executed}`);
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failures.length}`);
if (failures.length) {
  console.error("Actionable failures:");
  for (const failure of failures) console.error(`  - ${failure}`);
  console.error("Final exit code: 1");
  process.exitCode = 1;
} else {
  console.log("Final exit code: 0");
}
