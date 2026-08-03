# Frontend media optimization plan

## Current phase outcome

No photographs were re-encoded in this phase. The workstation does not provide ImageMagick, `jpegtran`, `cwebp`, FFmpeg, Sharp, or an existing repository optimization script. The originals therefore remain unchanged and referenced. This document records the approved future conversion plan; the proposed optimized paths do not exist yet and must not be referenced until verified derivatives are created.

The 13 currently warned source photographs total 95,421,671 bytes. A future controlled run should preserve every source, write derivatives under `imges/optimized/`, compare visual output against the source, and update Arabic and English references together.

## Proposed source-to-optimized mapping

| Original path | Proposed optimized path | Original dimensions | Original size | Target maximum | Pages/data affected | Role | Reason |
|---|---|---:|---:|---:|---|---|---|
| `imges/beaches1.JPG` | `imges/optimized/beaches-1.webp` | 5472×3648 | 8,068,055 B | 1600 px | Arabic experiences; Bomba Bay gallery | Editorial/gallery | Excess pixels and more than 5 MB |
| `imges/bengazi.JPG` | `imges/optimized/benghazi-gallery-2.webp` | 5280×3956 | 12,193,792 B | 1600 px | Benghazi destination gallery | Gallery | Excess pixels and more than 5 MB |
| `imges/bengazi1.JPG` | `imges/optimized/benghazi-primary.webp` | 5280×3956 | 11,522,048 B | 1600 px | Curated Benghazi destination and gallery | Destination/gallery | Excess pixels and more than 5 MB |
| `imges/bengazi3.JPG` | `imges/optimized/benghazi-gallery-3.webp` | 5280×3956 | 12,107,776 B | 1600 px | Benghazi destination gallery | Gallery | Excess pixels and more than 5 MB |
| `imges/Cyrene2.JPG` | `imges/optimized/cyrene-2.webp` | 5472×3648 | 9,365,106 B | 1600 px | English/Arabic home; Green Mountain gallery | Card/gallery | Excess pixels and more than 5 MB |
| `imges/desert.jpg` | `imges/optimized/desert-camp.webp` | 3872×2592 | 3,362,184 B | 1920 px | Arabic experiences; desert gallery; legacy hero rule | Hero/editorial/gallery | More than 2 MB and excess pixels |
| `imges/gallery/Architectural heritage.JPG` | `imges/optimized/architectural-heritage.webp` | 3216×2136 | 3,660,002 B | 1920 px | English/Arabic services | Hero | More than 2 MB and excess pixels |
| `imges/gallery/beaches18.JPG` | `imges/optimized/beaches-18.webp` | 5472×3648 | 5,981,570 B | 1600 px | Bomba Bay destination gallery | Gallery | Excess pixels and more than 5 MB |
| `imges/ghadames6.JPG` | `imges/optimized/ghadames-6.webp` | 2880×1920 | 2,569,055 B | 1600 px | Ghadames destination gallery | Gallery | More than 2 MB and excess pixels |
| `imges/landscapes5.JPG` | `imges/optimized/green-mountain-landscape.webp` | 5280×3956 | 11,931,648 B | 1600 px | Arabic experiences; curated Green Mountain; destination gallery; English experience card | Editorial/card/gallery | Excess pixels and more than 5 MB |
| `imges/landscapes7.jpg` | `imges/optimized/green-mountain-landscape-3.webp` | 1920×1080 | 3,235,127 B | 1600 px | Green Mountain destination gallery | Gallery | More than 2 MB |
| `imges/natural lakes2.JPG` | `imges/optimized/natural-lakes-2.webp` | 5472×3648 | 7,765,306 B | 1920 px | Arabic atlas hero and experiences | Hero/editorial | Excess pixels and more than 5 MB |
| `imges/tripoliMarcus Arch.JPG` | `imges/optimized/tripoli-marcus-arch.webp` | 3216×2136 | 3,660,002 B | 1600 px | Tripoli destination gallery | Gallery | More than 2 MB and excess pixels |

Optimized dimensions, optimized sizes, percentage reductions, and final mappings remain pending because no trusted encoder is available. Recommended settings are WebP quality 80–85, metadata removal where safely supported, no upscaling, and preserved aspect ratio and color interpretation.

