# Visit Libya frontend runtime configuration

The Visit Libya frontend is static HTML, CSS, and native JavaScript. Its one public environment-specific configuration source is `config/frontend-config.js`, loaded before every API-dependent page controller. The module `assets/js/app/config/runtime-config.js` only validates and normalizes that public object; page controllers must not define API origins or deployment policy.

Frontend configuration is visible to every visitor. Never put passwords, API keys, JWTs, database URLs, or other secrets in it.

## Configuration fields

```js
window.VISIT_LIBYA_CONFIG = Object.freeze({
  apiBaseUrl: "",
  apiEnabled: false,
  debug: false,
  requestTimeoutMs: 10000,
  deploymentEnvironment: "static",
  siteBasePath: "",
  defaultLocale: "en",
});
```

- `apiBaseUrl`: absolute API prefix, including `/api/v1`, or an empty string.
- `apiEnabled`: the explicit switch for live API features. A URL alone does not enable requests.
- `debug`: permits sanitized diagnostics only. It never logs tokens or request bodies.
- `requestTimeoutMs`: bounded to 1,000–120,000 milliseconds; invalid values become 10,000.
- `deploymentEnvironment`: `local`, `static`, `staging`, or `production`.
- `siteBasePath`: optional repository path for a future runtime use. Keep it empty because current assets and navigation use correct relative paths.
- `defaultLocale`: `en` or `ar`; the page language remains authoritative.

## Local development

`config/frontend-config.example.js` is a local-development example only. To connect explicitly to a local FastAPI server, configure the public runtime file with `apiEnabled: true`, `deploymentEnvironment: "local"`, and the documented loopback API URL. The backend is optional: curated destination content remains available if a live request fails.

Serve the frontend over HTTP rather than opening pages directly when testing ES modules. Configure the backend CORS allowlist with the exact local frontend origin, including scheme and port.

## GitHub Pages and other static-only hosting

Keep the committed safe configuration unchanged: API disabled and URL empty. The browser makes no API request. Destination explorer and known destination-detail pages render immediately from the curated local collection. Registration, sign-in, saved trips, and trip editing display localized unavailable states and disable their live actions.

GitHub Pages serves static files only. It cannot run FastAPI processes, connect privately to PostgreSQL, manage backend environment variables, or execute database migrations. Those services require separate application and database hosting.

All frontend assets, modules, images, language links, and destination slug links remain relative, so a repository project path such as `/repository-name/` works without rewriting paths or setting `siteBasePath`.

## Future production HTTPS API

When a backend is deployed, change only `config/frontend-config.js`:

```js
window.VISIT_LIBYA_CONFIG = Object.freeze({
  apiBaseUrl: "https://YOUR-API-HOST.example/api/v1",
  apiEnabled: true,
  debug: false,
  requestTimeoutMs: 10000,
  deploymentEnvironment: "production",
  siteBasePath: "",
  defaultLocale: "en",
});
```

Replace the illustrative hostname; the project does not assume a production domain. An HTTPS page accepts only an HTTPS API. Malformed URLs, URL credentials, loopback URLs on remote pages, and HTTP APIs on HTTPS pages are disabled before `fetch`.

The FastAPI deployment must allow the exact frontend origin through CORS. It must support the methods used by the frontend and request headers including `Authorization` and `Content-Type`. Do not use `*` as a substitute when credentialed behavior is introduced. CORS is an API response policy, not a frontend workaround.

## Feature behavior

| Feature | API disabled | Temporary live API failure |
|---|---|---|
| Homepage | Static curated content | Unaffected |
| Destination explorer | Immediate curated collection | Curated collection with live-update notice and retry |
| Known destination detail | Immediate curated detail | Curated detail with live-update notice and retry |
| Unknown destination detail | Unavailable state | Retryable error or not-found response |
| Registration | Disabled with localized message | Localized temporary failure |
| Sign-in and saved trips | Disabled with localized message | Localized temporary failure and retry where applicable |
| Trip editor/search | Disabled with localized message | Localized temporary failure and existing conflict handling |
| Favorites and reviews | No frontend controller currently | No frontend controller currently |

## Validation

Run:

```text
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
```

The commands exit non-zero for deployment violations or failed static HTTP/runtime checks. The smoke runner serves the repository temporarily under a simulated GitHub Pages project subpath and shuts down without writing generated files.

Use the [frontend deployment smoke-test checklist](frontend-deployment-smoke-tests.md) for pre-publication review, post-publication URLs, browser checks, rollback criteria, and evidence capture.
