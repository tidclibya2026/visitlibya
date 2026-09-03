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
  Object.freeze({
    slug: "ubari-lakes",
    name_en: "Ubari Lakes",
    name_ar: "بحيرات أوباري",
    description_en: "The Ubari lake landscapes create one of Libya’s most distinctive Saharan scenes, where water, dunes, palms and open desert meet in striking contrast.",
    description_ar: "تشكل بحيرات أوباري أحد أكثر المشاهد الصحراوية تميزاً في ليبيا، حيث تلتقي المياه بالكثبان والنخيل والفضاء الصحراوي المفتوح في تباين بصري لافت.",
    region_en: "Fezzan / Southwest Libya",
    region_ar: "فزان / جنوب غرب ليبيا",
    category_en: "Natural destination / Desert lakes",
    category_ar: "وجهة طبيعية / بحيرات صحراوية",
    category_key: "desert-lakes",
    image: "imges/Destination Detail/Ubari_Lakes/Ubari_01_Cinematic_Preserved_HQ.jpg",
    image_alt_en: "Desert lake, dunes, and palms in the Ubari Lakes landscape",
    image_alt_ar: "بحيرة صحراوية وكثبان ونخيل في مشهد بحيرات أوباري",
  }),
  Object.freeze({
    slug: "cyrene",
    name_en: "Cyrene",
    name_ar: "قورينا – شحات",
    description_en: "Cyrene combines monumental archaeological remains with the elevated landscapes of Jebel Akhdar, creating one of Libya’s most distinctive heritage settings.",
    description_ar: "تجمع قورينا بين المعالم الأثرية الكبرى والمشاهد المرتفعة للجبل الأخضر، لتشكل أحد أكثر المواقع التراثية تميزاً في ليبيا.",
    region_en: "Shahat / Jebel Akhdar",
    region_ar: "شحات / الجبل الأخضر",
    category_en: "Archaeological and cultural destination",
    category_ar: "وجهة أثرية وثقافية",
    category_key: "archaeological-cultural",
    image: "imges/Destination Detail/Cyrene/shahat_01_cinematic_preserved.jpg",
    image_alt_en: "Archaeological remains of Cyrene in the Jebel Akhdar landscape",
    image_alt_ar: "معالم قورينا الأثرية في مشهد الجبل الأخضر",
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
