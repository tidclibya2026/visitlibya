import { apiClient } from "../app/api/client.js";
import { addTripItem, getTrip, listTrips } from "../app/api/trips-api.js";
import { bootstrap } from "../app/bootstrap.js";
import { getLocalizedErrorMessage } from "../app/errors/error-messages.js";
import { createTranslator } from "../app/i18n/translator.js";
import { announce } from "../app/ui/announcer.js";
import { setLoading } from "../app/ui/loading.js";
import { createModal } from "../app/ui/modal.js";
import { toast } from "../app/ui/toast.js";
import { createElement, setText, setVisible } from "../app/utils/dom.js";
import { loadRuntimeConfig } from "../app/config/runtime-config.js";
import { curatedDestinations } from "../data/curated-destinations.js";
import { resolveResponsiveImage } from "../data/responsive-images.js";
import { configureAtlasExternalLink } from "../app/config/runtime-config.js";

const isArabic = document.documentElement.lang === "ar";
const locale = isArabic ? "ar" : "en";
const pathPrefix = isArabic ? "../" : "";
const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const runtimeConfig = loadRuntimeConfig();
const pageTranslator = createTranslator(locale);
let activeRequest = null;
let requestSequence = 0;
let currentDestination = null;
let activeTripModal = null;
let naturalTourismGeneration = 0;
let naturalTourismController = null;

const NATURAL_TOURISM_DESTINATIONS = Object.freeze({
  "green-mountain": "green-mountain",
  desert: "libyan-sahara",
});

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
  acacus: ["imges/curated/acacus-rock-art-chariot.jpg", "imges/curated/acacus-rock-art-scene-2.jpg", "imges/curated/acacus-rock-art-scene-3.jpg"],
  "green-mountain": ["imges/landscapes5.JPG", "imges/Cyrene2.JPG", "imges/landscapes7.jpg"],
  desert: ["imges/The Sahara Desert.jpg", "imges/natural lakes.jpg", "imges/desert.jpg"],
  nafusa: ["imges/destinations/temporary/nafusa-mountains.jpg", "imges/pottery.jpg", "imges/qaser aje.jpg"],
  "bomba-bay": ["imges/destinations/temporary/bomba-bay.png", "imges/beaches.jpg", "imges/beaches1.JPG"],
  awjila: ["imges/destinations/temporary/awjila-master.jpg", "imges/destinations/temporary/awjila-gallery-01.jpg", "imges/destinations/temporary/awjila-gallery-02.jpg", "imges/destinations/temporary/awjila-gallery-03.jpg", "imges/destinations/temporary/awjila-gallery-04.jpg"],
  sabratha: ["imges/Sabratha.jpg", "imges/Sabratha.jpeg"],
  "leptis-magna": ["imges/Leptis Magna3.jpeg", "imges/Leptis Magna1.jpg", "imges/Leptis Magna.jpeg"],
  "villa-sileen": ["imges/destinations/temporary/villa-sileen-columns.jpg"],
});
const localImageAlt = Object.freeze({
  "imges/curated/villa-sileen-aerial.jpg": {
    en: "Aerial view of Villa Sileen on the Mediterranean coast",
    ar: "منظر جوي لفيلا سيلين على ساحل البحر المتوسط",
  },
  "imges/curated/villa-sileen-theatre.jpg": {
    en: "Theatre remains at Villa Sileen",
    ar: "بقايا المسرح في فيلا سيلين",
  },
  "imges/curated/villa-sileen-coast.jpg": {
    en: "Villa Sileen beside the Mediterranean coast",
    ar: "فيلا سيلين بجوار ساحل البحر المتوسط",
  },
  "imges/curated/acacus-rock-art-chariot.jpg": {
    en: "Rock-art scene depicting a chariot and horses in the Acacus region",
    ar: "مشهد من الفن الصخري يصور عربة وخيولًا في منطقة أكاكوس",
  },
  "imges/curated/acacus-rock-art-scene-2.jpg": {
    en: "Rock-art scene in the Acacus region",
    ar: "مشهد من الفن الصخري في منطقة أكاكوس",
  },
  "imges/curated/acacus-rock-art-scene-3.jpg": {
    en: "Ancient rock art in the Acacus region",
    ar: "فن صخري قديم في منطقة أكاكوس",
  },
  "imges/destinations/temporary/awjila-master.jpg": {
    en: "Earthen mosque and palm oasis architecture in Awjila, Libya",
    ar: "العمارة الطينية والمسجد وواحة النخيل في أوجلة، ليبيا",
  },
  "imges/destinations/temporary/awjila-gallery-01.jpg": {
    en: "Community members in traditional dress in Awjila",
    ar: "أفراد من المجتمع باللباس التقليدي في أوجلة",
  },
  "imges/destinations/temporary/awjila-gallery-02.jpg": {
    en: "Domed earthen architecture in Awjila",
    ar: "عمارة طينية ذات قباب في أوجلة",
  },
  "imges/destinations/temporary/awjila-gallery-03.jpg": {
    en: "Palm-lined entrance in Awjila",
    ar: "مدخل تحيط به أشجار النخيل في أوجلة",
  },
  "imges/destinations/temporary/awjila-gallery-04.jpg": {
    en: "Interior passage in Awjila's earthen architecture",
    ar: "ممر داخلي ضمن العمارة الطينية في أوجلة",
  },
  "imges/destinations/temporary/nafusa-mountains.jpg": {
    en: "Mountain settlement and heritage landscape in the Nafusa Mountains",
    ar: "تجمع جبلي ومشهد تراثي في جبل نفوسة",
  },
  "imges/destinations/temporary/bomba-bay.png": {
    en: "Coastal landscape of Bomba Bay in eastern Libya",
    ar: "المشهد الساحلي لخليج بمبة في شرق ليبيا",
  },
  "imges/destinations/temporary/villa-sileen-columns.jpg": {
    en: "Archaeological columns associated with the Roman Villa Sileen site",
    ar: "أعمدة أثرية مرتبطة بموقع فيلا سيلين الرومانية",
  },
});

