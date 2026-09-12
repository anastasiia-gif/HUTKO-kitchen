/* ── HUTKO — main.js ────────────────────────────────
   v2.0 (2026-09-12) — THE CART NOW CARRIES THE CUSTOMER'S CHOICE AS DATA.

   Every cart line stores what was chosen in its own field — `variant` for a
   product size/flavour, `choice` for a pack option — instead of smuggling it
   inside a display string that later code had to guess at and re-split. Nothing
   anywhere branches on HOW MANY options a thing has: a product with one flavour
   records its flavour exactly like a product with eight, so adding a new flavour
   can never quietly change behaviour.

   hutkoLineTitle() is the ONLY place a human-readable line is built. The cart
   panel, the checkout summary, the order, Stripe, the emails and the Trello card
   all call it, so they can no longer disagree with each other.
   ------------------------------------------------------------------------- */

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

/* ── CART ───────────────────────────────────────────
   Cart line shape (v2):
     { id, kind:'product'|'bundle', name, emoji, price, qty,
       variant: '',   // chosen product size/flavour, verbatim from the catalogue
       choice:  '',   // chosen pack option, verbatim from the catalogue
       size:    '' }  // pack size label, for the record
   ------------------------------------------------------------------------- */
const CART_KEY     = 'hutko_cart_v2';
const CART_KEY_OLD = 'hutko_cart';

function _esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/* The single source of truth for how a cart line reads to a human.
   It never drops a choice — duplication would be ugly, losing a flavour is a
   phone call to the customer. */
function hutkoLineTitle(item) {
  if (!item) return '';
  const name = String(item.name || item.id || '');
  const extra = item.kind === 'bundle' ? (item.choice || '') : (item.variant || '');
  return extra ? `${name} — ${extra}` : name;
}
window.hutkoLineTitle = hutkoLineTitle;

/* Identity of a cart line. Two different flavours of the same product are two
   different lines, always — no matter how many flavours exist. */
function hutkoCartKey(item) {
  return [item.kind || 'product', item.id || '', item.variant || '', item.choice || ''].join('|');
}
window.hutkoCartKey = hutkoCartKey;

function getCart() {
  try {
    const raw = localStorage.getItem(CART_KEY);
    if (raw) return JSON.parse(raw) || {};
  } catch (e) { return {}; }
  /* A basket saved by the old website stored the choice as an ambiguous string
     that can no longer be interpreted safely. Rather than guess (and risk
     cooking the wrong thing) we drop it — an abandoned basket is worth far less
     than a correct order. */
  try {
    if (localStorage.getItem(CART_KEY_OLD)) localStorage.removeItem(CART_KEY_OLD);
  } catch (e) { /* ignore */ }
  return {};
}

function saveCart(cart) {
  try { localStorage.setItem(CART_KEY, JSON.stringify(cart)); } catch (e) { /* private mode */ }
  updateCartUI();
}

/* addToCart({ id, kind, name, emoji, price, variant, choice, size })
   The old positional form addToCart(id, name, emoji, price, label) still works,
   so a page that hasn't been updated yet keeps functioning instead of throwing. */
