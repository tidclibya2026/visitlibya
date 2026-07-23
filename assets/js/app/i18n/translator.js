import { ar } from "./ar.js";
import { en } from "./en.js";

const dictionaries = Object.freeze({ ar, en });

function readKey(dictionary, key) {
  return key.split(".").reduce((value, part) => value?.[part], dictionary);
}

function interpolate(template, params) {
  return template.replace(/\{([A-Za-z0-9_]+)\}/g, (match, key) => {
    const value = params[key];
    return value == null ? match : String(value);
  });
}

export function detectLocale(defaultLocale = "en", documentRef = globalThis.document) {
  const pageLocale = documentRef?.documentElement?.lang?.toLowerCase().split("-")[0];
  if (pageLocale === "ar" || pageLocale === "en") return pageLocale;
  return defaultLocale === "ar" ? "ar" : "en";
}

export function createTranslator(locale = "en", fallbackLocale = "en") {
  const activeLocale = locale === "ar" ? "ar" : "en";
  const fallback = fallbackLocale === "ar" ? "ar" : "en";

  return Object.freeze({
    locale: activeLocale,
    direction: activeLocale === "ar" ? "rtl" : "ltr",
    t(key, params = {}) {
      const value =
        readKey(dictionaries[activeLocale], key) ??
        readKey(dictionaries[fallback], key);
      return typeof value === "string" ? interpolate(value, params) : key;
    },
    applyDirection(element = globalThis.document?.documentElement) {
      if (!element) return;
      element.dir = activeLocale === "ar" ? "rtl" : "ltr";
    },
  });
}
