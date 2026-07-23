import { createElement } from "../utils/dom.js";

const FOCUSABLE =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), ' +
  'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function createModal(options = {}) {
  const dialog = createElement("dialog", {
    className: options.className ?? "app-modal",
    attributes: { "aria-modal": "true" },
  });
  const titleId = `app-modal-title-${crypto.randomUUID()}`;
  const title = createElement("h2", { text: options.title ?? "", attributes: { id: titleId } });
  const content = createElement("div", { attributes: { "data-modal-content": "" } });
  const actions = createElement("div", { attributes: { "data-modal-actions": "" } });
  dialog.setAttribute("aria-labelledby", titleId);
  dialog.append(title, content, actions);

  let critical = Boolean(options.critical);
  let previousFocus = null;

  const close = (value = "") => {
    if (!dialog.open || critical) return false;
    dialog.close(value);
    return true;
  };

  dialog.addEventListener("cancel", (event) => {
    if (critical) event.preventDefault();
  });
  dialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && critical) {
      event.preventDefault();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = [...dialog.querySelectorAll(FOCUSABLE)];
    if (!focusable.length) {
      event.preventDefault();
      dialog.focus();
      return;
    }
    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });
  dialog.addEventListener("close", () => {
    previousFocus?.focus?.();
  });

  return Object.freeze({
    element: dialog,
    content,
    actions,
    open() {
      previousFocus = document.activeElement;
      if (!dialog.isConnected) document.body.appendChild(dialog);
      dialog.showModal();
      dialog.querySelector(FOCUSABLE)?.focus() ?? dialog.focus();
    },
    close,
    setCritical(value) {
      critical = Boolean(value);
    },
    destroy() {
      if (dialog.open && !critical) dialog.close();
      dialog.remove();
    },
  });
}

export function confirmAction(options = {}) {
  return new Promise((resolve) => {
    const modal = createModal({ title: options.title });
    const message = createElement("p", { text: options.message });
    const cancel = createElement("button", {
      text: options.cancelLabel ?? "Cancel",
      attributes: { type: "button" },
    });
    const confirm = createElement("button", {
      text: options.confirmLabel ?? "Confirm",
      attributes: { type: "button" },
    });

    const finish = (result) => {
      modal.close(result ? "confirm" : "cancel");
      modal.destroy();
      resolve(result);
    };
    cancel.addEventListener("click", () => finish(false));
    confirm.addEventListener("click", () => finish(true));
    modal.element.addEventListener("cancel", () => finish(false), { once: true });
    modal.content.appendChild(message);
    modal.actions.append(cancel, confirm);
    modal.open();
  });
}