function imageAlt(source, fallback) {
  const normalized = source.replace(/^\.\.\//, "");
  return localImageAlt[normalized]?.[locale] ?? fallback;
}

const elements = {
  loading: document.getElementById("destinationLoading"),
  notFound: document.getElementById("destinationNotFound"),
  error: document.getElementById("destinationError"),
  retry: document.getElementById("destinationRetry"),
  content: document.getElementById("destinationContent"),
  languageLink: document.getElementById("destinationLanguageLink"),
  heroImage: document.getElementById("destinationHeroImage"),
  heroPicture: document.querySelector(".destination-detail-hero__picture"),
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
  addToTrip: document.getElementById("destinationAddToTrip"),
  tripAvailability: document.getElementById("destinationTripAvailability"),
  naturalSection: document.getElementById("destinationNaturalSection"),
  naturalFilter: document.getElementById("destinationNaturalFilter"),
  naturalMap: document.getElementById("destinationNaturalMap"),
  naturalFailure: document.getElementById("destinationNaturalMapFailure"),
};

function resetNaturalTourism() {
  naturalTourismGeneration += 1;
  naturalTourismController?.update({ features: [] });
  naturalTourismController = null;
  elements.naturalFilter.onchange = null;
  elements.naturalSection.hidden = true;
  elements.naturalFailure.hidden = true;
  elements.naturalMap.hidden = false;
  elements.naturalFilter.replaceChildren(
    createElement("option", {
      text: isArabic ? "جميع الفئات" : "All categories",
      attributes: { value: "all" },
    }),
  );
}

async function renderNaturalTourism(slug) {
  resetNaturalTourism();
  const layerId = NATURAL_TOURISM_DESTINATIONS[slug];
  if (!layerId) return;

  const generation = naturalTourismGeneration;
  elements.naturalSection.hidden = false;

  try {
    const [dataModule, mapModule] = await Promise.all([
      import("../data/natural-tourism-layers.js"),
      import("../app/map/natural-tourism-map.js"),
    ]);
    if (generation !== naturalTourismGeneration) return;

    const features = dataModule.getNaturalTourismFeatures(layerId);
    const categories = mapModule.naturalLayerCategoryOptions(features);
    const options = [
      createElement("option", {
        text: isArabic ? "جميع الفئات" : "All categories",
        attributes: { value: "all" },
      }),
      ...categories.map((category) =>
        createElement("option", {
          text: isArabic ? category.ar : category.en,
          attributes: { value: category.key },
        }),
      ),
    ];

    elements.naturalFilter.replaceChildren(...options);
    naturalTourismController = mapModule.createNaturalTourismMap({
      root: elements.naturalMap,
      locale,
    });
    naturalTourismController.update({ layerId, features });

    elements.naturalFilter.onchange = () => {
      naturalTourismController?.setCategory(elements.naturalFilter.value);
    };
  } catch (error) {
    if (generation !== naturalTourismGeneration) return;
    reportDevelopmentError("Natural tourism map failed", error);
    elements.naturalMap.hidden = true;
    elements.naturalFailure.hidden = false;
  }
}

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

function localMedia(source) {
  const src = localPath(source);
  if (!src) return null;
  return { src, ...resolveResponsiveImage(source, pathPrefix) };
}

function createResponsivePicture(image, media, sizes) {
  if (!media?.webp) return image;
  const picture = document.createElement("picture");
  picture.className = "responsive-picture";
  const source = document.createElement("source");
  source.type = "image/webp";
  source.srcset = media.srcset || media.webp;
  if (media.srcset) source.sizes = sizes;
  picture.append(source, image);
  return picture;
}
function curatedBySlug(slug) {
  return curatedDestinations.find((item) => item.slug === slug) ?? null;
}

function localizedCurated(item) {
  return {
    id: null,
    slug: item.slug,
    name: isArabic ? item.name_ar : item.name_en,
    introduction: isArabic ? item.description_ar : item.description_en,
    description: isArabic ? item.description_ar : item.description_en,
    category: isArabic ? item.category_ar : item.category_en,
    region: isArabic ? item.region_ar : item.region_en,
    municipality: copy.unspecified,
    hero: localPath(item.image),
    heroAlt: isArabic ? item.image_alt_ar : item.image_alt_en,
    heroMedia: resolveResponsiveImage(item.image, pathPrefix),
    gallery: (localGalleries[item.slug] ?? [item.image]).map(localMedia).filter(Boolean),
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
  const { latitude, longitude } = payload;
  const coordinates = Number.isFinite(latitude) && latitude >= -90 && latitude <= 90 &&
    Number.isFinite(longitude) && longitude >= -180 && longitude <= 180
    ? Object.freeze({ latitude, longitude })
    : null;
  return {
    id: Number.isSafeInteger(payload.id) && payload.id > 0 ? payload.id : null,
    slug: payload.slug,
    name: text(translation.name, curatedRecord?.name ?? copy.destination),
    introduction,
    description,
    category: curatedRecord?.category ?? copy.destination,
    region: text(payload.region, curatedRecord?.region ?? copy.libya),
    municipality: text(payload.municipality, curatedRecord?.municipality ?? copy.unspecified),
    hero: curatedRecord?.hero ?? localPath("imges/beaches.jpg"),
    heroMedia: curatedRecord?.heroMedia ?? null,
    gallery: curatedRecord?.gallery ?? [],
    translationFallback: usedAlternate,
    coordinates,
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
  destination.gallery.slice(0, 5).forEach((media, index) => {
    const figure = document.createElement("figure");
    figure.className = "destination-detail-gallery__figure";
    const image = document.createElement("img");
    image.src = media.src;
    image.alt = imageAlt(media.src, isArabic
      ? `الصورة ${new Intl.NumberFormat("ar-LY").format(index + 1)} في معرض ${destination.name}`
      : `Image ${index + 1} in the ${destination.name} gallery`);
    image.loading = "lazy";
    image.decoding = "async";
    image.addEventListener("error", () => figure.remove(), { once: true });
    const caption = document.createElement("figcaption");
    caption.textContent = isArabic ? `مشهد من ${destination.name}` : `A local view of ${destination.name}`;
    const sizes = index === 0
      ? "100vw"
      : "(max-width: 768px) calc(100vw - 2rem), min(50vw, 720px)";
    figure.append(createResponsivePicture(image, media, sizes), caption);
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
    image.alt = localized.heroAlt || localized.name;
    image.loading = "lazy";
    image.decoding = "async";
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
    card.append(createResponsivePicture(image, localized.heroMedia, "(max-width: 700px) calc(100vw - 2rem), (max-width: 1100px) 50vw, 33vw"), body);
    fragment.appendChild(card);
  });
  elements.related.replaceChildren(fragment);
  elements.relatedSection.hidden = candidates.length === 0;
}

function parseDateOnly(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value ?? "")) return null;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  return date.getFullYear() === year &&
    date.getMonth() === month - 1 &&
    date.getDate() === day
    ? date
    : null;
}

function tripDays(trip) {
  const start = parseDateOnly(trip?.start_date);
  const end = parseDateOnly(trip?.end_date);
  if (start && end && end >= start) {
    return Array.from(
      { length: Math.round((end - start) / 86_400_000) + 1 },
      (_, index) => index + 1,
    );
  }
  const maximum = Math.max(
    1,
    ...(Array.isArray(trip?.items)
      ? trip.items.map((item) => Number(item.day_number) || 1)
      : []),
  );
  return Array.from({ length: maximum + 1 }, (_, index) => index + 1);
}

function dateForTripDay(trip, dayNumber) {
  const start = parseDateOnly(trip?.start_date);
  if (!start) return null;
  const date = new Date(start);
  date.setDate(date.getDate() + dayNumber - 1);
  return new Intl.DateTimeFormat(isArabic ? "ar-LY" : "en-GB", {
    dateStyle: "medium",
  }).format(date);
}

function closeTripModal() {
  if (!activeTripModal) return;
  activeTripModal.setCritical(false);
  activeTripModal.close();
  activeTripModal.destroy();
  activeTripModal = null;
}

function tripRoute(tripId) {
  return `${pathPrefix}trip.html?id=${encodeURIComponent(tripId)}`;
}

function tripsRoute() {
  return `${pathPrefix}trips.html`;
}

function publicTripError(error, t) {
  if (error?.code === "NETWORK_ERROR" || error?.code === "TIMEOUT") {
    return t("tripIntegration.networkError");
  }
  if (error?.code === "TRIP_VERSION_CONFLICT") {
    return t("tripIntegration.conflict");
  }
  if (error?.code === "TRIP_DUPLICATE_DESTINATION") {
    return t("tripIntegration.duplicate");
  }
  if (error?.status === 404) return t("tripIntegration.tripUnavailable");
  return getLocalizedErrorMessage(error, t);
}

function appendModalLink(modal, label, href, className = "destination-trip-button") {
  const link = createElement("a", {
    className,
    text: label,
    attributes: { href },
  });
  modal.actions.appendChild(link);
  return link;
}

function renderSignInState(modal, t) {
  modal.content.replaceChildren(
    createElement("p", {
      className: "destination-trip-message",
      text: t("tripIntegration.signInRequired"),
    }),
  );
  modal.actions.replaceChildren();
  const cancel = createElement("button", {
    className: "destination-trip-button destination-trip-button--secondary",
    text: t("common.cancel"),
    attributes: { type: "button" },
  });
  cancel.addEventListener("click", closeTripModal);
  modal.actions.appendChild(cancel);
  appendModalLink(
    modal,
    t("tripIntegration.signIn"),
    tripsRoute(),
    "destination-trip-button destination-trip-button--primary",
  );
}

function renderTripSuccess(modal, t, trip, destination) {
  const message = t("tripIntegration.success", {
    name: destination.name,
    trip: trip.title,
  });
  modal.content.replaceChildren(
    createElement("p", {
      className: "destination-trip-success",
      text: message,
      attributes: { role: "status" },
    }),
  );
  modal.actions.replaceChildren();
  appendModalLink(
    modal,
    t("tripIntegration.openTrip"),
    tripRoute(trip.id),
    "destination-trip-button destination-trip-button--primary",
  );
  appendModalLink(
    modal,
    t("tripIntegration.viewTrips"),
    tripsRoute(),
    "destination-trip-button destination-trip-button--secondary",
  );
  const continueButton = createElement("button", {
    className: "destination-trip-button destination-trip-button--secondary",
    text: t("tripIntegration.continueExploring"),
    attributes: { type: "button" },
  });
  continueButton.addEventListener("click", closeTripModal);
  modal.actions.appendChild(continueButton);
  toast.success(message, { closeLabel: t("common.close") });
  announce(message, { force: true });
}

async function openTripIntegration() {
  if (activeTripModal || !currentDestination?.id) return;
  const context = await bootstrap();
  if (!context) return;
  const { t } = context.translator;
  const modal = createModal({
    title: t("tripIntegration.title"),
    className: "app-modal destination-trip-modal",
  });
  activeTripModal = modal;
  modal.element.addEventListener("close", () => {
    if (activeTripModal === modal) {
      activeTripModal = null;
      modal.destroy();
    }
  }, { once: true });
  modal.element.dir = isArabic ? "rtl" : "ltr";
  modal.content.appendChild(
    createElement("p", {
      className: "destination-trip-summary",
      text: t("tripIntegration.destinationSummary", {
        name: currentDestination.name,
      }),
    }),
  );
  modal.open();

  if (!context.session.authenticated) {
    renderSignInState(modal, t);
    return;
  }

  const loading = createElement("p", {
    text: t("tripIntegration.loadingTrips"),
    attributes: { role: "status" },
  });
  modal.content.appendChild(loading);
  try {
    const response = await listTrips({ limit: 100 });
    if (!Array.isArray(response?.items) || response.items.length === 0) {
      modal.content.replaceChildren(
        createElement("p", {
          className: "destination-trip-message",
          text: t("tripIntegration.noTrips"),
        }),
      );
      modal.actions.replaceChildren();
      const cancel = createElement("button", {
        className: "destination-trip-button destination-trip-button--secondary",
        text: t("common.cancel"),
        attributes: { type: "button" },
      });
      cancel.addEventListener("click", closeTripModal);
      modal.actions.appendChild(cancel);
      appendModalLink(
        modal,
        t("tripIntegration.createTrip"),
        tripsRoute(),
        "destination-trip-button destination-trip-button--primary",
      );
      return;
    }

    const suffix = crypto.randomUUID();
    const form = createElement("form", {
      className: "destination-trip-form",
      attributes: { id: `destinationTripForm-${suffix}`, novalidate: "" },
    });
    const tripLabel = createElement("label", {
      text: t("tripIntegration.chooseTrip"),
      attributes: { for: `destinationTrip-${suffix}` },
    });
    const tripSelect = createElement("select", {
      attributes: {
        id: `destinationTrip-${suffix}`,
        name: "trip_id",
        required: "",
      },
    });
    tripSelect.appendChild(
      createElement("option", {
        text: t("tripIntegration.chooseTripPlaceholder"),
        attributes: { value: "" },
      }),
    );
    response.items.forEach((trip) => {
      const dates = trip.start_date && trip.end_date
        ? t("tripIntegration.dates", {
          start: trip.start_date,
          end: trip.end_date,
        })
        : t("tripIntegration.noDates");
      tripSelect.appendChild(
        createElement("option", {
          text: `${trip.title} — ${dates} — ${t(`trips.status${trip.status[0].toUpperCase()}${trip.status.slice(1)}`)}`,
          attributes: { value: trip.id },
        }),
      );
    });
    const dayLabel = createElement("label", {
      text: t("tripIntegration.chooseDay"),
      attributes: { for: `destinationDay-${suffix}` },
    });
    const daySelect = createElement("select", {
      attributes: {
        id: `destinationDay-${suffix}`,
        name: "day_number",
        required: "",
        disabled: "",
      },
    });
    const error = createElement("p", {
      className: "destination-trip-error",
      attributes: { id: `destinationTripError-${suffix}`, role: "alert", hidden: "" },
    });
    tripSelect.setAttribute("aria-describedby", error.id);
    daySelect.setAttribute("aria-describedby", error.id);
    const refresh = createElement("button", {
      className: "destination-trip-refresh",
      text: t("tripIntegration.refresh"),
      attributes: { type: "button", hidden: "" },
    });
    let selectedTrip = null;
    let loadingTrip = false;

    const showError = (message, { canRefresh = false } = {}) => {
      setText(error, message);
      setVisible(error, true);
      setVisible(refresh, canRefresh);
      announce(message, { priority: "assertive", force: true });
    };
    const clearError = () => {
      setText(error, "");
      setVisible(error, false);
      setVisible(refresh, false);
    };
    const loadSelectedTrip = async () => {
      const tripId = Number(tripSelect.value);
      selectedTrip = null;
      daySelect.replaceChildren();
      daySelect.disabled = true;
      clearError();
      if (!Number.isSafeInteger(tripId) || tripId < 1) return;
      loadingTrip = true;
      tripSelect.disabled = true;
      try {
        const trip = await getTrip(tripId);
        selectedTrip = trip;
        tripDays(trip).forEach((dayNumber) => {
          const date = dateForTripDay(trip, dayNumber);
          daySelect.appendChild(
            createElement("option", {
              text: date
                ? t("tripIntegration.dayWithDate", { day: dayNumber, date })
                : t("tripIntegration.day", { day: dayNumber }),
              attributes: { value: dayNumber },
            }),
          );
        });
        daySelect.disabled = false;
      } catch (loadError) {
        if (loadError?.status === 401) {
          renderSignInState(modal, t);
          return;
        }
        showError(publicTripError(loadError, t));
      } finally {
        loadingTrip = false;
        tripSelect.disabled = false;
      }
    };
    tripSelect.addEventListener("change", () => void loadSelectedTrip());
    refresh.addEventListener("click", () => void loadSelectedTrip());

    const cancel = createElement("button", {
      className: "destination-trip-button destination-trip-button--secondary",
      text: t("common.cancel"),
      attributes: { type: "button" },
    });
    const submit = createElement("button", {
      className: "destination-trip-button destination-trip-button--primary",
      text: t("tripIntegration.add"),
      attributes: { type: "submit", form: form.id },
    });
    cancel.addEventListener("click", closeTripModal);
    form.append(tripLabel, tripSelect, dayLabel, daySelect, error, refresh);
    modal.content.replaceChildren(
      createElement("p", {
        className: "destination-trip-summary",
        text: t("tripIntegration.destinationSummary", {
          name: currentDestination.name,
        }),
      }),
      form,
    );
    modal.actions.replaceChildren(cancel, submit);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (loadingTrip || submit.disabled) return;
      const tripId = Number(tripSelect.value);
      const dayNumber = Number(daySelect.value);
      if (!selectedTrip || selectedTrip.id !== tripId) {
        showError(t("tripIntegration.chooseTrip"));
        tripSelect.focus();
        return;
      }
      if (!Number.isInteger(dayNumber) || !tripDays(selectedTrip).includes(dayNumber)) {
        showError(t("tripIntegration.invalidDay"));
        daySelect.focus();
        return;
      }
      modal.setCritical(true);
      cancel.disabled = true;
      tripSelect.disabled = true;
      daySelect.disabled = true;
      setLoading(submit, true, {
        disable: true,
        text: t("tripIntegration.adding"),
      });
      clearError();
      try {
        const latestTrip = await getTrip(tripId);
        if (!tripDays(latestTrip).includes(dayNumber)) {
          selectedTrip = latestTrip;
          throw Object.assign(new Error("Trip day changed"), {
            code: "TRIP_VERSION_CONFLICT",
          });
        }
        await addTripItem(tripId, {
          expected_version: latestTrip.version,
          destination_id: currentDestination.id,
          day_number: dayNumber,
        });
        modal.setCritical(false);
        renderTripSuccess(modal, t, latestTrip, currentDestination);
      } catch (mutationError) {
        modal.setCritical(false);
        if (mutationError?.status === 401) {
          renderSignInState(modal, t);
          return;
        }
        showError(publicTripError(mutationError, t), {
          canRefresh: mutationError?.code === "TRIP_VERSION_CONFLICT",
        });
      } finally {
        cancel.disabled = false;
        tripSelect.disabled = false;
        daySelect.disabled = !selectedTrip;
        setLoading(submit, false, { disable: true });
        setText(submit, t("tripIntegration.add"));
      }
    });
  } catch (error) {
    if (error?.status === 401) {
      renderSignInState(modal, t);
      return;
    }
    const message = publicTripError(error, t);
    modal.content.replaceChildren(
      createElement("p", {
        className: "destination-trip-error",
        text: message,
        attributes: { role: "alert" },
      }),
    );
    announce(message, { priority: "assertive", force: true });
  }
}

