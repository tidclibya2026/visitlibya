import { clearChildren, createElement, setVisible } from "../app/utils/dom.js";

function formatDate(value, locale, options = {}) {
  if (!value) return null;
  const date = new Date(options.dateOnly ? `${value}T00:00:00` : value);
  if (Number.isNaN(date.valueOf())) return null;
  return new Intl.DateTimeFormat(locale === "ar" ? "ar-LY" : "en-GB", {
    dateStyle: options.dateOnly ? "medium" : "long",
  }).format(date);
}

function translatedEnum(t, prefix, value) {
  const suffix = String(value ?? "")
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
  return t(`trips.${prefix}${suffix}`);
}

export function renderTripsLoading(container, label) {
  clearChildren(container);
  const status = createElement("p", {
    className: "trips-visually-hidden",
    text: label,
    attributes: { role: "status" },
  });
  const grid = createElement("div", {
    className: "trips-grid",
    attributes: { "aria-hidden": "true" },
  });
  for (let index = 0; index < 3; index += 1) {
    const card = createElement("div", { className: "trip-card trip-card--skeleton" });
    card.append(
      createElement("span"),
      createElement("span"),
      createElement("span"),
    );
    grid.appendChild(card);
  }
  container.append(status, grid);
  container.setAttribute("aria-busy", "true");
}

export function renderTripsEmpty(container, t, onCreate) {
  clearChildren(container);
  container.setAttribute("aria-busy", "false");
  const empty = createElement("section", {
    className: "trips-empty",
    attributes: { role: "status" },
  });
  empty.append(
    createElement("h3", { text: t("trips.empty") }),
    createElement("p", { text: t("trips.emptyAction") }),
  );
  const action = createElement("button", {
    className: "trips-primary-button",
    text: t("trips.create"),
    attributes: { type: "button" },
  });
  action.addEventListener("click", onCreate);
  empty.appendChild(action);
  container.appendChild(empty);
}

export function renderTripsError(container, message, retryLabel, onRetry) {
  clearChildren(container);
  container.setAttribute("aria-busy", "false");
  const panel = createElement("section", {
    className: "trips-error-state",
    attributes: { role: "alert" },
  });
  panel.appendChild(createElement("p", { text: message }));
  const retry = createElement("button", {
    className: "trips-secondary-button",
    text: retryLabel,
    attributes: { type: "button" },
  });
  retry.addEventListener("click", onRetry);
  panel.appendChild(retry);
  container.appendChild(panel);
}

export function renderTrips(
  container,
  trips,
  { locale, t, onOpen, onClone, onDelete },
) {
  clearChildren(container);
  container.setAttribute("aria-busy", "false");
  const grid = createElement("div", { className: "trips-grid" });

  trips.forEach((trip) => {
    const article = createElement("article", { className: "trip-card" });
    const header = createElement("div", { className: "trip-card__header" });
    const title = createElement("h3", { text: trip.title });
    const status = createElement("span", {
      className: `trip-badge trip-badge--${trip.status}`,
      text: translatedEnum(t, "status", trip.status),
    });
    header.append(title, status);

    if (trip.description) {
      article.append(header, createElement("p", {
        className: "trip-card__description",
        text: trip.description,
      }));
    } else {
      article.appendChild(header);
    }

    const facts = createElement("dl", { className: "trip-card__facts" });
    const start = formatDate(trip.start_date, locale, { dateOnly: true });
    const end = formatDate(trip.end_date, locale, { dateOnly: true });
    const dateText = start && end
      ? t("trips.dates", { start, end })
      : start ?? end ?? t("trips.noDates");
    const factValues = [
      [t("trips.status"), translatedEnum(t, "status", trip.status)],
      [t("trips.visibility"), translatedEnum(t, "visibility", trip.visibility)],
      [t("trips.datesLabel"), dateText],
      [t("trips.itemCount"), t("trips.items", { count: trip.item_count })],
    ];
    factValues.forEach(([label, value]) => {
      facts.append(
        createElement("dt", { text: label }),
        createElement("dd", { text: value }),
      );
    });
    article.appendChild(facts);

    const updated = formatDate(trip.updated_at, locale);
    if (updated) {
      article.appendChild(createElement("p", {
        className: "trip-card__updated",
        text: t("trips.updated", { date: updated }),
      }));
    }

    const actions = createElement("div", { className: "trip-card__actions" });
    const open = createElement("button", {
      className: "trips-primary-button",
      text: t("trips.open"),
      attributes: { type: "button" },
    });
    const clone = createElement("button", {
      className: "trips-secondary-button",
      text: t("trips.clone"),
      attributes: { type: "button" },
    });
    const remove = createElement("button", {
      className: "trips-danger-button",
      text: t("common.delete"),
      attributes: { type: "button" },
    });
    open.addEventListener("click", () => onOpen(trip));
    clone.addEventListener("click", () => onClone(trip));
    remove.addEventListener("click", () => onDelete(trip));
    actions.append(open, clone, remove);
    article.appendChild(actions);
    grid.appendChild(article);
  });

  container.appendChild(grid);
}

export function renderPagination(
  container,
  { page, total, limit, t, loading, onPageChange },
) {
  clearChildren(container);
  const pages = Math.max(1, Math.ceil(total / limit));
  if (total <= limit && page === 1) {
    setVisible(container, false);
    return;
  }

  const previous = createElement("button", {
    text: t("trips.previous"),
    attributes: { type: "button" },
  });
  const label = createElement("span", {
    text: t("trips.pageLabel", { page, pages }),
    attributes: { "aria-current": "page" },
  });
  const next = createElement("button", {
    text: t("trips.next"),
    attributes: { type: "button" },
  });
  previous.disabled = loading || page <= 1;
  next.disabled = loading || page >= pages;
  previous.addEventListener("click", () => onPageChange(page - 1));
  next.addEventListener("click", () => onPageChange(page + 1));
  container.append(previous, label, next);
  setVisible(container, true);
}
