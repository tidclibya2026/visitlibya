function normalizeSlug(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase();
}


export async function enrichPlannerDestinationsWithCoordinates(
  destinations,
  {
    listDestinationCatalogue,
  },
) {
  if (!Array.isArray(destinations)) {
    return [];
  }

  if (typeof listDestinationCatalogue !== "function") {
    throw new TypeError(
      "listDestinationCatalogue dependency is required",
    );
  }

  const requiredSlugs = new Set(
    destinations
      .map((destination) =>
        normalizeSlug(destination?.slug),
      )
      .filter(Boolean),
  );

  const catalogueBySlug = new Map();

  let page = 1;
  let pageCount = Number.POSITIVE_INFINITY;

  while (
    page <= pageCount &&
    catalogueBySlug.size < requiredSlugs.size
  ) {
    const payload =
      await listDestinationCatalogue(page);

    if (!payload || !Array.isArray(payload.items)) {
      throw new TypeError(
        "Invalid destination catalogue response",
      );
    }

    for (const item of payload.items) {
      const slug =
        normalizeSlug(item?.slug);

      if (!requiredSlugs.has(slug)) {
        continue;
      }

      const rawLatitude = item?.latitude;
      const rawLongitude = item?.longitude;

      const latitude =
        rawLatitude === null ||
        rawLatitude === undefined ||
        rawLatitude === ""
          ? null
          : Number(rawLatitude);

      const longitude =
        rawLongitude === null ||
        rawLongitude === undefined ||
        rawLongitude === ""
          ? null
          : Number(rawLongitude);

      catalogueBySlug.set(slug, {
        latitude:
          Number.isFinite(latitude)
            ? latitude
            : null,

        longitude:
          Number.isFinite(longitude)
            ? longitude
            : null,
      });
    }

    const pages = Number(payload.pages);

    pageCount =
      Number.isSafeInteger(pages) && pages >= 1
        ? pages
        : page;

    page += 1;
  }

  return destinations.map((destination) => {
    const slug =
      normalizeSlug(destination?.slug);

    const catalogue =
      catalogueBySlug.get(slug);

    if (!catalogue) {
      return {
        ...destination,
      };
    }

    return {
      ...destination,

      latitude:
        catalogue.latitude ??
        destination.latitude ??
        null,

      longitude:
        catalogue.longitude ??
        destination.longitude ??
        null,
    };
  });
}