function addToCart(a, name, emoji, price, label) {
  const item = (a && typeof a === 'object')
    ? a
    : { id: a, kind: 'product', name: name, emoji: emoji, price: price, variant: label || '' };

  const line = {
    id:      String(item.id || ''),
    kind:    item.kind === 'bundle' ? 'bundle' : 'product',
    name:    String(item.name || ''),
    emoji:   item.emoji || '🍽️',
    price:   Number(item.price) || 0,
    variant: String(item.variant || ''),
    choice:  String(item.choice || ''),
    size:    String(item.size || ''),
    qty:     1,
  };

  const cart = getCart();
  const key  = hutkoCartKey(line);
  if (cart[key]) cart[key].qty++; else cart[key] = line;
  saveCart(cart);

  if (window.gtag) window.gtag('event', 'add_to_cart', {
    currency: 'EUR', value: line.price,
    items: [{ item_id: line.id, item_name: line.name,
              item_variant: line.variant || line.choice || '',
              price: line.price, quantity: 1 }]
  });
  const tr = (typeof window.t === 'function') ? window.t : (k) => k;
  showToast(`✓ ${hutkoLineTitle(line)} ${tr('shop_added') || 'added'}`);
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
  const keys  = Object.keys(cart);
  const items = keys.map(k => cart[k]);
  const count = items.reduce((s,i) => s+i.qty, 0);
  const total = items.reduce((s,i) => s+i.qty*i.price, 0);

  document.querySelectorAll('.cart-count').forEach(el => {
    el.textContent = count;
    el.style.display = count ? 'flex' : 'none';
  });
  const totEl = document.getElementById('cartTotal');
  if (totEl) totEl.textContent = `€${total.toFixed(2)}`;

  const listEl = document.getElementById('cartItemsList');
  if (!listEl) return;
  if (!items.length) {
    listEl.innerHTML = '<div class="cart-empty">Your cart is empty.<br>Add some delicious food!</div>';
    return;
  }
  listEl.innerHTML = keys.map(key => {
    const item  = cart[key];
    const extra = item.kind === 'bundle' ? (item.choice || item.size || '') : (item.variant || '');
    return `
    <div class="cart-item">
      <div class="ci-icon">${_esc(item.emoji)}</div>
      <div class="ci-info">
        <div class="ci-name">${_esc(item.name)}</div>
        <div class="ci-variant">${_esc(extra)}</div>
        <div class="ci-row">
          <span class="ci-price">€${(item.qty * item.price).toFixed(2)}</span>
          <div class="ci-qty">
            <button class="ci-qbtn" data-key="${_esc(key)}" data-delta="-1">−</button>
            <span class="ci-qnum">${item.qty}</span>
            <button class="ci-qbtn" data-key="${_esc(key)}" data-delta="1">+</button>
          </div>
        </div>
      </div>
    </div>`;
  }).join('');
}

function toggleCart() {
  const panel = document.getElementById('cartPanel');
  const opening = panel && !panel.classList.contains('open');
  panel?.classList.toggle('open');
  document.getElementById('cartOverlay')?.classList.toggle('open');
  if (opening && window.gtag) {
    const items = Object.values(getCart());
    window.gtag('event', 'view_cart', {
      currency: 'EUR', value: items.reduce((s, i) => s + i.qty * i.price, 0),
      items: items.map(i => ({ item_id: i.id, item_name: hutkoLineTitle(i),
                               item_variant: i.variant || i.choice || '',
                               price: i.price, quantity: i.qty }))
    });
  }
}

window.toggleCart   = toggleCart;
window.addToCart    = addToCart;
window.changeQty    = changeQty;
window.getCart      = getCart;
window.updateCartUI = updateCartUI;

/* Quantity buttons are bound by delegation rather than inline onclick, because
   a flavour like  Chicken, Mushrooms & Cheese · 6 pcs  cannot be safely pasted
   into an onclick="" string. */