function render(destination, { fallback = false } = {}) {
  currentDestination = destination;
  elements.title.textContent = destination.name;
  elements.category.textContent = destination.category;
  elements.categoryFact.textContent = destination.category;
  elements.introduction.textContent = destination.introduction;
  elements.location.textContent = destination.region;
  elements.region.textContent = destination.region;
  elements.municipality.textContent = destination.municipality;
  elements.heroImage.src = destination.hero || localPath("imges/beaches.jpg");
  elements.heroPicture.querySelector("source")?.remove();
  if (destination.heroMedia?.webp) {
    const source = document.createElement("source");
    source.type = "image/webp";
    source.srcset = destination.heroMedia.srcset || destination.heroMedia.webp;
    if (destination.heroMedia.srcset) source.sizes = "100vw";
    elements.heroPicture.prepend(source);
  }
  elements.heroImage.alt = imageAlt(destination.hero, destination.heroAlt || (isArabic ? `مشهد سياحي من ${destination.name}` : `Tourism view of ${destination.name}`));
  elements.heroImage.addEventListener("error", () => {
    elements.heroPicture.querySelector("source")?.remove();
    elements.heroImage.src = localPath("imges/beaches.jpg");
  }, { once: true });
  elements.fallbackNotice.hidden = !fallback;
  if (elements.fallbackRetry) elements.fallbackRetry.hidden = !runtimeConfig.apiEnabled;
  elements.translationNotice.hidden = !destination.translationFallback;
  elements.planLink.href = `${pathPrefix}plan.html?destination=${encodeURIComponent(destination.slug)}`;
  configureAtlasExternalLink(elements.atlasLink, {
    locale: isArabic ? "ar" : "en",
    context: destination.name,
  });
  const canSaveToTrip = Number.isSafeInteger(destination.id) && destination.id > 0;
  elements.addToTrip.disabled = !canSaveToTrip;
  elements.addToTrip.setAttribute("aria-disabled", String(!canSaveToTrip));
  elements.tripAvailability.hidden = canSaveToTrip;
  setText(
    elements.tripAvailability,
    canSaveToTrip
      ? ""
      : pageTranslator.t("tripIntegration.unavailableForCurated"),
  );
  appendParagraphs(elements.description, destination.description);
  renderGallery(destination);
  renderRelated(destination);
  void renderNaturalTourism(destination.slug);
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
    if (curated && !runtimeConfig.apiEnabled) {
      result = { view: "curated" };
      return;
    }

    if (!runtimeConfig.apiEnabled) {
      result = { view: "error" };
      return;
    }

    const payload = await apiClient.get(`/destinations/${encodeURIComponent(slug)}`, {
      signal: controller.signal,
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
elements.addToTrip?.addEventListener("click", () => void openTripIntegration());
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
