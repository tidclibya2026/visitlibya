import { getAccessToken, clearSession } from "../auth/session.js";
import { loadRuntimeConfig } from "../config/runtime-config.js";
import { AppError, isAppError } from "../errors/app-error.js";

const STATUS_CODES = Object.freeze({
  400: "BAD_REQUEST",
  401: "UNAUTHORIZED",
  403: "FORBIDDEN",
  404: "NOT_FOUND",
  409: "CONFLICT",
  422: "VALIDATION_ERROR",
  429: "RATE_LIMITED",
});

function extractFieldErrors(detail) {
  if (!Array.isArray(detail)) return {};

  return detail.reduce((errors, entry) => {
    const location = Array.isArray(entry?.loc)
      ? entry.loc.filter((part) => part !== "body").join(".")
      : "";
    if (location && typeof entry?.msg === "string") {
      (errors[location] ??= []).push(entry.msg);
    }
    return errors;
  }, {});
}

function getServerDetail(payload) {
  if (typeof payload?.detail === "string") return payload.detail;
  if (typeof payload?.message === "string") return payload.message;
  return null;
}

function classifyError(status, payload) {
  const detail = getServerDetail(payload);
  if (status === 409 && detail === "Trip was modified by another request") {
    return "TRIP_VERSION_CONFLICT";
  }
  if (status >= 500) return "SERVER_ERROR";
  return STATUS_CODES[status] ?? "UNKNOWN_ERROR";
}

function createHttpError(response, payload, requestId) {
  const status = response.status;
  const code = classifyError(status, payload);
  return new AppError(getServerDetail(payload) ?? response.statusText ?? "Request failed", {
    status,
    code,
    details: Array.isArray(payload?.detail) ? null : payload?.detail ?? null,
    fieldErrors: status === 422 ? extractFieldErrors(payload?.detail) : {},
    requestId,
    retryable: status === 429 || status >= 500,
  });
}

async function readResponse(response) {
  if (response.status === 204) return null;

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return text || null;
}

function createAbortContext(externalSignal, timeoutMs) {
  const controller = new AbortController();
  let timedOut = false;
  const abortFromExternal = () => controller.abort(externalSignal?.reason);
  if (externalSignal?.aborted) abortFromExternal();
  else externalSignal?.addEventListener("abort", abortFromExternal, { once: true });

  const timer = globalThis.setTimeout(() => {
    timedOut = true;
    controller.abort(new DOMException("Request timed out", "TimeoutError"));
  }, timeoutMs);

  return {
    signal: controller.signal,
    didTimeOut: () => timedOut,
    cleanup() {
      globalThis.clearTimeout(timer);
      externalSignal?.removeEventListener("abort", abortFromExternal);
    },
  };
}

function buildBody(body, headers) {
  if (body == null) return undefined;
  if (
    body instanceof FormData ||
    body instanceof URLSearchParams ||
    body instanceof Blob ||
    typeof body === "string"
  ) {
    return body;
  }
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return JSON.stringify(body);
}

export function createApiClient(config = loadRuntimeConfig()) {
  async function request(path, options = {}) {
    const method = String(options.method ?? "GET").toUpperCase();
    const retries = method === "GET" ? Math.max(0, Number(options.retries ?? 0)) : 0;
    let attempt = 0;

    while (true) {
      const abort = createAbortContext(
        options.signal,
        options.timeoutMs ?? config.requestTimeoutMs,
      );
      const headers = new Headers({ Accept: "application/json", ...options.headers });
      const token = getAccessToken();
      if (token) headers.set("Authorization", `Bearer ${token}`);

      try {
        const response = await fetch(`${config.apiBaseUrl}${path}`, {
          method,
          headers,
          body: ["GET", "HEAD"].includes(method)
            ? undefined
            : buildBody(options.body, headers),
          signal: abort.signal,
          credentials: "same-origin",
        });
        const payload = await readResponse(response);
        const requestId =
          response.headers.get("x-request-id") ??
          (typeof payload?.request_id === "string" ? payload.request_id : null);

        if (!response.ok) {
          const error = createHttpError(response, payload, requestId);
          if (error.status === 401) {
            clearSession({ reason: "expired" });
            globalThis.dispatchEvent?.(
              new CustomEvent("visitlibya:auth-expired", { detail: { requestId } }),
            );
          }
          throw error;
        }
        return payload;
      } catch (error) {
        let appError = error;
        if (!isAppError(error)) {
          const aborted = abort.signal.aborted;
          const timedOut = abort.didTimeOut();
          appError = new AppError(
            timedOut ? "Request timed out" : aborted ? "Request was aborted" : "Network request failed",
            {
              code: timedOut ? "TIMEOUT" : aborted ? "ABORTED" : "NETWORK_ERROR",
              retryable: !aborted || timedOut,
              cause: error,
            },
          );
        }

        if (attempt < retries && appError.retryable && appError.code !== "TRIP_VERSION_CONFLICT") {
          attempt += 1;
          continue;
        }
        throw appError;
      } finally {
        abort.cleanup();
      }
    }
  }

  return Object.freeze({
    request,
    get: (path, options) => request(path, { ...options, method: "GET" }),
    post: (path, body, options) => request(path, { ...options, method: "POST", body }),
    patch: (path, body, options) => request(path, { ...options, method: "PATCH", body }),
    put: (path, body, options) => request(path, { ...options, method: "PUT", body }),
    delete: (path, options) => request(path, { ...options, method: "DELETE" }),
  });
}

export const apiClient = createApiClient();
