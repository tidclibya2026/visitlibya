const HOME_REVEAL_SELECTOR = [
  ".home-section__heading", ".home-theme-card", ".home-inspiration-card",
  ".home-destination-card", ".home-planner", ".home-heritage",
].join(",");

function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// HOME — HEADER SCROLL STATE
function initHomeHeader(documentRef = document) {
  const header = documentRef.getElementById("siteHeader");
  if (!header) return;
  let framePending = false;
  const render = () => {
    header.classList.toggle("panorama-header--scrolled", window.scrollY > 48);
    framePending = false;
  };
  const requestRender = () => {
    if (framePending) return;
    framePending = true;
    window.requestAnimationFrame(render);
  };
  render();
  window.addEventListener("scroll", requestRender, { passive: true });
}

// HOME — REVEAL OBSERVER
function initHomeReveals(documentRef = document) {
  const targets = [...documentRef.querySelectorAll(HOME_REVEAL_SELECTOR)];
  if (!targets.length) return;
  let destinationIndex = 0;
  targets.forEach((element) => {
    element.classList.add("home-reveal");
    if (element.classList.contains("home-destination-card")) {
      element.style.setProperty("--home-reveal-delay", `${destinationIndex * 55}ms`);
      destinationIndex += 1;
    }
  });
  if (prefersReducedMotion() || !("IntersectionObserver" in window)) {
    targets.forEach((element) => element.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver((entries, activeObserver) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      activeObserver.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -8%", threshold: 0.12 });
  targets.forEach((element) => observer.observe(element));
}

// HOME — DISCOVERY / FILTERS
function initHomeDiscovery(documentRef = document) {
  const form = documentRef.querySelector("[data-home-search-form]");
  const input = documentRef.querySelector("[data-home-search-input]");
  const reset = documentRef.querySelector("[data-home-search-reset]");
  const count = documentRef.querySelector("[data-home-result-count]");
  const empty = documentRef.querySelector("[data-home-no-results]");
  const items = [...documentRef.querySelectorAll("[data-home-search-item]")];
  const filters = [...documentRef.querySelectorAll("[data-home-filter]")];
  if (!form || !input || !count || !empty || !items.length) return;

  const isArabic = documentRef.documentElement.lang === "ar";
  const numberFormat = new Intl.NumberFormat(isArabic ? "ar-LY" : "en");
  const normalize = (value) => String(value ?? "").normalize("NFKC").trim()
    .toLocaleLowerCase(isArabic ? "ar" : "en");
  const searchableText = (item) =>
    normalize(`${item.textContent} ${item.dataset.homeKeywords ?? ""}`);
  const setFilterState = (query) => {
    filters.forEach((button) => button.setAttribute("aria-pressed", String(
      normalize(button.dataset.homeFilter) === query && query !== "",
    )));
  };
  const announceResults = (visible) => {
    const formatted = numberFormat.format(visible);
    count.textContent = isArabic
      ? `${formatted} نتيجة متاحة للاستكشاف.`
      : `${formatted} ${visible === 1 ? "result" : "results"} ready to explore.`;
    empty.hidden = visible !== 0;
  };
  const applyFilter = () => {
    const query = normalize(input.value);
    let visible = 0;
    items.forEach((item) => {
      const matches = !query || searchableText(item).includes(query);
      item.hidden = !matches;
      if (matches) visible += 1;
    });
    setFilterState(query);
    announceResults(visible);
  };

  form.addEventListener("submit", (event) => { event.preventDefault(); applyFilter(); });
  input.addEventListener("input", applyFilter);
  form.addEventListener("reset", () => window.requestAnimationFrame(() => {
    applyFilter();
    input.focus();
  }));
  filters.forEach((button) => {
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      input.value = button.dataset.homeFilter ?? "";
      applyFilter();
      documentRef.getElementById("featured-destinations")?.scrollIntoView({
        behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start",
      });
    });
  });
  reset?.removeAttribute("hidden");
  applyFilter();
}

// HOME — INITIALIZATION
function initializeHome(documentRef = document) {
  if (!documentRef.body.classList.contains("home-page")) return;
  initHomeHeader(documentRef);
  initHomeReveals(documentRef);
  initHomeDiscovery(documentRef);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => initializeHome(), { once: true });
} else {
  initializeHome();
}
