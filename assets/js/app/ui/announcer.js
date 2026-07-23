import { createElement, setText } from "../utils/dom.js";

let region = null;
let lastAnnouncement = "";

function getRegion() {
  if (region?.isConnected) return region;

  region = createElement("div", {
    attributes: {
      "data-visitlibya-announcer": "",
      "aria-live": "polite",
      "aria-atomic": "true",
    },
  });
  Object.assign(region.style, {
    position: "fixed",
    width: "1px",
    height: "1px",
    overflow: "hidden",
    clip: "rect(0 0 0 0)",
    whiteSpace: "nowrap",
  });
  document.body.appendChild(region);
  return region;
}

export function announce(message, { priority = "polite", force = false } = {}) {
  const text = String(message ?? "").trim();
  if (!text || (!force && text === lastAnnouncement)) return;

  const element = getRegion();
  element.setAttribute("aria-live", priority === "assertive" ? "assertive" : "polite");
  setText(element, "");
  globalThis.setTimeout(() => setText(element, text), 20);
  lastAnnouncement = text;
}
