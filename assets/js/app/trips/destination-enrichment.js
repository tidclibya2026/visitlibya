import {
  listTripDestinationCatalogue,
} from "../api/trips-api.js";
import { curatedDestinations } from "../../data/curated-destinations.js";
import { resolveResponsiveImage } from "../../data/responsive-images.js";

const DESTINATION_SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const destinationCatalogueById = new Map();
const destinationCatalogueBySlug = new Map();

const curatedDestinationBySlug = new Map(
  curatedDestinations.map((item) => [item.slug, item]),
);

let nextDestinationPage = 1;
let destinationPageCount = Number.POSITIVE_INFINITY;
let destinationPageRequest = null;

function safeDestinationText(value) {
  return typeof value === "string" && value.trim()
    ? value.trim()
    : "";
}

export function validDestinationIdentity(destination) {
  const id = Number(destination?.id);
  const slug = safeDestinationText(destination?.slug).toLowerCase();

  return Number.isSafeInteger(id) &&
    id > 0 &&
    DESTINATION_SLUG_PATTERN.test(slug)
    ? { id, slug }
    : null;
}

function localizedDestinationName(value, locale) {
  return (
    safeDestinationText(
      locale === "ar" ? value?.name_ar : value?.name_en,
    ) ||
    safeDestinationText(
      locale === "ar" ? value?.name_en : value?.name_ar,
    )
  );
}

function destinationCoordinates(...sources) {
  for (const source of sources) {
    const { latitude, longitude } = source ?? {};

    if (
      Number.isFinite(latitude) &&
      latitude >= -90 &&
      latitude <= 90 &&
      Number.isFinite(longitude) &&
      longitude >= -180 &&
      longitude <= 180
    ) {
      return Object.freeze({ latitude, longitude });
    }
  }

  return null;
}

async function loadNextDestinationPage() {
  if (nextDestinationPage > destinationPageCount) return;

  if (!destinationPageRequest) {
    const requestedPage = nextDestinationPage;

    destinationPageRequest = listTripDestinationCatalogue(requestedPage)
      .then((payload) => {
        if (!payload || !Array.isArray(payload.items)) {
          throw new TypeError(
            "Invalid destination catalogue response",
          );
        }

        payload.items.forEach((item) => {
          const identity = validDestinationIdentity(item);
          if (!identity) return;

          destinationCatalogueById.set(identity.id, item);
          destinationCatalogueBySlug.set(identity.slug, item);
        });

        const pages = Number(payload.pages);

        destinationPageCount =
          Number.isSafeInteger(pages) && pages >= 0
            ? pages
            : requestedPage;

        nextDestinationPage = requestedPage + 1;
      })
      .finally(() => {
        destinationPageRequest = null;
      });
  }

  await destinationPageRequest;
}

function findDestinationCatalogueItem(identity) {
  const byId = destinationCatalogueById.get(identity.id);

  if (
    byId &&
    safeDestinationText(byId.slug).toLowerCase() === identity.slug
  ) {
    return byId;
  }

  const bySlug = destinationCatalogueBySlug.get(identity.slug);

  return Number(bySlug?.id) === identity.id
    ? bySlug
    : null;
}

function mergeDestinationContext(
  destination,
  locale,
  pathPrefix,
) {
  const identity = validDestinationIdentity(destination);
  if (!identity) return null;

  const api = findDestinationCatalogueItem(identity);
  const curated = curatedDestinationBySlug.get(identity.slug);

  const imageSource = safeDestinationText(curated?.image);

  const responsive = imageSource
    ? resolveResponsiveImage(imageSource, pathPrefix)
    : null;

  const municipality = safeDestinationText(api?.municipality);
  const region = safeDestinationText(api?.region);

  return Object.freeze({
    category:
      localizedDestinationName(api?.category, locale) ||
      safeDestinationText(
        locale === "ar"
          ? curated?.category_ar
          : curated?.category_en,
      ),

    location:
      [...new Set([municipality, region].filter(Boolean))].join(
        " · ",
      ) ||
      safeDestinationText(
        locale === "ar"
          ? curated?.region_ar
          : curated?.region_en,
      ),

    description:
      safeDestinationText(
        locale === "ar"
          ? api?.short_description_ar
          : api?.short_description_en,
      ) ||
      safeDestinationText(
        locale === "ar"
          ? api?.short_description_en
          : api?.short_description_ar,
      ) ||
      safeDestinationText(
        locale === "ar"
          ? curated?.description_ar
          : curated?.description_en,
      ),

    image: imageSource
      ? `${pathPrefix}${imageSource}`
      : "",

    imageAlt:
      safeDestinationText(
        locale === "ar"
          ? curated?.image_alt_ar
          : curated?.image_alt_en,
      ) ||
      localizedDestinationName(destination, locale),

    imageWebp: responsive?.webp ?? "",
    imageSrcset: responsive?.srcset ?? "",

    coordinates: destinationCoordinates(
      destination,
      api,
    ),
  });
}

export async function enrichTripDestinations(
  destinations,
  locale,
  pathPrefix = "",
) {
  const identities = [
    ...new Map(
      destinations
        .map(validDestinationIdentity)
        .filter(Boolean)
        .map((item) => [item.id, item]),
    ).values(),
  ];

  while (
    identities.some(
      (identity) =>
        !findDestinationCatalogueItem(identity),
    ) &&
    nextDestinationPage <= destinationPageCount
  ) {
    await loadNextDestinationPage();
  }

  return new Map(
    destinations
      .map((destination) => [
        Number(destination?.id),
        mergeDestinationContext(
          destination,
          locale,
          pathPrefix,
        ),
      ])
      .filter(
        ([id, value]) =>
          Number.isSafeInteger(id) && value,
      ),
  );
}
