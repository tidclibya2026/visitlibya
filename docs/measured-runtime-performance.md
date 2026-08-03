# Measured runtime performance

## Scope and starting point

This phase measures non-image frontend delivery from starting commit `d432ce9` on `feature/measured-runtime-performance`. It covers CSS, the external web-font dependency, JavaScript scope, main-thread work, layout shift, local interaction behavior, and the deterministic Pages artifact. It does not redesign pages, alter images, change content, enable the API, supply `SITE_ORIGIN`, deploy, or claim production Core Web Vitals.

## Environment and methodology

- Browser: Microsoft Edge `151.0.4129.59`, headless through Chrome DevTools Protocol (CDP).
- Node.js: `v22.16.0`.
- Lighthouse: not installed; no Lighthouse scores or terminology are used.
- Server: loopback, ephemeral port, `/visitlibya/` project subpath, correct static MIME types.
- Cache: disabled and cleared before every navigation; service workers bypassed.
- Matrix: 28 English/Arabic routes, seven DPR-1 viewports (1440, 1280, 1024, 768, 430, 390, and 360 CSS pixels), plus 430 and 1440 at DPR 2. Source and artifact each produced 252 records before and after.
- Readiness: `load` plus a destination terminal state; synthetic menu, filter, and safe field interactions ran where controls existed.
- Observers: LCP, layout shift, long task, and Event Timing where Edge exposed entries. Performance domain timings, request bytes, JS precise coverage, CSS rule usage, failures, console errors, and overflow were also collected.
- Repeated comparisons: three cold runs for English home mobile, Arabic home mobile, destinations mobile, Benghazi detail mobile, English home desktop, and Arabic home desktop.

These are local comparative laboratory measurements, not production field LCP, CLS, or INP.

## Untouched baseline

The source validator passed 15 sections across 26 pages with 14 warnings. Source smoke tests passed 67/67. The Pages artifact contained 152 payload files and 127,814,418 bytes; artifact validation and 67/67 artifact smoke tests passed.

Across the 252-case source baseline, CDP recorded 4,964 requests, 440,238,163 transferred bytes, 12,489,087 CSS bytes, 13,155,678 JavaScript bytes, and 14,251,401 font bytes. There were zero failed local requests, zero console errors, and zero horizontal-overflow cases.

## CSS inventory and coverage limits

Nine public CSS files total 105,041 source bytes:

| File | Bytes | Role |
|---|---:|---|
| `style.css` | 31,455 | legacy/shared shell, heroes, broad page components |
| `assets/css/design-system.css` | 3,388 | shared tokens |
| `assets/css/base.css` | 2,605 | shared base and language typography |
| `assets/css/layout.css` | 7,144 | shared layout |
| `assets/css/components.css` | 6,082 | shared components |
| `assets/css/home.css` | 17,796 | home family |
| `assets/css/destinations.css` | 12,841 | listing family |
| `assets/css/destination-details.css` | 9,720 | detail family |
| `assets/css/trips.css` | 14,010 | registration/trips family |

CDP rule-usage tracking covered all routes, viewports, and the scripted interactions. It confirmed that modular pages load overlapping legacy/shared layers, but stylesheet IDs were not reliably attributable to filenames in the captured protocol stream. Coverage therefore remains approximate and was not used to delete selectors. Focus, hover, reduced-motion, error, unavailable, generated-card, and dynamic states also make static “unused CSS” unsafe evidence. No CSS was removed or reordered.

## Font baseline and decision

`style.css` contains one Google Fonts request for Cairo weights 400/700/800/900 and Inter weights 400/600/700/800/900 with `display=swap`. English and Arabic retain robust system fallback stacks.

With external fonts available, a typical English navigation transferred about 48.3 KB of fonts and an Arabic navigation about 64.8 KB. In the 252-case blocked-font matrix, font transfer was zero, there were no local failures, console errors, or overflow cases, and fallback text remained rendered. The dependency is still an availability and privacy consideration.

A direct document-level stylesheet/preconnect trial was rejected: two full matrices stalled during provider slowness. The original single `display=swap` import was restored. No fonts were downloaded, bundled, removed, or moved to another provider.

## JavaScript inventory and evidence

The repository has 32 public JavaScript files after the change, totaling 210,168 bytes in the audited `main.js` and `assets/js` scope. Modules for destination listings/details, responsive image metadata, authentication, trips, and page controllers remain page-specific. The repeatable waste was in `main.js`: 14,735 bytes of bilingual AI response/controller logic were transferred to every page while only `ai.html` and `ar/ai.html` expose the AI UI.

### Applied change RTP-001

The AI-only block was moved without content changes to `assets/js/pages/ai.js`. Only English and Arabic AI pages load it; `main.js` retains shared navigation, slideshow, filtering, image fallback, and gallery behavior. This avoids dynamic import complexity and preserves deterministic static behavior.

