# Responsive image delivery

Responsive delivery is evidence-based and uses the central `assets/js/data/responsive-images.js` manifest for dynamic destination media. Original JPG/JPEG files remain immutable fallbacks. Width-specific WebPs use lowercase ASCII names, preserve aspect ratio, never upscale, and retain the manually approved Q84/Q88 family setting.

Static `<picture>` sources use ascending width descriptors and a required layout-derived `sizes` value. Dynamic cards use compact card sizes; destination heroes use `100vw`; below-the-fold galleries remain lazy. The first gallery image shares the hero selection width when it is the same source, avoiding duplicate candidates.

CSS background images retain `image-set()` where responsive width selection would require a broad rewrite. Semantic inline heroes should not also request a redundant CSS background.

Validation requires valid WebP signatures, descriptor/file-width agreement, ascending unique widths, exact-case paths, original fallbacks, allowlist coverage, no upscale, and static-safe runtime configuration. See `measured-responsive-image-performance.md` for measurements and deferred families.
