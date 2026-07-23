export function queryRequired(selector, root = document) {
  const element = root.querySelector(selector);
  if (!element) throw new Error(`Required element not found: ${selector}`);
  return element;
}

export function createElement(tagName, options = {}) {
  const element = document.createElement(tagName);
  if (options.className) element.className = options.className;
  if (options.text != null) element.textContent = String(options.text);
  if (options.attributes) {
    Object.entries(options.attributes).forEach(([name, value]) => {
      if (value != null) element.setAttribute(name, String(value));
    });
  }
  return element;
}

export function setText(element, value) {
  element.textContent = value == null ? "" : String(value);
  return element;
}

export function clearChildren(element) {
  element.replaceChildren();
  return element;
}

export function setVisible(element, visible) {
  element.hidden = !visible;
  element.setAttribute("aria-hidden", String(!visible));
  return element;
}

export function setDisabled(element, disabled) {
  element.disabled = Boolean(disabled);
  element.setAttribute("aria-disabled", String(Boolean(disabled)));
  return element;
}