## Responsive delivery changes in this phase

- Justified primary inline LCP heroes remain eager and use at most one `fetchpriority="high"` image per page; zero is valid when no inline image warrants high priority.
- Audited below-the-fold inline images use `loading="lazy"`.
- Audited inline images use `decoding="async"`.
- Verified intrinsic dimensions are declared where the local decoder supports the format.
- No `<picture>`, `srcset`, or `sizes` markup was added because no verified alternative derivative exists.
- CSS background images retain their existing delivery and visual behavior.

## Font dependency audit

`style.css` imports:

`https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;800;900&family=Inter:wght@400;600;700;800;900&display=swap`

The dependency affects every page loading `style.css`. English uses `Inter, Cairo, Arial, sans-serif`; Arabic uses `Tajawal, Cairo, Noto Kufi Arabic, system-ui, sans-serif`. The component design system also falls back through Inter, Cairo, Noto Sans Arabic, Arial, Tahoma, and generic sans-serif fonts. No approved WOFF, WOFF2, TTF, or OTF files are stored in the repository.

If Google Fonts is unavailable, the interface remains readable but font metrics, line wrapping, visual hierarchy, and Arabic/Latin weight matching may shift. A future self-hosting phase should obtain properly licensed WOFF2 files, subset Latin and Arabic glyph coverage where appropriate, add local `@font-face` declarations with `font-display: swap`, and verify layout at all representative widths before removing the external import.

## Referenced image inventory

This inventory covers the 52 unique public image URLs referenced by the audited tourism pages, curated destination data, destination gallery data, and applicable shared CSS. “Excess pixels” compares the longest edge with the role ceiling defined for this phase.

