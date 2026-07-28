import { apiClient } from "../app/api/client.js";
import { loadRuntimeConfig } from "../app/config/runtime-config.js";

const isArabic = document.documentElement.lang === "ar";
const locale = isArabic ? "ar-LY" : "en";
const pathPrefix = isArabic ? "../" : "";

const copy = Object.freeze({
  allCategories: isArabic ? "كل الوجهات" : "All destinations",
  allRegions: isArabic ? "جميع المناطق" : "All regions",
  atlas: isArabic ? "استكشف في الأطلس" : "Explore in the atlas",
  plan: isArabic ? "خطط لرحلتك" : "Plan a trip",
  locationUnknown: isArabic ? "ليبيا" : "Libya",
  categoryUnknown: isArabic ? "وجهة ليبية" : "Libyan destination",
  descriptionUnknown: isArabic
    ? "اكتشف هذه الوجهة ضمن تنوع ليبيا الطبيعي والثقافي."
    : "Discover this destination within Libya’s natural and cultural diversity.",
  loading: isArabic ? "جارٍ تحميل وجهات ليبيا…" : "Loading Libya’s destinations…",
  oneResult: isArabic ? "وجهة واحدة" : "1 destination",
  resultCount: (count) =>
    isArabic
      ? `${new Intl.NumberFormat(locale).format(count)} وجهة`
      : `${new Intl.NumberFormat(locale).format(count)} destinations`,
  curatedCount: (count) =>
    isArabic
      ? `نعرض ${new Intl.NumberFormat(locale).format(count)} وجهة من المجموعة المنسقة`
      : `Showing ${new Intl.NumberFormat(locale).format(count)} destinations from the curated collection`,
  searchSummary: (count, query) =>
    isArabic
      ? `${count} لبحث «${query}»`
      : `${count} for “${query}”`,
});

