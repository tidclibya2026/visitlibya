import { apiClient } from "./client.js";
import { buildQueryString } from "../utils/query-string.js";
import { validateReorderPayload } from "../utils/validation.js";

const tripPath = (tripId) => `/trips/${encodeURIComponent(tripId)}`;
const itemPath = (tripId, itemId) =>
  `${tripPath(tripId)}/items/${encodeURIComponent(itemId)}`;

/**
 * @typedef {object} TripSummaryResponse
 * @property {number} id
 * @property {string} title
 * @property {string|null} description
 * @property {string|null} start_date
 * @property {string|null} end_date
 * @property {"draft"|"planned"|"active"|"completed"|"cancelled"} status
 * @property {"private"|"unlisted"|"public"} visibility
 * @property {number} version
 * @property {number|null} duration_days
 * @property {number} item_count
 * @property {string} created_at
 * @property {string} updated_at
 *
 * @typedef {object} TripItemResponse
 * @property {number} id
 * @property {{id:number, slug:string, name_ar:string|null, name_en:string|null}} destination
 * @property {number} day_number
 * @property {string|null} visit_date
 * @property {string|null} start_time
 * @property {number|null} duration_minutes
 * @property {number} sort_order
 * @property {string|null} notes
 * @property {string} created_at
 * @property {string} updated_at
 *
 * @typedef {TripSummaryResponse & {items: TripItemResponse[]}} TripDetailResponse
 *
 * @typedef {object} TripListResponse
 * @property {TripSummaryResponse[]} items
 * @property {number} total
 * @property {number} skip
 * @property {number} limit
 */

/**
 * @returns {Promise<TripListResponse>}
 */
export function listTrips({ skip = 0, limit = 20 } = {}, options = {}) {
  return apiClient.get(`/trips${buildQueryString({ skip, limit })}`, options);
}

/** @returns {Promise<TripDetailResponse>} */
export function getTrip(tripId, options = {}) {
  return apiClient.get(tripPath(tripId), options);
}

/**
 * @param {{title: string, description?: string|null, start_date?: string|null,
 * end_date?: string|null, status?: string, visibility?: string}} payload
 * @returns {Promise<TripDetailResponse>}
 */
export function createTrip(payload, options = {}) {
  return apiClient.post("/trips", payload, options);
}

/**
 * Partial TripUpdate. Backend accepts title, description, start_date, end_date,
 * status and visibility; omitted fields remain unchanged.
 * @returns {Promise<TripDetailResponse>}
 */
export function updateTrip(tripId, payload, options = {}) {
  return apiClient.patch(tripPath(tripId), payload, options);
}

export function deleteTrip(tripId, options = {}) {
  return apiClient.delete(tripPath(tripId), options);
}

/**
 * TripItemCreate: destination_id, optional day_number, visit_date, start_time,
 * duration_minutes, sort_order and notes.
 * @returns {Promise<TripItemResponse>}
 */
export function addTripItem(tripId, payload, options = {}) {
  return apiClient.post(`${tripPath(tripId)}/items`, payload, options);
}

/**
 * Partial TripItemUpdate using the TripItemCreate field names.
 * @returns {Promise<TripItemResponse>}
 */
export function updateTripItem(tripId, itemId, payload, options = {}) {
  return apiClient.patch(itemPath(tripId, itemId), payload, options);
}

export function deleteTripItem(
  tripId,
  itemId,
  expectedVersion,
  options = {},
) {
  return apiClient.delete(
    `${itemPath(tripId, itemId)}${buildQueryString({
      expected_version: expectedVersion,
    })}`,
    options,
  );
}

/**
 * @param {{expected_version: number, items: Array<{item_id: number, day_number: number}>}} payload
 * Reorder is atomic and is never retried automatically.
 * @returns {Promise<TripDetailResponse>}
 */
export function reorderTripItems(tripId, payload, options = {}) {
  validateReorderPayload(payload);
  return apiClient.put(`${tripPath(tripId)}/items/reorder`, payload, options);
}

/**
 * Search the bounded public destination catalog for stop selection.
 */
export function searchTripDestinations(query, options = {}) {
  return apiClient.get(
    `/search/destinations${buildQueryString({
      q: String(query ?? "").trim() || null,
      page: 1,
      page_size: 10,
      sort_by: "name",
      sort_order: "asc",
    })}`,
    options,
  );
}

/**
 * Load one bounded page of the public destination catalogue for optional
 * trip-card enrichment. This never carries or persists private trip data.
 */
export function listTripDestinationCatalogue(page = 1, options = {}) {
  return apiClient.get(
    `/search/destinations${buildQueryString({
      page,
      page_size: 100,
      sort_by: "name",
      sort_order: "asc",
    })}`,
    options,
  );
}