| Image path | Dimensions | Bytes | Format | Role | Priority | Threshold / risk | Referenced by |
|---|---:|---:|---|---|---|---|---|
| `imges/Acacus.jpg` | 1280×707 | 699827 | JPG | card, hero | high | filename case/space | ar/experiences.html, ar/index.html, experiences.html, index.html, style.css |
| `imges/Awjila.jpg` | 1280×715 | 994487 | JPG | gallery, other | lazy | filename case/space; exact duplicate | assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js |
| `imges/Bazin.jpg` | 250×187 | 19407 | JPG | hero | high | filename case/space | style.css |
| `imges/beaches.jpg` | 1280×715 | 776524 | JPG | card, editorial, gallery, hero, other | high | filename case/space | ar/destination.html, ar/destinations.html, ar/experiences.html, ar/heritage.html, ar/index.html, assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js, destination.html, destinations.html, experiences.html, index.html |
| `imges/beaches1.JPG` | 5472×3648 | 8068055 | JPG | editorial, gallery | normal/lazy | >5 MB; excess pixels; filename case/space | ar/experiences.html, assets/js/pages/destination-details.js |
| `imges/bengazi.JPG` | 5280×3956 | 12193792 | JPG | other | lazy | >5 MB; excess pixels; filename case/space | assets/js/pages/destination-details.js |
| `imges/bengazi1.JPG` | 5280×3956 | 11522048 | JPG | gallery, other | lazy | >5 MB; excess pixels; filename case/space | assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js |
| `imges/bengazi3.JPG` | 5280×3956 | 12107776 | JPG | other | lazy | >5 MB; excess pixels; filename case/space | assets/js/pages/destination-details.js |
| `imges/curated/acacus-rock-art-chariot.jpg` | 1280×720 | 325768 | JPG | card, editorial, other | normal/lazy | filename case/space | ar/experiences.html, ar/heritage.html, assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js, experiences.html, heritage.html |
| `imges/curated/acacus-rock-art-scene-2.jpg` | 1280×720 | 444405 | JPG | other | lazy | filename case/space | assets/js/pages/destination-details.js |
| `imges/curated/acacus-rock-art-scene-3.jpg` | 1280×720 | 256720 | JPG | other | lazy | filename case/space | assets/js/pages/destination-details.js |
| `imges/curated/horse-rider-traditional.jpg` | 1280×913 | 114237 | JPG | card | normal/lazy | excess pixels; filename case/space | culture.html |
| `imges/curated/horse-riding-group.jpg` | 1280×834 | 124522 | JPG | editorial | normal/lazy | filename case/space | ar/culture.html, ar/experiences.html, culture.html |
| `imges/curated/libyan-couscous-detail.jpg` | 810×1080 | 112872 | JPG | card, gallery | normal/lazy | filename case/space | culture.html, experiences.html |
| `imges/curated/libyan-couscous.jpg` | 1080×719 | 47196 | JPG | editorial | normal/lazy | filename case/space | ar/culture.html, culture.html |
| `imges/curated/libyan-traditional-dress.jpg` | 1000×1250 | 65521 | JPG | card, editorial, hero | high | filename case/space | ar/culture.html, ar/experiences.html, culture.html, experiences.html |
| `imges/curated/villa-sileen-aerial.jpg` | 1280×720 | 142276 | JPG | other | lazy | filename case/space | assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js |
| `imges/curated/villa-sileen-coast.jpg` | 1280×720 | 134164 | JPG | other | lazy | filename case/space | assets/js/pages/destination-details.js |
| `imges/curated/villa-sileen-theatre.jpg` | 1280×720 | 135717 | JPG | other | lazy | filename case/space | assets/js/pages/destination-details.js |
| `imges/Cyrene.jpg` | 1280×707 | 978820 | JPG | card | normal/lazy | excess pixels; filename case/space | ar/heritage.html, ar/index.html, heritage.html, index.html |
| `imges/Cyrene2.JPG` | 5472×3648 | 9365106 | JPG | other | lazy | >5 MB; excess pixels; filename case/space | ar/index.html, assets/js/pages/destination-details.js, index.html |
| `imges/desert.jpg` | 3872×2592 | 3362184 | JPG | editorial, gallery, hero | high | >2 MB; excess pixels; filename case/space; exact duplicate | ar/experiences.html, assets/js/pages/destination-details.js, style.css |
| `imges/gallery/Architectural%20heritage.JPG` | 3216×2136 | 3660002 | JPG | hero | high | >2 MB; excess pixels; filename case/space; exact duplicate | ar/services.html, services.html |
| `imges/gallery/awajla.jpg` | 1280×715 | 994487 | JPG | gallery | lazy | filename case/space; exact duplicate | assets/js/pages/destination-details.js |
| `imges/gallery/beaches18.JPG` | 5472×3648 | 5981570 | JPG | gallery | lazy | >5 MB; excess pixels; filename case/space | assets/js/pages/destination-details.js |
| `imges/Ghadames.jpg` | 1280×707 | 1161594 | JPG | hero | high | filename case/space | style.css |
| `imges/Ghadames2.JPG` | 2880×1920 | 1644703 | JPG | card, other | normal/lazy | excess pixels; filename case/space | ar/culture.html, ar/heritage.html, ar/index.html, assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js, heritage.html, index.html |
| `imges/ghadames5.JPG` | 1920×2880 | 1450141 | JPG | other | lazy | excess pixels; filename case/space | assets/js/pages/destination-details.js |
| `imges/ghadames6.JPG` | 2880×1920 | 2569055 | JPG | other | lazy | >2 MB; excess pixels; filename case/space | assets/js/pages/destination-details.js |
| `imges/landscapes5.JPG` | 5280×3956 | 11931648 | JPG | card, editorial, other | normal/lazy | >5 MB; excess pixels; filename case/space | ar/experiences.html, assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js, experiences.html |
| `imges/landscapes7.jpg` | 1920×1080 | 3235127 | JPG | other | lazy | >2 MB; excess pixels; filename case/space | assets/js/pages/destination-details.js |
| `imges/Leptis Magna.jpeg` | 1366×768 | 447598 | JPEG | card, other | normal/lazy | excess pixels; filename case/space | ar/index.html, assets/js/pages/destination-details.js, index.html |
| `imges/Leptis Magna.jpg` | 1280×707 | 833490 | JPG | hero | high | filename case/space | style.css |
| `imges/Leptis Magna1.jpg` | 1280×715 | 814452 | JPG | other | lazy | filename case/space | assets/js/pages/destination-details.js |
| `imges/Leptis Magna3.jpeg` | 1080×887 | 313847 | JPEG | card, gallery, hero, other | high | filename case/space | ar/heritage.html, ar/index.html, assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js, culture.html, experiences.html, heritage.html, index.html |
| `imges/Museumtripoli.jpg` | 512×565 | 38619 | JPG | editorial, gallery | normal/lazy | filename case/space | ar/heritage.html, assets/js/pages/destination-details.js |
| `imges/natural lakes.jpg` | 1280×707 | 1124737 | JPG | card, gallery | normal/lazy | filename case/space | ar/index.html, assets/js/pages/destination-details.js, index.html |
| `imges/natural lakes1.jpg` | 1280×707 | 730694 | JPG | gallery, hero | high | filename case/space | assets/js/pages/destination-details.js, atlas.html |
| `imges/natural lakes2.JPG` | 5472×3648 | 7765306 | JPG | hero, other | high | >5 MB; excess pixels; filename case/space | ar/atlas.html, ar/experiences.html |
| `imges/oldtripoli.jpg` | 1280×707 | 568035 | JPG | card, editorial, gallery, hero, other | high | filename case/space | ar/culture.html, ar/heritage.html, ar/index.html, assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js, culture.html, index.html |
| `imges/pottery.jpg` | 960×1280 | 335500 | JPG | card, editorial, gallery | normal/lazy | filename case/space | ar/index.html, assets/js/pages/destination-details.js, culture.html, index.html |
| `imges/qaser aje.jpg` | 1280×707 | 480018 | JPG | editorial, gallery | normal/lazy | filename case/space | ar/heritage.html, assets/js/pages/destination-details.js |
| `imges/Sabratha.jpeg` | 1600×1200 | 357191 | JPEG | gallery | lazy | filename case/space | assets/js/pages/destination-details.js |
| `imges/Sabratha.jpg` | 1280×707 | 804523 | JPG | card, editorial, gallery, other | normal/lazy | filename case/space | ar/heritage.html, ar/index.html, assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js, culture.html, heritage.html, index.html |
| `imges/The Sahara Desert.jpg` | 1280×707 | 655683 | JPG | card, editorial, gallery, other | normal/lazy | filename case/space | ar/experiences.html, ar/heritage.html, ar/index.html, assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js, index.html |
| `imges/traditional food.jpg` | 810×1080 | 138183 | JPG | editorial | normal/lazy | filename case/space | ar/culture.html |
| `imges/traditional industries.jpg` | 972×628 | 913548 | JPG | editorial, gallery, other | normal/lazy | filename case/space | ar/culture.html, assets/js/data/curated-destinations.js, assets/js/pages/destination-details.js |
| `imges/tripoliMarcus Arch.JPG` | 3216×2136 | 3660002 | JPG | gallery | lazy | >2 MB; excess pixels; filename case/space; exact duplicate | assets/js/pages/destination-details.js |
| `imges/tripolinow.jpg` | 1980×1080 | 1812712 | JPG | hero | high | excess pixels; filename case/space | style.css |
| `imges/الدبلة.webp` | unknown | 60406 | WEBP | editorial | normal/lazy | filename case/space | ar/culture.html |
| `panel/desert.jpg` | 3872×2592 | 3362184 | JPG | other | lazy | >2 MB; excess pixels; filename case/space; exact duplicate | ar/index.html, index.html |
| `panel/panel1.png` | 1512×592 | 1518707 | PNG | hero | high | filename case/space | style.css |

## Visual presentation refinement

The visual-system phase added reusable semantic presentation rules for hero, card, editorial, natural-ratio, and logo media. Editorial and documentary images remain fully visible with natural height and `object-fit: contain`; controlled hero and card frames retain `object-fit: cover`. Mobile hero bounds were refined without changing image paths, subjects, loading, decoding, fetch priority, or intrinsic dimensions.

No original image was deleted, renamed, replaced, recompressed, or encoded. The thirteen oversized source photographs and all future WebP conversions remain pending until a trusted encoder and visual quality review are available.

## Measured responsive delivery

Measured cold-cache Edge evidence selected six approved families for twelve width-specific WebP derivatives. Original files and approved maximum WebPs remain unchanged. Across 160 source cases, recorded image transfer fell 21.8%; unapproved high-impact families remain deferred. See measured-responsive-image-performance.md.
