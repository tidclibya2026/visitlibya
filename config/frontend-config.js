// Safe local-development configuration. Replace apiBaseUrl during deployment.
// This file must never contain credentials, access tokens, or other secrets.
window.VISIT_LIBYA_CONFIG = Object.freeze({
  apiBaseUrl: "http://127.0.0.1:8000/api/v1",
  requestTimeoutMs: 10000,
  defaultLocale: "en",
  debug: false,
});
