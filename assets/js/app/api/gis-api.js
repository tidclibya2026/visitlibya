import { apiClient } from "./client.js";

function queryString(values) {
  const params = new URLSearchParams();

  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });

  return params.toString();
}

export function validateFeatureCollection(payload) {
  if (
    payload?.type !== "FeatureCollection" ||
    !Array.isArray(payload.features)
  ) {
    throw new TypeError("Invalid GIS FeatureCollection");
  }

  return payload;
}

export async function getDestinationBBox({
  minLongitude,
  minLatitude,
  maxLongitude,
  maxLatitude,
  skip = 0,
  limit = 100,
  signal,
} = {}) {
  const query = queryString({
    min_longitude: minLongitude,
    min_latitude: minLatitude,
    max_longitude: maxLongitude,
    max_latitude: maxLatitude,
    skip,
    limit,
  });

  const payload = await apiClient.get(
    `/destinations/spatial/bbox?${query}`,
    {
      signal,
      retries: 1,
    },
  );

  return validateFeatureCollection(payload);
}

export async function getNearbyDestinations({
  longitude,
  latitude,
  radiusMeters = 25000,
  limit = 50,
  signal,
} = {}) {
  const query = queryString({
    longitude,
    latitude,
    radius_meters: radiusMeters,
    limit,
  });

  const payload = await apiClient.get(
    `/destinations/spatial/nearby?${query}`,
    {
      signal,
      retries: 1,
    },
  );

  return validateFeatureCollection(payload);
}
