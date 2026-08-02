import { apiClient } from "../app/api/client.js";
import { loadRuntimeConfig } from "../app/config/runtime-config.js";
import { curatedDestinations } from "../data/curated-destinations.js";

const isArabic = document.documentElement.lang === "ar";
const locale = isArabic ? "ar" : "en";
const pathPrefix = isArabic ? "../" : "";
const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const DETAIL_REQUEST_TIMEOUT_MS = 5_000;
const runtimeConfig = loadRuntimeConfig();
let activeRequest = null;
let requestSequence = 0;

const copy = Object.freeze({
  destination: isArabic ? "وجهة ليبية" : "Libyan destination",
  libya: isArabic ? "ليبيا" : "Libya",
  unspecified: isArabic ? "غير محددة" : "Not specified",
  view: isArabic ? "عرض الوجهة" : "View destination",
});

const localGalleries = Object.freeze({
  tripoli: ["imges/oldtripoli.jpg", "imges/tripoliMarcus Arch.JPG", "imges/Museumtripoli.jpg"],
  benghazi: ["imges/bengazi1.JPG", "imges/bengazi.JPG", "imges/bengazi3.JPG"],
  ghadames: ["imges/Ghadames2.JPG", "imges/ghadames5.JPG", "imges/ghadames6.JPG"],
  acacus: ["imges/Acacus.jpg", "imges/Acacus1.jpeg", "imges/Acacus2.jpeg"],
  "green-mountain": ["imges/landscapes5.JPG", "imges/Cyrene2.JPG", "imges/landscapes7.jpg"],
  desert: ["imges/The Sahara Desert.jpg", "imges/natural lakes.jpg", "imges/desert.jpg"],
  nafusa: ["imges/traditional industries.jpg", "imges/pottery.jpg", "imges/qaser aje.jpg"],
  "bomba-bay": ["imges/beaches.jpg", "imges/beaches1.JPG", "imges/gallery/beaches18.JPG"],
  awjila: ["imges/Awjila.jpg", "imges/gallery/awajla.jpg", "imges/natural lakes1.jpg"],
  sabratha: ["imges/Sabratha.jpg", "imges/Sabratha.jpeg", "imges/Leptis Magna3.jpeg"],
  "leptis-magna": ["imges/Leptis Magna3.jpeg", "imges/Leptis Magna1.jpg", "imges/Leptis Magna.jpeg"],
  "villa-sileen": ["imges/Leptis Magna.jpg", "imges/Leptis Magna1.jpg", "imges/Leptis Magna.jpeg"],
});

const elements = {
  loading: document.getElementById("destinationLoading"),
  notFound: document.getElementById("destinationNotFound"),
  error: document.getElementById("destinationError"),
  retry: document.getElementById("destinationRetry"),
  content: document.getElementById("destinationContent"),
  languageLink: document.getElementById("destinationLanguageLink"),
  heroImage: document.getElementById("destinationHeroImage"),
  category: document.getElementById("destinationCategory"),
  title: document.getElementById("destinationTitle"),
  introduction: document.getElementById("destinationIntroduction"),
  location: document.getElementById("destinationLocation"),
  description: document.getElementById("destinationDescription"),
  region: document.getElementById("destinationRegion"),
  municipality: document.getElementById("destinationMunicipality"),
  categoryFact: document.getElementById("destinationCategoryFact"),
  fallbackNotice: document.getElementById("destinationFallbackNotice"),
  fallbackRetry: document.getElementById("destinationFallbackRetry"),
  translationNotice: document.getElementById("destinationTranslationNotice"),
  gallerySection: document.getElementById("destinationGallerySection"),
  gallery: document.getElementById("destinationGallery"),
  relatedSection: document.getElementById("destinationRelatedSection"),
  related: document.getElementById("destinationRelated"),
  planLink: document.getElementById("destinationPlanLink"),
  atlasLink: document.getElementById("destinationAtlasLink"),
};

function readSlug(search = globalThis.location.search) {
  const parameters = new URLSearchParams(search);
  const values = parameters.getAll("slug");
  if (values.length !== 1) return null;
  const slug = values[0].trim().toLowerCase();
  return slug.length <= 200 && SLUG_PATTERN.test(slug) ? slug : null;
}

function localPath(source) {
  if (typeof source !== "string" || !/^(?:imges|assets)\/[A-Za-z0-9\u0600-\u06ff _().-]+(?:\/[A-Za-z0-9\u0600-\u06ff _().-]+)*$/u.test(source)) {
    return "";
  }
  return `${pathPrefix}${source}`;
}

function curatedBySlug(slug) {
  return curatedDestinations.find((item) => item.slug === slug) ?? null;
}

function localizedCurated(item) {
  return {
    slug: item.slug,
    name: isArabic ? item.name_ar : item.name_en,
    introduction: isArabic ? item.description_ar : item.description_en,
    description: isArabic ? item.description_ar : item.description_en,
    category: isArabic ? item.category_ar : item.category_en,
    region: isArabic ? item.region_ar : item.region_en,
    municipality: copy.unspecified,
    hero: localPath(item.image),
    gallery: (localGalleries[item.slug] ?? [item.image]).map(localPath).filter(Boolean),
    translationFallback: false,
  };
}

