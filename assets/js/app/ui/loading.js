import { createElement, setText } from "../utils/dom.js";

export function setLoading(element, loading, options = {}) {
  const active = Boolean(loading);
  element.setAttribute("aria-busy", String(active));

  if (options.disable && "disabled" in element) {
    element.disabled = active;
  }

  let indicator = element.querySelector(":scope > [data-loading-indicator]");
  if (active && !indicator) {
    indicator = createElement("span", {
      text: options.text ?? "Loading…",
      attributes: {
        "data-loading-indicator": "",
        role: "status",
      },
    });
    element.appendChild(indicator);
  } else if (active && indicator) {
    setText(indicator, options.text ?? "Loading…");
  } else {
    indicator?.remove();
  }

  return () => setLoading(element, false, options);
}

export function createLoadingIndicator(text = "Loading…") {
  return createElement("span", {
    text,
    attributes: { role: "status", "aria-live": "polite" },
  });
}
