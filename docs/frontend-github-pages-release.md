# Visit Libya GitHub Pages release

## Architecture and publication decision

Visit Libya is published as a static, sanitized artifact. FastAPI, PostgreSQL, migrations, tests, Office sources, documentation, CI sources, and environment examples are not website assets and must never enter the Pages artifact. The existing validation workflow remains validation-only. `.github/workflows/pages-release.yml` is a separate, manual `workflow_dispatch` release using only official GitHub Pages actions.

Branch-root publication is unsafe because the repository contains backend and source material. Automatic push deployment is intentionally disabled. `.nojekyll` makes asset handling predictable and prevents Jekyll processing.

## Build and validate locally

Use Node.js 22; no packages are installed.

```text
node scripts/validate-frontend.mjs
node scripts/smoke-test-static-site.mjs
node scripts/build-pages-artifact.mjs
node scripts/validate-pages-artifact.mjs
```

A no-origin build intentionally has no sitemap, canonical, absolute hreflang, `og:url`, or absolute social image metadata. For release metadata, supply the confirmed HTTPS origin without a path:

```text
node scripts/build-pages-artifact.mjs --site-origin https://confirmed-origin.example
node scripts/validate-pages-artifact.mjs
```

The base path `/visitlibya/` comes from `config/frontend-pages.json`. Never guess the origin, place credentials in it, or put tokens, database URLs, private data, or backend secrets in public frontend config.

## GitHub UI prerequisites and manual release

1. Obtain approval for the public origin, legal/footer content, and release checklist.
2. In repository Settings > Pages, select **GitHub Actions** as the source. Do not use Deploy from a branch.
3. Configure protection/required reviewers for the `github-pages` environment where governance requires it.
4. Open Actions > Manual GitHub Pages release > Run workflow.
5. Select the reviewed commit/branch and enter the confirmed HTTPS origin, excluding `/visitlibya/`.
6. Review validation and environment approval before allowing the deploy job to finish.

Running the workflow is a separate human publication action and was not performed during implementation.

## Live verification

Verify `/visitlibya/`, `/visitlibya/ar/`, all 26 manifest pages, curated destination query pages, `404.html`, an unknown URL, assets with spaces/Unicode/case, `robots.txt`, and `sitemap.xml`. Check browser console/network for errors and confirm static mode makes no API requests. Inspect canonical/hreflang/social URLs and ensure they contain the confirmed origin and repository path.

## Cache refresh

GitHub Pages cache headers are not controlled here. When shared CSS, JavaScript, or runtime config changes, update affected query-string versions consistently across English and Arabic pages, publish a reviewed artifact, test a private-window hard refresh, and allow CDN propagation. Do not add a service worker for this release.

## Backend and CORS later

GitHub Pages cannot run FastAPI or PostgreSQL. A future API needs separate HTTPS hosting, managed secrets, migrations, monitoring, and an exact CORS allowlist containing the final Pages origin. Only then update `config/frontend-config.js` through a reviewed release: set the HTTPS API URL and enable it. Never expose credentials, JWT secrets, database URLs, internal hosts, or privileged keys in frontend config.

## Rollback

Stop rollout when critical navigation/assets fail, Arabic parity breaks, unintended files are public, metadata uses the wrong origin, API requests occur in static mode, or a privacy/security issue appears. Disable/cancel the active run if still pending. Identify a previously validated commit, run the same manual workflow for that commit with the same confirmed origin, approve the protected environment, and verify the live checks again. If exposure is suspected, disable Pages in repository Settings while incident handling proceeds; disabling is a manual owner action.

## Deferred approvals

No privacy policy, terms, accessibility statement, cookie/analytics claim, official contact details, custom domain, or production API domain is invented. Obtain official legal/content approval before adding those items. Structured data is deferred until the public origin and official organization facts are confirmed. Curated query-string destination URLs are not in the sitemap until per-slug canonical URLs can be represented reliably; dedicated destination URLs are a future option.
