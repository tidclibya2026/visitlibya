import { createElement } from "../utils/dom.js";

let container = null;

function getContainer() {
  if (container?.isConnected) return container;
  container = createElement("div", {
    attributes: {
      "data-toast-container": "",
      "aria-label": "Notifications",
    },
  });
  document.body.appendChild(container);
  return container;
}

export function showToast(message, options = {}) {
  const type = ["success", "error", "info", "warning"].includes(options.type)
    ? options.type
    : "info";
  const toast = createElement("div", {
    className: `app-toast app-toast--${type}`,
    attributes: {
      role: type === "error" ? "alert" : "status",
      "aria-live": type === "error" ? "assertive" : "polite",
    },
  });
  const text = createElement("span", { text: message });
  const close = createElement("button", {
    text: options.closeLabel ?? "Close",
    attributes: { type: "button", "aria-label": options.closeLabel ?? "Close" },
  });
  const dismiss = () => toast.remove();
  close.addEventListener("click", dismiss);
  toast.append(text, close);
  getContainer().appendChild(toast);

  const timeout = Number(options.timeout ?? 5_000);
  if (timeout > 0) globalThis.setTimeout(dismiss, timeout);
  return Object.freeze({ element: toast, dismiss });
}

export const toast = Object.freeze({
  success: (message, options) => showToast(message, { ...options, type: "success" }),
  error: (message, options) => showToast(message, { ...options, type: "error" }),
  info: (message, options) => showToast(message, { ...options, type: "info" }),
  warning: (message, options) => showToast(message, { ...options, type: "warning" }),
});
