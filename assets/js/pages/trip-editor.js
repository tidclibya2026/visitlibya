import {
  addTripItem,
  deleteTripItem,
  getTrip,
  listTripDestinationCatalogue,
  reorderTripItems,
  searchTripDestinations,
  updateTrip,
  updateTripItem,
} from "../app/api/trips-api.js";
import { bootstrap } from "../app/bootstrap.js";
import { getLocalizedErrorMessage } from "../app/errors/error-messages.js";
import { curatedDestinations } from "../data/curated-destinations.js";
import { resolveResponsiveImage } from "../data/responsive-images.js";
import { announce } from "../app/ui/announcer.js";
import { setLoading } from "../app/ui/loading.js";
import { createModal } from "../app/ui/modal.js";
import { toast } from "../app/ui/toast.js";
import {
  createElement,
  queryRequired,
  setText,
  setVisible,
} from "../app/utils/dom.js";
import { updateQueryParameters } from "../app/utils/query-string.js";
import {
  TRIP_LIMITS,
  validateDateRange,
  validateOptionalText,
  validateRequiredText,
} from "../app/utils/validation.js";

const EDITABLE_FIELDS = Object.freeze([
  "title",
  "description",
  "start_date",
  "end_date",
  "status",
  "visibility",
]);
const DESTINATION_SEARCH_DEBOUNCE_MS = 300;
const DESTINATION_SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const destinationCatalogueById = new Map();
const destinationCatalogueBySlug = new Map();
const curatedDestinationBySlug = new Map(curatedDestinations.map((item) => [item.slug, item]));

let nextDestinationPage = 1;
let destinationPageCount = Number.POSITIVE_INFINITY;
let destinationPageRequest = null;

function safeDestinationText(value) {
  return typeof value === "string" && value.trim() ? value.trim() : "";
}

function validDestinationIdentity(destination) {
  const id = Number(destination?.id);
  const slug = safeDestinationText(destination?.slug).toLowerCase();
  return Number.isSafeInteger(id) && id > 0 && DESTINATION_SLUG_PATTERN.test(slug) ? { id, slug } : null;
}

async function loadNextDestinationPage() {
  if (nextDestinationPage > destinationPageCount) return;
  if (!destinationPageRequest) {
    const requestedPage = nextDestinationPage;
    destinationPageRequest = listTripDestinationCatalogue(requestedPage)
      .then((payload) => {
        if (!payload || !Array.isArray(payload.items)) throw new TypeError("Invalid destination catalogue response");
        payload.items.forEach((item) => {
          const identity = validDestinationIdentity(item);
          if (!identity) return;
          destinationCatalogueById.set(identity.id, item);
          destinationCatalogueBySlug.set(identity.slug, item);
        });
        const pages = Number(payload.pages);
        destinationPageCount = Number.isSafeInteger(pages) && pages >= 0 ? pages : requestedPage;
        nextDestinationPage = requestedPage + 1;
      })
      .finally(() => { destinationPageRequest = null; });
  }
  await destinationPageRequest;
}

function findDestinationCatalogueItem(identity) {
  const byId = destinationCatalogueById.get(identity.id);
  if (byId && safeDestinationText(byId.slug).toLowerCase() === identity.slug) return byId;
  const bySlug = destinationCatalogueBySlug.get(identity.slug);
  return Number(bySlug?.id) === identity.id ? bySlug : null;
}

function localizedDestinationName(value, locale) {
  return safeDestinationText(locale === "ar" ? value?.name_ar : value?.name_en) ||
    safeDestinationText(locale === "ar" ? value?.name_en : value?.name_ar);
}

function mergeDestinationContext(destination, locale, pathPrefix) {
  const identity = validDestinationIdentity(destination);
  if (!identity) return null;
  const api = findDestinationCatalogueItem(identity);
  const curated = curatedDestinationBySlug.get(identity.slug);
  const imageSource = safeDestinationText(curated?.image);
  const responsive = imageSource ? resolveResponsiveImage(imageSource, pathPrefix) : null;
  const municipality = safeDestinationText(api?.municipality);
  const region = safeDestinationText(api?.region);
  return Object.freeze({
    category: localizedDestinationName(api?.category, locale) || safeDestinationText(locale === "ar" ? curated?.category_ar : curated?.category_en),
    location: [...new Set([municipality, region].filter(Boolean))].join(" · ") || safeDestinationText(locale === "ar" ? curated?.region_ar : curated?.region_en),
    description: safeDestinationText(locale === "ar" ? api?.short_description_ar : api?.short_description_en) || safeDestinationText(locale === "ar" ? api?.short_description_en : api?.short_description_ar) || safeDestinationText(locale === "ar" ? curated?.description_ar : curated?.description_en),
    image: imageSource ? `${pathPrefix}${imageSource}` : "",
    imageAlt: safeDestinationText(locale === "ar" ? curated?.image_alt_ar : curated?.image_alt_en),
    imageWebp: responsive?.webp ?? "",
    imageSrcset: responsive?.srcset ?? "",
  });
}

async function enrichTripDestinations(destinations, locale, pathPrefix = "") {
  const identities = [...new Map(destinations.map(validDestinationIdentity).filter(Boolean).map((item) => [item.id, item])).values()];
  while (identities.some((identity) => !findDestinationCatalogueItem(identity)) && nextDestinationPage <= destinationPageCount) await loadNextDestinationPage();
  return new Map(destinations.map((destination) => [Number(destination?.id), mergeDestinationContext(destination, locale, pathPrefix)]).filter(([id, value]) => Number.isSafeInteger(id) && value));
}

function readTripId(search = globalThis.location?.search ?? "") {
  const parameters = new URLSearchParams(search);
  const values = parameters.getAll("id");
  if (values.length !== 1 || !/^[1-9]\d*$/.test(values[0])) return null;
  const value = Number(values[0]);
  return Number.isSafeInteger(value) ? value : null;
}

function formPayload(form) {
  const data = new FormData(form);
  return {
    title: validateRequiredText(data.get("title"), {
      field: "title",
      maxLength: TRIP_LIMITS.title,
    }),
    description: validateOptionalText(data.get("description"), {
      field: "description",
      maxLength: TRIP_LIMITS.description,
    }),
    start_date: String(data.get("start_date") ?? "") || null,
    end_date: String(data.get("end_date") ?? "") || null,
    status: String(data.get("status") ?? ""),
    visibility: String(data.get("visibility") ?? ""),
  };
}

