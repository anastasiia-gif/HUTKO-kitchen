/* ── HUTKO — main.js ──────────────────────────────── */

/* NAV: active link */
(function () {
  const page = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a, .nav-drawer a').forEach(a => {
    if (a.getAttribute('href') === page) a.classList.add('active');
  });
})();

/* NAV: hamburger */
const hamburger = document.getElementById('navHamburger');
const drawer    = document.getElementById('navDrawer');
if (hamburger && drawer) {
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    drawer.classList.toggle('open');
  });
  document.addEventListener('click', e => {
    if (!hamburger.contains(e.target) && !drawer.contains(e.target)) {
      hamburger.classList.remove('open');
      drawer.classList.remove('open');
    }
  });
}

/* LANG SWITCHER */
document.querySelectorAll('.lang-switcher button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.lang-switcher button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  });
});

/* SCROLL REVEAL */
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      revealObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

/* TOAST */
function showToast(msg, duration = 3000) {
  let t = document.getElementById('siteToast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'siteToast';
    t.className = 'toast';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration);
}
window.showToast = showToast;

/* ── CART (shared state via localStorage) ─────────── */
const CART_KEY = 'hutko_cart';

function getCart() {
  try { return JSON.parse(localStorage.getItem(CART_KEY)) || {}; }
  catch { return {}; }
}
function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  updateCartUI();
}
function addToCart(id, name, emoji, price, label) {
  const cart = getCart();
  const key  = `${id}_${label}`;
  if (cart[key]) { cart[key].qty++; }
  else { cart[key] = { id, name, emoji, price, label, qty: 1 }; }
  saveCart(cart);
  showToast(`✓ ${name} added to cart`);
}
function changeQty(key, delta) {
  const cart = getCart();
  if (!cart[key]) return;
  cart[key].qty += delta;
  if (cart[key].qty <= 0) delete cart[key];
  saveCart(cart);
}
function updateCartUI() {
  const cart   = getCart();
  const items  = Object.values(cart);
  const count  = items.reduce((s, i) => s + i.qty, 0);
  const total  = items.reduce((s, i) => s + i.qty * i.price, 0);

  // Badge
  document.querySelectorAll('.cart-count').forEach(el => {
    el.textContent = count;
    el.style.display = count ? 'flex' : 'none';
  });

  // Total
  const totEl = document.getElementById('cartTotal');
  if (totEl) totEl.textContent = `€${total}`;

  // Items list
  const listEl = document.getElementById('cartItemsList');
  if (!listEl) return;
  if (!items.length) {
    listEl.innerHTML = '<div class="cart-empty">Your cart is empty.<br>Add some delicious food!</div>';
    return;
  }
  listEl.innerHTML = items.map(item => `
    <div class="cart-item">
      <div class="ci-icon">${item.emoji}</div>
      <div class="ci-info">
        <div class="ci-name">${item.name}</div>
        <div class="ci-variant">${item.label}</div>
        <div class="ci-row">
          <span class="ci-price">€${item.qty * item.price}</span>
          <div class="ci-qty">
            <button class="ci-qbtn" onclick="changeQty('${item.id}_${item.label}',-1);renderCartItems()">−</button>
            <span class="ci-qnum">${item.qty}</span>
            <button class="ci-qbtn" onclick="changeQty('${item.id}_${item.label}',1);renderCartItems()">+</button>
          </div>
        </div>
      </div>
    </div>`).join('');
}

function renderCartItems() { updateCartUI(); }

/* Cart panel open/close */
function toggleCart() {
  document.getElementById('cartPanel')?.classList.toggle('open');
  document.getElementById('cartOverlay')?.classList.toggle('open');
}
window.toggleCart    = toggleCart;
window.addToCart     = addToCart;
window.changeQty     = changeQty;
window.renderCartItems = renderCartItems;

document.getElementById('cartOverlay')?.addEventListener('click', toggleCart);
document.getElementById('cartClose')?.addEventListener('click', toggleCart);

/* Init cart UI on page load */
updateCartUI();
