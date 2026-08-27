const LIBYA_VIEWPORT = Object.freeze({
  minLongitude: 9,
  maxLongitude: 25.5,
  minLatitude: 19,
  maxLatitude: 33.5,
});

export function isPointFeature(feature) {
  const coordinates = feature?.geometry?.coordinates;

  return (
    feature?.type === "Feature" &&
    feature?.geometry?.type === "Point" &&
    Array.isArray(coordinates) &&
    coordinates.length >= 2 &&
    Number.isFinite(coordinates[0]) &&
    Number.isFinite(coordinates[1])
  );
}

export function projectGeoJSONPoint(feature) {
  if (!isPointFeature(feature)) return null;

  const [longitude, latitude] = feature.geometry.coordinates;

  const longitudeSpan =
    LIBYA_VIEWPORT.maxLongitude - LIBYA_VIEWPORT.minLongitude;

  const latitudeSpan =
    LIBYA_VIEWPORT.maxLatitude - LIBYA_VIEWPORT.minLatitude;

  return Object.freeze({
    x:
      ((longitude - LIBYA_VIEWPORT.minLongitude) /
        longitudeSpan) *
      100,
    y:
      100 -
      ((latitude - LIBYA_VIEWPORT.minLatitude) /
        latitudeSpan) *
        100,
  });
}

export function createDestinationGISMap({
  root,
  locale = "en",
  onFeatureActivate,
}) {
  if (!root) {
    throw new Error("Destination GIS map root is required");
  }

  const plot = root.querySelector("[data-gis-map-plot]");
  const status = root.querySelector("[data-gis-map-status]");
  const context = root.querySelector("[data-gis-map-context]");

  if (!plot || !status || !context) {
    throw new Error("Destination GIS map hooks are incomplete");
  }

  const render = (collection) => {
    plot.replaceChildren();
    context.replaceChildren();
    context.hidden = true;

    const features = Array.isArray(collection?.features)
      ? collection.features.filter(isPointFeature)
      : [];

    root.dataset.featureCount = String(features.length);

    status.textContent =
      locale === "ar"
        ? `يتم عرض ${features.length} وجهة منشورة.`
        : `Showing ${features.length} published destinations.`;

    if (!features.length) {
      root.dataset.mapState = "empty";
      return;
    }

    root.dataset.mapState = "ready";

    features.forEach((feature) => {
      const point = projectGeoJSONPoint(feature);

      if (
        !point ||
        point.x < 0 ||
        point.x > 100 ||
        point.y < 0 ||
        point.y > 100
      ) {
        return;
      }

      const properties = feature.properties ?? {};
      const marker = document.createElement("button");

      marker.type = "button";
      marker.className = "atlas-gis-marker";
      marker.style.left = `${point.x}%`;
      marker.style.top = `${point.y}%`;
      marker.dataset.destinationSlug = properties.slug ?? "";

      const name =
        locale === "ar"
          ? properties.name_ar || properties.name_en || properties.slug
          : properties.name_en || properties.name_ar || properties.slug;

      marker.setAttribute("aria-label", name || "Tourism destination");

      marker.addEventListener("click", () => {
        plot
          .querySelectorAll(".atlas-gis-marker.is-active")
          .forEach((element) => element.classList.remove("is-active"));

        marker.classList.add("is-active");

        const heading = document.createElement("strong");
        heading.textContent = name || "";

        const location = document.createElement("span");
        location.textContent = [
          properties.municipality,
          properties.region,
        ]
          .filter(Boolean)
          .join(" · ");

        context.replaceChildren(heading, location);
        context.hidden = false;

        onFeatureActivate?.(feature);
      });

      plot.appendChild(marker);
    });
  };

  const unavailable = () => {
    plot.replaceChildren();
    context.replaceChildren();
    context.hidden = true;
    root.dataset.mapState = "unavailable";

    status.textContent =
      locale === "ar"
        ? "الخريطة الجغرافية الحية غير متاحة حاليًا."
        : "The live geographic map is currently unavailable.";
  };

  return Object.freeze({
    render,
    unavailable,
  });
}
