const STORAGE_KEY = "visitlibya.auth.session";
const listeners = new Set();

let session = Object.freeze({
  accessToken: null,
  currentUser: null,
  rememberForSession: false,
  verified: false,
});

function notify() {
  const snapshot = getSessionSnapshot();
  listeners.forEach((listener) => listener(snapshot));
  globalThis.dispatchEvent?.(
    new CustomEvent("visitlibya:session-changed", { detail: snapshot }),
  );
}

function getSessionStorage() {
  try {
    return globalThis.sessionStorage ?? null;
  } catch {
    return null;
  }
}

function persist() {
  const storage = getSessionStorage();
  if (!storage) return;

  if (!session.rememberForSession || !session.accessToken) {
    storage.removeItem(STORAGE_KEY);
    return;
  }

  storage.setItem(
    STORAGE_KEY,
    JSON.stringify({ accessToken: session.accessToken }),
  );
}

export function setSession({
  accessToken,
  currentUser = null,
  rememberForSession = false,
  verified = Boolean(currentUser),
}) {
  if (typeof accessToken !== "string" || !accessToken.trim()) {
    throw new TypeError("A non-empty access token is required");
  }

  session = Object.freeze({
    accessToken: accessToken.trim(),
    currentUser: currentUser ? Object.freeze({ ...currentUser }) : null,
    rememberForSession: Boolean(rememberForSession),
    verified: Boolean(verified && currentUser),
  });
  persist();
  notify();
  return getSessionSnapshot();
}

export function getAccessToken() {
  return session.accessToken;
}

export function getCurrentUser() {
  return session.verified ? session.currentUser : null;
}

export function isAuthenticated() {
  return Boolean(session.accessToken && session.verified && session.currentUser);
}

export function getSessionSnapshot() {
  return Object.freeze({
    currentUser: getCurrentUser(),
    rememberForSession: session.rememberForSession,
    verified: session.verified,
    authenticated: isAuthenticated(),
  });
}

export function clearSession({ reason = "manual" } = {}) {
  session = Object.freeze({
    accessToken: null,
    currentUser: null,
    rememberForSession: false,
    verified: false,
  });
  getSessionStorage()?.removeItem(STORAGE_KEY);
  notify();
  return reason;
}

export function restoreSession() {
  const storage = getSessionStorage();
  if (!storage) return getSessionSnapshot();

  try {
    const stored = JSON.parse(storage.getItem(STORAGE_KEY) ?? "null");
    if (typeof stored?.accessToken !== "string" || !stored.accessToken.trim()) {
      clearSession({ reason: "invalid-storage" });
      return getSessionSnapshot();
    }
    session = Object.freeze({
      accessToken: stored.accessToken.trim(),
      currentUser: null,
      rememberForSession: true,
      verified: false,
    });
    notify();
  } catch {
    clearSession({ reason: "invalid-storage" });
  }
  return getSessionSnapshot();
}

export function subscribe(listener) {
  if (typeof listener !== "function") {
    throw new TypeError("Session subscriber must be a function");
  }
  listeners.add(listener);
  return () => unsubscribe(listener);
}

export function unsubscribe(listener) {
  listeners.delete(listener);
}
