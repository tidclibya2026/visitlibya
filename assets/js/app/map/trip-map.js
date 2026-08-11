const SVG_NS = "http://www.w3.org/2000/svg";
const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function validCoordinatePair(destination) {
  const latitude = destination?.latitude;
  const longitude = destination?.longitude;
  return Number.isFinite(latitude) && latitude >= -90 && latitude <= 90 &&
    Number.isFinite(longitude) && longitude >= -180 && longitude <= 180;
}

export function buildTripMapStops(items = [], locale = "en") {
  const ordered = [...items].sort((left, right) =>
    Number(left.day_number) - Number(right.day_number) ||
    Number(left.sort_order) - Number(right.sort_order) ||
    Number(left.id) - Number(right.id));
  const positionsByDay = new Map();
  return ordered.flatMap((item, index) => {
    const dayNumber = Number(item.day_number);
    const position = (positionsByDay.get(dayNumber) ?? 0) + 1;
    positionsByDay.set(dayNumber, position);
    if (!validCoordinatePair(item.destination)) return [];
    const primaryName = locale === "ar" ? item.destination?.name_ar : item.destination?.name_en;
    const alternateName = locale === "ar" ? item.destination?.name_en : item.destination?.name_ar;
    return [Object.freeze({
      itemId: Number(item.id),
      destinationId: Number(item.destination?.id),
      slug: SLUG_PATTERN.test(item.destination?.slug ?? "") ? item.destination.slug : "",
      name: String(primaryName || alternateName || (locale === "ar" ? "وجهة" : "Destination")),
      dayNumber,
      position,
      sequenceNumber: index + 1,
      visitTime: typeof item.start_time === "string" ? item.start_time.slice(0, 5) : "",
      latitude: item.destination.latitude,
      longitude: item.destination.longitude,
    })];
  });
}

export function mapCoverageSummary(totalStops, mappedStops, locale = "en") {
  if (totalStops === 0) return locale === "ar"
    ? "أضف وجهات تتوفر لها إحداثيات جغرافية لعرضها على الخريطة."
    : "Add destinations with geographic coordinates to see them on the map.";
  if (mappedStops === 0) return locale === "ar"
    ? "الموقع الجغرافي غير متاح لهذه المحطات حتى الآن."
    : "Map location is not available for these stops yet.";
  if (mappedStops < totalStops) return locale === "ar"
    ? `يتم عرض ${mappedStops} من أصل ${totalStops} محطات مخططة تتوفر لها إحداثيات جغرافية موثوقة.`
    : `Showing ${mappedStops} of ${totalStops} planned stops with verified geographic coordinates.`;
  return locale === "ar"
    ? `يتم عرض جميع المحطات المخططة وعددها ${mappedStops} بإحداثيات جغرافية موثوقة.`
    : `Showing all ${mappedStops} planned stops with verified geographic coordinates.`;
}

function projectedPositions(stops) {
  if (stops.length === 1) return new Map([[stops[0].itemId, { x: 50, y: 50 }]]);
  const latitudes = stops.map((stop) => stop.latitude);
  const longitudes = stops.map((stop) => stop.longitude);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);
  const latitudeSpan = maxLatitude - minLatitude || 1;
  const longitudeSpan = maxLongitude - minLongitude || 1;
  return new Map(stops.map((stop) => [stop.itemId, {
    x: 10 + ((stop.longitude - minLongitude) / longitudeSpan) * 80,
    y: 90 - ((stop.latitude - minLatitude) / latitudeSpan) * 80,
  }]));
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
  return element;
}