// This is the destination content that existed in the two static pages before
// the API-backed explorer. It remains available only as the established,
// curated fallback when live public search cannot be reached.
const curatedDestinations = Object.freeze([
  {
    slug: "tripoli",
    name_en: "Tripoli Old City",
    name_ar: "طرابلس",
    description_en: "Historic streets, traditional markets, and Mediterranean architecture express the capital’s living spirit.",
    description_ar: "مدينة تجمع بين عبق التاريخ وجمال الحاضر، وتضم المدينة القديمة وقوس ماركوس أوريليوس والسرايا الحمراء والأسواق التقليدية.",
    region_en: "Tripoli · Mediterranean Coast",
    region_ar: "طرابلس · الساحل المتوسطي",
    category_en: "Historic Cities",
    category_ar: "المدن التاريخية",
    category_key: "historic-cities",
    image: "imges/oldtripoli.jpg",
  },
  {
    slug: "benghazi",
    name_en: "Benghazi",
    name_ar: "بنغازي",
    description_en: "A Mediterranean city where urban heritage, culture, lakes, and gateways to the Green Mountain meet.",
    description_ar: "مدينة عريقة تطل على البحر المتوسط وتجمع بين التاريخ والثقافة والطبيعة، ومنها تنطلق المسارات نحو الجبل الأخضر.",
    region_en: "Benghazi · Eastern Libya",
    region_ar: "بنغازي · شرق ليبيا",
    category_en: "Historic Cities",
    category_ar: "المدن التاريخية",
    category_key: "historic-cities",
    image: "imges/bengazi1.JPG",
  },
  {
    slug: "ghadames",
    name_en: "Ghadames",
    name_ar: "غدامس",
    description_en: "A UNESCO oasis city of shaded passages, white houses, traditional craft, and enduring desert heritage.",
    description_ar: "جوهرة الصحراء ومدينة تراث عالمي تتميز بشوارعها المسقوفة وبيوتها البيضاء وأسواق الصناعات التقليدية.",
    region_en: "Ghadames · Western Desert",
    region_ar: "غدامس · الصحراء الغربية",
    category_en: "Oases and Heritage",
    category_ar: "الواحات والتراث",
    category_key: "oases-heritage",
    image: "imges/Ghadames2.JPG",
  },
  {
    slug: "acacus",
    name_en: "Tadrart Acacus",
    name_ar: "تادرارت أكاكوس",
    description_en: "Rock formations, prehistoric art, natural arches, and vast desert scenery preserve early human memory.",
    description_ar: "موطن لحضارة ما قبل التدوين، يشتهر بالفن الصخري والوديان والتشكيلات الصخرية والأقواس الطبيعية.",
    region_en: "Fezzan · Southwest Libya",
    region_ar: "فزان · جنوب غرب ليبيا",
    category_en: "Sahara and Rock Art",
    category_ar: "الصحراء والفن الصخري",
    category_key: "sahara-rock-art",
    image: "imges/Acacus.jpg",
  },
  {
    slug: "green-mountain",
    name_en: "Jebel Akhdar",
    name_ar: "الجبل الأخضر",
    description_en: "Green valleys, forests, cliffs, ancient sites, and coastal beauty connect Shahat, Sousa, and Ras Al Hilal.",
    description_ar: "منطقة تجمع بين الغابات والشواطئ والمرتفعات والوديان والعيون والمواقع الأثرية من شحات إلى رأس الهلال.",
    region_en: "Cyrenaica · Northeast Libya",
    region_ar: "برقة · شمال شرق ليبيا",
    category_en: "Mountains and Nature",
    category_ar: "الجبال والطبيعة",
    category_key: "mountains-nature",
    image: "imges/landscapes5.JPG",
  },
  {
    slug: "desert",
    name_en: "The Libyan Sahara",
    name_ar: "الصحراء الليبية",
    description_en: "Dunes, lakes, oases, mountains, rock art, and star-filled skies shape the heart of Libya’s desert.",
    description_ar: "قلب المتعة الحقيقية بما يضمه من كثبان وبحيرات وواحات وجبال وفن صخري وسماء صافية للنجوم.",
    region_en: "Sahara · Southern Libya",
    region_ar: "الصحراء الكبرى · جنوب ليبيا",
    category_en: "Sahara and Desert",
    category_ar: "الصحراء",
    category_key: "sahara-desert",
    image: "imges/The Sahara Desert.jpg",
  },
  {
    slug: "nafusa",
    name_en: "Nafusa Mountains",
    name_ar: "جبل نفوسة",
    description_en: "Mountain settlements, fortified granaries, cave homes, pottery, textiles, and olive groves reveal a distinct cultural landscape.",
    description_ar: "كنز تاريخي وثقافي يضم القصور الجبلية وبيوت الحفر والفخار والصوفيات وزيت الزيتون.",
    region_en: "Nafusa · Northwest Libya",
    region_ar: "جبل نفوسة · شمال غرب ليبيا",
    category_en: "Mountains and Heritage",
    category_ar: "الجبال والتراث",
    category_key: "mountains-heritage",
    image: "imges/traditional industries.jpg",
  },
  {
    slug: "bomba-bay",
    name_en: "Bomba Bay",
    name_ar: "خليج بمبة",
    description_en: "Secluded beaches, islands, marine life, and submerged heritage shape one of northeastern Libya’s distinctive bays.",
    description_ar: "من أجمل المواقع الساحلية في شمال شرق ليبيا، يتميز بجزره وشواطئه المنعزلة وثرائه البحري.",
    region_en: "Derna District · Northeast Coast",
    region_ar: "منطقة درنة · الساحل الشمالي الشرقي",
    category_en: "Mediterranean Coast",
    category_ar: "الساحل المتوسطي",
    category_key: "mediterranean-coast",
    image: "imges/beaches.jpg",
  },
  {
    slug: "awjila",
    name_en: "Awjila",
    name_ar: "أوجلة",
    description_en: "An eastern oasis shaped by local hospitality, markets, palm groves, and the rhythms of oasis life.",
    description_ar: "واحة شرقية بطابع تراثي محلي تجمع بين الضيافة والأسواق والحياة الواحية ضمن مسارات الصحراء.",
    region_en: "Al Wahat · Eastern Libya",
    region_ar: "الواحات · شرق ليبيا",
    category_en: "Oases and Nature",
    category_ar: "الواحات والطبيعة",
    category_key: "oases-nature",
    image: "imges/Awjila.jpg",
  },
  {
    slug: "sabratha",
    name_en: "Sabratha",
    name_ar: "صبراتة",
    description_en: "A UNESCO coastal archaeological city known for its Roman theatre, temples, baths, and Mediterranean setting.",
    description_ar: "مدينة أثرية على الساحل الليبي ومدرجة ضمن التراث العالمي، تشتهر بمسرحها الروماني ومعابدها وحماماتها.",
    region_en: "Sabratha · Northwest Coast",
    region_ar: "صبراتة · الساحل الشمالي الغربي",
    category_en: "Archaeological Sites",
    category_ar: "المواقع الأثرية",
    category_key: "archaeological-sites",
    image: "imges/Sabratha.jpg",
  },
  {
    slug: "villa-sileen",
    name_en: "Villa Sileen",
    name_ar: "فيلا سيلين",
    description_en: "A Roman coastal villa distinguished by its central courtyard, colonnades, mosaics, and garden setting.",
    description_ar: "جوهرة معمارية رومانية تتميز بفنائها المركزي وأروقتها المعمدة وفسيفسائها وحدائقها الخارجية.",
    region_en: "Khoms · Northwest Coast",
    region_ar: "الخمس · الساحل الشمالي الغربي",
    category_en: "Archaeological Sites",
    category_ar: "المواقع الأثرية",
    category_key: "archaeological-sites",
    image: "imges/Leptis Magna.jpg",
  },
]);

