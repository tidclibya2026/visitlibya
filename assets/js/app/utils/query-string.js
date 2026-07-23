export function buildQueryString(parameters = {}) {
  const search = new URLSearchParams();
  Object.entries(parameters).forEach(([key, value]) => {
    if (value == null || value === "") return;
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function readQueryParameters(search = globalThis.location?.search ?? "") {
  const parameters = new URLSearchParams(search);
  return Object.freeze(Object.fromEntries(parameters.entries()));
}

export function readPositiveIntegerParameter(
  name,
  search = globalThis.location?.search ?? "",
) {
  const raw = new URLSearchParams(search).get(name);
  if (!raw || !/^\d+$/.test(raw)) return null;
  const value = Number(raw);
  return Number.isSafeInteger(value) && value > 0 ? value : null;
}

export function updateQueryParameters(updates, url = globalThis.location?.href) {
  const next = new URL(url);
  Object.entries(updates).forEach(([key, value]) => {
    if (value == null || value === "") next.searchParams.delete(key);
    else next.searchParams.set(key, String(value));
  });
  return `${next.pathname}${next.search}${next.hash}`;
}
