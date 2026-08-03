# Visit Libya release artifact guide

## Purpose

This guide describes deterministic preparation and validation of the allowlisted static GitHub Pages artifact. The work began from commit `b840a7d90f17814f90f5fbb941a87422db9e44da`. It does not deploy, publish Pages, create a release, select a custom domain, modify DNS, or activate the API.

## Public artifact scope

`config/pages-artifact-allowlist.json` is authoritative. The builder includes the manifest-declared English and Arabic HTML pages; `.nojekyll`; bilingual `404.html`; `robots.txt`; root CSS and JavaScript; frontend runtime and page configuration; approved CSS and browser JavaScript trees; an exact 53-file referenced/representative-media allowlist; logo and favicon. `sitemap.xml` is generated only when an approved origin is explicitly supplied. `release-manifest.json` is always generated.

CSS/JavaScript tree rules are limited by directory and extension, while media files are individually enumerated. Filename case, spaces, and Arabic filenames are preserved. Source symlinks are rejected rather than followed.

## Excluded content

The artifact excludes `.git`, `.github`, backend code, deployment sources, documentation, scripts, tests, virtual environments, `node_modules`, caches, environment files, logs, screenshots, archives, office documents, source maps, repository metadata, and untracked files outside the allowlist. No CNAME is created or copied.

## Preview build

```powershell
node scripts/build-pages-artifact.mjs
node scripts/validate-pages-artifact.mjs
node scripts/smoke-test-static-site.mjs --root .pages-artifact
```

The default ignored output is `.pages-artifact`. A preview build omits `sitemap.xml`, canonical links, and `og:url`, and prints that it is not a production SEO artifact.

## Production-origin build template

Use only after the release owner approves the exact public HTTPS origin:

```powershell
$env:SITE_ORIGIN = "<APPROVED_HTTPS_ORIGIN>"
node scripts/build-pages-artifact.mjs
node scripts/validate-pages-artifact.mjs
node scripts/smoke-test-static-site.mjs --root .pages-artifact
```

`--site-origin` is an equivalent explicit input. There is no default domain and no inference from repository names.

## SITE_ORIGIN validation

The value must be an absolute HTTPS origin with no credentials, path, query, or fragment. Localhost, loopback, link-local, RFC1918 IPv4 ranges, `.test`, and `.invalid` hosts are rejected. A trailing root slash is normalized by the URL parser. Unsafe origins are rejected before output cleanup.

## Canonical, hreflang, and sitemap behavior

With an approved origin, artifact copies of indexable static pages receive exactly one canonical link, matching `og:url`, absolute English/Arabic/x-default hreflang values, and absolute social-image metadata. The sitemap uses the same origin and `/visitlibya/` project base. `robots.txt` receives the matching sitemap URL. Source HTML is never modified by injection. Noindex AI/account/trip pages and `404.html` remain noindex and origin-neutral.

### Dynamic destination strategy

`destination.html` and `ar/destination.html` depend on a query-string slug. A single build-time generic canonical would collapse distinct destinations incorrectly. They are therefore excluded from sitemap and production metadata injection. Their source-relative language links remain intact. Full destination SEO requires approved slug-specific prerendered URLs or request-aware runtime metadata before those records can enter the sitemap.

## Artifact manifest

`release-manifest.json` contains schema version, UTC build timestamp, 40-character source commit, project base path, release-origin status (`supplied` or `not-supplied`), payload file count, payload bytes, and a sorted entry for every payload file containing its relative path, bytes, and SHA-256. It contains no workstation path, Git remote, user identity, or credential. The manifest does not hash itself because a self-hash is not mathematically stable; every other public artifact file is covered.

The timestamp may differ between builds. For identical source and origin options, payload file lists, bytes, and SHA-256 entries must match exactly.

## Local verification

1. Run source validation and the 67 source smoke tests.
2. Build the preview artifact twice and compare manifests after omitting only `buildTimestampUtc`.
3. Run artifact validation and `node scripts/smoke-test-static-site.mjs --root .pages-artifact`.
4. Inspect the artifact top level against the allowlist and confirm forbidden directories are absent.
5. Search public text for populated secrets, private endpoints, workstation paths, source-map references, and merge markers.
6. Confirm `apiEnabled: false`, `apiBaseUrl: ""`, and `deploymentEnvironment: "static"` inside the artifact.

## GitHub Actions handoff

`.github/workflows/release-artifact-validation.yml` validates preview artifacts on pull requests, selected pushes, and manual runs. It has `contents: read` only and cannot deploy. `.github/workflows/pages-release.yml` remains manual-only, accepts an explicit origin, builds and validates before upload, separates the read-only build job from the Pages/id-token deploy job, restricts deployment to `main`, uses concurrency protection, and binds deployment to the `github-pages` environment.

## Pages prerequisites

Before dispatching any deployment, approve the public origin, Pages source, custom-domain decision, HTTPS/certificate state, environment protection rules, required GitHub Actions results, canonical strategy, artifact manifest archive, and rollback commit. Confirm that the selected origin and `/visitlibya/` base path describe the real public route.

## Rollback

Record the exact deployed source commit and artifact manifest. If validation or launch fails, redeploy the last approved immutable Pages artifact/commit through the controlled workflow; do not rewrite history. Re-run artifact validation, artifact smoke tests, and 404/project-subpath checks before rollback approval.

## Known warnings

The external Google Fonts dependency and thirteen oversized original photographs remain the fourteen documented non-blocking warnings. Source photographs are unchanged. The production origin, custom-domain decision, and destination prerendering strategy remain operational/product decisions.

## Non-deployment statement

This phase prepares and validates artifacts only. It does not deploy, publish GitHub Pages, create a GitHub release, change DNS, create a CNAME, or enable backend/API behavior.