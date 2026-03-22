/* HUTKO — api.js
   Token-based auth. Token stored in localStorage.
   Sent as Authorization: Bearer <token> on every request.
*/

const API_BASE = 'https://hutko-kitchen.onrender.com';
const TOKEN_KEY = 'hutko_token';
const USER_KEY  = 'hutko_user';

function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }
function saveToken(t) { localStorage.setItem(TOKEN_KEY, t); }
function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function apiCall(method, path, body = null) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  try {
    const res  = await fetch(API_BASE + path, opts);
    const data = await res.json();
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    /* Network error or timeout (e.g. Render cold start) —
       return a network error but DO NOT clear the token.
       The user is still logged in, the server just isn't awake yet. */
    console.warn(`API network error [${method} ${path}]:`, err.message);
    return { ok: false, status: 0, data: { error: 'network_error' } };
  }
}

/* getUser — reads cached user from localStorage (used by components.js) */
function getUser() {
  try { return JSON.parse(localStorage.getItem(USER_KEY)) || null; }
  catch { return null; }
}
window.getUser = getUser;

const Auth = {
  async register(name, email, password, phone = '') {
    const res = await apiCall('POST', '/api/register', { name, email, password, phone });
    if (res.ok && res.data.token) {
      saveToken(res.data.token);
      localStorage.setItem(USER_KEY, JSON.stringify({
        id: res.data.user.id, name: res.data.user.name, email: res.data.user.email
      }));
    }
    return res;
  },
  async login(email, password) {
    const res = await apiCall('POST', '/api/login', { email, password });
    if (res.ok && res.data.token) {
      saveToken(res.data.token);
      localStorage.setItem(USER_KEY, JSON.stringify({
        id: res.data.user.id, name: res.data.user.name, email: res.data.user.email
      }));
    }
    return res;
  },
  async logout() {
    await apiCall('POST', '/api/logout');
    clearAuth();
  },
  async me() { return apiCall('GET', '/api/me'); },
  async updateProfile(name, phone, password = '') {
    return apiCall('PUT', '/api/profile', { name, phone, password });
  },
  async saveAddress(street, postcode, city, province) {
    return apiCall('PUT', '/api/address', { street, postcode, city, province });
  },
};

const Orders = {
  async checkout(payload) { return apiCall('POST', '/api/checkout', payload); },
  async myOrders()        { return apiCall('GET', '/api/orders'); },
  async getOrder(ref)     { return apiCall('GET', `/api/orders/${ref}`); },
};

const Contact = {
  async send(name, email, phone, social, topic, title, body) {
    return apiCall('POST', '/api/contact', { name, email, phone, social, topic, title, body });
  },
  async subscribe(email) { return apiCall('POST', '/api/newsletter', { email }); },
};

const Admin = {
  async login(password) {
    const res = await apiCall('POST', '/api/admin/login', { password });
    if (res.ok && res.data.token) saveToken(res.data.token);
    return res;
  },
  async stats()  { return apiCall('GET', '/api/admin/stats'); },
  exportUrl()    { return `${API_BASE}/api/admin/export`; },
};

/* syncSession — runs on every page load.
   Only clears auth on a real 401 (token invalid/expired).
   Ignores network errors so a sleeping Render doesn't log the user out. */
async function syncSession() {
  const token = getToken();
  if (!token) return;   /* not logged in, nothing to do */

  const res = await Auth.me();

  if (res.status === 401) {
    /* Token is genuinely invalid — clear it */
    clearAuth();
    return;
  }

  if (res.ok && res.data.user) {
    /* Update stored user data with fresh data from server */
    const user = res.data.user;
    localStorage.setItem(USER_KEY, JSON.stringify({
      id: user.id, name: user.name, email: user.email
    }));
    /* Pre-fill checkout address fields if on checkout page */
    if (user.addr_street) {
      const fill = (id, val) => {
        const el = document.getElementById(id);
        if (el && !el.value) el.value = val || '';
      };
      fill('coStreet',   user.addr_street);
      fill('coPost',     user.addr_postcode);
      fill('coCity',     user.addr_city);
      fill('coProvince', user.addr_province);
    }
  }
  /* If status === 0 (network error / Render sleeping):
     do nothing — keep existing localStorage user data intact */
}

/* Guard for pages that require login (account.html, checkout.html).
   Call this instead of syncSession on protected pages. */
async function requireLogin(redirectTo = 'login.html') {
  const token = getToken();
  const user  = localStorage.getItem(USER_KEY);

  /* If we have both token and cached user — show the page immediately
     using cached data, then verify in background */
  if (token && user) {
    /* Background verify — don't block the page */
    Auth.me().then(res => {
      if (res.status === 401) {
        clearAuth();
        window.location.href = redirectTo + '?redirect=' + encodeURIComponent(window.location.pathname.split('/').pop());
      }
    });
    return true;   /* page can render */
  }

  /* No token at all — redirect to login */
  clearAuth();
  window.location.href = redirectTo + '?redirect=' + encodeURIComponent(window.location.pathname.split('/').pop());
  return false;
}

window.Api          = { Auth, Orders, Contact, Admin };
window.syncSession  = syncSession;
window.requireLogin = requireLogin;
window.getToken     = getToken;
window.clearAuth    = clearAuth;

document.addEventListener('DOMContentLoaded', syncSession);
