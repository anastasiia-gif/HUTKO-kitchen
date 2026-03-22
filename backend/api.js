/* ── HUTKO — api.js ──────────────────────────────────────
   Single source of truth for all backend API calls.
   Replace API_BASE with your Render URL when deployed.
   ─────────────────────────────────────────────────────── */

const API_BASE = 'https://hutko-kitchen.onrender.com';

async function apiCall(method, path, body = null) {
  const opts = {
    method,
    credentials: 'include',          // send session cookie cross-origin
    headers: { 'Content-Type': 'application/json' },
  };
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
    return apiCall('POST', '/api/register', { name, email, password, phone });
  },
  async login(email, password) {
    return apiCall('POST', '/api/login', { email, password });
  },
  async logout() {
    return apiCall('POST', '/api/logout');
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
    return apiCall('POST', '/api/admin/login', { password });
  },
  async stats() {
    return apiCall('GET', '/api/admin/stats');
  },
  exportUrl() {
    return `${API_BASE}/api/admin/export`;
  },
};

/* ── SESSION HELPER ──────────────────────────────────── */
/* Checks /api/me on page load — updates navbar if logged in */
async function syncSession() {
  const res = await Auth.me();
  if (res.ok && res.data.user) {
    const user = res.data.user;
    /* Store minimal info for navbar rendering */
    localStorage.setItem('hutko_user', JSON.stringify({
      id:    user.id,
      name:  user.name,
      email: user.email,
    }));
    /* Pre-fill saved address if on checkout page */
    if (user.addr_street) {
      const fill = (id, val) => { const el = document.getElementById(id); if (el && !el.value) el.value = val || ''; };
      fill('coStreet',   user.addr_street);
      fill('coPost',     user.addr_postcode);
      fill('coCity',     user.addr_city);
      fill('coProvince', user.addr_province);
    }
  } else {
    localStorage.removeItem('hutko_user');
  }
}

window.Api     = { Auth, Orders, Contact, Admin };
window.syncSession = syncSession;

/* Run on every page load */
document.addEventListener('DOMContentLoaded', syncSession);
