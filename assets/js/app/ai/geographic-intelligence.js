const REGION_DESTINATIONS = Object.freeze({
  northwest: new Set([
    "tripoli",
    "sabratha",
    "leptis-magna",
    "villa-sileen",
    "nafusa",
  ]),

  east: new Set([
    "benghazi",
    "green-mountain",
    "bomba-bay",
  ]),

  easternOases: new Set([
    "awjila",
  ]),

  westernDesert: new Set([
    "ghadames",
  ]),

  southwest: new Set([
    "acacus",
    "desert",
  ]),
});


const STARTING_REGION = Object.freeze({
  tripoli: "northwest",
  benghazi: "east",
  sebha: "southwest",
});


const REGION_NEIGHBORS = Object.freeze({
  northwest: new Set([
    "westernDesert",
  ]),

  east: new Set([
    "easternOases",
  ]),

  easternOases: new Set([
    "east",
    "southwest",
  ]),

  westernDesert: new Set([
    "northwest",
    "southwest",
  ]),

  southwest: new Set([
    "westernDesert",
    "easternOases",
  ]),
});


function normalize(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase();
}


export function destinationRegion(destination) {
  const slug = normalize(destination?.slug);

  for (const [region, slugs] of Object.entries(
    REGION_DESTINATIONS,
  )) {
    if (slugs.has(slug)) {
      return region;
    }
  }

  return "unknown";
}


export function startingRegion(startingPoint) {
  return STARTING_REGION[
    normalize(startingPoint)
  ] ?? "unknown";
}


export function maxMajorRegionsForDays(days) {
  const parsed = Number(days);

  if (!Number.isFinite(parsed)) {
    return 1;
  }

  if (parsed <= 3) {
    return 1;
  }

  if (parsed <= 6) {
    return 2;
  }

  return 3;
}


export function regionRelationship(
  sourceRegion,
  targetRegion,
) {
  if (
    !sourceRegion ||
    !targetRegion ||
    sourceRegion === "unknown" ||
    targetRegion === "unknown"
  ) {
    return "unknown";
  }

  if (sourceRegion === targetRegion) {
    return "same";
  }

  if (
    REGION_NEIGHBORS[sourceRegion]?.has(
      targetRegion,
    )
  ) {
    return "adjacent";
  }

  return "distant";
}


export function geographicPenalty({
  destination,
  startingPoint,
  days,
}) {
  const tripRegion =
    startingRegion(startingPoint);

  const candidateRegion =
    destinationRegion(destination);

  const relationship =
    regionRelationship(
      tripRegion,
      candidateRegion,
    );

  const maxRegions =
    maxMajorRegionsForDays(days);

  if (relationship === "same") {
    return 0;
  }

  if (relationship === "adjacent") {
    if (maxRegions === 1) {
      return 30;
    }

    return 8;
  }

  if (relationship === "distant") {
    if (days <= 3) {
      return 70;
    }

    if (days <= 6) {
      return 40;
    }

    return 15;
  }

  return 10;
}


export function itineraryRegionCount(
  destinations,
) {
  return new Set(
    destinations
      .map(destinationRegion)
      .filter((region) =>
        region !== "unknown",
      ),
  ).size;
}


export function geographicallyAllowed(
  destinations,
  days,
) {
  return (
    itineraryRegionCount(destinations) <=
    maxMajorRegionsForDays(days)
  );
}
