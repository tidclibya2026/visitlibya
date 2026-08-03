const entry = (webp, candidates = []) => Object.freeze({
  webp,
  candidates: Object.freeze(candidates.map(([width, src]) => Object.freeze({ width, src }))),
});

export const responsiveImages = Object.freeze({
  "imges/Cyrene2.JPG": entry("imges/optimized/cyrene2.webp", [[640, "imges/optimized/cyrene2-640.webp"], [1280, "imges/optimized/cyrene2-1280.webp"], [1600, "imges/optimized/cyrene2.webp"]]),
  "imges/natural lakes2.JPG": entry("imges/optimized/natural-lakes2.webp", [[768, "imges/optimized/natural-lakes2-768.webp"], [1280, "imges/optimized/natural-lakes2-1280.webp"], [1920, "imges/optimized/natural-lakes2.webp"]]),
  "imges/tripoliMarcus Arch.JPG": entry("imges/optimized/tripoli-marcus-arch.webp"),
  "imges/gallery/Architectural heritage.JPG": entry("imges/optimized/architectural-heritage.webp", [[768, "imges/optimized/architectural-heritage-768.webp"], [1280, "imges/optimized/architectural-heritage-1280.webp"], [1920, "imges/optimized/architectural-heritage.webp"]]),
  "imges/beaches1.JPG": entry("imges/optimized/beaches1.webp"),
  "imges/bengazi1.JPG": entry("imges/optimized/benghazi1.webp", [[640, "imges/optimized/benghazi1-640.webp"], [1280, "imges/optimized/benghazi1-1280.webp"], [1600, "imges/optimized/benghazi1.webp"]]),
  "imges/bengazi3.JPG": entry("imges/optimized/benghazi3.webp"),
  "imges/bengazi.JPG": entry("imges/optimized/benghazi.webp"),
  "imges/desert.jpg": entry("imges/optimized/desert.webp", [[768, "imges/optimized/desert-768.webp"], [1280, "imges/optimized/desert-1280.webp"], [1920, "imges/optimized/desert.webp"]]),
  "imges/ghadames6.JPG": entry("imges/optimized/ghadames6.webp"),
  "imges/landscapes5.JPG": entry("imges/optimized/landscapes5.webp", [[640, "imges/optimized/landscapes5-640.webp"], [1280, "imges/optimized/landscapes5-1280.webp"], [1600, "imges/optimized/landscapes5.webp"]]),
  "imges/landscapes7.jpg": entry("imges/optimized/landscapes7.webp"),
  "imges/gallery/beaches18.JPG": entry("imges/optimized/beaches18.webp"),
});

export function resolveResponsiveImage(source, pathPrefix = "") {
  const image = responsiveImages[source];
  if (!image) return null;
  return Object.freeze({
    webp: `${pathPrefix}${image.webp}`,
    srcset: image.candidates.length
      ? image.candidates.map(({ width, src }) => `${pathPrefix}${src} ${width}w`).join(", ")
      : "",
  });
}
