import { readPositiveIntegerParameter, updateQueryParameters } from "../app/utils/query-string.js";
import { setText, setVisible } from "../app/utils/dom.js";

export function initializeTripPlaceholder(documentRef = document) {
  const locale = documentRef.documentElement.lang === "ar" ? "ar" : "en";
  const tripId = readPositiveIntegerParameter("id");
  const idText = documentRef.querySelector("[data-trip-id-text]");
  const error = documentRef.querySelector("[data-trip-id-error]");
  const languageLink = documentRef.querySelector("[data-trip-language-link]");

  if (tripId) {
    setText(
      idText,
      locale === "ar"
        ? `معرّف الرحلة: ${tripId}`
        : `Trip ID: ${tripId}`,
    );
    setVisible(error, false);
    if (languageLink) {
      languageLink.href = updateQueryParameters(
        { id: tripId },
        new URL(languageLink.href, globalThis.location.href).href,
      );
    }
  } else {
    setText(
      idText,
      locale === "ar"
        ? "تعذر فتح الرحلة لأن المعرّف غير صالح."
        : "The trip cannot be opened because its identifier is invalid.",
    );
    setVisible(error, true);
  }
}

if (typeof document !== "undefined") {
  initializeTripPlaceholder();
}
