// Public runtime configuration for Visit Libya.
// Local development may use the local API.
// Static/remote hosting remains API-disabled until an approved staging/production endpoint exists.
// Never place secrets in this public file.

(() => {
  const hostname = String(window.location?.hostname || "").toLowerCase();
  const isLocal =
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "[::1]";

  window.VISIT_LIBYA_CONFIG = Object.freeze({
    apiBaseUrl: isLocal ? "http://127.0.0.1:8001/api/v1" : "",
    apiEnabled: isLocal,
    debug: false,
    requestTimeoutMs: 10000,
    deploymentEnvironment: isLocal ? "local" : "static",
    siteBasePath: "",
    defaultLocale: "en",
  });
})();