function text(value, fallback = "") {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function apiTranslation(payload) {
  const translations = Array.isArray(payload?.translations) ? payload.translations : [];
  const requested = translations.find((item) => item?.language_code?.toLowerCase() === locale);
  const alternate = translations.find((item) => text(item?.name));
  return { translation: requested ?? alternate ?? null, usedAlternate: !requested && Boolean(alternate) };
}

function normalizeApiDestination(payload, curated) {
  if (!payload || typeof payload !== "object" || payload.slug !== readSlug()) return null;
  const { translation, usedAlternate } = apiTranslation(payload);
  if (!translation) return null;
  const curatedRecord = curated ? localizedCurated(curated) : null;
  const introduction = text(translation.short_description, text(translation.description, curatedRecord?.introduction ?? ""));
  const description = text(translation.description, introduction);
  return {
    slug: payload.slug,
    name: text(translation.name, curatedRecord?.name ?? copy.destination),
    introduction,
    description,
    category: curatedRecord?.category ?? copy.destination,
    region: text(payload.region, curatedRecord?.region ?? copy.libya),
    municipality: text(payload.municipality, curatedRecord?.municipality ?? copy.unspecified),
    hero: curatedRecord?.hero ?? localPath("imges/beaches.jpg"),
    gallery: curatedRecord?.gallery ?? [],
    translationFallback: usedAlternate,
  };
}

function setView(view) {
  elements.loading.hidden = view !== "loading";
  elements.notFound.hidden = view !== "not-found";
  elements.error.hidden = view !== "error";
  elements.content.hidden = view !== "content";
}

function reportDevelopmentError(context, error) {
  if (!runtimeConfig.debug || !globalThis.console?.error) return;
  console.error(`[Visit Libya] ${context}`, {
    code: typeof error?.code === "string" ? error.code : "UNEXPECTED_ERROR",
    status: Number.isInteger(error?.status) ? error.status : null,
  });
}

function shouldSkipLoopbackRequest() {
  try {
    const apiHost = new URL(runtimeConfig.apiBaseUrl).hostname;
    const pageHost = globalThis.location.hostname;
    const apiIsLoopback = apiHost === "127.0.0.1" || apiHost === "localhost" || apiHost === "::1";
    const pageIsLoopback = pageHost === "127.0.0.1" || pageHost === "localhost" || pageHost === "::1" || pageHost === "";
    return apiIsLoopback && !pageIsLoopback;
  } catch {
    return false;
  }
}

function appendParagraphs(container, value) {
  const paragraphs = text(value).split(/\n{2,}/).map((part) => part.trim()).filter(Boolean);
  const fragment = document.createDocumentFragment();
  (paragraphs.length ? paragraphs : [isArabic ? "لا يتوفر وصف إضافي لهذه الوجهة حاليًا." : "No additional destination description is currently available."])
    .forEach((part) => {
      const paragraph = document.createElement("p");
      paragraph.textContent = part;
      fragment.appendChild(paragraph);
    });
  container.replaceChildren(fragment);
}

function renderGallery(destination) {
  const fragment = document.createDocumentFragment();
  destination.gallery.slice(0, 3).forEach((source, index) => {
    const figure = document.createElement("figure");
    figure.className = "destination-detail-gallery__figure";
    const image = document.createElement("img");
    image.src = source;
    image.alt = isArabic
      ? `${destination.name}، مشهد محلي ${new Intl.NumberFormat("ar-LY").format(index + 1)}`
      : `${destination.name}, local view ${index + 1}`;
    image.loading = "lazy";
    image.decoding = "async";
    image.addEventListener("error", () => figure.remove(), { once: true });
    const caption = document.createElement("figcaption");
    caption.textContent = isArabic ? `مشهد من ${destination.name}` : `A local view of ${destination.name}`;
    figure.append(image, caption);
    fragment.appendChild(figure);
  });
  elements.gallery.replaceChildren(fragment);
  elements.gallerySection.hidden = destination.gallery.length === 0;
}

function renderRelated(destination) {
  const current = curatedBySlug(destination.slug);
  const candidates = curatedDestinations
    .filter((item) => item.slug !== destination.slug)
    .sort((left, right) => Number(right.category_key === current?.category_key) - Number(left.category_key === current?.category_key))
    .slice(0, 3);
  const fragment = document.createDocumentFragment();
  candidates.forEach((item) => {
    const localized = localizedCurated(item);
    const card = document.createElement("article");
    card.className = "destination-detail-related-card";
    const image = document.createElement("img");
    image.src = localized.hero;
    image.alt = localized.name;
    image.loading = "lazy";
    const body = document.createElement("div");
    body.className = "destination-detail-related-card__body";
    const title = document.createElement("h3");
    title.textContent = localized.name;
    const location = document.createElement("p");
    location.textContent = localized.region;
    const link = document.createElement("a");
    link.href = `${pathPrefix}destination.html?slug=${encodeURIComponent(item.slug)}`;
    link.textContent = copy.view;
    link.setAttribute("aria-label", `${copy.view}: ${localized.name}`);
    body.append(title, location, link);
    card.append(image, body);
    fragment.appendChild(card);
  });
  elements.related.replaceChildren(fragment);
  elements.relatedSection.hidden = candidates.length === 0;
}

function render(destination, { fallback = false } = {}) {
  elements.title.textContent = destination.name;
  elements.category.textContent = destination.category;
  elements.categoryFact.textContent = destination.category;
  elements.introduction.textContent = destination.introduction;
  elements.location.textContent = destination.region;
  elements.region.textContent = destination.region;
  elements.municipality.textContent = destination.municipality;
  elements.heroImage.src = destination.hero || localPath("imges/beaches.jpg");
  elements.heroImage.alt = isArabic ? `مشهد سياحي من ${destination.name}` : `Tourism view of ${destination.name}`;
  elements.heroImage.addEventListener("error", () => {
    elements.heroImage.src = localPath("imges/beaches.jpg");
  }, { once: true });
  elements.fallbackNotice.hidden = !fallback;
  elements.translationNotice.hidden = !destination.translationFallback;
  elements.planLink.href = `${pathPrefix}plan.html?destination=${encodeURIComponent(destination.slug)}`;
  elements.atlasLink.href = `${pathPrefix}atlas.html?destination=${encodeURIComponent(destination.slug)}`;
  appendParagraphs(elements.description, destination.description);
  renderGallery(destination);
  renderRelated(destination);
  document.title = `${destination.name} | Visit Libya`;
  setView("content");
}

function commitTerminalState(result, curated) {
  try {
    if (result.view === "curated") {
      render(localizedCurated(curated), { fallback: true });
    } else if (result.view === "content") {
      render(result.destination, { fallback: result.fallback });
    } else {
      setView(result.view);
    }
  } catch (error) {
    reportDevelopmentError("Destination rendering failed", error);
    try {
      if (curated && result.view !== "curated") {
        render(localizedCurated(curated), { fallback: true });
      } else {
        setView("error");
      }
    } catch (fallbackError) {
      reportDevelopmentError("Curated destination rendering failed", fallbackError);
      setView("error");
    }
  } finally {
    elements.loading.hidden = true;
  }
}

async function loadDestination() {
  const slug = readSlug();
  if (!slug) {
    commitTerminalState({ view: "not-found" }, null);
    return;
  }

  const languageTarget = isArabic ? `../destination.html?slug=${encodeURIComponent(slug)}` : `ar/destination.html?slug=${encodeURIComponent(slug)}`;
  elements.languageLink.href = languageTarget;
  document.querySelectorAll('link[rel="alternate"]').forEach((link) => {
    const language = link.getAttribute("hreflang");
    if (language === "ar") link.href = `${isArabic ? "" : "ar/"}destination.html?slug=${encodeURIComponent(slug)}`;
    if (language === "en" || language === "x-default") link.href = `${isArabic ? "../" : ""}destination.html?slug=${encodeURIComponent(slug)}`;
  });

  const curated = curatedBySlug(slug);
  activeRequest?.abort();
  const requestId = ++requestSequence;
  const controller = new AbortController();
  activeRequest = controller;
  let result = null;
  setView("loading");

  try {
    if (curated && shouldSkipLoopbackRequest()) {
      result = { view: "curated" };
      return;
    }

    const payload = await apiClient.get(`/destinations/${encodeURIComponent(slug)}`, {
      signal: controller.signal,
      timeoutMs: DETAIL_REQUEST_TIMEOUT_MS,
      retries: 0,
    });
    const destination = normalizeApiDestination(payload, curated);
    if (!destination) {
      result = curated
        ? { view: "curated" }
        : { view: "not-found" };
      return;
    }
    result = { view: "content", destination, fallback: false };
  } catch (error) {
    if (requestId !== requestSequence) return;
    reportDevelopmentError("Destination API request failed", error);
    if (curated) {
      result = { view: "curated" };
    } else if (error?.status === 404) {
      result = { view: "not-found" };
    } else {
      result = { view: "error" };
    }
  } finally {
    if (requestId === requestSequence) {
      activeRequest = null;
      commitTerminalState(result ?? { view: curated ? "curated" : "error" }, curated);
    }
  }
}

elements.retry?.addEventListener("click", loadDestination);
elements.fallbackRetry?.addEventListener("click", loadDestination);
loadDestination().catch((error) => {
  reportDevelopmentError("Destination initialization failed", error);
  const curated = curatedBySlug(readSlug());
  commitTerminalState(
    curated
      ? { view: "curated" }
      : { view: "error" },
    curated,
  );
});
