/* ── HUTKO — api.js ──────────────────────────────────────
   Single source of truth for all backend API calls.
   ─────────────────────────────────────────────────────── */

const API_BASE = 'https://hutko-kitchen.onrender.com';

function getToken() {
  try { return localStorage.getItem('hutko_token') || ''; } catch { return ''; }
}
function saveToken(token) {
  try { localStorage.setItem('hutko_token', token); } catch {}
}
function clearToken() {
  try { localStorage.removeItem('hutko_token'); localStorage.removeItem('hutko_user'); } catch {}
}
// getUser defined here (not only in components.js) so syncSession can call it safely
function getUser() {
  try { return JSON.parse(localStorage.getItem('hutko_user')) || null; } catch { return null; }
}
window.getUser = getUser;

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
    console.error(`API error [${method} ${path}]:`, err);
    return { ok: false, status: 0, data: { error: 'Network error. Please try again.' } };
  }
}

/* ── AUTH ────────────────────────────────────────────── */
const Auth = {
  async register(name, email, password, phone = '') {
    const res = await apiCall('POST', '/api/register', { name, email, password, phone });
    if (res.ok && res.data.token) saveToken(res.data.token);
    return res;
  },
  async login(email, password) {
    const res = await apiCall('POST', '/api/login', { email, password });
    if (res.ok && res.data.token) saveToken(res.data.token);
    return res;
  },
  async logout() {
    const res = await apiCall('POST', '/api/logout');
    clearToken();
    return res;
  },
  async me() {
    return apiCall('GET', '/api/me');
  },
  async updateProfile(name, phone, password = '') {
    return apiCall('PUT', '/api/profile', { name, phone, password });
  },
  async saveAddress(street, postcode, city, province) {
    return apiCall('PUT', '/api/address', { street, postcode, city, province });
  },
};

/* ── ORDERS ──────────────────────────────────────────── */
const Orders = {
  async checkout(payload) {
    return apiCall('POST', '/api/checkout', payload);
  },
  async myOrders() {
    return apiCall('GET', '/api/orders');
  },
  async getOrder(ref) {
    return apiCall('GET', `/api/orders/${ref}`);
  },
};

/* ── CONTACT ─────────────────────────────────────────── */
const Contact = {
  async send(name, email, phone, social, topic, title, body) {
    return apiCall('POST', '/api/contact', { name, email, phone, social, topic, title, body });
  },
  async subscribe(email) {
    return apiCall('POST', '/api/newsletter', { email });
  },
};

/* ── ADMIN ───────────────────────────────────────────── */
const Admin = {
  async login(password) {
    const res = await apiCall('POST', '/api/admin/login', { password });
    if (res.ok && res.data.token) saveToken('admin_' + res.data.token);
    return res;
  },
  async stats() {
    return apiCall('GET', '/api/admin/stats');
  },
  exportUrl() {
    return `${API_BASE}/api/admin/export`;
  },
};

/* ── SESSION HELPER ──────────────────────────────────── */
async function syncSession() {
  const token = getToken();
  if (!token) {
    localStorage.removeItem('hutko_user');
    return;
  }
  // If we have cached user data, use it immediately (no flicker)
  const cached = getUser();
  if (cached) return; // Already have user data, skip API call

  try {
    const res = await Auth.me();
    if (res.ok && res.data.user) {
      const user = res.data.user;
      localStorage.setItem('hutko_user', JSON.stringify({
        id:    user.id,
        name:  user.name,
        email: user.email,
      }));
    } else if (res.status === 401) {
      // Only clear on explicit auth failure, not network errors
      clearToken();
    }
    // On 0 (network error) or 5xx — keep token, server might be sleeping
  } catch(e) {
    // Network error — keep token
  }
}

window.Api         = { Auth, Orders, Contact, Admin };
window.syncSession = syncSession;
window.getToken    = getToken;
window.getUser     = getUser;

/* Run on every page load — only if token exists to avoid unnecessary requests */
document.addEventListener('DOMContentLoaded', () => {
  if (getToken()) syncSession();
});
