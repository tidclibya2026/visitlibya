const SAFE_DEFAULTS = Object.freeze({
  apiBaseUrl: "",
  apiEnabled: false,
  debug: false,
  requestTimeoutMs: 10_000,
  deploymentEnvironment: "static",
  siteBasePath: "",
  defaultLocale: "en",
});

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);
const ENVIRONMENTS = new Set(["local", "static", "staging", "production"]);

function normalizeTimeout(value) {
  const timeout = Number(value);
  return Number.isInteger(timeout) && timeout >= 1_000 && timeout <= 120_000
    ? timeout
    : SAFE_DEFAULTS.requestTimeoutMs;
}

function normalizeLocale(value) {
  return value === "ar" || value === "en" ? value : SAFE_DEFAULTS.defaultLocale;
}

function normalizeEnvironment(value) {
  const environment = String(value ?? "").trim().toLowerCase();
  return ENVIRONMENTS.has(environment) ? environment : SAFE_DEFAULTS.deploymentEnvironment;
}

function normalizeSiteBasePath(value) {
  const path = String(value ?? "").trim();
  if (!path || path === "/") return "";
  if (!path.startsWith("/") || path.includes("?") || path.includes("#") || path.includes("..")) {
    return "";
  }
  return path.replace(/\/+$/, "");
}

function pageContext(locationRef) {
  const protocol = String(locationRef?.protocol ?? "").toLowerCase();
  const hostname = String(locationRef?.hostname ?? "").toLowerCase();
  return Object.freeze({
    isHttps: protocol === "https:",
    isLocal: hostname === "" || LOOPBACK_HOSTS.has(hostname),
  });
}

function resolveApiPolicy(supplied, locationRef) {
  if (supplied.apiEnabled !== true) {
    return Object.freeze({ apiEnabled: false, apiBaseUrl: "", apiStatus: "disabled" });
  }

  const candidate = String(supplied.apiBaseUrl ?? "").trim();
  if (!candidate) {
    return Object.freeze({ apiEnabled: false, apiBaseUrl: "", apiStatus: "missing-url" });
  }

  let url;
  try {
    url = new URL(candidate);
  } catch {
    return Object.freeze({ apiEnabled: false, apiBaseUrl: "", apiStatus: "invalid-url" });
  }

  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    return Object.freeze({ apiEnabled: false, apiBaseUrl: "", apiStatus: "invalid-url" });
  }

  const page = pageContext(locationRef);
  const apiIsLocal = LOOPBACK_HOSTS.has(url.hostname.toLowerCase());
  if (apiIsLocal && !page.isLocal) {
    return Object.freeze({ apiEnabled: false, apiBaseUrl: "", apiStatus: "local-url-on-remote-host" });
  }
  if (page.isHttps && url.protocol !== "https:") {
    return Object.freeze({ apiEnabled: false, apiBaseUrl: "", apiStatus: "insecure-url" });
  }

  return Object.freeze({
    apiEnabled: true,
    apiBaseUrl: url.href.replace(/\/+$/, ""),
    apiStatus: "available",
  });
}

export function loadRuntimeConfig(
  source = globalThis.VISIT_LIBYA_CONFIG,
  locationRef = globalThis.location,
) {
  const supplied = source && typeof source === "object" ? source : {};
  const api = resolveApiPolicy(supplied, locationRef);
  return Object.freeze({
    ...api,
    debug: supplied.debug === true,
    requestTimeoutMs: normalizeTimeout(supplied.requestTimeoutMs),
    deploymentEnvironment: normalizeEnvironment(supplied.deploymentEnvironment),
    siteBasePath: normalizeSiteBasePath(supplied.siteBasePath),
    defaultLocale: normalizeLocale(supplied.defaultLocale),
  });
}

export { SAFE_DEFAULTS };
