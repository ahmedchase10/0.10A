// =============================================
// DIGI-SCHOOL AI — Auth State
// Stores JWT token + user profile in sessionStorage.
// =============================================

const USER_KEY  = 'digischool_user';
const TOKEN_KEY = 'digischool_token';

export function isLoggedIn() {
  return !!sessionStorage.getItem(TOKEN_KEY);
}

export function getUser() {
  const raw = sessionStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setSession(user, token) {
  sessionStorage.setItem(USER_KEY,  JSON.stringify(user));
  sessionStorage.setItem(TOKEN_KEY, token);
}

// keep setUser for any legacy calls
export function setUser(user) {
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function logout() {
  sessionStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
}