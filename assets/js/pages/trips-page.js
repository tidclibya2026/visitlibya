import { login } from "../app/api/auth-api.js";
import { createTrip, deleteTrip, listTrips } from "../app/api/trips-api.js";
import { clearSession } from "../app/auth/session.js";
import { bootstrap } from "../app/bootstrap.js";
import { getLocalizedErrorMessage } from "../app/errors/error-messages.js";
import { announce } from "../app/ui/announcer.js";
import { setLoading } from "../app/ui/loading.js";
import { createModal } from "../app/ui/modal.js";
import { toast } from "../app/ui/toast.js";
import {
  createElement,
  queryRequired,
  setText,
  setVisible,
} from "../app/utils/dom.js";
import {
  readPositiveIntegerParameter,
  updateQueryParameters,
} from "../app/utils/query-string.js";
import { openCreateTripForm } from "./trips-form.js";
import {
  renderPagination,
  renderTrips,
  renderTripsEmpty,
  renderTripsError,
  renderTripsLoading,
} from "./trips-renderer.js";

const PAGE_LIMIT = 9;

function currentPage() {
  return readPositiveIntegerParameter("page") ?? 1;
}

function replacePageInUrl(page, replace = false) {
  const next = updateQueryParameters({ page: page > 1 ? page : null });
  globalThis.history[replace ? "replaceState" : "pushState"]({ page }, "", next);
}

function publicErrorMessage(error, t) {
  if (error?.code === "NETWORK_ERROR" && globalThis.navigator?.onLine === false) {
    return t("errors.offline");
  }
  return getLocalizedErrorMessage(error, t);
}

