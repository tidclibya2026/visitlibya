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
  "imges/destinations/temporary/awjila-master.jpg": entry("imges/optimized/destinations/awjila-master-1600.webp", [[640, "imges/optimized/destinations/awjila-master-640.webp"], [1280, "imges/optimized/destinations/awjila-master-1280.webp"], [1600, "imges/optimized/destinations/awjila-master-1600.webp"]]),
  "imges/destinations/temporary/awjila-gallery-01.jpg": entry("imges/optimized/destinations/awjila-gallery-01-960.webp", [[960, "imges/optimized/destinations/awjila-gallery-01-960.webp"]]),
  "imges/destinations/temporary/awjila-gallery-02.jpg": entry("imges/optimized/destinations/awjila-gallery-02-960.webp", [[960, "imges/optimized/destinations/awjila-gallery-02-960.webp"]]),
  "imges/destinations/temporary/awjila-gallery-03.jpg": entry("imges/optimized/destinations/awjila-gallery-03-960.webp", [[960, "imges/optimized/destinations/awjila-gallery-03-960.webp"]]),
  "imges/destinations/temporary/awjila-gallery-04.jpg": entry("imges/optimized/destinations/awjila-gallery-04-960.webp", [[960, "imges/optimized/destinations/awjila-gallery-04-960.webp"]]),
  "imges/destinations/temporary/nafusa-mountains.jpg": entry("imges/optimized/destinations/nafusa-1600.webp", [[640, "imges/optimized/destinations/nafusa-640.webp"], [1280, "imges/optimized/destinations/nafusa-1280.webp"], [1600, "imges/optimized/destinations/nafusa-1600.webp"]]),
  "imges/destinations/temporary/bomba-bay.png": entry("imges/optimized/destinations/bomba-bay-1042.webp", [[640, "imges/optimized/destinations/bomba-bay-640.webp"], [1042, "imges/optimized/destinations/bomba-bay-1042.webp"]]),
  "imges/destinations/temporary/villa-sileen-columns.jpg": entry("imges/optimized/destinations/villa-sileen-columns-1600.webp", [[960, "imges/optimized/destinations/villa-sileen-columns-960.webp"], [1600, "imges/optimized/destinations/villa-sileen-columns-1600.webp"]]),
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
