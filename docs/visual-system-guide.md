# Visit Libya visual system guide

## Purpose and identity

Visit Libya uses a tourism-first, cinematic visual language built around Mediterranean blue (`#0B3A67`), desert gold (`#C89B3C`), oasis green (`#2E7D5B`), heritage red (`#8C2F22`), snow white (`#F8FAFC`), and charcoal (`#111827`). Visual refinement must preserve authentic local photography and bilingual semantic parity.

## Tokens

Shared tokens cover brand and semantic colors, Latin and Arabic font stacks, a responsive text scale, line heights, spacing, content widths, radii, shadows, motion, header height, and the focus ring. Use existing tokens before introducing one-off values. Responsive display headings may use `clamp()`; ordinary controls should use stable token values.

## Typography

English uses `"Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif`. Arabic uses `"Cairo", "Noto Sans Arabic", Tahoma, Arial, sans-serif`. Body copy should stay near 60–75 characters per line. Arabic paragraphs use a more relaxed line height and headings, navigation, and buttons do not use letter spacing.

The single Google Fonts import uses `display=swap` and only the weights already used by the interface. It remains a non-blocking availability/privacy dependency. No approved local font files are present; system fallbacks preserve readability if the provider is unavailable.

## Spacing, radii, shadows, and motion

Use the shared spacing scale from `--space-1` through `--space-24`, the named radius tokens, and card/navigation/modal elevation tokens. Hover movement remains subtle. Focus must remain visible, and reduced-motion preferences must reduce transitions and animations.

## Image presentation

- `.media-hero`: controlled hero crop with `object-fit: cover`; use a page-specific position only when the photograph requires it.
- `.media-card`: stable card crop with `object-fit: cover`.
- `.media-editorial` and `.media-natural`: full image visibility with `width: 100%`, `height: auto`, `max-height: none`, and `object-fit: contain`.
- `.media-logo`: contained brand artwork without distortion.
- Gallery crops may use cover when the grid requires consistent cells; documentary/editorial images must retain their natural composition.

Keep intrinsic width/height, lazy loading, async decoding, and justified hero priority. Never impose one global fixed height or object position on all photographs. The heritage grid remains 3+2 on desktop, two columns on tablet, and one column on mobile.

## Heroes, cards, and responsive behavior

Heroes use readable overlays, bounded copy widths, and shorter mobile viewport sizing. Card families share radius, shadow, focus, and restrained transition behavior while keeping their established image ratios. Test LTR and RTL at 1440, 1280, 1024, 768, 430, and 360 pixels.

## Logo and icons

`visitlibyalogo.png` (544×459, transparent PNG) is the approved header mark. It is displayed at natural aspect ratio inside a bounded header area and is decorative within an already accessible home link. `favicon.png` (64×64, transparent PNG) remains the approved favicon on every public page. No ICO, Apple touch, 192px, or 512px derivatives were created because no trusted local conversion tool was available; future derivatives must be made from these approved assets without stretching or redesign.

## Accessibility and future pages

Maintain meaningful alt text for content imagery, empty alt only for decorative images, visible focus, keyboard-accessible navigation, sufficient contrast, useful landmarks, logical headings, and reduced-motion support. New pages must use the shared tokens and media roles, correct language-specific homepage logo link, project-relative assets, and exact filename case.

## Known limitations

The external font dependency and thirteen oversized source photographs remain documented non-blocking warnings. No photograph was recompressed, replaced, renamed, or deleted in this phase. Browser screenshot review is recorded separately only when an installed browser was actually used.


## Precision header and RTL width rules

Shared headers must use a 100%-wide, shrink-safe grid. Central navigation uses `min-width: 0`, `max-width: 100%`, responsive gaps, and a `minmax(0, 1fr)` track. Language switches remain normal-flow, non-shrinking items placed with logical auto margin; they must never be absolutely positioned to compensate for width pressure.

The approved non-square logo uses natural height, `object-fit: contain`, and responsive width: moderately larger on desktop and compact on mobile without increasing header height. RTL form grids use `minmax(0, 1fr)`, and form controls use `min-width: 0` and `max-width: 100%` where intrinsic sizing could displace the page.

## Responsive photography rule

Use measured, layout-derived sizes values with ascending WebP width candidates. Preserve original intrinsic dimensions and fallback, existing object-fit/object-position, and hero composition. When the same source appears as hero and first gallery item, align candidate selection to avoid a duplicate transfer.
