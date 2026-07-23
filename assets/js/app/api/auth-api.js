import { apiClient } from "./client.js";
import {
  clearSession,
  getAccessToken,
  setSession,
} from "../auth/session.js";

/**
 * @typedef {object} TokenResponse
 * @property {string} access_token
 * @property {"bearer"} token_type
 * @property {number} expires_in
 *
 * @typedef {object} CurrentUserResponse
 * @property {number} id
 * @property {string} email
 * @property {string} username
 * @property {string} full_name
 * @property {boolean} is_active
 * @property {boolean} is_superuser
 * @property {string[]} roles
 */

/**
 * Authenticate with FastAPI OAuth2PasswordRequestForm, then verify identity
 * through GET /auth/me.
 * @returns {Promise<{token: TokenResponse, currentUser: CurrentUserResponse}>}
 */
export async function login({ username, password, rememberForSession = false }, options = {}) {
  const form = new URLSearchParams();
  form.set("username", String(username ?? ""));
  form.set("password", String(password ?? ""));

  const token = await apiClient.post("/auth/login", form, {
    ...options,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      ...options.headers,
    },
  });

  setSession({
    accessToken: token.access_token,
    rememberForSession,
    verified: false,
  });

  try {
    const currentUser = await getCurrentUser(options);
    setSession({
      accessToken: token.access_token,
      currentUser,
      rememberForSession,
      verified: true,
    });
    return Object.freeze({ token, currentUser });
  } catch (error) {
    clearSession({ reason: "identity-verification-failed" });
    throw error;
  }
}

export function getCurrentUser(options = {}) {
  return apiClient.get("/auth/me", options);
}

export async function verifyRestoredSession(options = {}) {
  const accessToken = getAccessToken();
  if (!accessToken) return null;

  try {
    const currentUser = await getCurrentUser(options);
    setSession({
      accessToken,
      currentUser,
      rememberForSession: true,
      verified: true,
    });
    return currentUser;
  } catch (error) {
    clearSession({ reason: "restore-verification-failed" });
    throw error;
  }
}
