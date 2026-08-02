# Frontend release checklist

Release: __________  Commit: __________  Date: __________  Public origin: __________

## Code and artifact

- [ ] Branch/commit and clean diff reviewed; no backend or media rename changes.
- [ ] Node syntax, frontend validator, static smoke suite, artifact build, and artifact validator pass.
- [ ] Artifact contains only approved HTML, `ar/`, assets, `imges/`, `panel/`, public config, 404, robots, sitemap, `.nojekyll`, and release manifest.
- [ ] No backend, docs, scripts, CI source, environment examples, Office/source documents, symlinks, TIF/TIFF, secrets, private data, localhost, or internal hosts are present.
- [ ] Static config remains `apiEnabled: false`, empty API URL, and `deploymentEnvironment: "static"` unless separately approved backend/CORS work is complete.

## Content, language, images, accessibility

- [ ] English/Arabic parity, navigation labels, official content, RTL/LTR, headings, and unavailable states reviewed.
- [ ] Local Libyan images resolve with exact case; crops are undistorted; alt text is appropriate.
- [ ] Keyboard navigation, skip links, visible focus, mobile menu, disabled forms, reduced motion, and no-JavaScript fallback manually reviewed.
- [ ] No broken links/fragments, default blue links, horizontal overflow, or console errors.

## Metadata and legal

- [ ] Titles/descriptions are accurate; core pages index; account/trip/AI demo pages are `noindex,follow`.
- [ ] Confirmed HTTPS origin and `/visitlibya/` appear correctly in canonical, hreflang, social metadata, sitemap, and robots sitemap directive.
- [ ] 404 is bilingual, accessible, backend-free, and noindex; unknown-path recovery links work.
- [ ] Ministry/Tourism Information & Documentation Center names remain footer-only.
- [ ] Privacy, terms, accessibility, contact, copyright, external-link, data fallback, and AI disclaimer content has official/legal approval or is explicitly deferred; no claims are invented.
- [ ] No cookie or analytics claim is made unless the implementation and approved policy exist.

## Release control and post-release evidence

- [ ] Pages source is GitHub Actions; `github-pages` environment protection/approval is configured as required.
- [ ] Manual workflow input and selected commit independently reviewed; no automatic push deployment exists.
- [ ] Home EN: ______  Home AR: ______  404: ______  robots: ______  sitemap: ______
- [ ] 26-page HTTP/content check: ______  asset/case check: ______  console/network check: ______
- [ ] Cache/private-window check: ______  metadata inspection: ______  static API-disabled check: ______
- [ ] Rollback commit identified: ______  rollback criteria reviewed: ______

Technical validation sign-off: __________  Content sign-off: __________  Legal sign-off: __________  Release sign-off: __________
