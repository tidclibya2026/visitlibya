import {
  getPublicTrip,
  getSharedTrip,
} from "../app/api/trips-api.js";
import { bootstrap } from "../app/bootstrap.js";
import { announce } from "../app/ui/announcer.js";
import {
  createElement,
  queryRequired,
  setText,
  setVisible,
} from "../app/utils/dom.js";

function readViewerRequest(search = globalThis.location?.search ?? "") {
  const params = new URLSearchParams(search);
  const ids = params.getAll("id");
  const tokens = params.getAll("token");

  if (ids.length === 1 && tokens.length === 0 && /^[1-9]\d*$/.test(ids[0])) {
    const id = Number(ids[0]);
    if (Number.isSafeInteger(id)) {
      return Object.freeze({ type: "public", value: id });
    }
  }

  if (
    tokens.length === 1 &&
    ids.length === 0 &&
    tokens[0].length >= 20 &&
    tokens[0].length <= 128
  ) {
    return Object.freeze({ type: "shared", value: tokens[0] });
  }

  return null;
}

function destinationName(destination, locale) {
  return (
    (locale === "ar" ? destination?.name_ar : destination?.name_en) ||
    destination?.name_en ||
    destination?.name_ar ||
    destination?.slug ||
    ""
  );
}

function orderedItems(items = []) {
  return [...items].sort(
    (a, b) =>
      a.day_number - b.day_number ||
      a.sort_order - b.sort_order ||
      a.id - b.id,
  );
}

function renderTrip(root, trip, locale) {
  setText(queryRequired("[data-shared-trip-title]", root), trip.title);

  const description = queryRequired("[data-shared-trip-description]", root);
  setText(description, trip.description ?? "");
  setVisible(description, Boolean(trip.description));

  const itinerary = queryRequired("[data-shared-trip-itinerary]", root);
  itinerary.replaceChildren();

  const items = orderedItems(trip.items);

  if (!items.length) {
    itinerary.appendChild(createElement("p", {
      text: locale === "ar"
        ? "لا توجد محطات في هذه الرحلة."
        : "This trip has no itinerary stops.",
    }));
    return;
  }

  [...new Set(items.map((item) => item.day_number))].forEach((day) => {
    const section = createElement("section", { className: "trip-day" });

    section.appendChild(createElement("h3", {
      text: locale === "ar" ? `اليوم ${day}` : `Day ${day}`,
    }));

    const list = createElement("div", { className: "trip-stop-list" });

    items
      .filter((item) => item.day_number === day)
      .forEach((item, index) => {
        const card = createElement("article", { className: "trip-stop" });
        const content = createElement("div", { className: "trip-stop__content" });

        content.append(
          createElement("span", {
            className: "trip-stop__sequence",
            text: locale === "ar"
              ? `المحطة ${index + 1}`
              : `Stop ${index + 1}`,
          }),
          createElement("h4", {
            text: destinationName(item.destination, locale),
          }),
        );

        if (item.start_time || item.duration_minutes) {
          content.appendChild(createElement("p", {
            className: "trip-stop__meta",
            text: [
              item.start_time?.slice(0, 5),
              item.duration_minutes
                ? locale === "ar"
                  ? `${item.duration_minutes} دقيقة`
                  : `${item.duration_minutes} minutes`
                : null,
            ].filter(Boolean).join(" · "),
          }));
        }

        if (item.notes) {
          content.appendChild(createElement("p", {
            className: "trip-stop__notes",
            text: item.notes,
          }));
        }

        const slug = String(item.destination?.slug ?? "");
        if (/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
          content.appendChild(createElement("a", {
            className: "trip-stop__destination-link",
            text: locale === "ar" ? "عرض الوجهة" : "View destination",
            attributes: {
              href: `destination.html?slug=${encodeURIComponent(slug)}`,
            },
          }));
        }

        card.appendChild(content);
        list.appendChild(card);
      });

    section.appendChild(list);
    itinerary.appendChild(section);
  });
}

async function initializeSharedTripPage(documentRef = document) {
  const context = await bootstrap();
  if (!context) return;

  const { config, locale } = context;

  const loading = queryRequired("[data-shared-trip-loading]", documentRef);
  const error = queryRequired("[data-shared-trip-error]", documentRef);
  const errorMessage = queryRequired(
    "[data-shared-trip-error-message]",
    documentRef,
  );
  const content = queryRequired("[data-shared-trip-content]", documentRef);

  const request = readViewerRequest();

  if (!config.apiEnabled || !request) {
    setVisible(loading, false);
    setText(
      errorMessage,
      locale === "ar"
        ? "رابط الرحلة غير صالح أو أن الخدمة غير متاحة حاليًا."
        : "The trip link is invalid or the service is currently unavailable.",
    );
    setVisible(error, true);
    return;
  }

  try {
    const trip = request.type === "public"
      ? await getPublicTrip(request.value, { retries: 1 })
      : await getSharedTrip(request.value, { retries: 1 });

    renderTrip(documentRef, trip, locale);
    setVisible(loading, false);
    setVisible(error, false);
    setVisible(content, true);
  } catch (failure) {
    setVisible(loading, false);
    setVisible(content, false);
    setText(
      errorMessage,
      failure.status === 404
        ? locale === "ar"
          ? "لم تعد هذه الرحلة متاحة عبر هذا الرابط."
          : "This trip is no longer available through this link."
        : locale === "ar"
          ? "تعذر تحميل الرحلة المشتركة."
          : "The shared trip could not be loaded.",
    );
    setVisible(error, true);
    announce(errorMessage.textContent, {
      priority: "assertive",
      force: true,
    });
  }
}

if (typeof document !== "undefined") {
  void initializeSharedTripPage();
}

export {
  initializeSharedTripPage,
  orderedItems,
  readViewerRequest,
};
