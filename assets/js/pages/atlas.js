import { getDestinationBBox } from "../app/api/gis-api.js";
import { createDestinationGISMap } from "../app/map/destination-gis-map.js";

const LIBYA_BBOX = Object.freeze({
  minLongitude: 9,
  minLatitude: 19,
  maxLongitude: 25.5,
  maxLatitude: 33.5,
});

function localeFromDocument() {
  return document.documentElement.lang?.toLowerCase().startsWith("ar")
    ? "ar"
    : "en";
}

async function initAtlas() {
  const root = document.querySelector("[data-governed-gis-map]");
  if (!root) return;

  const map = createDestinationGISMap({
    root,
    locale: localeFromDocument(),
  });

  const controller = new AbortController();

  globalThis.addEventListener(
    "pagehide",
    () => controller.abort(),
    { once: true },
  );

  root.dataset.mapState = "loading";

  try {
    const collection = await getDestinationBBox({
      ...LIBYA_BBOX,
      limit: 200,
      signal: controller.signal,
    });

    map.render(collection);
  } catch (error) {
    const technicalFailure = new Set([
      "API_UNAVAILABLE",
      "NETWORK_ERROR",
      "TIMEOUT",
      "SERVER_ERROR",
    ]);

    if (technicalFailure.has(error?.code)) {
      map.unavailable();
      return;
    }

    root.dataset.mapState = "error";
    throw error;
  }
}

initAtlas().catch((error) => {
  console.error("Atlas GIS initialization failed", error);
});