export function createTripMap({ root, locale = "en", onMarkerActivate }) {
  const plot = root.querySelector("[data-trip-map-plot]");
  const status = root.querySelector("[data-trip-map-status]");
  const context = root.querySelector("[data-trip-map-context]");
  if (!plot || !status || !context) throw new Error("Trip map hooks are incomplete");
  let stopsByItemId = new Map();
  let markersByItemId = new Map();

  const showContext = (stop) => {
    const identity = locale === "ar"
      ? `اليوم ${stop.dayNumber} · المحطة ${stop.position}`
      : `Day ${stop.dayNumber} · Stop ${stop.position}`;
    const heading = document.createElement("strong");
    heading.textContent = `${stop.sequenceNumber}. ${stop.name}`;
    const detail = document.createElement("span");
    detail.textContent = stop.visitTime ? `${identity} · ${stop.visitTime}` : identity;
    context.replaceChildren(heading, detail);
    if (stop.slug) {
      const link = document.createElement("a");
      link.href = `destination.html?slug=${encodeURIComponent(stop.slug)}`;
      link.textContent = locale === "ar" ? "عرض الوجهة" : "View Destination";
      context.appendChild(link);
    }
    context.hidden = false;
  };

  const activate = (itemId, { focusMarker = false } = {}) => {
    const stop = stopsByItemId.get(Number(itemId));
    const marker = markersByItemId.get(Number(itemId));
    if (!stop || !marker) return false;
    markersByItemId.forEach((entry) => entry.classList.remove("is-active"));
    marker.classList.add("is-active");
    showContext(stop);
    if (focusMarker) marker.focus({ preventScroll: true });
    return true;
  };

  const update = (trip) => {
    const allItems = Array.isArray(trip?.items) ? trip.items : [];
    const stops = buildTripMapStops(allItems, locale);
    const positions = projectedPositions(stops);
    stopsByItemId = new Map(stops.map((stop) => [stop.itemId, stop]));
    markersByItemId = new Map();
    plot.replaceChildren();
    context.replaceChildren();
    context.hidden = true;
    const coverage = mapCoverageSummary(allItems.length, stops.length, locale);
    if (allItems.length === 0) {
      const title = document.createElement("strong");
      title.textContent = locale === "ar" ? "ستظهر خريطة رحلتك هنا" : "Your trip map will appear here";
      const description = document.createElement("span");
      description.textContent = coverage;
      status.replaceChildren(title, description);
    } else {
      status.textContent = coverage;
    }
    root.dataset.mapState = allItems.length === 0 ? "empty" : stops.length === 0 ? "unavailable" : stops.length < allItems.length ? "partial" : "complete";
    if (!stops.length) return;

    const svg = svgElement("svg", { viewBox: "0 0 100 100", role: "img", "aria-hidden": "true", preserveAspectRatio: "none" });
    const days = new Map();
    stops.forEach((stop) => (days.get(stop.dayNumber) ?? days.set(stop.dayNumber, []).get(stop.dayNumber)).push(stop));
    days.forEach((dayStops) => {
      if (dayStops.length < 2) return;
      const points = dayStops.map((stop) => {
        const point = positions.get(stop.itemId);
        return `${point.x},${point.y}`;
      }).join(" ");
      svg.appendChild(svgElement("polyline", { points, class: "trip-map__sequence-line", vectorEffect: "non-scaling-stroke" }));
    });
    plot.appendChild(svg);

    stops.forEach((stop) => {
      const point = positions.get(stop.itemId);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "trip-map__marker";
      button.dataset.mapItemId = String(stop.itemId);
      button.style.left = `${point.x}%`;
      button.style.top = `${point.y}%`;
      button.textContent = String(stop.sequenceNumber);
      button.setAttribute("aria-label", locale === "ar"
        ? `${stop.sequenceNumber}. ${stop.name}، اليوم ${stop.dayNumber}، المحطة ${stop.position}`
        : `${stop.sequenceNumber}. ${stop.name}, Day ${stop.dayNumber}, Stop ${stop.position}`);
      button.addEventListener("click", () => {
        activate(stop.itemId);
        onMarkerActivate?.(stop);
      });
      markersByItemId.set(stop.itemId, button);
      plot.appendChild(button);
    });
  };

  return Object.freeze({ update, activate });
}
