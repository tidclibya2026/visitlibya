# Visit Libya visual QA report

## Scope and evidence

This phase resumed from commit `08170ae` on `feature/visual-qa-precision-fixes`. Human inspection was completed against the 189 before screenshots and labeled contact sheets stored outside the repository. Confirmed defects VQ-001 through VQ-004 were corrected and verified with 189 after screenshots in Microsoft Edge 151.0.4129.59.

Routes covered 14 English pages and 13 Arabic pages at 1440×1000, 1280×900, 1024×900, 768×900, 430×900, 390×844, and 360×800.

## Confirmed defects and corrections

### VQ-001 — English desktop header overflow

Before, the seven legacy editorial pages measured 1280px client width, 1402px scroll width, and 122px horizontal overflow in the complete capture report. Detailed scrollbar-aware diagnostics measured 1265px client width, 1402px scroll width, and 137px overflow.

Root selectors in `style.css` were `.vl-topbar`, `.vl-nav`, and `.vl-language`: fixed grid tracks, 76px padding, a fixed 46px navigation gap, and no shrink floor displaced the language switch.

The correction uses a 100%-wide shrink-safe header, `minmax(0,1fr)` for navigation, responsive gaps/padding, and a non-absolute language switch with `margin-inline-start:auto`.

After, every affected 1280×900 capture measures 1280px client width and 1280px scroll width (zero overflow). Intentional 1.02 hero overscan remains unchanged and clipped.

### VQ-002 — Arabic AI mobile displacement

Before, `ar/ai.html` at 360×800 measured 360px client width and 372px scroll width.

The legacy skip link was first removed from RTL root flow using fixed, focus-revealed positioning. The remaining owning component was the AI `.chat-form` grid: its `1fr auto` track retained the input min-content width. The correction uses `minmax(0,1fr)`, `min-width:0`, and a 100%-wide input.

After measurements are 430/430, 390/390, and 360/360, with zero overflow.

### VQ-003 — Header logo optical size

The approved `visitlibyalogo.png` remains unchanged at 544×459. Rendered sizes changed:

| Evidence | Before | After |
|---|---:|---:|
| English/Arabic desktop 1440 | 42×35.4 | 52×43.9 |
| English desktop 1280 | 42×35.4 | 51.2×43.2 |
| English/Arabic mobile 430 | 36×30.4 | 42×35.4 |

The logo retains natural height, `object-fit:contain`, and its intrinsic aspect ratio. Header height did not increase on mobile.

### VQ-004 — Destination QA loading state

The external QA server originally omitted JavaScript MIME types, preventing module-driven destination pages from resolving. The external harness now serves correct static MIME types and polls for populated `#destinationTitle` with visible `#destinationContent`, or an explicit not-found/error state, for at most ten seconds. A timeout becomes a recorded capture failure.

All 14 destination-detail matrix captures resolved; no production delay or application behavior changed.

## Evidence names

Before evidence remains under `VisitLibya-Visual-QA/before-screenshots`. After evidence is under `after-screenshots`, with viewport-prefixed filenames such as:

- `1280x900__experiences.html.png`
- `1280x900__heritage.html.png`
- `360x800__ar__ai.html.png`
- `1280x900__destination.html_slug-tripoli.png`
- `390x844__ar__destination.html_slug-tripoli.png`

After contact sheets include seven viewport sheets plus `header-and-logo-after.png`, `English-overflow-pages-after.png`, `Arabic-AI-mobile-after.png`, `destination-details-after.png`, and `focused-fixes-after.png`.

## Objective results

- Before screenshots: 189
- After screenshots: 189
- After capture failures/timeouts: 0
- After horizontal-overflow cases: 0
- Required local asset failure cases: 0
- Console-error cases: 0
- Destination resolved captures: 14
- Image files changed: none
- Heritage grid changed: no
- API state changed: no
- Deployment performed: no

## Remaining review

Release-owner visual approval remains pending. The existing external Google Fonts dependency and thirteen oversized-source-image warnings remain non-blocking and unchanged.

