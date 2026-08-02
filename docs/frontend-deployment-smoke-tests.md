# Frontend deployment smoke tests

This checklist validates the static Visit Libya frontend before and after GitHub Pages publication. It does not deploy FastAPI, PostgreSQL, or any other backend service.

## Automated pre-deployment checks

Run from the repository root:

```text
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
```

PowerShell syntax check, without packages:

```powershell
$files = @(Get-ChildItem assets/js,config,scripts -Recurse -File | Where-Object { $_.Extension -in '.js', '.mjs' }) + @(Get-Item main.js,partials.js)
$files | ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw "Syntax check failed: $($_.FullName)" } }
```

Before publication confirm:

- Pull-request checks are green and `main` contains the intended revision.
- `config/frontend-config.js` still has `apiEnabled: false`, an empty `apiBaseUrl`, and `deploymentEnvironment: "static"`.
- No password, token, key, database URL, private hostname, or other secret is present in frontend files.
- The validator, smoke tests, and JavaScript syntax checks pass from a clean checkout.
- No backend, dependency, generated, or media-renaming change is included unintentionally.

## Post-deployment URL checklist

Set `{SITE}` to the published repository URL, including its project subpath, with no trailing slash. Test at least:

| Area | English URL | Arabic URL |
|---|---|---|
| Home | `{SITE}/index.html` | `{SITE}/ar/index.html` |
| Destinations | `{SITE}/destinations.html` | `{SITE}/ar/destinations.html` |
| Leptis Magna | `{SITE}/destination.html?slug=leptis-magna` | `{SITE}/ar/destination.html?slug=leptis-magna` |
| Unknown destination | `{SITE}/destination.html?slug=unknown-destination` | `{SITE}/ar/destination.html?slug=unknown-destination` |
| Registration | `{SITE}/register.html` | `{SITE}/ar/register.html` |
| Saved trips | `{SITE}/trips.html` | `{SITE}/ar/trips.html` |
| Trip editor | `{SITE}/trip.html?id=1` | `{SITE}/ar/trip.html?id=1` |
| Plan | `{SITE}/plan.html` | `{SITE}/ar/plan.html` |
| Services | `{SITE}/services.html` | `{SITE}/ar/services.html` |
| Experiences | `{SITE}/experiences.html` | `{SITE}/ar/experiences.html` |
| Culture | `{SITE}/culture.html` | `{SITE}/ar/culture.html` |
| Heritage | `{SITE}/heritage.html` | `{SITE}/ar/heritage.html` |
| Atlas launcher | `{SITE}/atlas.html` | `{SITE}/ar/atlas.html` |
| VisitLibya AI demo | `{SITE}/ai.html` | `{SITE}/ar/ai.html` |

Refresh query-string pages directly; do not reach them only through client navigation.

## Manual visual checks

Repeat representative checks at desktop, tablet, and mobile widths.

- Header, desktop navigation, mobile menu, footer, hero media, galleries, destination cards, detail hero, buttons, and focus states render correctly.
- There is no horizontal overflow, stretched image, broken image, default blue link, obscured control, or mixed-language label.
- Arabic pages are right-to-left throughout, with correct alignment, navigation order, icons, cards, forms, and readable Arabic typography.
- English pages remain left-to-right.
- Mobile menus open, close, restore focus, and do not trap or obscure content.

## Developer tools checks

For English and Arabic home, destination listing, destination detail, registration, trips, and trip editor pages:

- Console: no uncaught exception, module load error, or critical accessibility/runtime error.
- Network: no 404/403 assets and no request to `localhost` or `127.0.0.1` in static mode.
- Network: JavaScript modules use a JavaScript MIME type; CSS and JSON use their correct MIME types.
- Network: no mixed-content or CORS errors in static mode.
- Network: cache-busting query strings return the current files after a hard refresh.
- Sources: `config/frontend-config.js` is the expected static-safe revision.

## Functional checks

- Search, filter, sort, clear, and refresh the destination explorer.
- Open several destination cards, including Leptis Magna, and use browser Back.
- Switch English/Arabic on a destination detail and confirm the same `slug` remains in the URL.
- Refresh both destination detail languages with the slug query string intact.
- Confirm an unknown valid slug reaches a visible terminal unavailable state and never remains in loading.
- Confirm registration fields and action are disabled with a localized unavailable message.
- Confirm trips sign-in is disabled with a localized unavailable message.
- Confirm the trip editor shows a localized planner-unavailable state and no infinite loading indicator.
- Confirm no backend request occurs from these pages in static mode.
- Confirm internal header, footer, CTA, back, trip-planner, and atlas links work.
- Confirm external links open a new tab safely where intended.

## Rollback criteria

Treat publication as failed and roll back to the last known-good static revision when any of these occurs:

- English or Arabic homepage is unavailable or unstyled.
- Critical CSS, JavaScript, module, configuration, or image request fails.
- A module is served with an invalid MIME type.
- Static mode sends a request to localhost, loopback, or an unintended API origin.
- Critical internal navigation returns 404.
- Destination listing or known curated destination details fail.
- Registration, trips, or trip editor remains loading instead of showing its unavailable state.
- An unhandled JavaScript exception prevents core navigation or content.
- Technical data, credentials, tokens, private URLs, or raw backend errors are exposed.
- Required CI validation or smoke checks are not green for the published revision.

## Evidence record

| URL | Browser/device | Result | Screenshot/link | Console | Network | Reviewer | Date/time with zone |
|---|---|---|---|---|---|---|---|
|  |  | Pass / Fail |  | Clean / Notes | Clean / Notes |  |  |
|  |  | Pass / Fail |  | Clean / Notes | Clean / Notes |  |  |
|  |  | Pass / Fail |  | Clean / Notes | Clean / Notes |  |  |

Record failures explicitly. Do not mark a deployment successful when console, network, Arabic parity, or backend-unavailable checks were skipped.
