/* HUTKO — api.js
   Token-based auth. Token stored in localStorage, sent as
   Authorization: Bearer <token> on every request.
   No cross-origin cookie issues.
*/

const API_BASE = 'https://hutko-kitchen.onrender.com';
const TOKEN_KEY = 'hutko_token';

function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }
function saveToken(token) { localStorage.setItem(TOKEN_KEY, token); }
function clearToken() { localStorage.removeItem(TOKEN_KEY); }

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
    localStorage.removeItem('hutko_user');
    return res;
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
  async stats()     { return apiCall('GET',  '/api/admin/stats'); },
  exportUrl()       { return `${API_BASE}/api/admin/export`; },
};

/* On every page load: verify token is still valid, sync user data */
async function syncSession() {
  const token = getToken();
  if (!token) { localStorage.removeItem('hutko_user'); return; }

  const res = await Auth.me();
  if (res.ok && res.data.user) {
    const user = res.data.user;
    localStorage.setItem('hutko_user', JSON.stringify({
      id: user.id, name: user.name, email: user.email,
    }));
    /* Pre-fill checkout address fields if present */
    if (user.addr_street) {
      const fill = (id, val) => { const el = document.getElementById(id); if (el && !el.value) el.value = val || ''; };
      fill('coStreet',   user.addr_street);
      fill('coPost',     user.addr_postcode);
      fill('coCity',     user.addr_city);
      fill('coProvince', user.addr_province);
    }
  } else {
    /* Token expired or invalid — clear it */
    clearToken();
    localStorage.removeItem('hutko_user');
  }
}

window.Api = { Auth, Orders, Contact, Admin };
window.syncSession = syncSession;
window.getToken    = getToken;

document.addEventListener('DOMContentLoaded', syncSession);