const elements = {
  form: document.getElementById("destinationSearchForm"),
  query: document.getElementById("destinationQuery"),
  region: document.getElementById("destinationRegion"),
  sort: document.getElementById("destinationSort"),
  categories: document.getElementById("destinationCategories"),
  status: document.getElementById("destinationResultsStatus"),
  results: document.getElementById("destinationResults"),
  grid: document.getElementById("destinationGrid"),
  loading: document.getElementById("destinationLoading"),
  empty: document.getElementById("destinationEmpty"),
  error: document.getElementById("destinationError"),
  retry: document.getElementById("destinationRetry"),
  clear: document.getElementById("clearDestinationFilters"),
  toolbarClear: document.getElementById("clearDestinationFiltersToolbar"),
  emptyClear: document.getElementById("destinationEmptyClear"),
};

const state = {
  query: "",
  category: "",
  region: "",
  sort: "name:asc",
  loading: false,
  source: "api",
  showCuratedError: false,
  categories: new Map(),
  regions: new Set(),
  requestKey: "",
  abortController: null,
};

function readUrlState() {
  const params = new URLSearchParams(location.search);
  state.query = (params.get("q") ?? "").trim().slice(0, 250);
  state.category = params.get("category") ?? "";
  state.region = params.get("region") ?? "";
  const requestedSort = params.get("sort") ?? "";
  state.sort = ["name:asc", "name:desc", "updated_at:desc"].includes(requestedSort)
    ? requestedSort
    : "name:asc";
  elements.query.value = state.query;
  elements.sort.value = state.sort;
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.query) params.set("q", state.query);
  if (state.category) params.set("category", state.category);
  if (state.region) params.set("region", state.region);
  if (state.sort !== "name:asc") params.set("sort", state.sort);
  const query = params.toString();
  history.replaceState(null, "", `${location.pathname}${query ? `?${query}` : ""}${location.hash}`);
}

function hasFilters() {
  return Boolean(state.query || state.category || state.region || state.sort !== "name:asc");
}

function setView(view) {
  elements.loading.hidden = view !== "loading";
  elements.grid.hidden = view !== "results";
  elements.empty.hidden = view !== "empty";
  elements.error.hidden = view !== "error";
  elements.results.setAttribute("aria-busy", String(view === "loading"));
  elements.toolbarClear.hidden = !hasFilters();
}

