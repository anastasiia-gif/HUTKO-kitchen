/* ── HUTKO — main.js ──────────────────────────────── */

/* SCROLL REVEAL */
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); revealObserver.unobserve(e.target); }});
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

/* TOAST */
function showToast(msg, duration = 3200) {
  let t = document.getElementById('siteToast');
  if (!t) { t = document.createElement('div'); t.id = 'siteToast'; t.className = 'toast'; document.body.appendChild(t); }
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), duration);
}
window.showToast = showToast;

/* ── CART ─────────────────────────────────────────── */
const CART_KEY = 'hutko_cart';
function getCart() { try { return JSON.parse(localStorage.getItem(CART_KEY)) || {}; } catch { return {}; } }
function saveCart(cart) { localStorage.setItem(CART_KEY, JSON.stringify(cart)); updateCartUI(); }

function addToCart(id, name, emoji, price, label) {
  const cart = getCart();
  const key  = `${id}_${label}`;
  if (cart[key]) { cart[key].qty++; } else { cart[key] = { id, name, emoji, price, label, qty:1 }; }
  saveCart(cart);
  const tr = (typeof window.t === 'function') ? window.t : (k) => k;
  showToast(`✓ ${name} ${tr('shop_added') || 'added'}`);
}

function changeQty(key, delta) {
  const cart = getCart();
  if (!cart[key]) return;
  cart[key].qty += delta;
  if (cart[key].qty <= 0) delete cart[key];
  saveCart(cart);
}

function updateCartUI() {
  const cart  = getCart();
  const items = Object.values(cart);
  const count = items.reduce((s,i) => s+i.qty, 0);
  const total = items.reduce((s,i) => s+i.qty*i.price, 0);

  document.querySelectorAll('.cart-count').forEach(el => {
    el.textContent = count;
    el.style.display = count ? 'flex' : 'none';
  });
  const totEl = document.getElementById('cartTotal');
  if (totEl) totEl.textContent = `€${total}`;

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
            <button class="ci-qbtn" onclick="changeQty('${item.id}_${item.label}',-1);updateCartUI()">−</button>
            <span class="ci-qnum">${item.qty}</span>
            <button class="ci-qbtn" onclick="changeQty('${item.id}_${item.label}',1);updateCartUI()">+</button>
          </div>
        </div>
      </div>
    </div>`).join('');
}

function toggleCart() {
  document.getElementById('cartPanel')?.classList.toggle('open');
  document.getElementById('cartOverlay')?.classList.toggle('open');
}

window.toggleCart   = toggleCart;
window.addToCart    = addToCart;
window.changeQty    = changeQty;
window.getCart      = getCart;
window.updateCartUI = updateCartUI;

document.addEventListener('click', e => {
  if (e.target.id === 'cartOverlay' || e.target.id === 'cartClose') toggleCart();
});

/* Init */
document.addEventListener('DOMContentLoaded', () => {
  updateCartUI();
  /* Re-observe any dynamically added .reveal elements */
  setTimeout(() => {
    document.querySelectorAll('.reveal:not(.visible)').forEach(el => revealObserver.observe(el));
  }, 300);
});
