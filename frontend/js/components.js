/* ── HUTKO — components.js ────────────────────────── */

const LOGO_SVG = `<svg width="34" height="34" viewBox="0 0 38 38" fill="none"><circle cx="19" cy="19" r="19" fill="#E8622A" opacity="0.13"/><path d="M19 32C19 32 6 23 6 14.5C6 10.4 9.4 7 13.5 7C15.9 7 18 8.2 19 10C20 8.2 22.1 7 24.5 7C28.6 7 32 10.4 32 14.5C32 23 19 32 19 32Z" fill="#E8622A"/></svg>`;
const CART_SVG = `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M1 1h2.5l2 8h7l1.5-5.5H4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/><circle cx="7.5" cy="13.5" r="1.2" fill="currentColor"/><circle cx="11.5" cy="13.5" r="1.2" fill="currentColor"/></svg>`;
const USER_SVG = `<svg width="15" height="15" viewBox="0 0 15 15" fill="none"><circle cx="7.5" cy="4.5" r="3" stroke="currentColor" stroke-width="1.4"/><path d="M1 14c0-3.314 2.91-6 6.5-6s6.5 2.686 6.5 6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>`;
const SEARCH_ICON = `<svg width="13" height="13" viewBox="0 0 13 13" fill="none"><circle cx="5.5" cy="5.5" r="4" stroke="#1a2356" stroke-width="1.3" opacity="0.5"/><path d="M9 9L12 12" stroke="#1a2356" stroke-width="1.3" stroke-linecap="round" opacity="0.5"/></svg>`;

const NAV_LINKS = [
  { href:'index.html',    key:'nav_home' },
  { href:'shop.html',     key:'nav_shop' },
  { href:'about.html',    key:'nav_about' },
  { href:'delivery.html', key:'nav_delivery' },
  { href:'contact.html',  key:'nav_contact' },
];

function getUser() {
  try { return JSON.parse(localStorage.getItem('hutko_user')) || null; } catch { return null; }
}
function logoutUser() { localStorage.removeItem('hutko_user'); window.location.href = 'index.html'; }
function toggleUserMenu() { document.getElementById('userDropdown')?.classList.toggle('open'); }
window.logoutUser = logoutUser;
window.toggleUserMenu = toggleUserMenu;

function renderNavbar() {
  const lang = (typeof getLang === 'function') ? getLang() : 'en';
  const tr   = (key) => (typeof t === 'function') ? t(key) : key;

  const links = NAV_LINKS.map(l => `<li><a href="${l.href}">${tr(l.key)}</a></li>`).join('');
  const drawerLinks = NAV_LINKS.map(l => `<a href="${l.href}">${tr(l.key)}</a>`).join('');
  const user = getUser();

  const authBtn = user
    ? `<div class="nav-user-menu">
         <button class="btn btn-ghost" style="padding:8px 14px;font-size:13px;gap:7px;" onclick="toggleUserMenu()">
           ${USER_SVG} ${user.name.split(' ')[0]}
           <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 3.5L5 6.5L8 3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
         </button>
         <div class="user-dropdown" id="userDropdown">
           <a href="account.html">${tr('nav_myaccount')}</a>
           <a href="account.html#orders">${tr('nav_myorders')}</a>
           <a href="#" onclick="logoutUser()">${tr('nav_signout')}</a>
         </div>
       </div>`
    : `<a href="login.html" class="btn btn-ghost" style="padding:8px 16px;font-size:13px;gap:7px;">${USER_SVG} <span data-i18n="nav_signin">${tr('nav_signin')}</span></a>`;

  const langBtns = ['en','ua','nl'].map(l =>
    `<button data-lang="${l}" class="${l === lang ? 'active' : ''}" onclick="setLang('${l}')">${l.toUpperCase()}</button>`
  ).join('');

  document.getElementById('navbar-placeholder').innerHTML = `
  <nav class="navbar">
    <div class="navbar-inner">
      <a href="index.html" class="nav-logo">${LOGO_SVG} HUTKO</a>
      <ul class="nav-links">${links}</ul>
      <div class="nav-right">
        <div class="nav-search">
          ${SEARCH_ICON}
          <input type="text" placeholder="${tr('nav_search')}" autocomplete="off" id="globalSearch">
        </div>
        <div class="lang-switcher">${langBtns}</div>
        ${authBtn}
        <button class="btn btn-dark" style="padding:9px 16px;gap:8px;font-size:13px;" onclick="toggleCart()">
          ${CART_SVG} <span data-i18n="nav_cart">${tr('nav_cart')}</span>
          <span class="cart-count" style="background:#E8622A;color:#fff;border-radius:50%;width:18px;height:18px;font-size:10px;display:none;align-items:center;justify-content:center;font-weight:700;">0</span>
        </button>
        <button class="nav-hamburger" id="navHamburger" aria-label="Menu"><span></span><span></span><span></span></button>
      </div>
    </div>
  </nav>
  <div class="nav-drawer" id="navDrawer">
    ${drawerLinks}
    ${user
      ? `<a href="account.html">${tr('nav_myaccount')}</a><a href="#" onclick="logoutUser()">${tr('nav_signout')}</a>`
      : `<a href="login.html">${tr('nav_signin')}</a><a href="register.html">${tr('nav_register')}</a>`}
  </div>`;

  /* Hamburger */
  const h = document.getElementById('navHamburger');
  const d = document.getElementById('navDrawer');
  if (h && d) {
    h.addEventListener('click', () => { h.classList.toggle('open'); d.classList.toggle('open'); });
    document.addEventListener('click', e => {
      if (!h.contains(e.target) && !d.contains(e.target)) { h.classList.remove('open'); d.classList.remove('open'); }
    });
  }

  /* User dropdown outside click */
  document.addEventListener('click', e => {
    const menu = document.getElementById('userDropdown');
    if (menu && !e.target.closest('.nav-user-menu')) menu.classList.remove('open');
  });

  /* Re-init search after navbar re-render */
  if (typeof initSearch === 'function') setTimeout(initSearch, 50);

  /* Mark active link */
  const page = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a, .nav-drawer a').forEach(a => {
    if (a.getAttribute('href') === page) a.classList.add('active');
  });
}