document.addEventListener('click', e => {
  const btn = e.target.closest && e.target.closest('.ci-qbtn[data-key]');
  if (btn) {
    changeQty(btn.getAttribute('data-key'), parseInt(btn.getAttribute('data-delta'), 10) || 0);
    return;
  }
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


/* ── SEO (v1) ─────────────────────────────────────────────────────────────
   Titles, meta descriptions, canonical, Open Graph + structured data (JSON-LD).
   Centralised here so every page gets it (all public pages load main.js).
   Language selection stays as-is — this optimises the existing pages.
   ------------------------------------------------------------------------- */
(function () {
  const API  = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? 'http://localhost:5000' : 'https://hutko-kitchen.onrender.com';
  const SITE = 'https://hutko-kitchen.com';
  const DEFAULT_IMG = SITE + '/assets/og-cover.jpg';

  // ▼▼ Paste your GA4 Measurement ID here to switch analytics on (e.g. 'G-XXXXXXXXXX'). Leave '' for off. ▼▼
  const GA4_ID = 'G-JY5LL1FPN0';
  // ▲▲ ─────────────────────────────────────────────────────────────────── ▲▲

  const page = (location.pathname.split('/').pop() || 'index.html') || 'index.html';

  // Per-page titles + descriptions (English baseline — the crawlable default language).
  const META = {
    'index.html':    { title: 'HUTKO Kitchen — Ukrainian Frozen Food Delivered in the Netherlands',
                       desc:  'Authentic Ukrainian frozen food — borscht, syrnyky, chicken Kyiv balls and more. Cooked in small batches, frozen fresh, delivered across the Netherlands.' },
    'shop.html':     { title: 'Order Ukrainian Food Online — Shop | HUTKO Kitchen',
                       desc:  'Buy authentic Ukrainian dishes online: borscht, syrnyky, chicken Kyiv balls, zrazy and more. Frozen fresh and delivered across the Netherlands.' },
    'about.html':    { title: 'About HUTKO — Ukrainian Home Cooking in the Netherlands',
                       desc:  'A small Ukrainian kitchen bringing authentic home cooking to the Netherlands — real recipes, small batches, frozen fresh. Our story.' },
    'delivery.html': { title: 'Delivery & Pickup — Ukrainian Food Across the Netherlands | HUTKO',
                       desc:  'HUTKO delivers Tuesday & Thursday across the Netherlands — insulated and frozen. See delivery zones, fees, free delivery over €100, and pickup.' },
    'contact.html':  { title: 'Contact HUTKO Kitchen — Ukrainian Food, Netherlands',
                       desc:  'Questions about your order or a collaboration? Contact HUTKO Kitchen — authentic Ukrainian frozen food delivered across the Netherlands.' }
  };
  const NOINDEX = ['account.html','login.html','register.html','checkout.html','confirm-delivery.html','admin.html'];

  function setMeta(name, content, attr) {
    attr = attr || 'name';
    if (!content) return;
    let el = document.head.querySelector('meta[' + attr + '="' + name + '"]');
    if (!el) { el = document.createElement('meta'); el.setAttribute(attr, name); document.head.appendChild(el); }
    el.setAttribute('content', content);
  }
  function setLink(rel, href) {
    let el = document.head.querySelector('link[rel="' + rel + '"]');
    if (!el) { el = document.createElement('link'); el.setAttribute('rel', rel); document.head.appendChild(el); }
    el.setAttribute('href', href);
  }
  function addJsonLd(obj, id) {
    if (id && document.getElementById(id)) return;
    const s = document.createElement('script');
    s.type = 'application/ld+json';
    if (id) s.id = id;
    s.textContent = JSON.stringify(obj);
    document.head.appendChild(s);
  }
  function absUrl(u) {
    if (!u) return null;
    return /^https?:\/\//.test(u) ? u : (SITE + '/' + String(u).replace(/^\//, ''));
  }

  // Utility pages: keep out of the index (they aren't landing pages).
  if (NOINDEX.indexOf(page) !== -1) setMeta('robots', 'noindex, follow');

  // Title / description / canonical / Open Graph for the main pages.
  let title = document.title;
  let descEl = document.head.querySelector('meta[name="description"]');
  let desc = descEl ? descEl.getAttribute('content') : '';
  const m = META[page];
  if (m) { title = m.title; desc = m.desc; document.title = title; setMeta('description', desc); }

  const canonical = SITE + '/' + (page === 'index.html' ? '' : page) + (page === 'product.html' ? location.search : '');
  setLink('canonical', canonical);

  setMeta('og:site_name', 'HUTKO Kitchen', 'property');
  setMeta('og:type', 'website', 'property');
  setMeta('og:title', title, 'property');
  setMeta('og:description', desc, 'property');
  setMeta('og:url', canonical, 'property');
  setMeta('og:image', DEFAULT_IMG, 'property');
  setMeta('twitter:card', 'summary_large_image');
  setMeta('twitter:title', title);
  setMeta('twitter:description', desc);
  setMeta('twitter:image', DEFAULT_IMG);

  // LocalBusiness / FoodEstablishment — on every page, details pulled from settings.
  async function localBusiness() {
    let s = {};
    try { const r = await fetch(API + '/api/shop/settings'); if (r.ok) s = (await r.json()).settings || {}; } catch (e) {}
    const sameAs = [];
    if (s.instagram) sameAs.push('https://instagram.com/' + String(s.instagram).replace(/^@/, '').replace(/^https?:\/\/(www\.)?instagram\.com\//, ''));
    else sameAs.push('https://instagram.com/hutko.kitchen');
    if (s.facebook) sameAs.push(/^https?:\/\//.test(s.facebook) ? s.facebook : 'https://' + s.facebook);

    const ld = {
      '@context': 'https://schema.org',
      '@type': 'FoodEstablishment',
      '@id': SITE + '/#business',
      name: 'HUTKO Kitchen',
      description: 'Authentic Ukrainian frozen food, cooked in small batches and delivered across the Netherlands.',
      url: SITE,
      logo: SITE + '/assets/logos/logo_nav.png',
      image: DEFAULT_IMG,
      servesCuisine: 'Ukrainian',
      priceRange: '€€',
      areaServed: { '@type': 'Country', name: 'Netherlands' },
      address: { '@type': 'PostalAddress', addressCountry: 'NL' },
      sameAs: sameAs
    };
    if (s.email_contact) ld.email = s.email_contact;
    if (s.phone) ld.telephone = s.phone;
    if (s.address_street) ld.address.streetAddress = s.address_street;
    addJsonLd(ld, 'ld-business');
  }

  // Product schema (+ product-specific title/description/image) on product pages.
  async function productSchema() {
    const id = new URLSearchParams(location.search).get('id');
    if (!id) return;
    try {
      const r = await fetch(API + '/api/shop/products'); if (!r.ok) return;
      const list = (await r.json()).products || [];
      const p = list.find(x => x.id === id); if (!p) return;
      const name  = p.name_en || p.name || p.id;
      const price = (p.variants && p.variants[0] && p.variants[0].price != null) ? p.variants[0].price : (p.base_price || 0);
      const img   = absUrl(p.photo);
      const pdesc = p.desc_en || (name + ' — authentic Ukrainian frozen food, delivered across the Netherlands.');

      if (window.gtag) window.gtag('event', 'view_item', {
        currency: 'EUR', value: Number(price) || 0,
        items: [{ item_id: p.id, item_name: name, price: Number(price) || 0 }]
      });

      document.title = name + ' — Ukrainian Frozen Food | HUTKO Kitchen';
      setMeta('description', pdesc);
      setMeta('og:title', document.title, 'property');
      setMeta('og:description', pdesc, 'property');
      setMeta('og:type', 'product', 'property');
      if (img) { setMeta('og:image', img, 'property'); setMeta('twitter:image', img); }

      const ld = {
        '@context': 'https://schema.org',
        '@type': 'Product',
        name: name,
        description: pdesc,
        brand: { '@type': 'Brand', name: 'HUTKO Kitchen' },
        offers: {
          '@type': 'Offer',
          price: Number(price).toFixed(2),
          priceCurrency: 'EUR',
          availability: 'https://schema.org/InStock',
          url: canonical
        }
      };
      if (img) ld.image = [img];
      if (p.category) ld.category = p.category;
      addJsonLd(ld, 'ld-product');
    } catch (e) {}
  }

  // GA4 — only injected if you set GA4_ID above.
  if (GA4_ID) {
    const g = document.createElement('script');
    g.async = true; g.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
    document.head.appendChild(g);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', GA4_ID);
  }

  localBusiness();
  if (page === 'product.html') productSchema();
})();
