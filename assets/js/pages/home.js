function initializeHomepage(documentRef = document) {
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

  const normalize = (value) =>
    String(value ?? "")
      .normalize("NFKC")
      .trim()
      .toLocaleLowerCase(isArabic ? "ar" : "en");

  const searchableText = (item) =>
    normalize(`${item.textContent} ${item.dataset.homeKeywords ?? ""}`);

  const setFilterState = (query) => {
    filters.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        String(normalize(button.dataset.homeFilter) === query && query !== ""),
      );
    });
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

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    applyFilter();
  });

  input.addEventListener("input", applyFilter);

  form.addEventListener("reset", () => {
    requestAnimationFrame(() => {
      applyFilter();
      input.focus();
    });
  });

  filters.forEach((button) => {
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      input.value = button.dataset.homeFilter ?? "";
      applyFilter();
      documentRef
        .getElementById("featured-destinations")
        ?.scrollIntoView({
          behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "auto"
            : "smooth",
          block: "start",
        });
    });
  });

  reset?.removeAttribute("hidden");
  applyFilter();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => initializeHomepage(), {
    once: true,
  });
} else {
  initializeHomepage();
}