function renderCartPanel() {
  const tr = (key) => (typeof t === 'function') ? t(key) : key;
  document.getElementById('cart-placeholder').innerHTML = `
  <div class="cart-overlay" id="cartOverlay"></div>
  <div class="cart-panel" id="cartPanel">
    <div class="cart-head"><h2 data-i18n="cart_title">${tr('cart_title')}</h2><button class="cart-close" id="cartClose">&#x2715;</button></div>
    <div class="cart-items" id="cartItemsList"><div class="cart-empty" data-i18n="cart_empty">${tr('cart_empty')}</div></div>
    <div class="cart-foot">
      <div class="cart-total-row">
        <span class="cart-total-label" data-i18n="cart_total">${tr('cart_total')}</span>
        <span class="cart-total-val" id="cartTotal">€0</span>
      </div>
      <a href="checkout.html" class="btn btn-primary" style="width:100%;justify-content:center;" data-i18n="cart_checkout">${tr('cart_checkout')}</a>
    </div>
  </div>`;
}

function renderFooter() {
  const tr = (key) => (typeof t === 'function') ? t(key) : key;
  const links = NAV_LINKS.map(l => `<a href="${l.href}" data-i18n="${l.key}">${tr(l.key)}</a>`).join('');
  document.getElementById('footer-placeholder').innerHTML = `
  <footer class="footer"><div class="footer-inner">
    <div class="footer-grid">
      <div><div class="footer-brand">${LOGO_SVG} HUTKO</div><p class="footer-tagline" data-i18n="footer_tagline">${tr('footer_tagline')}</p></div>
      <div class="footer-col"><h4 data-i18n="footer_pages">${tr('footer_pages')}</h4>${links}</div>
      <div class="footer-col"><h4 data-i18n="footer_products">${tr('footer_products')}</h4>
        <a href="shop.html">Syrnyky</a><a href="shop.html">Borscht</a>
        <a href="shop.html">Kyiv Chicken Balls</a><a href="shop.html">Solyanka</a><a href="shop.html">Zrazy</a>
      </div>
      <div class="footer-col"><h4 data-i18n="footer_contact">${tr('footer_contact')}</h4>
        <a href="mailto:info@hutko.nl">info@hutko.nl</a>
        <a href="tel:+31600000000">+31 6 00 00 00 00</a>
        <a href="https://www.instagram.com/hutko.kitchen/" target="_blank" rel="noopener">@hutko.kitchen</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p data-i18n="footer_copy">${tr('footer_copy')}</p>
      <div class="footer-social">
        <a href="https://www.facebook.com" target="_blank" rel="noopener" title="Facebook">fb</a>
        <a href="https://www.instagram.com/hutko.kitchen/" target="_blank" rel="noopener" title="Instagram">ig</a>
      </div>
    </div>
  </div></footer>`;
}

document.addEventListener('DOMContentLoaded', () => {
  renderNavbar();
  renderCartPanel();
  renderFooter();
});
