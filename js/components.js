/* ── HUTKO — components.js ────────────────────────── */
/* Injects shared navbar, cart panel and footer into every page */

const LOGO_SVG = `<svg width="34" height="34" viewBox="0 0 38 38" fill="none">
  <circle cx="19" cy="19" r="19" fill="#E8622A" opacity="0.13"/>
  <path d="M19 32C19 32 6 23 6 14.5C6 10.4 9.4 7 13.5 7C15.9 7 18 8.2 19 10C20 8.2 22.1 7 24.5 7C28.6 7 32 10.4 32 14.5C32 23 19 32 19 32Z" fill="#E8622A"/>
</svg>`;

const SEARCH_ICON = `<svg width="13" height="13" viewBox="0 0 13 13" fill="none">
  <circle cx="5.5" cy="5.5" r="4" stroke="#1a2356" stroke-width="1.3" opacity="0.5"/>
  <path d="M9 9L12 12" stroke="#1a2356" stroke-width="1.3" stroke-linecap="round" opacity="0.5"/>
</svg>`;

const NAV_LINKS = [
  { href: 'index.html',    label: 'Home' },
  { href: 'shop.html',     label: 'Shop / Order' },
  { href: 'about.html',   label: 'About Us' },
  { href: 'delivery.html', label: 'Delivery & Info' },
  { href: 'contact.html',  label: 'Contact' },
];

function renderNavbar() {
  const links = NAV_LINKS.map(l =>
    `<li><a href="${l.href}">${l.label}</a></li>`
  ).join('');
  const drawerLinks = NAV_LINKS.map(l =>
    `<a href="${l.href}">${l.label}</a>`
  ).join('');

  const html = `
  <nav class="navbar">
    <div class="navbar-inner">
      <a href="index.html" class="nav-logo">${LOGO_SVG} HUTKO</a>
      <ul class="nav-links">${links}</ul>
      <div class="nav-right">
        <div class="nav-search">
          ${SEARCH_ICON}
          <input type="text" placeholder="Search products…" id="globalSearch" autocomplete="off">
        </div>
        <div class="lang-switcher">
          <button class="active">EN</button>
          <button>UA</button>
        </div>
        <button class="btn btn-dark" style="padding:9px 18px;gap:8px;font-size:13px;" onclick="toggleCart()">
          ${CART_SVG}
          Cart
          <span class="cart-count" style="background:#E8622A;color:#fff;border-radius:50%;width:18px;height:18px;font-size:10px;display:none;align-items:center;justify-content:center;font-weight:700;">0</span>
        </button>
        <button class="nav-hamburger" id="navHamburger" aria-label="Menu">
          <span></span><span></span><span></span>
        </button>
      </div>
    </div>
  </nav>
  <div class="nav-drawer" id="navDrawer">${drawerLinks}</div>`;

  document.getElementById('navbar-placeholder').innerHTML = html;
}

const CART_SVG = `<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
  <path d="M1 1h2.5l2 8h7l1.5-5.5H4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="7.5" cy="13.5" r="1.2" fill="currentColor"/>
  <circle cx="11.5" cy="13.5" r="1.2" fill="currentColor"/>
</svg>`;

function renderCartPanel() {
  const html = `
  <div class="cart-overlay" id="cartOverlay"></div>
  <div class="cart-panel" id="cartPanel">
    <div class="cart-head">
      <h2>Your order</h2>
      <button class="cart-close" id="cartClose">&#x2715;</button>
    </div>
    <div class="cart-items" id="cartItemsList">
      <div class="cart-empty">Your cart is empty.<br>Add some delicious food!</div>
    </div>
    <div class="cart-foot">
      <div class="cart-total-row">
        <span class="cart-total-label">Total</span>
        <span class="cart-total-val" id="cartTotal">€0</span>
      </div>
      <a href="shop.html" class="btn btn-primary" style="width:100%;justify-content:center;">Proceed to checkout →</a>
    </div>
  </div>`;
  document.getElementById('cart-placeholder').innerHTML = html;
}

function renderFooter() {
  const links = NAV_LINKS.map(l =>
    `<a href="${l.href}">${l.label}</a>`
  ).join('');
  const html = `
  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-grid">
        <div>
          <div class="footer-brand">${LOGO_SVG} HUTKO</div>
          <p class="footer-tagline">Authentic Ukrainian frozen food, delivered with love across the Netherlands.</p>
        </div>
        <div class="footer-col">
          <h4>Pages</h4>
          ${links}
        </div>
        <div class="footer-col">
          <h4>Products</h4>
          <a href="shop.html">Syrnyky</a>
          <a href="shop.html">Borscht</a>
          <a href="shop.html">Kyiv Chicken Balls</a>
          <a href="shop.html">Solyanka</a>
          <a href="shop.html">Zrazy</a>
        </div>
        <div class="footer-col">
          <h4>Contact</h4>
          <a href="mailto:info@hutko.nl">info@hutko.nl</a>
          <a href="tel:+31600000000">+31 6 00 00 00 00</a>
          <a href="contact.html">Amsterdam, NL</a>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2025 HUTKO Frozen Food. All rights reserved.</p>
        <div class="footer-social">
          <a href="https://facebook.com" target="_blank" rel="noopener" title="Facebook">fb</a>
          <a href="https://instagram.com" target="_blank" rel="noopener" title="Instagram">ig</a>
        </div>
      </div>
    </div>
  </footer>`;
  document.getElementById('footer-placeholder').innerHTML = html;
}

/* Run on DOM ready */
document.addEventListener('DOMContentLoaded', () => {
  renderNavbar();
  renderCartPanel();
  renderFooter();
});
