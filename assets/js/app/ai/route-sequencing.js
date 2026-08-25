const REGION_ROUTE_ORDER = Object.freeze({
  northwest: [
    "tripoli",
    "leptis-magna",
    "villa-sileen",
    "sabratha",
    "nafusa",
  ],

  east: [
    "benghazi",
    "green-mountain",
    "bomba-bay",
  ],

  easternOases: [
    "awjila",
  ],

  westernDesert: [
    "ghadames",
  ],

  southwest: [
    "desert",
    "acacus",
  ],
});


function normalize(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase();
}


export function routePosition(
  destination,
  region,
) {
  const slug = normalize(destination?.slug);

  const route =
    REGION_ROUTE_ORDER[region] ?? [];

  const index = route.indexOf(slug);

  return index === -1
    ? Number.POSITIVE_INFINITY
    : index;
}


export function orderDestinationsWithinRegion(
  destinations,
  region,
) {
  return [...destinations].sort((left, right) => {
    const leftPosition =
      routePosition(left, region);

    const rightPosition =
      routePosition(right, region);

    if (leftPosition !== rightPosition) {
      return leftPosition - rightPosition;
    }

    return normalize(left?.slug)
      .localeCompare(normalize(right?.slug));
  });
}
