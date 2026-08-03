# Visit Libya public release readiness

## Release candidate scope

This audit covers the static bilingual public frontend at starting commit `95a4806`, its GitHub Pages project-subpath behavior, visitor journeys, accessibility, browser presentation, public metadata, security/privacy exposure, and release controls. It does not authorize a deployment, domain change, API activation, release publication, commit, or push.

## Public page inventory

All listed pages have a unique title and description, a local favicon, Open Graph and Twitter summary metadata, relative assets, consistent tourism navigation/footer treatment where the site shell applies, and responsive CSS. English pages use `lang="en" dir="ltr"`; Arabic pages use `lang="ar" dir="rtl"`. Each bilingual pair uses relative `en`, `ar`, and `x-default` hreflang links. Source canonical and `og:url` values are intentionally absent until the public origin is approved.

| English / Arabic page | Purpose and primary media | Runtime / page JavaScript | Release status |
|---|---|---|---|
| `index.html` / `ar/index.html` | Home; inline Sahara hero | site shell, home controller, legacy UI | Ready |
| `destinations.html` / `ar/destinations.html` | Curated destination listing; coast hero | runtime config, site shell, destinations controller | Ready with static curated fallback |
| `destination.html` / `ar/destination.html` | Destination detail/gallery; record-selected hero | runtime config, site shell, detail controller | Ready with curated fallback and slug-preserving switch |
| `experiences.html` / `ar/experiences.html` | Experience editorial; Acacus hero | legacy UI | Ready |
| `culture.html` / `ar/culture.html` | Culture and cuisine editorial | legacy UI | Ready |
| `heritage.html` / `ar/heritage.html` | Heritage editorial and five-card World Heritage grid | legacy UI | Ready; desktop 3+2 behavior retained |
| `plan.html` / `ar/plan.html` | Trip-planning guidance; coast hero | legacy UI | Ready |
| `services.html` / `ar/services.html` | Entry/service guidance; architecture hero | legacy UI | Ready; external official links protected |
| `atlas.html` / `ar/atlas.html` | External atlas gateway; nature hero | legacy UI | Ready; atlas remains an external launcher |
| `ai.html` / `ar/ai.html` | Clearly identified AI demonstration | legacy UI | Ready as noindex demonstration |
| `register.html` / `ar/register.html` | Registration form | runtime config, site shell, register controller | Ready as noindex unavailable state; no simulated success |
| `trips.html` / `ar/trips.html` | Saved-trips/sign-in surface | runtime config, site shell, trips controller | Ready as noindex unavailable state |
| `trip.html` / `ar/trip.html` | Trip editor | runtime config, site shell, trip editor | Ready as noindex unavailable state |
| `404.html` | Bilingual recovery page | inline project-base recovery logic | Ready and noindex |

Total: 27 public HTML files (13 bilingual pairs plus one bilingual 404 page).

## GitHub Pages project-subpath findings

The configured project base is `/visitlibya/`. Static pages, CSS, JavaScript modules, curated data, images, favicons, query strings, fragments, language switches, and destination slugs resolve using relative references. No genuine root-relative `href`, `src`, CSS `url()`, dynamic import, or public fetch defect was found. The 404 script intentionally chooses `/visitlibya/` only when the current pathname is under that project path and otherwise falls back to `/`; this is recovery logic, not a broken asset reference. Spaces, case-sensitive filenames, percent-encoded paths, and the Arabic WebP path remain validated. No Windows filesystem path is exposed.

## Production-origin decision

An explicit HTTPS origin is required only when producing release canonical metadata and the generated sitemap. It remains unknown and must not be guessed. Supply the approved origin as `SITE_ORIGIN` or `--site-origin` to `scripts/generate-sitemap.mjs`; use the same origin during release metadata injection and keep the manifest base path aligned with the actual Pages location. Source HTML, hreflang links, and `robots.txt` remain origin-neutral. No canonical or `og:url` points prematurely to `visitlibya.ly`.

## Navigation journeys

