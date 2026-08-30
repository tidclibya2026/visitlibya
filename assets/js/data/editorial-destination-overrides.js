export const editorialDestinationAdditions = Object.freeze([
  Object.freeze({
    slug: "ras-al-hilal",
    name_en: "Ras Al Hilal",
    name_ar: "رأس الهلال",
    description_en: "A dramatic Mediterranean destination where forested slopes, turquoise coves, rocky cliffs, and quiet beaches meet along Libya’s Green Mountain coast.",
    description_ar: "وجهة ساحلية مميزة على الجبل الأخضر، تجمع بين الخضرة والمنحدرات والخلجان ذات المياه الفيروزية والشواطئ الهادئة في مشهد متوسطي استثنائي.",
    region_en: "Jebel Akhdar · Northeast Coast",
    region_ar: "الجبل الأخضر · الساحل الشمالي الشرقي",
    category_en: "Mediterranean Coast",
    category_ar: "الساحل المتوسطي",
    category_key: "mediterranean-coast",
    image: "imges/destinations/temporary/ras-al-hilal.jpeg",
    image_alt_en: "Mediterranean coastline and turquoise bay at Ras Al Hilal, Libya",
    image_alt_ar: "الساحل المتوسطي والخليج الفيروزي في رأس الهلال، ليبيا",
  }),
]);

export const editorialExcludedDestinationSlugs = new Set([
  "bomba-bay",
]);

export function mergeEditorialDestinationCatalogue(primaryItems, fallbackItems) {
  const catalogue = [];
  const includedSlugs = new Set();

  for (const item of [...primaryItems, ...fallbackItems]) {
    const slug = typeof item?.slug === "string" ? item.slug.toLowerCase() : "";
    if (!slug || editorialExcludedDestinationSlugs.has(slug) || includedSlugs.has(slug)) continue;
    includedSlugs.add(slug);
    catalogue.push(item);
  }

  return catalogue;
}
