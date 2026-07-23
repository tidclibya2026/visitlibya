export const TRIP_LIMITS = Object.freeze({
  title: 200,
  description: 5_000,
  itemNotes: 2_000,
  items: 100,
});

export function normalizeText(value) {
  return String(value ?? "").trim();
}

export function validateRequiredText(value, { field = "value", maxLength } = {}) {
  const normalized = normalizeText(value);
  if (!normalized) throw new TypeError(`${field} is required`);
  if (maxLength && normalized.length > maxLength) {
    throw new RangeError(`${field} must not exceed ${maxLength} characters`);
  }
  return normalized;
}

export function validateOptionalText(value, { field = "value", maxLength } = {}) {
  if (value == null || value === "") return null;
  const normalized = normalizeText(value);
  if (maxLength && normalized.length > maxLength) {
    throw new RangeError(`${field} must not exceed ${maxLength} characters`);
  }
  return normalized;
}

export function validateDateRange(startDate, endDate) {
  if (!startDate || !endDate) return true;
  const start = new Date(`${startDate}T00:00:00`);
  const end = new Date(`${endDate}T00:00:00`);
  if (Number.isNaN(start.valueOf()) || Number.isNaN(end.valueOf())) {
    throw new TypeError("Dates must use a valid ISO date format");
  }
  if (end < start) throw new RangeError("End date must not be before start date");
  return true;
}

export function validateItemCount(items) {
  if (!Array.isArray(items)) throw new TypeError("items must be an array");
  if (items.length > TRIP_LIMITS.items) {
    throw new RangeError(`A trip cannot contain more than ${TRIP_LIMITS.items} items`);
  }
  return items;
}

export function validateReorderPayload(payload) {
  if (!Number.isInteger(payload?.expected_version) || payload.expected_version < 1) {
    throw new RangeError("expected_version must be a positive integer");
  }
  if (!Array.isArray(payload.items) || payload.items.length < 1) {
    throw new RangeError("Reorder requires at least one item");
  }
  validateItemCount(payload.items);
  payload.items.forEach((item) => {
    if (!Number.isInteger(item?.item_id) || item.item_id < 1) {
      throw new RangeError("item_id must be a positive integer");
    }
    if (!Number.isInteger(item?.day_number) || item.day_number < 1) {
      throw new RangeError("day_number must be a positive integer");
    }
  });
  return payload;
}