- A: Home → Destinations → destination details → language switch → destinations resolves in both languages; valid slugs are preserved.
- B: Home → Experiences → Culture → Heritage resolves in both languages with matching page purposes.
- C: Home → Atlas → external atlas link resolves structurally; external availability was not network-tested.
- D: Home → Plan → Trips → Trip details has no dead end; trips/editor surfaces clearly retain API-disabled behavior.
- E: Home → Services → Register resolves; registration remains unavailable instead of simulating success.

The static smoke suite verifies every internal public link under `/visitlibya/`, destination switches, 404 behavior, and API-disabled states. No redirect-loop mechanism or console-blocking local-script failure was found.

## Accessibility findings

All public pages now expose exactly one source-level `h1`. Loading, missing, and unavailable destination state headings were conservatively demoted to `h2` without changing their text. Static content page pairs now use the existing visible-on-focus skip-link pattern and `mainContent` target. Forms retain explicit labels, validation descriptions, and accessible buttons. Navigation and language switches have labels; dialogs and expanded-state controls retain their existing semantics. No duplicate IDs or positive `tabindex` values were found. Focus-visible and reduced-motion CSS are present. Empty image alt remains limited to decorative or dynamically populated destination hero images. Automated review cannot certify every color combination; visual contrast remains a manual release sign-off item.

## Security and privacy findings

No credential, token, API key, populated secret, password value, private endpoint, internal filesystem path, mixed-content public resource, tracker, or unknown form endpoint was found in public runtime files. Runtime localhost strings implement defensive rejection and local-test behavior; the example config and documentation examples are not production runtime values. External `_blank` links now require both `noopener` and `noreferrer`. The API client uses controlled request construction; reviewed `innerHTML` usage is limited to existing curated/static rendering paths and is not fed by enabled public API data in static mode. Three informational `console.log` statements in `main.js` contain version labels only and no sensitive data.

Repository HTML cannot provide platform HTTP headers. HTTPS enforcement, HSTS, CSP, `X-Content-Type-Options`, frame policy, referrer policy headers, Pages source selection, custom-domain verification, certificate health, and repository/environment permissions require GitHub Pages or hosting configuration review.

## Browser and responsive findings

Microsoft Edge is available locally. The site was exercised through a loopback server using the `/visitlibya/` project path at 1440×1000, 1280×900, 1024×900, 768×900, 430×900, and 360×800. Ninety captures covered English/Arabic home, destinations, destination detail, heritage, plan, trips, register, and the bilingual 404 route, with no Edge render-process failure. The local image-inspection bridge could not open the generated contact sheets, so this audit does not claim human visual approval; final visual review of overflow, alignment, image treatment, RTL coherence, footer layout, and controls remains a release-owner checklist item. Temporary screenshots remain outside the repository.

## Known warnings

- Google Fonts is an external availability/privacy dependency; local fallbacks remain available.
- Thirteen referenced source photographs exceed the documented 2 MB or 5 MB warning thresholds. They remain authentic source photographs and were not modified.
- External atlas, eVisa, and customs destinations were not network-requested during this controlled audit.
- Canonical origin, sitemap origin, HTTPS/custom-domain state, Pages source, and GitHub Actions status require release-owner or hosting verification.

## Launch assessment

Safe for a release candidate: bilingual static pages, curated fallback, project-subpath routing, internal links/assets, language switching, destination slugs, 404 recovery, API-disabled states, runtime configuration, responsive structure, accessibility fundamentals, and repository-level public security checks.

Launch blockers: no repository-code blocker remains. Operational release must stop until the release owner confirms the public origin, Pages source, successful required GitHub Actions checks, HTTPS/custom-domain decision, and acknowledgement of the 14 non-blocking warnings.

## Rollback procedure

1. Record `95a4806` as the last stable pre-audit commit.
2. Before any later deployment, record the exact deployed commit and artifact identity.
3. If launch validation fails, select the last approved artifact/commit through the documented GitHub Pages workflow; do not rewrite branch history.
4. Re-run frontend validation, static smoke tests, project-subpath checks, and 404 checks against the rollback candidate.
5. Restore DNS or custom-domain settings only through an independently approved hosting change; this repository audit does not authorize it.

## Final pre-launch checklist

Use `docs/release-checklist.md`. Every operational item must be checked by the responsible release owner immediately before launch; unchecked origin, Pages, Actions, HTTPS, or rollback items block production publication but do not block preparing this release candidate.