function safeText(value, fallback) {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function normalizeApiItem(item) {
  if (!item || typeof item !== "object") return null;
  const id = Number(item.id);
  const slug = safeText(item.slug, Number.isInteger(id) ? `destination-${id}` : "");
  if (!slug) return null;
  return {
    slug,
    name: safeText(isArabic ? item.name_ar : item.name_en, safeText(isArabic ? item.name_en : item.name_ar, copy.categoryUnknown)),
    description: safeText(
      isArabic ? item.short_description_ar : item.short_description_en,
      safeText(isArabic ? item.short_description_en : item.short_description_ar, copy.descriptionUnknown),
    ),
    region: safeText(item.region, safeText(item.municipality, copy.locationUnknown)),
    category: safeText(
      isArabic ? item.category?.name_ar : item.category?.name_en,
      copy.categoryUnknown,
    ),
    categoryId: Number.isInteger(Number(item.category?.id)) ? String(item.category.id) : "",
    image: normalizeImageUrl(item.primary_media_url),
  };
}

function normalizeImageUrl(value) {
  if (typeof value !== "string" || !value.trim()) return "";
  const source = value.trim();
  if (/^https?:\/\//i.test(source)) return source;
  if (source.startsWith("/")) {
    try {
      const url = new URL(source, loadRuntimeConfig().apiBaseUrl);
      return ["http:", "https:"].includes(url.protocol) ? url.href : "";
    } catch {
      return "";
    }
  }
  if (/^(?:\.\.\/|\.\/)?(?:imges|assets)\//i.test(source)) return source;
  return "";
}

function createCard(destination) {
  const article = document.createElement("article");
  article.className = "destination-explorer-card";
  article.id = destination.slug;

  const media = document.createElement("div");
  media.className = "destination-explorer-card__media";
  if (destination.image) {
    const image = document.createElement("img");
    image.src = destination.image;
    image.alt = destination.name;
    image.loading = "lazy";
    image.decoding = "async";
    image.addEventListener(
      "error",
      () => {
        image.remove();
        media.classList.add("is-fallback");
      },
      { once: true },
    );
    media.appendChild(image);
  } else {
    media.classList.add("is-fallback");
  }

  const body = document.createElement("div");
  body.className = "destination-explorer-card__body";

  const category = document.createElement("p");
  category.className = "destination-explorer-card__eyebrow";
  category.textContent = destination.category;

  const title = document.createElement("h3");
  title.textContent = destination.name;

  const locationText = document.createElement("p");
  locationText.className = "destination-explorer-card__location";
  locationText.textContent = destination.region;

  const description = document.createElement("p");
  description.className = "destination-explorer-card__description";
  description.textContent = destination.description;

  const actions = document.createElement("div");
  actions.className = "destination-explorer-card__actions";

  const atlas = document.createElement("a");
  atlas.className = "destination-explorer-card__link";
  atlas.href = `${pathPrefix}atlas.html`;
  atlas.textContent = copy.atlas;
  atlas.setAttribute("aria-label", `${copy.atlas}: ${destination.name}`);

  const plan = document.createElement("a");
  plan.className = "destination-explorer-card__link";
  plan.href = `${pathPrefix}plan.html`;
  plan.textContent = copy.plan;
  plan.setAttribute("aria-label", `${copy.plan}: ${destination.name}`);

  actions.append(atlas, plan);
  body.append(category, title, locationText, description, actions);
  article.append(media, body);
  return article;
}

function renderCards(items) {
  const fragment = document.createDocumentFragment();
  items.forEach((item) => fragment.appendChild(createCard(item)));
  elements.grid.replaceChildren(fragment);
  setView(items.length ? "results" : "empty");
  updateStatus(items.length);
  requestAnimationFrame(scrollToRequestedDestination);
}

function scrollToRequestedDestination() {
  if (!location.hash) return;
  const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
  target?.scrollIntoView({ block: "start" });
}

function updateStatus(count, curated = false) {
  const formatted = count === 1 ? copy.oneResult : copy.resultCount(count);
  if (curated) {
    elements.status.textContent = copy.curatedCount(count);
  } else if (state.query) {
    elements.status.textContent = copy.searchSummary(formatted, state.query);
  } else {
    elements.status.textContent = formatted;
  }
}

function renderCategoryControls(categories) {
  const fragment = document.createDocumentFragment();
  const all = document.createElement("button");
  all.type = "button";
  all.dataset.categoryId = "";
  all.textContent = copy.allCategories;
  all.classList.toggle("is-active", !state.category);
  all.setAttribute("aria-pressed", String(!state.category));
  fragment.appendChild(all);

  categories.forEach(({ id, name }) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.categoryId = id;
    button.textContent = name;
    button.classList.toggle("is-active", state.category === id);
    button.setAttribute("aria-pressed", String(state.category === id));
    fragment.appendChild(button);
  });
  elements.categories.replaceChildren(fragment);
}

function renderRegionOptions(regions) {
  const current = state.region;
  const fragment = document.createDocumentFragment();
  const all = document.createElement("option");
  all.value = "";
  all.textContent = copy.allRegions;
  fragment.appendChild(all);
  [...regions].sort((a, b) => a.localeCompare(b, locale)).forEach((region) => {
    const option = document.createElement("option");
    option.value = region;
    option.textContent = region;
    fragment.appendChild(option);
  });
  elements.region.replaceChildren(fragment);
  elements.region.value = current;
  if (elements.region.value !== current) {
    state.region = "";
  }
}

function collectApiFacets(items) {
  items.forEach((item) => {
    const categoryId = Number.isInteger(Number(item?.category?.id)) ? String(item.category.id) : "";
    const categoryName = safeText(
      isArabic ? item?.category?.name_ar : item?.category?.name_en,
      "",
    );
    if (categoryId && categoryName) state.categories.set(categoryId, categoryName);
    const region = safeText(item?.region, "");
    if (region) state.regions.add(region);
  });
  renderCategoryControls(
    [...state.categories].map(([id, name]) => ({ id, name })),
  );
  renderRegionOptions(state.regions);
}

function getApiPath() {
  const params = new URLSearchParams({ page: "1", page_size: "100" });
  const [sortBy, sortOrder] = state.sort.split(":");
  params.set("sort_by", sortBy);
  params.set("sort_order", sortOrder);
  if (state.query) params.set("q", state.query);
  if (/^[1-9]\d*$/.test(state.category)) params.set("category_id", state.category);
  if (state.region) params.set("region", state.region);
  return `/search/destinations?${params.toString()}`;
}

function fallbackItems() {
  const normalizedQuery = state.query.toLocaleLowerCase(locale);
  const selectedCategory = state.category.startsWith("curated:")
    ? state.category.slice("curated:".length)
    : "";
  const selectedRegion = state.region;
  const items = curatedDestinations
    .filter((item) => !selectedCategory || item.category_key === selectedCategory)
    .filter((item) => {
      const region = isArabic ? item.region_ar : item.region_en;
      return !selectedRegion || region === selectedRegion;
    })
    .filter((item) => {
      if (!normalizedQuery) return true;
      return [
        item.name_en,
        item.name_ar,
        item.description_en,
        item.description_ar,
        item.region_en,
        item.region_ar,
        item.category_en,
        item.category_ar,
      ].some((value) => value.toLocaleLowerCase(locale).includes(normalizedQuery));
    })
    .map((item) => ({
      slug: item.slug,
      name: isArabic ? item.name_ar : item.name_en,
      description: isArabic ? item.description_ar : item.description_en,
      region: isArabic ? item.region_ar : item.region_en,
      category: isArabic ? item.category_ar : item.category_en,
      categoryId: `curated:${item.category_key}`,
      image: `${pathPrefix}${item.image}`,
    }));

  const direction = state.sort === "name:desc" ? -1 : 1;
  return items.sort((a, b) => direction * a.name.localeCompare(b.name, locale));
}

function configureFallbackFacets() {
  const categoryMap = new Map();
  const regions = new Set();
  curatedDestinations.forEach((item) => {
    categoryMap.set(
      `curated:${item.category_key}`,
      isArabic ? item.category_ar : item.category_en,
    );
    regions.add(isArabic ? item.region_ar : item.region_en);
  });
  if (state.category && !state.category.startsWith("curated:")) state.category = "";
  renderCategoryControls(
    [...categoryMap].map(([id, name]) => ({ id, name })),
  );
  renderRegionOptions(regions);
}

function showFallback({ showError = true } = {}) {
  state.source = "curated";
  state.showCuratedError = showError;
  configureFallbackFacets();
  const items = fallbackItems();
  const fragment = document.createDocumentFragment();
  items.forEach((item) => fragment.appendChild(createCard(item)));
  elements.grid.replaceChildren(fragment);
  elements.loading.hidden = true;
  elements.empty.hidden = items.length > 0;
  elements.grid.hidden = items.length === 0;
  elements.error.hidden = !showError;
  elements.results.setAttribute("aria-busy", "false");
  elements.toolbarClear.hidden = !hasFilters();
  updateStatus(items.length, true);
  requestAnimationFrame(scrollToRequestedDestination);
}

async function loadDestinations({ force = false } = {}) {
  state.query = elements.query.value.trim().slice(0, 250);
  state.region = elements.region.value;
  state.sort = elements.sort.value;
  syncUrl();

  if (state.source === "curated" && !force) {
    const items = fallbackItems();
    const fragment = document.createDocumentFragment();
    items.forEach((item) => fragment.appendChild(createCard(item)));
    elements.grid.replaceChildren(fragment);
    elements.grid.hidden = items.length === 0;
    elements.empty.hidden = items.length > 0;
    elements.error.hidden = !state.showCuratedError;
    elements.toolbarClear.hidden = !hasFilters();
    updateStatus(items.length, true);
    return;
  }

  const path = getApiPath();
  if (!force && state.loading && state.requestKey === path) return;
  state.abortController?.abort();
  state.abortController = new AbortController();
  state.loading = true;
  state.requestKey = path;
  setView("loading");
  elements.status.textContent = copy.loading;

  try {
    const payload = await apiClient.get(path, {
      signal: state.abortController.signal,
      retries: 1,
    });
    if (!payload || !Array.isArray(payload.items)) throw new TypeError("Invalid destination response");
    state.source = "api";
    collectApiFacets(payload.items);
    const items = payload.items.map(normalizeApiItem).filter(Boolean);
    if (!items.length) {
      showFallback({ showError: false });
    } else {
      renderCards(items);
    }
  } catch (error) {
    if (error?.code === "ABORTED") return;
    showFallback();
  } finally {
    state.loading = false;
  }
}

function clearFilters() {
  state.query = "";
  state.category = "";
  state.region = "";
  state.sort = "name:asc";
  elements.query.value = "";
  elements.region.value = "";
  elements.sort.value = state.sort;
  updateCategoryState();
  loadDestinations({ force: state.source === "curated" });
}

function updateCategoryState() {
  elements.categories.querySelectorAll("button").forEach((button) => {
    const active = button.dataset.categoryId === state.category;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

let debounceTimer;
elements.query.addEventListener("input", () => {
  globalThis.clearTimeout(debounceTimer);
  debounceTimer = globalThis.setTimeout(() => loadDestinations(), 320);
});

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  globalThis.clearTimeout(debounceTimer);
  loadDestinations({ force: state.source === "curated" });
});

elements.region.addEventListener("change", () => loadDestinations());
elements.sort.addEventListener("change", () => loadDestinations());
elements.categories.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-category-id]");
  if (!button) return;
  state.category = button.dataset.categoryId ?? "";
  updateCategoryState();
  loadDestinations();
});

[elements.clear, elements.toolbarClear, elements.emptyClear].forEach((button) => {
  button.addEventListener("click", clearFilters);
});

elements.retry.addEventListener("click", () => {
  if (state.category.startsWith("curated:")) {
    state.category = "";
  }
  const curatedRegions = new Set(
    curatedDestinations.map((item) => (isArabic ? item.region_ar : item.region_en)),
  );
  if (curatedRegions.has(state.region)) {
    state.region = "";
    elements.region.value = "";
  }
  state.source = "api";
  state.showCuratedError = false;
  loadDestinations({ force: true });
});

globalThis.addEventListener("popstate", () => {
  readUrlState();
  loadDestinations({ force: true });
});

readUrlState();
loadDestinations();
