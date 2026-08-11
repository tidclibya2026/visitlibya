import { apiClient } from "../app/api/client.js";
import { loadRuntimeConfig } from "../app/config/runtime-config.js";
import { curatedDestinations } from "../data/curated-destinations.js";
import { resolveResponsiveImage } from "../data/responsive-images.js";

const isArabic = document.documentElement.lang === "ar";
const locale = isArabic ? "ar-LY" : "en";
const pathPrefix = isArabic ? "../" : "";
const runtimeConfig = loadRuntimeConfig();
const DESTINATION_SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

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
  const slug = safeText(item.slug, "").toLowerCase();
  if (!Number.isSafeInteger(id) || id < 1 || !DESTINATION_SLUG_PATTERN.test(slug)) return null;
  const curated = curatedDestinations.find((entry) => entry.slug === slug);
  const curatedName = safeText(isArabic ? curated?.name_ar : curated?.name_en, "");
  const curatedDescription = safeText(isArabic ? curated?.description_ar : curated?.description_en, "");
  const curatedRegion = safeText(isArabic ? curated?.region_ar : curated?.region_en, "");
  const curatedCategory = safeText(isArabic ? curated?.category_ar : curated?.category_en, "");
  const apiImage = normalizeImageUrl(item.primary_media_url);
  const responsive = apiImage || !curated ? null : resolveResponsiveImage(curated.image, pathPrefix);
  const coordinates = normalizeCoordinates(item.latitude, item.longitude);
  return {
    slug,
    name: safeText(isArabic ? item.name_ar : item.name_en, safeText(isArabic ? item.name_en : item.name_ar, curatedName || copy.categoryUnknown)),
    description: safeText(
      isArabic ? item.short_description_ar : item.short_description_en,
      safeText(isArabic ? item.short_description_en : item.short_description_ar, curatedDescription || copy.descriptionUnknown),
    ),
    region: safeText(item.region, safeText(item.municipality, curatedRegion || copy.locationUnknown)),
    category: safeText(
      isArabic ? item.category?.name_ar : item.category?.name_en,
      curatedCategory || copy.categoryUnknown,
    ),
    categoryId: Number.isInteger(Number(item.category?.id)) ? String(item.category.id) : "",
    image: apiImage || (curated?.image ? `${pathPrefix}${curated.image}` : ""),
    imageAlt: curated ? (isArabic ? curated.image_alt_ar : curated.image_alt_en) : "",
    imageWebp: responsive?.webp ?? "",
    imageWebpSrcset: responsive?.srcset ?? "",
    coordinates,
  };
}

function normalizeCoordinates(latitude, longitude) {
  return Number.isFinite(latitude) && latitude >= -90 && latitude <= 90 &&
    Number.isFinite(longitude) && longitude >= -180 && longitude <= 180
    ? Object.freeze({ latitude, longitude })
    : null;
}

function normalizeImageUrl(value) {
  if (typeof value !== "string" || !value.trim()) return "";
  const source = value.trim();
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
    image.alt = destination.imageAlt || destination.name;
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
    if (destination.imageWebp) {
      const picture = document.createElement("picture");
      picture.className = "responsive-picture";
      const source = document.createElement("source");
      source.type = "image/webp";
      source.srcset = destination.imageWebpSrcset || destination.imageWebp;
      if (destination.imageWebpSrcset) {
        source.sizes = "(max-width: 700px) calc(100vw - 2rem), (max-width: 1100px) 50vw, 33vw";
      }
      picture.append(source, image);
      media.appendChild(picture);
    } else {
      media.appendChild(image);
    }
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

  const details = document.createElement("a");
  details.className = "destination-explorer-card__link destination-explorer-card__link--primary";
  details.href = `${pathPrefix}destination.html?slug=${encodeURIComponent(destination.slug)}`;
  details.textContent = isArabic ? "عرض التفاصيل" : "View details";
  details.setAttribute(
    "aria-label",
    `${isArabic ? "عرض تفاصيل" : "View details for"} ${destination.name}`,
  );

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

  actions.append(details, atlas, plan);
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
      imageAlt: isArabic ? item.image_alt_ar : item.image_alt_en,
      imageWebp: resolveResponsiveImage(item.image, pathPrefix)?.webp ?? "",
      imageWebpSrcset: resolveResponsiveImage(item.image, pathPrefix)?.srcset ?? "",
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

  if (!runtimeConfig.apiEnabled) {
    showFallback();
    return;
  }
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

function initializeDestinationExplorer() {
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
}

if (elements.form) initializeDestinationExplorer();
