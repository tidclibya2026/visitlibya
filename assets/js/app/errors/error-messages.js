const MESSAGE_KEYS = Object.freeze({
  API_UNAVAILABLE: "errors.apiUnavailable",
  NETWORK_ERROR: "errors.network",
  TIMEOUT: "errors.timeout",
  ABORTED: "errors.aborted",
  BAD_REQUEST: "errors.badRequest",
  UNAUTHORIZED: "errors.unauthorized",
  FORBIDDEN: "errors.forbidden",
  NOT_FOUND: "errors.notFound",
  CONFLICT: "errors.conflict",
  AUTH_INVALID_CREDENTIALS: "auth.invalid",
  AUTH_EMAIL_CONFLICT: "auth.emailConflict",
  AUTH_USERNAME_CONFLICT: "auth.usernameConflict",
  AUTH_REGISTRATION_CONFLICT: "auth.accountConflict",
  TRIP_VERSION_CONFLICT: "trips.versionConflict",
  TRIP_DUPLICATE_DESTINATION: "tripIntegration.duplicate",
  TRIP_DESTINATION_UNAVAILABLE: "tripIntegration.invalidDestination",
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