async function initializeTripsPage() {
  const context = await bootstrap();
  if (!context) return;

  const { locale, store, translator } = context;
  const { t } = translator;
  const loginPanel = queryRequired("[data-login-panel]");
  const tripsPanel = queryRequired("[data-trips-panel]");
  const loginForm = queryRequired("[data-login-form]");
  const loginSubmit = queryRequired("[data-login-submit]");
  const loginError = queryRequired("[data-login-error]");
  const username = queryRequired('[name="username"]', loginForm);
  const password = queryRequired('[name="password"]', loginForm);
  const remember = queryRequired('[name="remember"]', loginForm);
  const tripsContent = queryRequired("[data-trips-content]");
  const pagination = queryRequired("[data-pagination]");
  const listTitle = queryRequired("#tripsListTitle");
  const greeting = queryRequired("[data-user-greeting]");
  const createButton = queryRequired("[data-create-trip]");
  const logoutButton = queryRequired("[data-logout]");

  let loadInProgress = false;

  const clearLoginErrors = () => {
    [username, password].forEach((field) => field.removeAttribute("aria-invalid"));
    loginForm.querySelectorAll("[data-error-for]").forEach((element) => setText(element, ""));
    setText(loginError, "");
    setVisible(loginError, false);
  };

  const resetTripsState = () => {
    store.setState({
      locale,
      trips: [],
      selectedTrip: null,
      loading: false,
      saving: false,
      error: null,
      pagination: { skip: 0, limit: PAGE_LIMIT, total: 0 },
      filters: {},
      authenticatedUser: null,
    });
    pagination.hidden = true;
  };

  const showLogin = (message = "") => {
    resetTripsState();
    setVisible(tripsPanel, false);
    setVisible(loginPanel, true);
    if (message) {
      setText(loginError, message);
      setVisible(loginError, true);
      announce(message, { priority: "assertive", force: true });
    }
    globalThis.setTimeout(() => username.focus(), 0);
  };

  const showTrips = (user) => {
    setVisible(loginPanel, false);
    setVisible(tripsPanel, true);
    store.updateState({ authenticatedUser: user });
    setText(
      greeting,
      t("trips.welcome", { name: user.full_name || user.username }),
    );
  };

  const openTrip = (trip) => {
    globalThis.location.assign(`trip.html?id=${encodeURIComponent(trip.id)}`);
  };

  const loadTripsPage = async (page, options = {}) => {
    if (loadInProgress || !store.getState().authenticatedUser) return;
    loadInProgress = true;
    store.updateState({ loading: true, error: null });
    renderTripsLoading(tripsContent, t("common.loading"));
    pagination.hidden = true;

    try {
      const response = await listTrips({
        skip: (page - 1) * PAGE_LIMIT,
        limit: PAGE_LIMIT,
      });
      const pages = Math.max(1, Math.ceil(response.total / response.limit));
      if (page > pages) {
        loadInProgress = false;
        replacePageInUrl(pages, true);
        await loadTripsPage(pages, options);
        return;
      }

      store.updateState({
        trips: response.items,
        loading: false,
        pagination: {
          skip: response.skip,
          limit: response.limit,
          total: response.total,
        },
      });

      if (response.items.length === 0) {
        renderTripsEmpty(tripsContent, t, () => openCreate());
      } else {
        renderTrips(tripsContent, response.items, {
          locale,
          t,
          onOpen: openTrip,
          onDelete: (trip) => openDeleteConfirmation(trip),
        });
      }
      renderPagination(pagination, {
        page,
        total: response.total,
        limit: response.limit,
        loading: false,
        t,
        onPageChange: (nextPage) => {
          if (loadInProgress) return;
          replacePageInUrl(nextPage);
          void loadTripsPage(nextPage, { focus: true, announce: true });
        },
      });

      if (options.focus) listTitle.focus();
      if (options.announce) announce(t("trips.listLoaded"), { force: true });
    } catch (error) {
      store.updateState({ loading: false, error });
      if (error.status === 401) return;
      const message = publicErrorMessage(error, t);
      renderTripsError(
        tripsContent,
        message,
        t("common.retry"),
        () => void loadTripsPage(page, { focus: true, announce: true }),
      );
      announce(message, { priority: "assertive", force: true });
    } finally {
      loadInProgress = false;
    }
  };

  const openCreate = () => {
    openCreateTripForm({
      t,
      onSubmit: async (payload) => {
        await createTrip(payload);
        toast.success(t("trips.saved"), { closeLabel: t("common.close") });
        announce(t("trips.saved"), { force: true });
        replacePageInUrl(1, true);
        void loadTripsPage(1, { focus: true });
      },
    });
  };

  const openDeleteConfirmation = (trip) => {
    const modal = createModal({
      title: t("trips.deleteTitle"),
      className: "app-modal trips-delete-modal",
    });
    const message = createElement("p", {
      text: t("trips.deleteMessage", { title: trip.title }),
    });
    const errorText = createElement("p", {
      className: "trips-form-error",
      attributes: { role: "alert", hidden: "" },
    });
    const cancel = createElement("button", {
      className: "trips-secondary-button",
      text: t("common.cancel"),
      attributes: { type: "button" },
    });
    const remove = createElement("button", {
      className: "trips-danger-button",
      text: t("common.delete"),
      attributes: { type: "button" },
    });
    const close = () => {
      modal.close();
      modal.destroy();
    };
    cancel.addEventListener("click", close);
    remove.addEventListener("click", async () => {
      if (remove.disabled) return;
      modal.setCritical(true);
      cancel.disabled = true;
      setLoading(remove, true, { disable: true, text: t("common.loading") });
      try {
        await deleteTrip(trip.id);
        modal.setCritical(false);
        close();
        toast.success(t("trips.deleted"), { closeLabel: t("common.close") });
        announce(t("trips.deleted"), { force: true });
        await loadTripsPage(currentPage(), { focus: true });
      } catch (error) {
        if (error.status === 401) {
          modal.setCritical(false);
          close();
          return;
        }
        if (error.status === 404) {
          modal.setCritical(false);
          close();
          toast.info(t("trips.noLongerExists"), { closeLabel: t("common.close") });
          await loadTripsPage(currentPage(), { focus: true });
          return;
        }
        const messageText = publicErrorMessage(error, t);
        setText(errorText, messageText);
        setVisible(errorText, true);
        announce(messageText, { priority: "assertive", force: true });
        modal.setCritical(false);
        cancel.disabled = false;
        setLoading(remove, false, { disable: true });
      }
    });
    modal.content.append(message, errorText);
    modal.actions.append(cancel, remove);
    modal.open();
  };

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (loginSubmit.disabled) return;
    clearLoginErrors();

    const identifier = username.value.trim();
    if (!identifier || !password.value) {
      if (!identifier) username.setAttribute("aria-invalid", "true");
      if (!password.value) password.setAttribute("aria-invalid", "true");
      setText(loginError, t("errors.validation"));
      setVisible(loginError, true);
      (identifier ? password : username).focus();
      return;
    }

    setLoading(loginSubmit, true, { disable: true, text: t("common.loading") });
    try {
      const result = await login({
        username: identifier,
        password: password.value,
        rememberForSession: remember.checked,
      });
      password.value = "";
      showTrips(result.currentUser);
      listTitle.focus();
      await loadTripsPage(currentPage(), { announce: true });
    } catch (error) {
      setText(loginError, publicErrorMessage(error, t));
      setVisible(loginError, true);
      announce(publicErrorMessage(error, t), { priority: "assertive", force: true });
      password.focus();
    } finally {
      setLoading(loginSubmit, false, { disable: true });
    }
  });

  createButton.addEventListener("click", openCreate);
  logoutButton.addEventListener("click", () => {
    clearSession({ reason: "logout" });
    showLogin();
    toast.info(t("trips.logout"), { closeLabel: t("common.close") });
    announce(t("trips.logout"), { force: true });
  });
  globalThis.addEventListener("visitlibya:auth-expired", () => {
    showLogin(t("auth.expired"));
  });
  globalThis.addEventListener("popstate", () => {
    void loadTripsPage(currentPage(), { focus: true, announce: true });
  });

  if (context.session.authenticated && context.session.currentUser) {
    showTrips(context.session.currentUser);
    await loadTripsPage(currentPage());
  } else {
    showLogin();
  }
}

if (typeof document !== "undefined") {
  void initializeTripsPage();
}

export { initializeTripsPage };
