export class AppError extends Error {
  constructor(message, options = {}) {
    super(message, { cause: options.cause });
    this.name = "AppError";
    this.status = options.status ?? 0;
    this.code = options.code ?? "UNKNOWN_ERROR";
    this.details = options.details ?? null;
    this.fieldErrors = Object.freeze({ ...(options.fieldErrors ?? {}) });
    this.requestId = options.requestId ?? null;
    this.retryable = Boolean(options.retryable);
  }
}

export function isAppError(error) {
  return error instanceof AppError;
}
