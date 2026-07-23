import { getLocalizedErrorMessage } from "../app/errors/error-messages.js";
import { createModal } from "../app/ui/modal.js";
import { setLoading } from "../app/ui/loading.js";
import { createElement, setText, setVisible } from "../app/utils/dom.js";
import {
  TRIP_LIMITS,
  validateDateRange,
  validateOptionalText,
  validateRequiredText,
} from "../app/utils/validation.js";

function createField({ name, label, type = "text", required = false, maxLength }) {
  const wrapper = createElement("div", { className: "trips-field" });
  const id = `createTrip-${name}`;
  const errorId = `${id}-error`;
  const labelElement = createElement("label", {
    text: label,
    attributes: { for: id },
  });
  const input = createElement(type === "textarea" ? "textarea" : "input", {
    attributes: {
      id,
      name,
      type: type === "textarea" ? null : type,
      required: required ? "" : null,
      maxlength: maxLength,
      "aria-describedby": errorId,
    },
  });
  const error = createElement("p", {
    className: "trips-field-error",
    attributes: { id: errorId, "data-error-for": name },
  });
  wrapper.append(labelElement, input, error);
  return { wrapper, input, error };
}

function createSelect({ name, label, options }) {
  const wrapper = createElement("div", { className: "trips-field" });
  const id = `createTrip-${name}`;
  const labelElement = createElement("label", {
    text: label,
    attributes: { for: id },
  });
  const select = createElement("select", { attributes: { id, name } });
  options.forEach(([value, text]) => {
    select.appendChild(createElement("option", { text, attributes: { value } }));
  });
  wrapper.append(labelElement, select);
  return { wrapper, input: select, error: null };
}

export function openCreateTripForm({ t, onSubmit }) {
  const modal = createModal({
    title: t("trips.createTitle"),
    className: "app-modal trips-create-modal",
  });
  const form = createElement("form", {
    className: "trips-form",
    attributes: {
      id: `create-trip-form-${crypto.randomUUID()}`,
      novalidate: "",
    },
  });
  const fields = {
    title: createField({
      name: "title",
      label: t("trips.title"),
      required: true,
      maxLength: TRIP_LIMITS.title,
    }),
    description: createField({
      name: "description",
      label: t("trips.description"),
      type: "textarea",
      maxLength: TRIP_LIMITS.description,
    }),
    start_date: createField({
      name: "start_date",
      label: t("trips.startDate"),
      type: "date",
    }),
    end_date: createField({
      name: "end_date",
      label: t("trips.endDate"),
      type: "date",
    }),
    status: createSelect({
      name: "status",
      label: t("trips.status"),
      options: [
        ["draft", t("trips.statusDraft")],
        ["planned", t("trips.statusPlanned")],
        ["active", t("trips.statusActive")],
        ["completed", t("trips.statusCompleted")],
        ["cancelled", t("trips.statusCancelled")],
      ],
    }),
    visibility: createSelect({
      name: "visibility",
      label: t("trips.visibility"),
      options: [
        ["private", t("trips.visibilityPrivate")],
        ["unlisted", t("trips.visibilityUnlisted")],
        ["public", t("trips.visibilityPublic")],
      ],
    }),
  };
  const dates = createElement("div", { className: "trips-form-row" });
  dates.append(fields.start_date.wrapper, fields.end_date.wrapper);
  const selections = createElement("div", { className: "trips-form-row" });
  selections.append(fields.status.wrapper, fields.visibility.wrapper);
  const formError = createElement("p", {
    className: "trips-form-error",
    attributes: { role: "alert", hidden: "" },
  });
  form.append(
    fields.title.wrapper,
    fields.description.wrapper,
    dates,
    selections,
    formError,
  );

  const cancel = createElement("button", {
    className: "trips-secondary-button",
    text: t("common.cancel"),
    attributes: { type: "button" },
  });
  const submit = createElement("button", {
    className: "trips-primary-button",
    text: t("common.save"),
    attributes: { type: "submit", form: form.id },
  });
  modal.actions.append(cancel, submit);
  modal.content.appendChild(form);

  const clearErrors = () => {
    Object.values(fields).forEach(({ input, error }) => {
      input.removeAttribute("aria-invalid");
      if (error) setText(error, "");
    });
    setText(formError, "");
    setVisible(formError, false);
  };
  const setFieldError = (name, message) => {
    const field = fields[name];
    if (!field || !message) return;
    field.input.setAttribute("aria-invalid", "true");
    if (field.error) setText(field.error, Array.isArray(message) ? message[0] : message);
  };
  const close = () => {
    modal.close();
    modal.destroy();
  };

  cancel.addEventListener("click", close);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submit.disabled) return;
    clearErrors();

    let payload;
    try {
      const title = validateRequiredText(fields.title.input.value, {
        field: "title",
        maxLength: TRIP_LIMITS.title,
      });
      const description = validateOptionalText(fields.description.input.value, {
        field: "description",
        maxLength: TRIP_LIMITS.description,
      });
      validateDateRange(fields.start_date.input.value, fields.end_date.input.value);
      payload = {
        title,
        description,
        start_date: fields.start_date.input.value || null,
        end_date: fields.end_date.input.value || null,
        status: fields.status.input.value,
        visibility: fields.visibility.input.value,
      };
    } catch (error) {
      const fieldName = error.message.startsWith("title") ? "title" : "end_date";
      setFieldError(fieldName, t("errors.validation"));
      fields[fieldName].input.focus();
      return;
    }

    modal.setCritical(true);
    cancel.disabled = true;
    setLoading(submit, true, { disable: true, text: t("common.loading") });
    try {
      await onSubmit(payload);
      modal.setCritical(false);
      close();
    } catch (error) {
      if (error.status === 401) {
        modal.setCritical(false);
        close();
        return;
      }
      Object.entries(error.fieldErrors ?? {}).forEach(([name, messages]) => {
        setFieldError(name.split(".").at(-1), messages);
      });
      setText(formError, getLocalizedErrorMessage(error, t));
      setVisible(formError, true);
      modal.setCritical(false);
      cancel.disabled = false;
      setLoading(submit, false, { disable: true });
    }
  });
  modal.open();
  fields.title.input.focus();
}