function normalizedSnapshot(trip) {
  return JSON.stringify(
    Object.fromEntries(
      EDITABLE_FIELDS.map((field) => [field, trip?.[field] ?? null]),
    ),
  );
}

function parseDateOnly(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value ?? "")) return null;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  return (
    date.getFullYear() === year &&
    date.getMonth() === month - 1 &&
    date.getDate() === day
  )
    ? date
    : null;
}

function tripDayCount(trip) {
  const start = parseDateOnly(trip?.start_date);
  const end = parseDateOnly(trip?.end_date);
  if (!start || !end || end < start) return null;
  return Math.round((end - start) / 86_400_000) + 1;
}

function dateForDay(trip, dayNumber) {
  const start = parseDateOnly(trip?.start_date);
  if (!start) return null;
  const date = new Date(start);
  date.setDate(date.getDate() + dayNumber - 1);
  return date;
}

function availableDays(trip) {
  const count = tripDayCount(trip);
  if (count) return Array.from({ length: count }, (_, index) => index + 1);
  const maximum = Math.max(
    1,
    ...trip.items.map((item) => item.day_number),
  );
  return Array.from({ length: maximum + 1 }, (_, index) => index + 1);
}

function orderedItems(items) {
  return [...items].sort(
    (left, right) =>
      left.day_number - right.day_number ||
      left.sort_order - right.sort_order ||
      left.id - right.id,
  );
}

function destinationName(item, locale) {
  const destination = item.destination ?? item;
  return (
    (locale === "ar" ? destination.name_ar : destination.name_en) ||
    destination.name_en ||
    destination.name_ar ||
    destination.slug ||
    String(destination.id)
  );
}

function localizedTripValue(prefix, value, t) {
  if (!value) return "—";
  const key = `${prefix}${value[0].toUpperCase()}${value.slice(1)}`;
  const translated = t(key);
  return translated === key ? value : translated;
}

function publicErrorMessage(error, t) {
  if (error?.code === "NETWORK_ERROR" && globalThis.navigator?.onLine === false) {
    return t("errors.offline");
  }
  return getLocalizedErrorMessage(error, t);
}

function isVersionConflict(error) {
  return error?.code === "TRIP_VERSION_CONFLICT";
}

function stopPayload(form, expectedVersion) {
  const data = new FormData(form);
  const dayNumber = Number(data.get("day_number"));
  const durationValue = String(data.get("duration_minutes") ?? "").trim();
  const notes = validateOptionalText(data.get("notes"), {
    field: "notes",
    maxLength: TRIP_LIMITS.itemNotes,
  });
  if (!Number.isInteger(dayNumber) || dayNumber < 1) {
    throw new RangeError("day_number");
  }
  const duration = durationValue ? Number(durationValue) : null;
  if (
    duration !== null &&
    (!Number.isInteger(duration) || duration < 1)
  ) {
    throw new RangeError("duration_minutes");
  }
  return {
    expected_version: expectedVersion,
    day_number: dayNumber,
    start_time: String(data.get("start_time") ?? "") || null,
    duration_minutes: duration,
    notes,
  };
}

function createLabeledField({
  label,
  input,
  description,
  errorName,
}) {
  const wrapper = createElement("div", { className: "trips-field" });
  const labelElement = createElement("label", {
    text: label,
    attributes: { for: input.id },
  });
  wrapper.append(labelElement, input);
  if (description) {
    wrapper.appendChild(createElement("p", { text: description }));
  }
  if (errorName) {
    wrapper.appendChild(
      createElement("p", {
        className: "trips-field-error",
        attributes: {
          "data-stop-error-for": errorName,
          "aria-live": "polite",
        },
      }),
    );
  }
  return wrapper;
}

function createStopForm(trip, t, item = null, defaultDay = 1) {
  const suffix = crypto.randomUUID();
  const form = createElement("form", {
    className: "trips-form",
    attributes: { novalidate: "" },
  });
  const day = createElement("select", {
    attributes: {
      id: `tripStopDay-${suffix}`,
      name: "day_number",
      required: "",
    },
  });
  availableDays(trip).forEach((dayNumber) => {
    const option = createElement("option", {
      text: t("trips.dayHeading", { day: dayNumber }),
      attributes: { value: dayNumber },
    });
    option.selected = dayNumber === (item?.day_number ?? defaultDay);
    day.appendChild(option);
  });
  const startTime = createElement("input", {
    attributes: {
      id: `tripStopTime-${suffix}`,
      name: "start_time",
      type: "time",
      value: item?.start_time?.slice(0, 5) ?? "",
    },
  });
  const duration = createElement("input", {
    attributes: {
      id: `tripStopDuration-${suffix}`,
      name: "duration_minutes",
      type: "number",
      min: "1",
      step: "1",
      inputmode: "numeric",
      value: item?.duration_minutes ?? "",
    },
  });
  const notes = createElement("textarea", {
    attributes: {
      id: `tripStopNotes-${suffix}`,
      name: "notes",
      maxlength: TRIP_LIMITS.itemNotes,
    },
  });
  notes.value = item?.notes ?? "";
  const error = createElement("p", {
    className: "trips-form-error",
    attributes: {
      "data-stop-form-error": "",
      role: "alert",
      hidden: "",
    },
  });
  form.append(
    createLabeledField({
      label: t("trips.day"),
      input: day,
      errorName: "day_number",
    }),
    createLabeledField({
      label: t("trips.startTime"),
      input: startTime,
    }),
    createLabeledField({
      label: t("trips.durationMinutes"),
      input: duration,
      errorName: "duration_minutes",
    }),
    createLabeledField({
      label: t("trips.notes"),
      input: notes,
      errorName: "notes",
    }),
    error,
  );
  return { form, day, startTime, duration, notes, error };
}

