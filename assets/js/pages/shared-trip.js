import {
  getPublicTrip,
  getSharedTrip,
} from "../app/api/trips-api.js";
import { bootstrap } from "../app/bootstrap.js";
import { configureAtlasExternalLink } from "../app/config/runtime-config.js";
import {
  enrichTripDestinations,
} from "../app/trips/destination-enrichment.js";
import { announce } from "../app/ui/announcer.js";
import {
  createElement,
  queryRequired,
  setText,
  setVisible,
} from "../app/utils/dom.js";

const DESTINATION_SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

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

function renderSharedTripHero(
  root,
  trip,
  locale,
  destinationEnrichment,
) {
  const media = queryRequired(
    "[data-shared-trip-hero-media]",
    root,
  );
  const source = queryRequired(
    "[data-shared-trip-hero-source]",
    root,
  );
  const image = queryRequired(
    "[data-shared-trip-hero-image]",
    root,
  );
  const title = queryRequired(
    "[data-shared-trip-hero-title]",
    root,
  );
  const description = queryRequired(
    "[data-shared-trip-hero-description]",
    root,
  );

  setText(title, trip.title);

  setText(
    description,
    trip.description ||
      (
        locale === "ar"
          ? "استعرض محطات هذه الرحلة السياحية عبر ليبيا."
          : "Explore the destinations included in this journey across Libya."
      ),
  );

  const heroContext = orderedItems(trip.items ?? [])
    .map((item) =>
      destinationEnrichment.get(
        Number(item.destination?.id),
      ),
    )
    .find((context) => context?.image);

  if (!heroContext?.image) {
    media.hidden = true;
    source.removeAttribute("srcset");
    return;
  }

  image.src = heroContext.image;
  image.alt =
    heroContext.imageAlt ||
    trip.title ||
    (
      locale === "ar"
        ? "صورة الرحلة السياحية"
        : "Trip destination image"
    );

  if (heroContext.imageSrcset) {
    source.srcset = heroContext.imageSrcset;
  } else if (heroContext.imageWebp) {
    source.srcset = heroContext.imageWebp;
  } else {
    source.removeAttribute("srcset");
  }

  image.addEventListener(
    "error",
    () => {
      media.hidden = true;
      source.removeAttribute("srcset");
    },
    { once: true },
  );

  media.hidden = false;
}

function renderTrip(
  root,
  trip,
  locale,
  destinationEnrichment = new Map(),
) {
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
        const card = createElement("article", {
          className: "trip-stop",
          attributes: {
            "data-stop-id": item.id,
            tabindex: "-1",
          },
        });
        const enrichment = destinationEnrichment.get(
          Number(item.destination?.id),
        );

        const media = createElement("div", {
          className: "trip-stop__media",
        });

        if (enrichment?.image) {
          const image = createElement("img", {
            attributes: {
              src: enrichment.image,
              alt:
                enrichment.imageAlt ||
                destinationName(item.destination, locale),
              width: "240",
              height: "160",
              loading: "lazy",
              decoding: "async",
            },
          });

          image.addEventListener(
            "error",
            () => {
              media.replaceChildren();
              media.classList.add("is-fallback");
              media.setAttribute("aria-hidden", "true");
            },
            { once: true },
          );

          if (enrichment.imageWebp) {
            const picture = createElement("picture", {
              className: "responsive-picture",
            });

            const source = createElement("source", {
              attributes: {
                type: "image/webp",
                srcset:
                  enrichment.imageSrcset ||
                  enrichment.imageWebp,
                sizes:
                  "(max-width: 480px) calc(100vw - 5rem), 240px",
              },
            });

            picture.append(source, image);
            media.appendChild(picture);
          } else {
            media.appendChild(image);
          }
        } else {
          media.classList.add("is-fallback");
          media.setAttribute("aria-hidden", "true");
        }

        const content = createElement("div", {
          className: "trip-stop__content",
        });

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

        const destinationContext = [
          enrichment?.category,
          enrichment?.location,
        ].filter(Boolean);

        if (destinationContext.length) {
          content.appendChild(
            createElement("p", {
              className: "trip-stop__context",
              text: destinationContext.join(" · "),
            }),
          );
        }

        if (enrichment?.description) {
          content.appendChild(
            createElement("p", {
              className: "trip-stop__description",
              text: enrichment.description,
            }),
          );
        }

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

        const links = createElement("div", {
          className: "trip-stop__links",
        });

        if (DESTINATION_SLUG_PATTERN.test(slug)) {
          links.appendChild(
            createElement("a", {
              className: "trip-stop__destination-link",
              text:
                locale === "ar"
                  ? "عرض الوجهة"
                  : "View destination",
              attributes: {
                href:
                  `destination.html?slug=${encodeURIComponent(slug)}`,
              },
            }),
          );
        }

        const atlasLink = createElement("a", {
          className: "trip-stop__destination-link",
          text:
            locale === "ar"
              ? "استكشف في الأطلس"
              : "Explore in Atlas",
        });

        configureAtlasExternalLink(atlasLink, {
          locale,
          context: destinationName(
            item.destination,
            locale,
          ),
        });

        links.appendChild(atlasLink);
        content.appendChild(links);

        card.append(media, content);
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
  const printButton = queryRequired(
    "[data-shared-trip-print]",
    documentRef,
  );
  const mapRoot = queryRequired("[data-shared-trip-map]", documentRef);
  const mapFailure = queryRequired(
    "[data-shared-trip-map-failure]",
    documentRef,
  );

  const highlightStopFromMap = (stop) => {
    const card = documentRef.querySelector(
      `[data-stop-id="${CSS.escape(String(stop.itemId))}"]`,
    );

    if (!(card instanceof HTMLElement)) return;

    documentRef
      .querySelectorAll(".is-map-highlighted")
      .forEach((element) => {
        element.classList.remove("is-map-highlighted");
      });

    card.classList.add("is-map-highlighted");
    card.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
    card.focus({ preventScroll: true });

    globalThis.setTimeout(() => {
      card.classList.remove("is-map-highlighted");
    }, 2400);
  };

  const renderSharedTripMap = async (trip) => {
    try {
      const { createTripMap } = await import("../app/map/trip-map.js");

      const controller = createTripMap({
        root: mapRoot,
        locale,
        onMarkerActivate: highlightStopFromMap,
      });

      controller.update(trip);
      mapFailure.hidden = true;
    } catch {
      mapFailure.hidden = false;
      mapRoot.dataset.mapState = "failed";
    }
  };

  printButton.addEventListener("click", () => {
    globalThis.print?.();
  });

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

    let destinationEnrichment = new Map();

    try {
      destinationEnrichment = await enrichTripDestinations(
        (trip.items ?? [])
          .map((item) => item.destination)
          .filter(Boolean),
        locale,
        locale === "ar" ? "../" : "",
      );
    } catch {
      // Enrichment is optional. Core itinerary data remains usable.
    }

    renderSharedTripHero(
      documentRef,
      trip,
      locale,
      destinationEnrichment,
    );

    renderTrip(
      documentRef,
      trip,
      locale,
      destinationEnrichment,
    );

    await renderSharedTripMap(trip);

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
