import {
  getSessionSnapshot,
  restoreSession,
  subscribe,
} from "../auth/session.js";
import { configureAtlasExternalLink } from "../config/runtime-config.js";

const MOBILE_NAV_QUERY = "(max-width: 1050px)";

function localizedText(english, arabic) {
  return document.documentElement.lang === "ar" ? arabic : english;
}

function ensureSkipLink() {
  if (document.querySelector(".trips-skip-link, .site-skip-link")) return;
  const main = document.querySelector("main");
  if (!main) return;
  if (!main.id) main.id = "mainContent";
  const link = document.createElement("a");
  link.className = "site-skip-link";
  link.href = `#${main.id}`;
  link.textContent = localizedText("Skip to content", "انتقل إلى المحتوى");
  document.body.prepend(link);
}

function enhanceHeader() {
  const header = document.querySelector(".vl-topbar");
  const toggle = document.getElementById("navToggle");
  const nav = document.getElementById("primaryNav");
  const language = header?.querySelector(".vl-language");
  if (!header || !toggle || !nav) return;

  const actions = document.createElement("div");
  actions.className = "site-header-actions";
  if (language) actions.appendChild(language);

  const account = document.createElement("a");
  account.className = "site-account-link";
  account.href = document.documentElement.lang === "ar" ? "trips.html" : "trips.html";
  actions.appendChild(account);
  header.appendChild(actions);

  const renderAccount = (session = getSessionSnapshot()) => {
    account.textContent = session.authenticated
      ? localizedText("My Trips", "رحلاتي")
      : localizedText("Sign in", "تسجيل الدخول");
    account.setAttribute(
      "aria-label",
      session.authenticated
        ? localizedText("Open My Trips", "فتح رحلاتي")
        : localizedText("Sign in to Visit Libya", "تسجيل الدخول إلى Visit Libya"),
    );
  };

  renderAccount(restoreSession());
  subscribe(renderAccount);

  const syncMenuState = () => {
    const open = toggle.getAttribute("aria-expanded") === "true";
    document.body.classList.toggle(
      "site-menu-open",
      open && matchMedia(MOBILE_NAV_QUERY).matches,
    );
    if (open && matchMedia(MOBILE_NAV_QUERY).matches) {
      requestAnimationFrame(() => nav.querySelector("a")?.focus());
    }
  };

  new MutationObserver(syncMenuState).observe(toggle, {
    attributes: true,
    attributeFilter: ["aria-expanded"],
  });

  matchMedia(MOBILE_NAV_QUERY).addEventListener("change", () => {
    if (!matchMedia(MOBILE_NAV_QUERY).matches) {
      document.body.classList.remove("site-menu-open");
    }
  });
}

function preserveLanguageQuery() {
  const languageLink = document.querySelector(".vl-language");
  if (!languageLink || !location.search) return;
  const target = new URL(languageLink.href, location.href);
  target.search = location.search;
  languageLink.href = target.href;
}

function enhanceFooter() {
  const footer = document.querySelector(".vl-footer");
  if (!footer || footer.querySelector(".site-footer-meta")) return;
  const meta = document.createElement("p");
  meta.className = "site-footer-meta";
  meta.textContent = localizedText(
    `© ${new Date().getFullYear()} Visit Libya. National tourism platform.`,
    `© ${new Date().getFullYear()} Visit Libya. المنصة السياحية الوطنية.`,
  );
  footer.appendChild(meta);
}

function markDocument() {
  document.body.classList.add("site-shell");
  document.querySelector("main")?.classList.add("site-page-main");
}

function enhanceAtlasLinks() {
  const locale = document.documentElement.lang === "ar" ? "ar" : "en";
  document.querySelectorAll("[data-atlas-external]").forEach((link) => {
    configureAtlasExternalLink(link, {
      locale,
      context: link.getAttribute("data-atlas-context") ?? "",
    });
  });
}

function initializeSiteShell() {
  ensureSkipLink();
  markDocument();
  enhanceHeader();
  preserveLanguageQuery();
  enhanceFooter();
  enhanceAtlasLinks();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeSiteShell, { once: true });
} else {
  initializeSiteShell();
}