- `main.js`: 21,650 bytes before; 7,086 bytes after.
- `assets/js/pages/ai.js`: 14,735 bytes, loaded only by two AI pages.
- Non-AI route saving: 14,565 JavaScript transfer bytes per cold navigation.
- AI routes: one additional page-specific request with essentially unchanged total logic.

## Before/after aggregate delivery

| Metric, 252 source cases | Before | After | Change |
|---|---:|---:|---:|
| JavaScript transfer | 13,155,678 B | 9,753,804 B | −3,401,874 B (−25.9%) |
| Total transfer | 440,238,163 B | 436,837,065 B | −3,401,098 B (−0.77%) |
| CSS transfer | 12,489,087 B | 12,487,570 B | effectively unchanged |
| Font transfer | 14,251,401 B | 14,252,263 B | normal provider variance |
| Requests | 4,964 | 4,982 | +18, one extra request on each AI case |
| Failed local requests | 0 | 0 | unchanged |
| Console errors | 0 | 0 | unchanged |
| Horizontal overflow cases | 0 | 0 | unchanged |

Aggregate long-task count changed from 43 to 47 and duration from 2,731 ms to 3,118 ms. Those tasks were not repeatedly attributable to the extracted AI logic; font/network and headless-browser variation dominated. No long-task optimization claim is made.

## Three-run critical medians

| Case | JS before → after | Local LCP before → after | CLS before → after | Script duration before → after |
|---|---:|---:|---:|---:|
| English home, 430 | 32,506 → 17,941 B | 196 → 180 ms | 0 → 0 | 1.87 → 1.96 ms |
| Arabic home, 430 | 32,506 → 17,941 B | 208 → 180 ms | 0 → 0 | 2.27 → 2.34 ms |
| Destinations, 430 | 73,330 → 58,765 B | 156 → 164 ms | 0 → 0 | 5.79 → 5.75 ms |
| Benghazi detail, 430 | 71,431 → 56,866 B | 204 → 180 ms | 0 → 0 | 2.79 → 2.98 ms |
| English home, 1440 | 32,506 → 17,941 B | 572 → 540 ms | 0.00238 → 0.00238 | 23.33 → 19.05 ms |
| Arabic home, 1440 | 32,506 → 17,941 B | 308 → 296 ms | 0.00827 → 0.00828 | 2.20 → 1.96 ms |

The consistent transfer reduction is the decision evidence. Millisecond changes are reported without claiming significance where local variance can explain them.

## CLS, long tasks, and interaction responsiveness

Destination detail ready-state transitions produced the largest individual desktop CLS observations, but values varied between cold runs and were not caused by the AI extraction. A global fixed height or speculative placeholder was rejected because it risks responsive and bilingual regressions. Existing intrinsic image dimensions remain intact.

Synthetic interactions completed without console errors or failed assets. CDP Event Timing did not consistently expose trusted interaction entries for programmatically triggered actions, so no field-INP claim is made. Menu, filter, safe input, destination resolution, unavailable states, and AI-controller presence were verified as functional checks; script duration and long-task observations remain the local responsiveness proxies.

## Visual and functional regression

Before/after screenshots were captured outside the repository for 28 routes at 1440×1000, 768×900, 430×900, and 360×800. Eight bilingual before/after contact sheets were generated and representative mobile/desktop sheets inspected. Font rendering, wrapping, header/logo, heroes, cards, forms, unavailable states, mobile navigation, RTL, and footer layout remained visually equivalent. No FOUC, missing styling, image change, or horizontal overflow was observed.

## Artifact effect and reproducibility

The final artifact contains 153 payload files and 127,814,746 bytes. Compared with baseline, this is one additional page-specific controller and +328 payload bytes overall because the same AI logic moved rather than disappeared. Runtime delivery improves on 24 non-AI pages despite the negligible stored-artifact increase. The artifact remains origin-neutral and excludes QA evidence.

Two final builds produced the same payload selection and content hashes apart from the intentional manifest timestamp (see validation record). Images and responsive mappings were unchanged.

## Validator guards

The validator now rejects duplicate stylesheet paths, duplicate script paths, an AI controller loaded outside the two AI pages, a missing AI controller on those pages, unapproved Google font families/weights, a font request without `display=swap`, and blocking classic scripts newly placed in a document head. Existing API, origin-neutrality, media, path-case, and artifact rules remain intact.

## Deferred opportunities

- CSS consolidation: defer until stylesheet-to-rule coverage attribution includes all dynamic, focus, print, reduced-motion, and error states.
- Font policy: self-hosting requires separately approved, licensed font files; removing approved web fonts requires owner approval.
- Destination ready-state CLS: investigate with a repeatable component-level trace before reserving space.
- Bundling/minification: not justified for this static architecture and would reduce source reviewability.

## Rollback

Revert the AI page script tags, restore the AI block to its original position in `main.js`, remove `assets/js/pages/ai.js`, and revert the associated validator/documentation changes. Re-run source and artifact validation and all 67 smoke tests.

No deployment, push, API activation, DNS change, `SITE_ORIGIN`, CNAME, image modification, or production configuration change occurred in this phase.