export async function initializeTripEditor(documentRef = document) {
  const context = await bootstrap();
  if (!context) return;

  const { locale, translator } = context;
  const { t } = translator;
  const tripId = readTripId();
  const languageLink = documentRef.querySelector("[data-trip-language-link]");
  const loading = queryRequired("[data-trip-loading]", documentRef);
  const errorPanel = queryRequired("[data-trip-error]", documentRef);
  const errorMessage = queryRequired("[data-trip-error-message]", documentRef);
  const retry = queryRequired("[data-trip-retry]", documentRef);
  const authRequired = queryRequired("[data-auth-required]", documentRef);
  const editor = queryRequired("[data-trip-editor]", documentRef);
  const heading = queryRequired("[data-trip-heading]", documentRef);
  const version = queryRequired("[data-trip-version]", documentRef);
  const form = queryRequired("[data-trip-form]", documentRef);
  const formError = queryRequired("[data-trip-form-error]", documentRef);
  const cancel = queryRequired("[data-trip-cancel]", documentRef);
  const save = queryRequired("[data-trip-save]", documentRef);
  const addStop = queryRequired("[data-add-stop]", documentRef);
  const itinerary = queryRequired("[data-trip-itinerary]", documentRef);
  const editTripDetails = queryRequired("[data-edit-trip-details]", documentRef);
  const overviewDescription = queryRequired("[data-trip-overview-description]", documentRef);
  const overviewDates = queryRequired("[data-trip-overview-dates]", documentRef);
  const overviewDays = queryRequired("[data-trip-overview-days]", documentRef);
  const overviewStops = queryRequired("[data-trip-overview-stops]", documentRef);
  const overviewStatus = queryRequired("[data-trip-overview-status]", documentRef);
  const overviewVisibility = queryRequired("[data-trip-overview-visibility]", documentRef);
  const summary = queryRequired("[data-trip-summary]", documentRef);
  const review = queryRequired("[data-trip-review]", documentRef);

  if (!context.config.apiEnabled) {
    setVisible(loading, false);
    setText(errorMessage, t("trips.plannerUnavailable"));
    retry.hidden = true;
    setVisible(errorPanel, true);
    setVisible(authRequired, false);
    setVisible(editor, false);
    announce(t("trips.plannerUnavailable"), { force: true });
    return;
  }

  let trip = null;
  let savedSnapshot = null;
  let dirtyMetadata = false;
  let activeMutation = false;
  let draggedItemId = null;
  let activeStopModal = null;
  let destinationEnrichment = new Map();
  let enrichmentGeneration = 0;

  if (tripId && languageLink) {
    languageLink.href = updateQueryParameters(
      { id: tripId },
      new URL(languageLink.href, globalThis.location.href).href,
    );
  }

  const hideStates = () => {
    setVisible(loading, false);
    setVisible(errorPanel, false);
    setVisible(authRequired, false);
    setVisible(editor, false);
  };

  const showError = (message, { canRetry = true } = {}) => {
    hideStates();
    setText(errorMessage, message);
    setVisible(retry, canRetry);
    setVisible(errorPanel, true);
    announce(message, { priority: "assertive", force: true });
  };

  const showAuthRequired = () => {
    hideStates();
    setVisible(authRequired, true);
    announce(t("auth.required"), { priority: "assertive", force: true });
  };

  const updateMetadataButtons = () => {
    cancel.disabled = activeMutation || !dirtyMetadata;
    save.disabled = activeMutation || !dirtyMetadata;
  };

  const clearFieldErrors = () => {
    form.querySelectorAll("[aria-invalid]").forEach((field) => {
      field.removeAttribute("aria-invalid");
    });
    form.querySelectorAll("[data-error-for]").forEach((element) => setText(element, ""));
    setText(formError, "");
    setVisible(formError, false);
  };

  const setFieldError = (name, message) => {
    const input = form.elements.namedItem(name);
    const output = form.querySelector(`[data-error-for="${CSS.escape(name)}"]`);
    if (!(input instanceof HTMLElement) || !output) return;
    input.setAttribute("aria-invalid", "true");
    setText(output, Array.isArray(message) ? message[0] : message);
  };

  const showConflict = () => {
    const modal = createModal({
      title: t("trips.conflictTitle"),
      className: "app-modal trip-editor-conflict",
    });
    const message = createElement("p", {
      text: t("trips.tripUpdatedElsewhere"),
      attributes: { role: "alert" },
    });
    const keep = createElement("button", {
      className: "trips-secondary-button",
      text: t("trips.keepReviewing"),
      attributes: { type: "button" },
    });
    const reload = createElement("button", {
      className: "trips-primary-button",
      text: t("trips.reloadLatest"),
      attributes: { type: "button" },
    });
    const close = () => {
      modal.close();
      modal.destroy();
    };
    keep.addEventListener("click", close);
    reload.addEventListener("click", () => {
      close();
      activeStopModal?.close();
      activeStopModal?.destroy();
      activeStopModal = null;
      void loadTrip({ focus: true });
    });
    modal.content.appendChild(message);
    modal.actions.append(keep, reload);
    modal.open();
  };

  const dayLabel = (dayNumber) => {
    const date = dateForDay(trip, dayNumber);
    if (!date) return t("trips.dayHeading", { day: dayNumber });
    const formatted = new Intl.DateTimeFormat(locale, {
      weekday: "long",
      month: "long",
      day: "numeric",
    }).format(date);
    return t("trips.dayWithDate", { day: dayNumber, date: formatted });
  };

  const mutationControls = () => {
    itinerary.querySelectorAll("button, [draggable]").forEach((element) => {
      if ("disabled" in element) {
        element.disabled =
          activeMutation ||
          element.hasAttribute("data-boundary-disabled") ||
          (element.hasAttribute("data-add-stop-action") &&
            trip.items.length >= TRIP_LIMITS.items);
      }
      element.setAttribute("aria-disabled", String(element.disabled ?? activeMutation));
      if (element.hasAttribute("draggable")) {
        element.draggable = !activeMutation;
      }
    });
    addStop.disabled =
      activeMutation || trip.items.length >= TRIP_LIMITS.items;
    updateMetadataButtons();
  };

  const renderItinerary = () => {
    itinerary.replaceChildren();
    if (!trip.items.length) {
      const empty = createElement("div", { className: "trip-empty-state" });
      empty.append(
        createElement("span", { className: "trip-empty-state__mark", text: "✦", attributes: { "aria-hidden": "true" } }),
        createElement("h3", { text: locale === "ar" ? "ابدأ في بناء رحلتك" : "Start building your journey" }),
        createElement("p", { text: locale === "ar" ? "أضف الوجهات لتنظيم برنامج رحلتك يومًا بيوم." : "Add destinations to organize your trip day by day." }),
      );
      const emptyActions = createElement("div", { className: "trips-toolbar-actions" });
      const emptyAdd = createElement("button", { className: "trips-primary-button", text: t("trips.addStop"), attributes: { type: "button", "data-add-stop-action": "" } });
      emptyAdd.addEventListener("click", () => openStopEditor());
      emptyActions.append(emptyAdd, createElement("a", { className: "trips-secondary-button", text: locale === "ar" ? "استكشف الوجهات" : "Explore Destinations", attributes: { href: locale === "ar" ? "destinations.html" : "destinations.html" } }));
      empty.appendChild(emptyActions);
      itinerary.appendChild(empty);
    }
    const days = createElement("div", { className: "trip-days" });
    const allItems = orderedItems(trip.items);
    availableDays(trip).forEach((dayNumber) => {
      const items = allItems.filter((item) => item.day_number === dayNumber);
      const section = createElement("section", {
        className: "trip-day",
        attributes: {
          "data-trip-day": dayNumber,
          "aria-labelledby": `trip-day-${dayNumber}`,
        },
      });
      const header = createElement("div", { className: "trip-day__header" });
      const headingBlock = createElement("div");
      headingBlock.append(
        createElement("h3", {
          text: dayLabel(dayNumber),
          attributes: { id: `trip-day-${dayNumber}` },
        }),
        createElement("p", {
          text: t("trips.stopCount", { count: items.length }),
        }),
      );
      const addForDay = createElement("button", {
        className: "trips-secondary-button",
        text: t("trips.addStop"),
        attributes: {
          type: "button",
          "data-add-stop-action": "",
          "aria-label": t("trips.addStopToDay", { day: dayNumber }),
        },
      });
      addForDay.addEventListener("click", () => openStopEditor(null, dayNumber));
      header.append(headingBlock, addForDay);
      const list = createElement("div", {
        className: "trip-stop-list",
        attributes: { "data-trip-day-list": dayNumber },
      });
      if (!items.length) {
        list.appendChild(
          createElement("p", {
            className: "trip-day__empty",
            text: t("trips.noStopsForDay"),
          }),
        );
      }
      items.forEach((item, index) => {
        const name = destinationName(item, locale);
        const enrichment = destinationEnrichment.get(Number(item.destination?.id));
        const card = createElement("article", {
          className: "trip-stop",
          attributes: { "data-stop-id": item.id },
        });
        const handle = createElement("button", {
          className: "trip-stop__handle",
          text: "↕",
          attributes: {
            type: "button",
            draggable: "true",
            "aria-label": t("trips.dragStop", { name }),
            title: t("trips.dragStop", { name }),
          },
        });
        handle.addEventListener("dragstart", (event) => {
          if (activeMutation) {
            event.preventDefault();
            return;
          }
          draggedItemId = item.id;
          card.classList.add("is-dragging");
          event.dataTransfer.effectAllowed = "move";
          event.dataTransfer.setData("text/plain", String(item.id));
        });
        handle.addEventListener("dragend", () => {
          draggedItemId = null;
          card.classList.remove("is-dragging");
          documentRef.querySelectorAll(".is-drag-over").forEach((element) => {
            element.classList.remove("is-drag-over");
          });
        });
        const media = createElement("div", { className: "trip-stop__media" });
        if (enrichment?.image) {
          const image = createElement("img", {
            attributes: {
              src: enrichment.image,
              alt: enrichment.imageAlt || name,
              width: "240",
              height: "160",
              loading: "lazy",
              decoding: "async",
            },
          });
          image.addEventListener("error", () => {
            media.replaceChildren();
            media.classList.add("is-fallback");
            media.setAttribute("aria-hidden", "true");
          }, { once: true });
          if (enrichment.imageWebp) {
            const picture = createElement("picture", { className: "responsive-picture" });
            const source = createElement("source", {
              attributes: {
                type: "image/webp",
                srcset: enrichment.imageSrcset || enrichment.imageWebp,
                sizes: "(max-width: 480px) calc(100vw - 5rem), 120px",
              },
            });
            picture.append(source, image);
            media.appendChild(picture);
          } else media.appendChild(image);
        } else {
          media.classList.add("is-fallback");
          media.setAttribute("aria-hidden", "true");
        }
        const content = createElement("div", { className: "trip-stop__content" });
        const stopTitle = createElement("h4");
        const slug = String(item.destination?.slug ?? "").trim();
        if (/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
          stopTitle.appendChild(createElement("a", { text: name, attributes: { href: `destination.html?slug=${encodeURIComponent(slug)}` } }));
        } else stopTitle.appendChild(documentRef.createTextNode(name));
        content.appendChild(stopTitle);
        const destinationContext = [enrichment?.category, enrichment?.location].filter(Boolean);
        if (destinationContext.length) {
          content.appendChild(createElement("p", {
            className: "trip-stop__context",
            text: destinationContext.join(" · "),
          }));
        }
        if (enrichment?.description) {
          content.appendChild(createElement("p", {
            className: "trip-stop__description",
            text: enrichment.description,
          }));
        }
        const meta = createElement("p", { className: "trip-stop__meta" });
        if (item.start_time) {
          meta.appendChild(createElement("span", { text: item.start_time.slice(0, 5) }));
        }
        if (item.duration_minutes) {
          meta.appendChild(
            createElement("span", {
              text: `${item.duration_minutes} ${t("trips.durationMinutes").toLowerCase()}`,
            }),
          );
        }
        if (meta.childNodes.length) content.appendChild(meta);
        if (item.notes) {
          content.appendChild(
            createElement("p", {
              className: "trip-stop__notes",
              text: item.notes,
            }),
          );
        }
        if (/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
          const links = createElement("div", { className: "trip-stop__links" });
          links.append(
            createElement("a", { className: "trip-stop__destination-link", text: locale === "ar" ? "عرض الوجهة" : "View Destination", attributes: { href: `destination.html?slug=${encodeURIComponent(slug)}`, "aria-label": `${locale === "ar" ? "عرض الوجهة" : "View Destination"}: ${name}` } }),
            createElement("a", { className: "trip-stop__destination-link", text: locale === "ar" ? "استكشف في الأطلس السياحي" : "Explore in Tourism Atlas", attributes: { href: `atlas.html?destination=${encodeURIComponent(slug)}`, "aria-label": `${locale === "ar" ? "استكشف في الأطلس السياحي" : "Explore in Tourism Atlas"}: ${name}` } }),
          );
          content.appendChild(links);
        }
        const actions = createElement("div", { className: "trip-stop__actions" });
        const action = (label, handler, disabled = false) => {
          const button = createElement("button", {
            text: label,
            attributes: { type: "button" },
          });
          button.disabled = disabled;
          if (disabled) {
            button.setAttribute("data-boundary-disabled", "");
          }
          button.addEventListener("click", handler);
          actions.appendChild(button);
        };
        action(
          "↑",
          () => void moveItem(item.id, { offset: -1 }),
          index === 0,
        );
        actions.lastChild.setAttribute("aria-label", t("trips.moveUp", { name }));
        action(
          "↓",
          () => void moveItem(item.id, { offset: 1 }),
          index === items.length - 1,
        );
        actions.lastChild.setAttribute("aria-label", t("trips.moveDown", { name }));
        action(
          "←",
          () => void moveItem(item.id, { dayOffset: -1 }),
          dayNumber === 1,
        );
        actions.lastChild.setAttribute(
          "aria-label",
          t("trips.movePreviousDay", { name }),
        );
        action(
          "→",
          () => void moveItem(item.id, { dayOffset: 1 }),
          dayNumber === availableDays(trip).at(-1),
        );
        actions.lastChild.setAttribute(
          "aria-label",
          t("trips.moveNextDay", { name }),
        );
        action(t("trips.editStop"), () => openStopEditor(item, dayNumber));
        action(t("trips.deleteStop"), () => openDeleteStop(item));
        card.append(handle, media, content, actions);
        list.appendChild(card);
      });
      list.addEventListener("dragover", (event) => {
        if (!draggedItemId || activeMutation) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        section.classList.add("is-drag-over");
      });
      list.addEventListener("dragleave", (event) => {
        if (!section.contains(event.relatedTarget)) {
          section.classList.remove("is-drag-over");
        }
      });
      list.addEventListener("drop", (event) => {
        event.preventDefault();
        section.classList.remove("is-drag-over");
        if (draggedItemId) {
          void moveItem(draggedItemId, { targetDay: dayNumber });
        }
      });
      section.append(header, list);
      days.appendChild(section);
    });
    itinerary.appendChild(days);
    mutationControls();
  };

  const populate = (loadedTrip) => {
    trip = Object.freeze({
      ...loadedTrip,
      items: Object.freeze(orderedItems(loadedTrip.items)),
    });
    EDITABLE_FIELDS.forEach((field) => {
      const input = form.elements.namedItem(field);
      if (input && "value" in input) input.value = trip[field] ?? "";
    });
    setText(heading, trip.title || t("trips.editorTitle"));
    setText(version, trip.version);
    const days = tripDayCount(trip);
    const dateFormatter = new Intl.DateTimeFormat(locale, { year: "numeric", month: "short", day: "numeric" });
    const start = parseDateOnly(trip.start_date);
    const end = parseDateOnly(trip.end_date);
    setText(overviewDates, start && end ? `${dateFormatter.format(start)} – ${dateFormatter.format(end)}` : start ? dateFormatter.format(start) : t("trips.noDates"));
    setText(overviewDays, days ?? "—");
    setText(overviewStops, trip.items.length);
    setText(overviewStatus, localizedTripValue("trips.status", trip.status, t));
    setText(overviewVisibility, localizedTripValue("trips.visibility", trip.visibility, t));
    setText(overviewDescription, trip.description ?? "");
    setVisible(overviewDescription, Boolean(trip.description));

    const represented = new Set(trip.items.map((item) => item.destination?.id).filter(Boolean)).size;
    const dayNumbers = availableDays(trip);
    const emptyDays = dayNumbers.filter((day) => !trip.items.some((item) => item.day_number === day)).length;
    const facts = locale === "ar"
      ? [["الأيام", days ?? "—"], ["المحطات المخططة", trip.items.length], ["الأيام الفارغة", emptyDays], ["الوجهات الممثلة", represented]]
      : [["Days", days ?? "—"], ["Planned stops", trip.items.length], ["Empty days", emptyDays], ["Destinations represented", represented]];
    summary.replaceChildren(...facts.map(([label, value]) => { const wrapper = createElement("div"); wrapper.append(createElement("dt", { text: label }), createElement("dd", { text: value })); return wrapper; }));
    const observations = [];
    if (!trip.items.length) observations.push(locale === "ar" ? "لا تحتوي الرحلة على محطات بعد." : "This trip has no stops yet.");
    if (!start || !end) observations.push(locale === "ar" ? "تواريخ الرحلة غير مكتملة." : "Trip dates are not complete.");
    dayNumbers.forEach((day) => {
      const stops = trip.items.filter((item) => item.day_number === day);
      if (!stops.length) observations.push(locale === "ar" ? `اليوم ${day} فارغ.` : `Day ${day} is empty.`);
      if (stops.length > 5) observations.push(locale === "ar" ? `يحتوي اليوم ${day} على عدد كبير من المحطات (${stops.length}).` : `Day ${day} has an unusually high number of stops (${stops.length}).`);
    });
    const missingTimes = trip.items.filter((item) => !item.start_time).length;
    if (missingTimes) observations.push(locale === "ar" ? `${missingTimes} من المحطات بلا وقت زيارة.` : `${missingTimes} ${missingTimes === 1 ? "stop is" : "stops are"} missing a visit time.`);
    if (!observations.length) observations.push(locale === "ar" ? "لم ترصد مراجعة التخطيط أي ملاحظات." : "The planning check found no observations.");
    review.replaceChildren(...observations.map((text) => createElement("li", { text })));
    savedSnapshot = normalizedSnapshot(trip);
    dirtyMetadata = false;
    clearFieldErrors();
    updateMetadataButtons();
    renderItinerary();
    const generation = ++enrichmentGeneration;
    const destinations = trip.items.map((item) => item.destination).filter(Boolean);
    if (destinations.length) {
      void enrichTripDestinations(destinations, locale, locale === "ar" ? "../" : "")
        .then((enriched) => {
          if (generation !== enrichmentGeneration) return;
          destinationEnrichment = enriched;
          renderItinerary();
        })
        .catch(() => {
          // Enrichment is optional; authoritative trip data and controls remain usable.
        });
    } else destinationEnrichment = new Map();
  };

  async function loadTrip({ focus = false } = {}) {
    if (!tripId || activeMutation) return;
    activeMutation = true;
    hideStates();
    setVisible(loading, true);
    loading.setAttribute("aria-busy", "true");
    try {
      const loadedTrip = await getTrip(tripId, { retries: 1 });
      populate(loadedTrip);
      hideStates();
      setVisible(editor, true);
      if (focus) heading.focus();
    } catch (error) {
      if (error.status === 401) {
        showAuthRequired();
      } else if (error.status === 404) {
        showError(t("trips.notFound"), { canRetry: false });
      } else {
        showError(publicErrorMessage(error, t));
      }
    } finally {
      loading.setAttribute("aria-busy", "false");
      activeMutation = false;
      if (trip) mutationControls();
    }
  }

  const refreshTripAfterMutation = async () => {
    const refreshed = await getTrip(tripId);
    populate(refreshed);
    return refreshed;
  };

  async function persistOrder(nextItems, movedItemId) {
    if (activeMutation) return;
    const previousTrip = trip;
    activeMutation = true;
    trip = Object.freeze({ ...trip, items: Object.freeze(orderedItems(nextItems)) });
    renderItinerary();
    try {
      const updated = await reorderTripItems(tripId, {
        expected_version: previousTrip.version,
        items: orderedItems(nextItems).map((item) => ({
          item_id: item.id,
          day_number: item.day_number,
        })),
      });
      populate(updated);
      const moved = updated.items.find((item) => item.id === movedItemId);
      const position =
        updated.items
          .filter((item) => item.day_number === moved.day_number)
          .findIndex((item) => item.id === moved.id) + 1;
      const message = t("trips.stopMoved", {
        name: destinationName(moved, locale),
        day: moved.day_number,
        position,
      });
      toast.success(t("trips.reorderSaved"), { closeLabel: t("common.close") });
      announce(message, { force: true });
      globalThis.setTimeout(() => {
        documentRef
          .querySelector(`[data-stop-id="${movedItemId}"] .trip-stop__handle`)
          ?.focus();
      }, 0);
    } catch (error) {
      trip = previousTrip;
      renderItinerary();
      if (isVersionConflict(error)) showConflict();
      else {
        const message =
          error.status === 409
            ? t("trips.duplicateDestination")
            : t("trips.reorderFailed");
        toast.error(message, { closeLabel: t("common.close") });
        announce(message, { priority: "assertive", force: true });
      }
    } finally {
      activeMutation = false;
      mutationControls();
    }
  }

  async function moveItem(itemId, options = {}) {
    if (activeMutation) return;
    const items = orderedItems(trip.items);
    const moving = items.find((item) => item.id === itemId);
    if (!moving) return;
    const targetDay =
      options.targetDay ??
      moving.day_number + (options.dayOffset ?? 0);
    if (!availableDays(trip).includes(targetDay)) return;
    const groups = new Map(
      availableDays(trip).map((day) => [
        day,
        items.filter((item) => item.day_number === day && item.id !== itemId),
      ]),
    );
    const target = groups.get(targetDay);
    if (targetDay === moving.day_number && options.offset) {
      const originalIndex = items
        .filter((item) => item.day_number === targetDay)
        .findIndex((item) => item.id === itemId);
      const nextIndex = Math.max(
        0,
        Math.min(target.length, originalIndex + options.offset),
      );
      target.splice(nextIndex, 0, { ...moving, day_number: targetDay });
    } else {
      target.push({ ...moving, day_number: targetDay });
    }
    const nextItems = [...groups.entries()].flatMap(([dayNumber, group]) =>
      group.map((item, index) => ({
        ...item,
        day_number: dayNumber,
        sort_order: index,
      })),
    );
    await persistOrder(nextItems, itemId);
  }

  const renderDestinationResults = (
    results,
    container,
    selectDestination,
  ) => {
    container.replaceChildren();
    if (!results.length) {
      container.appendChild(
        createElement("p", { text: t("trips.noDestinationResults") }),
      );
      return;
    }
    results.forEach((destination) => {
      const name = destinationName(destination, locale);
      const button = createElement("button", {
        className: "trip-destination-option",
        attributes: {
          type: "button",
          "aria-label": t("trips.selectDestination", { name }),
          "aria-pressed": "false",
        },
      });
      button.appendChild(createElement("strong", { text: name }));
      const location = [destination.municipality, destination.region]
        .filter(Boolean)
        .join(" — ");
      if (location) button.appendChild(createElement("span", { text: location }));
      button.addEventListener("click", () => {
        container.querySelectorAll("[aria-pressed]").forEach((element) => {
          element.setAttribute("aria-pressed", "false");
        });
        button.setAttribute("aria-pressed", "true");
        selectDestination(destination);
      });
      container.appendChild(button);
    });
  };

  function openStopEditor(item = null, defaultDay = 1) {
    if (activeMutation) return;
    if (!item && trip.items.length >= TRIP_LIMITS.items) {
      toast.warning(t("trips.itemLimit"), { closeLabel: t("common.close") });
      return;
    }
    const modal = createModal({
      title: item ? t("trips.editStop") : t("trips.addStop"),
      className: "app-modal trip-stop-modal",
    });
    activeStopModal = modal;
    const stopForm = createStopForm(trip, t, item, defaultDay);
    let selectedDestination = item?.destination ?? null;
    let destinationError = null;
    let stopSearchCleanup = () => {};

    if (item) {
      modal.content.appendChild(
        createElement("p", {
          text: t("trips.selectedDestination", {
            name: destinationName(item, locale),
          }),
        }),
      );
    } else {
      const searchSection = createElement("section", {
        className: "trip-destination-search",
        attributes: { "aria-labelledby": `destination-search-${item?.id ?? "new"}` },
      });
      searchSection.appendChild(
        createElement("h3", {
          text: t("trips.searchDestinations"),
          attributes: { id: `destination-search-${item?.id ?? "new"}` },
        }),
      );
      const controls = createElement("div", {
        className: "trip-destination-search__controls",
      });
      const query = createElement("input", {
        attributes: {
          type: "search",
          autocomplete: "off",
          maxlength: "250",
          placeholder: t("trips.destinationSearchHint"),
          "aria-label": t("trips.searchDestinations"),
        },
      });
      const searchButton = createElement("button", {
        className: "trips-secondary-button",
        text: t("trips.search"),
        attributes: { type: "button" },
      });
      const results = createElement("div", {
        className: "trip-destination-results",
        attributes: {
          role: "region",
          "aria-label": t("trips.searchResults"),
          "aria-live": "polite",
        },
      });
      destinationError = createElement("p", {
        className: "trips-field-error",
        attributes: { "aria-live": "polite" },
      });
      let searchTimer = null;
      let searchController = null;
      const performSearch = async () => {
        globalThis.clearTimeout(searchTimer);
        searchController?.abort();
        const controller = new AbortController();
        searchController = controller;
        results.setAttribute("aria-busy", "true");
        results.replaceChildren(
          createElement("p", { text: t("common.loading") }),
        );
        setText(destinationError, "");
        setLoading(searchButton, true, {
          disable: true,
          text: t("common.loading"),
        });
        try {
          const response = await searchTripDestinations(query.value, {
            signal: controller.signal,
          });
          if (searchController !== controller) return;
          renderDestinationResults(
            response.items,
            results,
            (destination) => {
              selectedDestination = destination;
              setText(destinationError, "");
            },
          );
        } catch (error) {
          if (error.code === "ABORTED") return;
          setText(destinationError, publicErrorMessage(error, t));
        } finally {
          if (searchController !== controller) return;
          searchController = null;
          results.removeAttribute("aria-busy");
          setLoading(searchButton, false, { disable: true });
          setText(searchButton, t("trips.search"));
        }
      };
      searchButton.addEventListener("click", () => void performSearch());
      query.addEventListener("input", () => {
        globalThis.clearTimeout(searchTimer);
        if (!query.value.trim()) {
          searchController?.abort();
          searchController = null;
          results.removeAttribute("aria-busy");
          results.replaceChildren(
            createElement("p", { text: t("trips.destinationSearchEmpty") }),
          );
          setLoading(searchButton, false, { disable: false });
          setText(searchButton, t("trips.search"));
          return;
        }
        searchTimer = globalThis.setTimeout(
          () => void performSearch(),
          DESTINATION_SEARCH_DEBOUNCE_MS,
        );
      });
      query.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          void performSearch();
        } else if (event.key === "ArrowDown") {
          const firstResult = results.querySelector("button");
          if (firstResult) {
            event.preventDefault();
            firstResult.focus();
          }
        }
      });
      results.addEventListener("keydown", (event) => {
        if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
          return;
        }
        const options = [...results.querySelectorAll("button")];
        const currentIndex = options.indexOf(documentRef.activeElement);
        if (currentIndex < 0 || !options.length) return;
        event.preventDefault();
        const nextIndex =
          event.key === "Home"
            ? 0
            : event.key === "End"
              ? options.length - 1
              : event.key === "ArrowDown"
                ? (currentIndex + 1) % options.length
                : (currentIndex - 1 + options.length) % options.length;
        options[nextIndex].focus();
      });
      results.appendChild(
        createElement("p", { text: t("trips.destinationSearchEmpty") }),
      );
      stopSearchCleanup = () => {
        globalThis.clearTimeout(searchTimer);
        searchController?.abort();
      };
      controls.append(query, searchButton);
      searchSection.append(controls, destinationError, results);
      modal.content.appendChild(searchSection);
      searchTimer = globalThis.setTimeout(() => void performSearch(), 0);
    }

    modal.content.appendChild(stopForm.form);
    const cancelButton = createElement("button", {
      className: "trips-secondary-button",
      text: t("common.cancel"),
      attributes: { type: "button" },
    });
    const submitButton = createElement("button", {
      className: "trips-primary-button",
      text: t("common.save"),
      attributes: { type: "submit" },
    });
    stopForm.form.appendChild(submitButton);
    const close = () => {
      stopSearchCleanup();
      modal.close();
      modal.destroy();
      activeStopModal = null;
    };
    cancelButton.addEventListener("click", close);
    modal.actions.appendChild(cancelButton);
    stopForm.form.addEventListener("input", (event) => {
      const fieldName = event.target?.name;
      if (!fieldName) return;
      const output = stopForm.form.querySelector(
        `[data-stop-error-for="${CSS.escape(fieldName)}"]`,
      );
      if (output) setText(output, "");
      event.target.removeAttribute("aria-invalid");
    });
    stopForm.form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (activeMutation || submitButton.disabled) return;
      setText(stopForm.error, "");
      setVisible(stopForm.error, false);
      if (!selectedDestination) {
        setText(destinationError, t("trips.destinationRequired"));
        return;
      }
      let payload;
      try {
        payload = stopPayload(stopForm.form, trip.version);
      } catch (error) {
        const errorText = String(error.message);
        const fieldName = errorText.startsWith("notes")
          ? "notes"
          : errorText;
        const message =
          fieldName === "duration_minutes"
            ? t("trips.durationInvalid")
            : fieldName === "notes"
              ? t("trips.notesTooLong")
              : t("trips.dayInvalid");
        const output = stopForm.form.querySelector(
          `[data-stop-error-for="${CSS.escape(fieldName)}"]`,
        );
        setText(output, message);
        const invalidField = stopForm.form.elements.namedItem(fieldName);
        invalidField?.setAttribute("aria-invalid", "true");
        invalidField?.focus();
        return;
      }
      activeMutation = true;
      modal.setCritical(true);
      cancelButton.disabled = true;
      setLoading(submitButton, true, {
        disable: true,
        text: t("trips.saving"),
      });
      try {
        if (item) {
          await updateTripItem(tripId, item.id, payload);
        } else {
          await addTripItem(tripId, {
            ...payload,
            destination_id: selectedDestination.id,
          });
        }
        await refreshTripAfterMutation();
        modal.setCritical(false);
        close();
        const message = item ? t("trips.stopUpdated") : t("trips.stopAdded");
        toast.success(message, { closeLabel: t("common.close") });
        announce(message, { force: true });
      } catch (error) {
        modal.setCritical(false);
        if (isVersionConflict(error)) {
          showConflict();
        } else {
          const message =
            error.status === 409
              ? t("trips.duplicateDestination")
              : publicErrorMessage(error, t);
          setText(stopForm.error, message);
          setVisible(stopForm.error, true);
          announce(message, { priority: "assertive", force: true });
        }
      } finally {
        activeMutation = false;
        cancelButton.disabled = false;
        setLoading(submitButton, false, { disable: true });
        setText(submitButton, t("common.save"));
        mutationControls();
      }
    });
    modal.open();
  }

  function openDeleteStop(item) {
    if (activeMutation) return;
    const name = destinationName(item, locale);
    const modal = createModal({
      title: t("trips.deleteStopTitle"),
      className: "app-modal trip-stop-delete-modal",
    });
    const message = createElement("p", {
      text: t("trips.deleteStopMessage", { name }),
    });
    const errorText = createElement("p", {
      className: "trips-form-error",
      attributes: { role: "alert", hidden: "" },
    });
    const cancelButton = createElement("button", {
      className: "trips-secondary-button",
      text: t("common.cancel"),
      attributes: { type: "button" },
    });
    const deleteButton = createElement("button", {
      className: "trips-danger-button",
      text: t("common.delete"),
      attributes: { type: "button" },
    });
    const close = () => {
      modal.close();
      modal.destroy();
    };
    cancelButton.addEventListener("click", close);
    deleteButton.addEventListener("click", async () => {
      if (activeMutation || deleteButton.disabled) return;
      activeMutation = true;
      modal.setCritical(true);
      cancelButton.disabled = true;
      setLoading(deleteButton, true, {
        disable: true,
        text: t("trips.saving"),
      });
      try {
        await deleteTripItem(tripId, item.id, trip.version);
        await refreshTripAfterMutation();
        modal.setCritical(false);
        close();
        toast.success(t("trips.stopDeleted"), { closeLabel: t("common.close") });
        announce(t("trips.stopDeleted"), { force: true });
        addStop.focus();
      } catch (error) {
        modal.setCritical(false);
        if (isVersionConflict(error)) {
          showConflict();
        } else {
          const text = publicErrorMessage(error, t);
          setText(errorText, text);
          setVisible(errorText, true);
        }
      } finally {
        activeMutation = false;
        cancelButton.disabled = false;
        setLoading(deleteButton, false, { disable: true });
        setText(deleteButton, t("common.delete"));
        mutationControls();
      }
    });
    modal.content.append(message, errorText);
    modal.actions.append(cancelButton, deleteButton);
    modal.open();
  }

  const updateDirtyMetadata = (event) => {
    const field = event?.target;
    if (field?.name) {
      field.removeAttribute("aria-invalid");
      const output = form.querySelector(
        `[data-error-for="${CSS.escape(field.name)}"]`,
      );
      if (output) setText(output, "");
    }
    try {
      dirtyMetadata = normalizedSnapshot(formPayload(form)) !== savedSnapshot;
    } catch {
      dirtyMetadata = true;
    }
    updateMetadataButtons();
  };
  form.addEventListener("input", updateDirtyMetadata);
  form.addEventListener("change", updateDirtyMetadata);

  cancel.addEventListener("click", () => {
    if (activeMutation || !trip) return;
    populate(trip);
    announce(t("trips.changesDiscarded"), { force: true });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (activeMutation || save.disabled || !trip) return;
    clearFieldErrors();
    let payload;
    try {
      payload = formPayload(form);
      validateDateRange(payload.start_date, payload.end_date);
    } catch (error) {
      const errorText = String(error.message);
      const field = errorText.startsWith("title")
        ? "title"
        : errorText.startsWith("description")
          ? "description"
          : "end_date";
      const message =
        field === "title"
          ? errorText.includes("exceed")
            ? t("trips.titleTooLong")
            : t("trips.titleRequired")
          : field === "description"
            ? t("trips.descriptionTooLong")
            : t("trips.dateRangeInvalid");
      setFieldError(field, message);
      form.elements.namedItem(field)?.focus();
      return;
    }
    activeMutation = true;
    cancel.disabled = true;
    setLoading(save, true, {
      disable: true,
      text: t("trips.saving"),
    });
    try {
      const updated = await updateTrip(tripId, {
        ...payload,
        expected_version: trip.version,
      });
      populate(updated);
      toast.success(t("trips.metadataSaved"), { closeLabel: t("common.close") });
      announce(t("trips.metadataSaved"), { force: true });
    } catch (error) {
      if (error.status === 401) {
        showAuthRequired();
      } else if (isVersionConflict(error)) {
        showConflict();
      } else {
        Object.keys(error.fieldErrors ?? {}).forEach((name) => {
          setFieldError(name.split(".").at(-1), t("errors.validation"));
        });
        const message = publicErrorMessage(error, t);
        setText(formError, message);
        setVisible(formError, true);
        announce(message, { priority: "assertive", force: true });
      }
    } finally {
      activeMutation = false;
      setLoading(save, false, { disable: true });
      setText(save, t("trips.saveChanges"));
      mutationControls();
    }
  });

  addStop.addEventListener("click", () => openStopEditor());
  editTripDetails.addEventListener("click", () => {
    const willOpen = form.hidden;
    form.hidden = !willOpen;
    editTripDetails.setAttribute("aria-expanded", String(willOpen));
    if (willOpen) form.elements.namedItem("title")?.focus();
  });
  retry.addEventListener("click", () => void loadTrip({ focus: true }));
  globalThis.addEventListener("visitlibya:auth-expired", showAuthRequired);
  globalThis.addEventListener("beforeunload", (event) => {
    if (!dirtyMetadata) return;
    event.preventDefault();
    event.returnValue = t("trips.unsavedWarning");
  });

  if (!tripId) {
    showError(t("trips.invalidId"), { canRetry: false });
    return;
  }
  if (!context.session.authenticated) {
    showAuthRequired();
    return;
  }
  await loadTrip();
}

if (typeof document !== "undefined") {
  void initializeTripEditor();
}

export {
  availableDays,
  destinationName,
  orderedItems,
  readTripId,
  tripDayCount,
};
