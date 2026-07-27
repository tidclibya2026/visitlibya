import { register } from "../app/api/auth-api.js";
import { bootstrap } from "../app/bootstrap.js";
import { getLocalizedErrorMessage } from "../app/errors/error-messages.js";
import { announce } from "../app/ui/announcer.js";
import { setLoading } from "../app/ui/loading.js";
import { createModal } from "../app/ui/modal.js";
import {
  createElement,
  queryRequired,
  setText,
  setVisible,
} from "../app/utils/dom.js";

const PASSWORD_MIN_LENGTH = 12;
const PASSWORD_MAX_LENGTH = 128;
const USERNAME_PATTERN = /^[a-z0-9][a-z0-9._-]{2,99}$/;

function passwordIsStrong(value) {
  return (
    value.length >= PASSWORD_MIN_LENGTH &&
    value.length <= PASSWORD_MAX_LENGTH &&
    /[a-z]/.test(value) &&
    /[A-Z]/.test(value) &&
    /\d/.test(value) &&
    /[^\p{L}\p{N}\s]/u.test(value)
  );
}

function initializeFields(form) {
  return Object.freeze({
    fullName: queryRequired('[name="full_name"]', form),
    email: queryRequired('[name="email"]', form),
    username: queryRequired('[name="username"]', form),
    password: queryRequired('[name="password"]', form),
    confirmPassword: queryRequired('[name="confirm_password"]', form),
  });
}

function showRegistrationSuccess(t, signInPath) {
  const modal = createModal({
    title: t("auth.registrationSuccessTitle"),
    className: "app-modal",
    critical: true,
  });
  const message = createElement("p", {
    text: t("auth.registrationSuccessMessage"),
    attributes: { role: "status", "aria-live": "polite" },
  });
  const signIn = createElement("button", {
    className: "trips-primary-button",
    text: t("auth.signIn"),
    attributes: { type: "button" },
  });
  signIn.addEventListener("click", () => globalThis.location.assign(signInPath));
  modal.content.appendChild(message);
  modal.actions.appendChild(signIn);
  modal.open();
  announce(t("auth.registrationSuccessMessage"), { force: true });
}

async function initializeRegistrationPage() {
  const context = await bootstrap();
  if (!context) return;

  const { locale, translator } = context;
  const { t } = translator;
  const form = queryRequired("[data-register-form]");
  const submit = queryRequired("[data-register-submit]", form);
  const formError = queryRequired("[data-register-error]", form);
  const fields = initializeFields(form);
  const signInPath = locale === "ar" ? "trips.html" : "trips.html";
  let submitting = false;

  const errorElement = (name) =>
    queryRequired(`[data-error-for="${name}"]`, form);

  const clearErrors = () => {
    Object.values(fields).forEach((field) => field.removeAttribute("aria-invalid"));
    form.querySelectorAll("[data-error-for]").forEach((element) => setText(element, ""));
    setText(formError, "");
    setVisible(formError, false);
  };

  const setFieldError = (name, message) => {
    fields[name].setAttribute("aria-invalid", "true");
    setText(errorElement(fields[name].name), message);
  };

  const validate = () => {
    clearErrors();
    const fullName = fields.fullName.value.trim();
    const email = fields.email.value.trim().toLowerCase();
    const username = fields.username.value.trim().toLowerCase();
    const password = fields.password.value;
    const confirmPassword = fields.confirmPassword.value;
    let firstInvalid = null;

    const invalidate = (name, message) => {
      setFieldError(name, message);
      firstInvalid ??= fields[name];
    };

    if (!fullName) invalidate("fullName", t("auth.fullNameRequired"));
    if (!email) invalidate("email", t("auth.emailRequired"));
    else if (!fields.email.validity.valid) {
      invalidate("email", t("auth.emailInvalid"));
    }
    if (!username) invalidate("username", t("auth.usernameRequired"));
    else if (!USERNAME_PATTERN.test(username)) {
      invalidate("username", t("auth.usernameInvalid"));
    }
    if (!password) invalidate("password", t("auth.passwordRequired"));
    else if (!passwordIsStrong(password)) {
      invalidate("password", t("auth.passwordInvalid"));
    }
    if (!confirmPassword) {
      invalidate("confirmPassword", t("auth.confirmPasswordRequired"));
    } else if (confirmPassword !== password) {
      invalidate("confirmPassword", t("auth.passwordMismatch"));
    }

    if (firstInvalid) {
      firstInvalid.focus();
      announce(t("errors.validation"), { priority: "assertive", force: true });
      return null;
    }
    return { fullName, email, username, password };
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submitting || submit.disabled) return;
    const payload = validate();
    if (!payload) return;

    submitting = true;
    setLoading(submit, true, {
      disable: true,
      text: t("auth.creatingAccount"),
    });
    try {
      await register(payload);
      fields.password.value = "";
      fields.confirmPassword.value = "";
      showRegistrationSuccess(t, signInPath);
    } catch (error) {
      if (error.code === "AUTH_EMAIL_CONFLICT") {
        setFieldError("email", t("auth.emailConflict"));
        setText(formError, t("auth.emailConflict"));
        fields.email.focus();
      } else if (error.code === "AUTH_USERNAME_CONFLICT") {
        setFieldError("username", t("auth.usernameConflict"));
        setText(formError, t("auth.usernameConflict"));
        fields.username.focus();
      } else if (error.status === 409) {
        setText(formError, getLocalizedErrorMessage(error, t));
      } else if (error.status === 422) {
        let firstServerField = null;
        Object.keys(error.fieldErrors ?? {}).forEach((fieldName) => {
          const mapping = {
            full_name: ["fullName", t("auth.fullNameRequired")],
            email: ["email", t("auth.emailInvalid")],
            username: ["username", t("auth.usernameInvalid")],
            password: ["password", t("auth.passwordInvalid")],
          };
          const target = mapping[fieldName.split(".").at(-1)];
          if (target) {
            setFieldError(...target);
            firstServerField ??= fields[target[0]];
          }
        });
        setText(formError, t("errors.validation"));
        firstServerField?.focus();
      } else {
        setText(
          formError,
          getLocalizedErrorMessage(error, t) || t("auth.registrationFailed"),
        );
      }
      setVisible(formError, true);
      announce(formError.textContent, { priority: "assertive", force: true });
    } finally {
      submitting = false;
      setLoading(submit, false, { disable: true });
    }
  });
}

if (typeof document !== "undefined") {
  void initializeRegistrationPage();
}

export {
  initializeRegistrationPage,
  passwordIsStrong,
};
