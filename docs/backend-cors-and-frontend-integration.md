# Backend CORS and frontend integration

The production frontend origin is exactly:

```text
https://tidclibya2026.github.io
```

Do not configure `https://tidclibya2026.github.io/visitlibya/`. CORS origins contain scheme, host, and optional port only. The backend explicitly permits GET, POST, PUT, PATCH, DELETE, OPTIONS and the Authorization, Content-Type, Accept, Origin, and X-Request-ID headers. Unknown origins receive no permissive origin header.

Local origins such as `http://localhost:5500` may be explicitly configured only for local development. Staging and future custom domains require separate exact entries; origin reflection and wildcards are prohibited.

## Future activation

Do not activate until an HTTPS API hostname, TLS, migrations, health, CORS, and security acceptance are confirmed. The future public configuration shape is:

```javascript
window.VISIT_LIBYA_CONFIG = Object.freeze({
  apiBaseUrl: "https://CONFIRMED-API-ORIGIN/api/v1",
  apiEnabled: true,
  debug: false,
  requestTimeoutMs: 10000,
  deploymentEnvironment: "production",
  siteBasePath: "/visitlibya/",
  defaultLocale: "en"
});
```

This is documentation, not active configuration. The committed frontend remains in static mode. The API must use HTTPS, curated destination fallback must remain available, and the controlled Pages release workflow must be rerun and verified after activation.
