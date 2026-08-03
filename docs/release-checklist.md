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
