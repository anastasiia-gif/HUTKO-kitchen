/* ── HUTKO — api.js ──────────────────────────────────────
   Single source of truth for all backend API calls.
   Token-based auth: saves JWT to localStorage, sends as
   Authorization: Bearer <token> on every request.
   ─────────────────────────────────────────────────────── */

const API_BASE = 'https://hutko-kitchen.onrender.com';

/* ── TOKEN HELPERS ───────────────────────────────────── */
function getToken() {
  try { return localStorage.getItem('hutko_token') || ''; } catch { return ''; }
}
function saveToken(token) {
  try { if (token) localStorage.setItem('hutko_token', token); } catch {}
}
function clearToken() {
  try {
    localStorage.removeItem('hutko_token');
    localStorage.removeItem('hutko_user');
  } catch {}
}
function getUser() {
  try { return JSON.parse(localStorage.getItem('hutko_user')) || null; } catch { return null; }
}
window.getToken = getToken;
window.getUser  = getUser;

/* ── CORE FETCH ──────────────────────────────────────── */
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
    if (res.ok && res.data.token) {
      saveToken(res.data.token);
      if (res.data.user) localStorage.setItem('hutko_user', JSON.stringify({
        id: res.data.user.id, name: res.data.user.name, email: res.data.user.email,
      }));
    }
    return res;
  },
  async login(email, password) {
    const res = await apiCall('POST', '/api/login', { email, password });
    if (res.ok && res.data.token) {
      saveToken(res.data.token);
      if (res.data.user) localStorage.setItem('hutko_user', JSON.stringify({
        id: res.data.user.id, name: res.data.user.name, email: res.data.user.email,
      }));
    }
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

/* ── SHOP ────────────────────────────────────────────── */
const Shop = {
  async all() {
    return apiCall('GET', '/api/shop/all');
  },
  async products() {
    return apiCall('GET', '/api/shop/products');
  },
  async bundles() {
    return apiCall('GET', '/api/shop/bundles');
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

/* ── SESSION SYNC ────────────────────────────────────── */
async function syncSession() {
  const token = getToken();
  if (!token) {
    localStorage.removeItem('hutko_user');
    return;
  }
  const res = await Auth.me();
  if (res.ok && res.data.user) {
    const user = res.data.user;
    localStorage.setItem('hutko_user', JSON.stringify({
      id:            user.id,
      name:          user.name,
      email:         user.email,
      addr_street:   user.addr_street   || '',
      addr_postcode: user.addr_postcode || '',
      addr_city:     user.addr_city     || '',
      addr_province: user.addr_province || '',
    }));
    if (user.addr_street) {
      const fill = (id, val) => { const el = document.getElementById(id); if (el && !el.value) el.value = val || ''; };
      fill('coStreet',   user.addr_street);
      fill('coPost',     user.addr_postcode);
      fill('coCity',     user.addr_city);
      fill('coProvince', user.addr_province);
    }
  } else {
    clearToken();
  }
}

window.Api         = { Auth, Orders, Contact, Shop, Admin };
window.syncSession = syncSession;

document.addEventListener('DOMContentLoaded', syncSession);
