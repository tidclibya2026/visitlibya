# Visit Libya release checklist

- [ ] Main is synchronized with the approved release commit.
- [ ] Working tree is clean before the release action.
- [ ] Frontend validation and static smoke tests pass.
- [ ] Required GitHub Actions checks pass.
- [ ] GitHub Pages source and sanitized artifact are verified.
- [ ] Custom-domain decision is recorded; do not infer a domain.
- [ ] HTTPS status is verified at the selected public origin.
- [ ] Canonical origin is supplied during the release artifact process.
- [ ] Sitemap is generated with the same HTTPS origin and `/visitlibya/` base path where applicable.
- [ ] `robots.txt` remains origin-neutral until the sitemap origin is known.
- [ ] `apiEnabled: false`, `apiBaseUrl: ""`, and `deploymentEnvironment: "static"` are confirmed.
- [ ] The 13 oversized-image warnings are acknowledged.
- [ ] The external Google Fonts availability/privacy dependency is acknowledged.
- [ ] Accessibility checks pass, including headings, skip links, labels, focus, RTL, and reduced motion.
- [ ] English/Arabic navigation and destination-slug parity pass.
- [ ] Desktop, tablet, and mobile layouts are reviewed.
- [ ] The project-subpath 404 recovery behavior is tested.
- [ ] Rollback commit `95a4806` is recorded before launch.
- [ ] No commit, deployment, Pages-setting change, or DNS change occurs without explicit approval.

## Release artifact approval

- [ ] Artifact allowlist reviewed.
- [ ] Artifact manifest archived.
- [ ] Artifact reproducibility passed after excluding only the UTC build timestamp.
- [ ] Source commit matches the artifact manifest.
- [ ] No private or development files are present in the artifact.
- [ ] No populated public secrets or private runtime endpoints are present.
- [ ] `SITE_ORIGIN` is explicitly approved.
- [ ] Canonical and absolute hreflang strategy is approved.
- [ ] Dynamic destination canonical/prerendering strategy is approved.
- [ ] Sitemap is generated from the approved origin and correct project base path.
- [ ] Artifact validation and all 67 artifact smoke tests pass.
- [ ] Deployment workflow permissions, environment protection, and concurrency are reviewed.
- [ ] Deployment remains manual and disabled until explicit operational approval.
## Visual system approval

- [ ] Favicon resolves with exact case on every public page.
- [ ] Approved logo is checked in English and Arabic desktop/mobile headers.
- [ ] English and Arabic typography and fallback stacks are checked.
- [ ] Editorial images show no stretching and card/hero crops remain intentional.
- [ ] Hero crops are reviewed at desktop, tablet, and mobile widths.
- [ ] Mobile visual review is completed at 430 px and 360 px.
- [ ] External-font fallback behavior is accepted.

## Evidence-based visual QA

- [x] Desktop visual QA evidence captured and technically reviewed.
- [x] Tablet visual QA evidence captured and technically reviewed.
- [x] Mobile visual QA evidence captured and technically reviewed.
- [x] Arabic and RTL visual QA completed.
- [x] English visual QA completed.
- [x] Header and logo sizing reviewed.
- [x] Hero overscan confirmed intentional and preserved.
- [x] Image distortion review completed without image-file changes.
- [x] Typography review completed.
- [x] Confirmed horizontal overflow corrected and remeasured.
- [x] Forms and disabled states reviewed.
- [ ] Final release-owner visual approval recorded.

## Measured responsive images

- [x] Cold-cache source performance matrix completed.
- [x] Responsive WebP widths match measured display needs.
- [x] Mobile currentSrc selects smaller candidates.
- [x] Original photograph integrity verified.
- [x] Responsive assets included in artifact allowlist.
- [x] Source and artifact image delivery checks completed.
- [ ] Final release-owner responsive-image approval recorded.

## Measured runtime performance

- [x] Cold-load source and artifact CDP matrices completed.
- [x] CSS rule usage reviewed without unsafe coverage-only deletion.
- [x] External-font available and blocked behavior measured.
- [x] AI-only JavaScript scoped to English and Arabic AI pages.
- [x] Duplicate CSS/script and font-request guards added.
- [x] Local LCP, CLS, long-task, and interaction proxies recorded.
- [x] Runtime visual and functional regression QA completed.
- [ ] Final release-owner runtime-performance approval recorded.
