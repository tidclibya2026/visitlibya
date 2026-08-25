const EARTH_RADIUS_KM = 6371;

const STARTING_POINT_COORDINATES = Object.freeze({
  tripoli: Object.freeze({
    latitude: 32.8872,
    longitude: 13.1913,
  }),

  benghazi: Object.freeze({
    latitude: 32.1167,
    longitude: 20.0667,
  }),

  sebha: Object.freeze({
    latitude: 27.0377,
    longitude: 14.4283,
  }),
});


function toRadians(value) {
  return value * Math.PI / 180;
}


export function startingPointCoordinates(
  startingPoint,
) {
  const key = String(startingPoint ?? "")
    .trim()
    .toLowerCase();

  return STARTING_POINT_COORDINATES[key] ?? null;
}


export function validCoordinates(value) {
  const latitude = Number(value?.latitude);
  const longitude = Number(value?.longitude);

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  if (
    latitude < -90 ||
    latitude > 90 ||
    longitude < -180 ||
    longitude > 180
  ) {
    return null;
  }

  return Object.freeze({
    latitude,
    longitude,
  });
}


export function distanceKm(
  source,
  target,
) {
  const start = validCoordinates(source);
  const end = validCoordinates(target);

  if (!start || !end) {
    return null;
  }

  const latitudeDelta =
    toRadians(
      end.latitude - start.latitude,
    );

  const longitudeDelta =
    toRadians(
      end.longitude - start.longitude,
    );

  const startLatitude =
    toRadians(start.latitude);

  const endLatitude =
    toRadians(end.latitude);

  const a =
    Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(startLatitude) *
      Math.cos(endLatitude) *
      Math.sin(longitudeDelta / 2) ** 2;

  const c =
    2 * Math.atan2(
      Math.sqrt(a),
      Math.sqrt(1 - a),
    );

  return EARTH_RADIUS_KM * c;
}


export function distanceBand(distance) {
  if (
    distance === null ||
    !Number.isFinite(distance)
  ) {
    return "unknown";
  }

  if (distance <= 80) {
    return "local";
  }

  if (distance <= 250) {
    return "regional";
  }

  if (distance <= 600) {
    return "long";
  }

  return "very-long";
}


export function coordinateTravelPenalty({
  source,
  target,
  days,
  pace = "balanced",
}) {
  const distance =
    distanceKm(source, target);

  if (distance === null) {
    return {
      distanceKm: null,
      band: "unknown",
      penalty: 0,
    };
  }

  const band = distanceBand(distance);

  let penalty = 0;

  if (band === "regional") {
    penalty = 5;
  }

  if (band === "long") {
    penalty =
      Number(days) <= 3
        ? 45
        : 18;
  }

  if (band === "very-long") {
    if (Number(days) <= 3) {
      penalty = 100;
    } else if (Number(days) <= 6) {
      penalty = 60;
    } else {
      penalty = 25;
    }
  }

  if (pace === "relaxed") {
    penalty +=
      band === "regional"
        ? 5
        : band === "long"
          ? 10
          : band === "very-long"
            ? 15
            : 0;
  }

  if (pace === "active") {
    penalty = Math.max(
      0,
      penalty - 5,
    );
  }

  return {
    distanceKm: distance,
    band,
    penalty,
  };
}


export function requiresCoordinateTravelDay(
  source,
  target,
) {
  const distance =
    distanceKm(source, target);

  if (distance === null) {
    return null;
  }

  return distance > 600;
}


export function orderByNearestCoordinate(
  destinations,
  startingCoordinates,
) {
  const remaining = [...destinations];

  const ordered = [];

  let current =
    validCoordinates(startingCoordinates);

  if (!current) {
    return remaining;
  }

  while (remaining.length) {
    let bestIndex = -1;
    let bestDistance =
      Number.POSITIVE_INFINITY;

    for (
      let index = 0;
      index < remaining.length;
      index += 1
    ) {
      const coordinates =
        validCoordinates(
          remaining[index],
        );

      if (!coordinates) {
        continue;
      }

      const distance =
        distanceKm(
          current,
          coordinates,
        );

      if (
        distance !== null &&
        distance < bestDistance
      ) {
        bestDistance = distance;
        bestIndex = index;
      }
    }

    if (bestIndex === -1) {
      ordered.push(...remaining);
      break;
    }

    const [next] =
      remaining.splice(
        bestIndex,
        1,
      );

    ordered.push(next);

    current =
      validCoordinates(next);
  }

  return ordered;
}
