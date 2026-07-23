const MESSAGE_KEYS = Object.freeze({
  NETWORK_ERROR: "errors.network",
  TIMEOUT: "errors.timeout",
  ABORTED: "errors.aborted",
  BAD_REQUEST: "errors.badRequest",
  UNAUTHORIZED: "errors.unauthorized",
  FORBIDDEN: "errors.forbidden",
  NOT_FOUND: "errors.notFound",
  CONFLICT: "errors.conflict",
  TRIP_VERSION_CONFLICT: "trips.versionConflict",
  VALIDATION_ERROR: "errors.validation",
  RATE_LIMITED: "errors.rateLimit",
  SERVER_ERROR: "errors.server",
  UNKNOWN_ERROR: "errors.unknown",
});

export function getErrorMessageKey(error) {
  return MESSAGE_KEYS[error?.code] ?? "errors.unknown";
}

export function getLocalizedErrorMessage(error, translate) {
  return translate(getErrorMessageKey(error));
}
