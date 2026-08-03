# Measured responsive image performance

## Scope and baseline

This phase starts from `0dd6570` on `feature/measured-responsive-images`. It measures cold-cache local delivery for 20 bilingual routes across six DPR-1 viewports plus selected DPR-2 mobile and desktop cases (160 records per source/artifact run). Microsoft Edge 151.0.4129.59 was driven through the DevTools Protocol with cache disabled and cleared before each navigation. Results are comparative local laboratory measurements, not production Core Web Vitals.

The untouched baseline passed 15 validator sections across 26 pages with 14 documented warnings and 67/67 source and artifact smoke tests. The preview artifact contained 140 files and 126,248,385 bytes, including 125,639,839 image bytes.

Pillow 12.3.0 with WebP support, `ImageOps.exif_transpose`, LANCZOS, WebP method 6, and the previously approved family quality were used. No dependency was installed.

## Impact ranking and decisions

| Rank | Family/evidence | Classification | Decision |
| ---: | --- | --- | --- |
| 1 | Home `panel/desert.jpg`, 3,362,363 transferred bytes per case and local LCP | High | Use the byte-identical approved Q84 desert family at 768/1280/1920 widths. |
| 2 | Services `architectural-heritage.webp`, 589,834 transferred bytes per case | High | Add Q88 768/1280 candidates; retain 1920 approved maximum. |
| 3 | Arabic atlas `natural-lakes2.webp`, 467,474 transferred bytes per case and local LCP | High | Add Q88 768/1280 candidates; retain 1920 approved maximum. |
| 4 | Benghazi cards/detail `benghazi1.webp`, 292,700 bytes per request | High | Add Q88 640/1280 candidates; retain 1600 approved maximum and reuse the hero candidate for the first gallery item. |
| 5 | `cyrene2.webp` home editorial/dynamic gallery | Medium | Add Q88 640/1280 candidates. |
| 6 | `landscapes5.webp` cards/editorial/gallery | Medium | Add Q84 640/1280 candidates. |
| Deferred | `beaches.jpg`, `oldtripoli.jpg`, heritage JPEGs, `Acacus.jpg`, and other unapproved families | Deferred | They rank highly but lack approved WebP quality families; no speculative conversion was made. |
| Deferred | Other approved gallery-only WebPs | Low/deferred | Existing lazy delivery and lower interaction priority do not justify extra variants in this phase. |

## Derivatives

| Family | Widths | Quality | Bytes by new width |
| --- | --- | ---: | --- |
| desert | 768, 1280 | Q84 | 10,446; 21,652 |
| natural-lakes2 | 768, 1280 | Q88 | 87,016; 224,168 |
| architectural-heritage | 768, 1280 | Q88 | 119,786; 308,520 |
| benghazi1 | 640, 1280 | Q88 | 46,664; 190,598 |
| cyrene2 | 640, 1280 | Q88 | 83,924; 310,796 |
| landscapes5 | 640, 1280 | Q84 | 37,078; 144,606 |

Twelve derivatives total 1,585,254 bytes. Identical settings produced identical SHA-256 output in repeat encodes. Widths, proportional heights, RIFF/WEBP signatures, decode, and no-upscale constraints were verified. All source hashes remained unchanged.

## Delivery strategy

Static heroes and editorial pictures use ascending WebP width descriptors with layout-derived `sizes`, while their original JPEG/JPG `img src` remains the fallback with existing intrinsic dimensions, alt text, loading, decoding, fetch priority, classes, and crop behavior. The home hero uses `100vw`; contained editorial sections and cards use their actual breakpoint widths.

`assets/js/data/responsive-images.js` is the central source/fallback/candidate manifest for dynamic destination cards, detail heroes, galleries, and related cards. Arabic paths are resolved with the existing `../` prefix. The first gallery item uses the same selection width as the destination hero to prevent a second differently-sized request for the same photograph.

Services and Arabic atlas already have semantic inline hero images. Their redundant inline CSS background declaration was removed so responsive candidates do not cause a second background request. Other CSS-background heroes retain their existing approved `image-set()` behavior; width-descriptor selection is not forced into CSS.

## Measured results

Across the 160-case source matrix, total recorded image transfer fell from 298,945,264 to 233,646,039 bytes: 65,299,225 bytes, or 21.8%. Cold-cache evidence recorded zero required local asset failures, zero console errors, and zero horizontal-overflow cases.

| Case | Before | After | Reduction | Selected after candidate |
| --- | ---: | ---: | ---: | --- |
| English home, 360×800 DPR1 | 3,422,146 | 70,406 | 97.9% | desert-768.webp |
| Arabic home, 360×800 DPR1 | 3,422,146 | 70,406 | 97.9% | desert-768.webp |
| English home, 1440×1000 DPR1 | 5,109,085 | 1,787,389 | 65.0% | desert.webp (1920) |
| Destinations, 360×800 DPR1 | 1,831,150 | 1,831,150 | 0% | unapproved beaches.jpg hero retained |
| Destinations, 1440×1000 DPR1 | 4,307,017 | 3,874,153 | 10.1% | smaller approved card candidates |
| Benghazi detail, 360×800 DPR1 | 1,129,185 | 883,326 | 21.8% | benghazi1-640.webp |
| Benghazi detail, 430×900 DPR2 | 1,224,442 | 1,122,518 | 8.3% | benghazi1-1280.webp |
| Benghazi detail, 1440×1000 DPR1 | 1,522,244 | 1,522,244 | 0% | approved 1600 maximum reused by gallery |
| Arabic atlas, 360×800 DPR1 | 527,257 | 146,976 | 72.1% | natural-lakes2-768.webp |
| Arabic atlas, 430×900 DPR2 | 527,257 | 284,129 | 46.1% | natural-lakes2-1280.webp |
| Heritage desktop | unchanged | unchanged | 0% | deferred unapproved hero family |

Local LCP remained the same semantic element in key cases and selected the expected responsive URL. Timing varied between runs on loopback and is retained in the external JSON/CSV evidence rather than presented as a production performance claim.

## Visual and artifact QA

Before/after screenshots cover English/Arabic home, destinations, Benghazi detail, experiences, heritage, and atlas at 1440, 768, 430, and 360 pixels. Reviewed samples preserved crop, color, object-position, RTL, hero composition, and layout. Browser measurements found no distortion, overflow, failed required image request, or console error. QA evidence remains outside the repository under `VisitLibya-Responsive-Image-QA`.

The artifact intentionally grows by the bytes of the additional derivative choices while page-level transfer falls because browsers select smaller candidates. The final preview artifact contains 153 files and 127,839,121 bytes versus the 140-file, 126,248,385-byte baseline. All derivatives are explicitly allowlisted and original fallbacks remain included. The 160-case artifact browser matrix recorded 234,094,731 image bytes, zero required asset failures, zero console errors, and zero overflow cases; mobile home selected `desert-768.webp`.

## Integrity, limitations, and rollback

Original photographs were neither deleted nor modified. The large fallback warnings remain non-blocking and distinguish source retention from selected responsive delivery. The largest remaining opportunities are unapproved `beaches.jpg`, `oldtripoli.jpg`, heritage imagery, and `Acacus.jpg`; they require their own visual-quality approval before conversion.

Rollback consists of reverting the responsive source metadata and `srcset`/`sizes` changes, removing the twelve width-specific derivatives from the allowlist/output, and retaining the previously approved single WebPs and original fallbacks.

No deployment, push, SITE_ORIGIN, API activation, CNAME, or production configuration change occurred.
