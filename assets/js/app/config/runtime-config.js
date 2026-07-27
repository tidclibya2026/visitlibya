const SAFE_DEFAULTS = Object.freeze({
  apiBaseUrl: "http://127.0.0.1:8001/api/v1",
  requestTimeoutMs: 10_000,
  defaultLocale: "en",
  debug: false,
});

function normalizeApiBaseUrl(value) {
  const candidate = String(value ?? SAFE_DEFAULTS.apiBaseUrl).trim();
  let url;

  try {
    url = new URL(candidate);
  } catch {
    throw new TypeError("apiBaseUrl must be a valid absolute URL");
  }

  if (!["http:", "https:"].includes(url.protocol)) {
    throw new TypeError("apiBaseUrl must use http or https");
  }
  if (url.username || url.password) {
    throw new TypeError("apiBaseUrl must not contain credentials");
  }
  if (url.search || url.hash) {
    throw new TypeError("apiBaseUrl must not contain query parameters or fragments");
  }

  return url.href.replace(/\/+$/, "");
}

function normalizeTimeout(value) {
  const timeout = Number(value);
  if (!Number.isInteger(timeout) || timeout < 1_000 || timeout > 120_000) {
    return SAFE_DEFAULTS.requestTimeoutMs;
  }
  return timeout;
}

function normalizeLocale(value) {
  return value === "ar" || value === "en" ? value : SAFE_DEFAULTS.defaultLocale;
}

export function loadRuntimeConfig(source = globalThis.VISIT_LIBYA_CONFIG) {
  const supplied = source && typeof source === "object" ? source : {};
  return Object.freeze({
    apiBaseUrl: normalizeApiBaseUrl(supplied.apiBaseUrl),
    requestTimeoutMs: normalizeTimeout(supplied.requestTimeoutMs),
    defaultLocale: normalizeLocale(supplied.defaultLocale),
    debug: supplied.debug === true,
  });
}

export { SAFE_DEFAULTS };
