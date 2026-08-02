import { verifyRestoredSession } from "./api/auth-api.js";
import {
  getAccessToken,
  getSessionSnapshot,
  restoreSession,
} from "./auth/session.js";
import { loadRuntimeConfig } from "./config/runtime-config.js";
import { createTranslator, detectLocale } from "./i18n/translator.js";
import { createTripStore } from "./state/trip-store.js";

let bootstrapPromise = null;

export function createAppContext() {
  const config = loadRuntimeConfig();
  const locale = detectLocale(config.defaultLocale);
  const translator = createTranslator(locale, config.defaultLocale);
  const session = restoreSession();
  const store = createTripStore({
    locale,
    authenticatedUser: session.currentUser,
  });

  return Object.freeze({ config, locale, translator, store, session });
}

async function runBootstrap() {
  try {
    const context = createAppContext();
    if (context.config.apiEnabled && getAccessToken()) {
      try {
        const currentUser = await verifyRestoredSession();
        context.store.updateState({ authenticatedUser: currentUser });
      } catch {
        context.store.updateState({ authenticatedUser: null });
      }
    }
    const readyContext = Object.freeze({
      ...context,
      session: getSessionSnapshot(),
    });
    globalThis.dispatchEvent?.(
      new CustomEvent("visitlibya:app-ready", { detail: readyContext }),
    );
    return readyContext;
  } catch {
    globalThis.dispatchEvent?.(
      new CustomEvent("visitlibya:app-error", {
        detail: Object.freeze({ message: "Application initialization failed" }),
      }),
    );
    return null;
  }
}

export function bootstrap() {
  bootstrapPromise ??= runBootstrap();
  return bootstrapPromise;
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => void bootstrap(), { once: true });
  } else {
    void bootstrap();
  }
}
