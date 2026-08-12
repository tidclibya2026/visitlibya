const SVG_NS = "http://www.w3.org/2000/svg";

/*
 * Fixed Libya-oriented geographic viewport.
 * Unlike Trip Map, this projection does NOT recalculate bounds
 * based on currently visible features.
 */
const LIBYA_BOUNDS = Object.freeze({
  minLongitude: 9.0,
  maxLongitude: 25.5,
  minLatitude: 19.0,
  maxLatitude: 33.5,
});

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);

  Object.entries(attributes).forEach(([key, value]) => {
    element.setAttribute(key, String(value));
  });

  return element;
}

export function validNaturalFeature(feature) {
  return (
    Number.isFinite(feature?.latitude) &&
    feature.latitude >= -90 &&
    feature.latitude <= 90 &&
    Number.isFinite(feature?.longitude) &&
    feature.longitude >= -180 &&
    feature.longitude <= 180
  );
}

export function projectNaturalFeature(feature) {
  const longitudeSpan =
    LIBYA_BOUNDS.maxLongitude - LIBYA_BOUNDS.minLongitude;

  const latitudeSpan =
    LIBYA_BOUNDS.maxLatitude - LIBYA_BOUNDS.minLatitude;

  return Object.freeze({
    x:
      ((feature.longitude - LIBYA_BOUNDS.minLongitude) /
        longitudeSpan) *
      100,

    y:
      100 -
      ((feature.latitude - LIBYA_BOUNDS.minLatitude) /
        latitudeSpan) *
        100,
  });
}

export function naturalLayerCategoryOptions(features = []) {
  const values = new Map();

  features.forEach((feature) => {
    if (!feature?.categoryKey) return;

    if (!values.has(feature.categoryKey)) {
      values.set(feature.categoryKey, {
        key: feature.categoryKey,
        ar: feature.categoryAr || feature.categoryKey,
        en: feature.categoryEn || feature.categoryKey,
      });
    }
  });

  return [...values.values()];
}

export function createNaturalTourismMap({
  root,
  locale = "en",
  onFeatureActivate,
}) {
  const plot = root.querySelector("[data-natural-map-plot]");
  const context = root.querySelector("[data-natural-map-context]");
  const status = root.querySelector("[data-natural-map-status]");

  if (!plot || !context || !status) {
    throw new Error("Natural tourism map hooks are incomplete");
  }

  let currentFeatures = [];
  let activeCategory = "all";
  let activeLayer = "";
  const numberFormatter = new Intl.NumberFormat(locale === "ar" ? "ar" : "en");

  const visibleFeatures = () =>
    currentFeatures.filter((feature) => {
      if (!validNaturalFeature(feature)) return false;

      if (
        activeCategory !== "all" &&
        feature.categoryKey !== activeCategory
      ) {
        return false;
      }

      return true;
    });

  const showContext = (feature) => {
    const heading = document.createElement("strong");

    heading.textContent =
      locale === "ar"
        ? feature.nameAr || feature.nameEn || "موقع طبيعي"
        : feature.nameEn || feature.nameAr || "Natural attraction";

    const category = document.createElement("span");

    category.textContent = locale === "ar"
      ? feature.categoryAr || feature.categoryEn || ""
      : feature.categoryEn || feature.categoryAr || "";

    context.replaceChildren(heading, category);
    context.hidden = false;
  };

  const render = () => {
    plot.replaceChildren();
    context.replaceChildren();
    context.hidden = true;

    const features = visibleFeatures();

    status.textContent =
      locale === "ar"
        ? `يتم عرض ${numberFormatter.format(features.length)} موقعًا طبيعيًا.`
        : `Showing ${numberFormatter.format(features.length)} natural sites.`;

    root.dataset.layer = activeLayer;
    root.dataset.featureCount = String(features.length);

    if (!features.length) {
      root.dataset.mapState = "empty";
      return;
    }

    root.dataset.mapState = "ready";

    const svg = svgElement("svg", {
      viewBox: "0 0 100 100",
      role: "img",
      "aria-hidden": "true",
      preserveAspectRatio: "none",
    });

    plot.appendChild(svg);

    features.forEach((feature) => {
      const point = projectNaturalFeature(feature);

      if (
        point.x < 0 ||
        point.x > 100 ||
        point.y < 0 ||
        point.y > 100
      ) {
        return;
      }

      const marker = document.createElement("button");

      marker.type = "button";
      marker.className = "natural-map__marker";

      marker.dataset.featureId = feature.id;
      marker.dataset.category = feature.categoryKey;

      marker.style.left = `${point.x}%`;
      marker.style.top = `${point.y}%`;

      marker.setAttribute(
        "aria-label",
        locale === "ar"
          ? [feature.nameAr || feature.nameEn || "موقع طبيعي", feature.categoryAr || feature.categoryEn].filter(Boolean).join("، ")
          : [feature.nameEn || feature.nameAr || "Natural attraction", feature.categoryEn || feature.categoryAr].filter(Boolean).join(", ")
      );

      marker.addEventListener("click", () => {
        plot
          .querySelectorAll(".natural-map__marker.is-active")
          .forEach((element) =>
            element.classList.remove("is-active")
          );

        marker.classList.add("is-active");
        showContext(feature);
        onFeatureActivate?.(feature);
      });

      plot.appendChild(marker);
    });
  };

  const update = ({
    layerId,
    features = [],
    category = "all",
  } = {}) => {
    activeLayer = String(layerId || "");
    activeCategory = category || "all";
    currentFeatures = Array.isArray(features)
      ? features
      : [];

    render();
  };

  const setCategory = (category = "all") => {
    activeCategory = category;
    render();
  };

  return Object.freeze({
    update,
    setCategory,
  });
}
