import {
  destinationRegion,
  regionRelationship,
} from "./geographic-intelligence.js";


export function requiresTravelDay(
  previousDestination,
  nextDestination,
) {
  if (!previousDestination || !nextDestination) {
    return false;
  }

  const previousRegion =
    destinationRegion(previousDestination);

  const nextRegion =
    destinationRegion(nextDestination);

  return (
    regionRelationship(
      previousRegion,
      nextRegion,
    ) === "distant"
  );
}


export function buildTravelAwareSequence(
  destinations,
) {
  if (!Array.isArray(destinations)) {
    return [];
  }

  const result = [];

  let previousDestination = null;

  for (const destination of destinations) {
    if (
      previousDestination &&
      requiresTravelDay(
        previousDestination,
        destination,
      )
    ) {
      result.push({
        type: "travel",
        fromRegion:
          destinationRegion(
            previousDestination,
          ),
        toRegion:
          destinationRegion(
            destination,
          ),
      });
    }

    result.push({
      type: "destination",
      destination,
    });

    previousDestination = destination;
  }

  return result;
}
