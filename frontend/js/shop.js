/* ── HUTKO — shop.js ────────────────────────────────
   v2.0 (2026-09-12)

   1. The variant picker is built the same way whether a product has one option
      or twenty. It used to be rendered only when `variants.length > 1`, so a
      single-option product silently fell back to the product's `unit` and
      `base_price` instead of the real variant — and the day you added a second
      flavour, the whole code path changed shape underneath you. Now the picker
      always exists (hidden when there is only one) and add-to-cart always reads
      the chosen option from it.

   2. Pack options come from the API as a ready-made list (`choice_options`), so
      the browser and the server agree on what a valid choice is. Local parsing
      is kept only as a fallback for an older backend, and now stops at the first
      separator that works instead of applying OR, АБО and OF in sequence — which
      used to tear apart any option containing the English word "of".

   3. If the API is unreachable the shop still renders, but ORDERING IS DISABLED.
      The old behaviour silently served hardcoded fallback data whose prices and
      flavour names no longer match the real menu — an order placed against it
      could not be fulfilled correctly.
   ------------------------------------------------------------------------- */

let ALL_PRODUCTS = [];
let ALL_BUNDLES = [];
let SHOP_FALLBACK = false;   // true when we are showing stale hardcoded data

async function _loadShopData() {
    const grid = document.getElementById('productGrid');
    const bgrid = document.getElementById('bundleGrid');
    if (grid) grid.innerHTML = `<div class="shop-loading">${typeof t === 'function' ? t('shop_loading') : 'Loading…'}</div>`;
    if (bgrid) bgrid.innerHTML = `<div class="shop-loading">${typeof t === 'function' ? t('shop_loading') : 'Loading…'}</div>`;

    try {
        const res = await Api.Shop.all();
        if (res.ok && res.data) {
            ALL_PRODUCTS = res.data.products || [];
            ALL_BUNDLES = res.data.bundles || [];
            SHOP_FALLBACK = false;
        } else {
            throw new Error('API returned error');
        }
    } catch (e) {
        console.warn('[SHOP] API failed, using fallback data', e);
        ALL_PRODUCTS = FALLBACK_PRODUCTS;
        ALL_BUNDLES = FALLBACK_BUNDLES;
        SHOP_FALLBACK = true;
    }

    renderFallbackBanner();
    renderProducts(ALL_PRODUCTS);
    renderBundles(ALL_BUNDLES);
    updateCount(ALL_PRODUCTS);
}

function renderFallbackBanner() {
    let el = document.getElementById('shopFallbackBanner');
    if (!SHOP_FALLBACK) { if (el) el.remove(); return; }
    if (el) return;
    el = document.createElement('div');
    el.id = 'shopFallbackBanner';
    el.style.cssText = 'margin:12px auto;max-width:900px;padding:12px 16px;border-radius:12px;'
        + 'background:#FFF3CD;color:#856404;border:1px solid #FFD761;font-size:14px;text-align:center;';
    el.innerHTML = '⏳ Our menu is still waking up — prices and options shown here may be out of date, '
        + 'so ordering is paused for a moment. Please refresh in a few seconds.';
    const grid = document.getElementById('productGrid');
    if (grid && grid.parentNode) grid.parentNode.insertBefore(el, grid);
}

function orderingBlocked() {
    if (!SHOP_FALLBACK) return false;
    if (typeof showToast === 'function') {
        showToast('The menu is still loading — please refresh in a few seconds before ordering.');
    }
    return true;
}

// ── LANG ─────────────────────────────────────────────
function lang() { try { return localStorage.getItem('hutko_lang') || 'en'; } catch { return 'en'; } }
function pName(p) { return p[`name_${lang()}`] || p.name_en || p.id; }
function pDesc(p) { return p[`desc_${lang()}`] || p.desc_en || ''; }
function bName(b) { return b[`name_${lang()}`] || b.name_en || b.id; }

function attr(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

const DIETARY_ICONS = {
    'vegetarian': '🌿', 'vegan': '🌱',
    'gluten-free': '🌾', 'gluten-free option': '🌾', 'halal option': '✅'
};

// ── PRODUCT CARD ──────────────────────────────────────
function productCard(p) {
    const list = (p.variants && p.variants.length) ? p.variants : [];
    const price = list.length ? list[0].price : p.base_price;
    const dietary = (p.dietary || []).map(t => DIETARY_ICONS[t] ? `<span class="dietary-tag" title="${attr(t)}">${DIETARY_ICONS[t]}</span>` : '').join('');

    // Always present when the product has options at all — hidden, not absent,
    // when there is only one, so the add-to-cart read path never changes shape.
    const variants = list.length
        ? `<select class="variant-select" id="var-${attr(p.id)}" onclick="event.stopPropagation()"
             onchange="updatePrice('${attr(p.id)}',this)"${list.length === 1 ? ' style="display:none"' : ''}>
        ${list.map(v => `<option value="${attr(v.price)}" data-l="${attr(v.label)}">${attr(v.label)} — €${attr(v.price)}</option>`).join('')}
       </select>`
        : '';

    return `<div class="prod-card reveal" data-cat="${attr(p.category)}" style="cursor:pointer;" onclick="location.href='product.html?id=${encodeURIComponent(p.id)}'">
    ${p.badge ? `<span class="prod-badge">${attr(p.badge)}</span>` : ''}
    <div class="prod-img-wrap">
      <img src="${attr(p.photo)}" alt="${attr(pName(p))}" loading="lazy" onerror="this.onerror=null;this.src='assets/products/syrnyky.png'">
    </div>
    <div class="prod-body">
      <div class="prod-cat">${attr(p.category)}</div>
      <div class="prod-name">${attr(pName(p))}</div>
      <div class="prod-desc">${attr(pDesc(p))}</div>
      ${dietary ? `<div class="dietary-tags">${dietary}</div>` : ''}
      <div class="prod-price">${t('shop_from')} <strong id="price-${attr(p.id)}">€${attr(price)}</strong> <span id="unit-${attr(p.id)}">/ ${attr(list.length ? list[0].label : p.unit)}</span></div>
      ${variants}
    </div>
    <div class="prod-footer" onclick="event.stopPropagation()">
      <button class="btn-view-product" onclick="location.href='product.html?id=${encodeURIComponent(p.id)}'">${t('btn_details')}</button>
      <button class="btn btn-dark" style="flex:2;justify-content:center;font-size:12px;"
        onclick="shopAddToCart('${attr(p.id)}')">${t('btn_add_cart')}</button>
    </div>
  </div>`;
}

// ── PACK OPTIONS ──────────────────────────────────────
/* Prefer the list the API already split for us, so the browser and the checkout
   endpoint can never disagree about what counts as a valid choice. */
const CHOICE_SEPARATORS = [/\s+OR\s+/i, /\s+АБО\s+/i, /\s+OF\s+/i];

function bundleOptions(b) {
    if (Array.isArray(b.choice_options) && b.choice_options.length) return b.choice_options;
    const raw = (b['choice_' + lang()] || b.choice_en || '').trim();
    if (!raw) return [];
    for (const sep of CHOICE_SEPARATORS) {          // first separator that works wins
        const parts = raw.split(sep).map(s => s.trim()).filter(Boolean);
        if (parts.length > 1) return parts;
    }
    return [raw];
}

function buildChoiceDropdown(b) {
    const opts = bundleOptions(b);
    if (!opts.length) return '';                     // genuinely no choice to make
    // NOTE: a single option still gets a picker. "Only one, so skip recording it"
    // is exactly the shortcut that lost a customer's mlyntsi flavour.
    return '<div class="pack-choice-row">'
         + '<div class="pack-choice-label">Choose one ↓</div>'
         + '<select class="pack-choice-select" id="choice-' + attr(b.id) + '" onchange="this.classList.remove(\'error\')">'
         + (opts.length > 1 ? '<option value="">— select an option —</option>' : '')
         + opts.map(o => '<option value="' + attr(o) + '">' + attr(o) + '</option>').join('')
         + '</select>'
         + '</div>';
}

function bundleCard(b) {
    const featured = b.badge === 'Most popular';
    const items = (b.items || []).map(item => {
        const prod = ALL_PRODUCTS.find(p => p.id === item.product_id);
        return `<span class="pack-item-chip">${attr(prod ? pName(prod) : item.product_id)} ×${attr(item.qty)}</span>`;
    }).join('');
    const oldPriceHtml = b.original_price !== b.discount_price
        ? `<span class="pack-price-old">€${attr(b.original_price)}</span>` : '';
    const portions = (b.items || []).reduce((s, i) => s + i.qty, 0);

    return `<div class="pack-card ${featured ? 'featured' : ''} reveal">
    <div class="pack-img-wrap" onclick="openPackLightbox('${attr(b.photo)}','${attr(bName(b)).replace(/'/g,"\\'")}')">
      <img src="${attr(b.photo)}" alt="${attr(bName(b))}" loading="lazy" onerror="this.onerror=null;this.src='assets/Bundles/s_pack_orange.png'">
    </div>
    <div class="pack-body">
      <div class="pack-size-badge">${attr(b.size_label)}${b.badge ? ' · ' + attr(b.badge) : ''}</div>
      <div class="pack-name">${attr(bName(b))}</div>
      <div class="pack-items">${items}</div>
      ${buildChoiceDropdown(b)}
      <div class="pack-price-row">${oldPriceHtml}<span class="pack-price-new">€${attr(b.discount_price)}</span></div>
      ${portions ? `<div class="pack-per">~€${(b.discount_price / portions).toFixed(1)} per portion</div>` : ''}
    </div>
    <div class="pack-footer">
      <button class="btn ${featured ? 'btn-primary' : 'btn-blue'}" style="width:100%;justify-content:center;"
        onclick="bundleAddToCart('${attr(b.id)}')">${t('btn_order_pack')}</button>
    </div>
  </div>`;
}

// ── RENDER ────────────────────────────────────────────
function renderProducts(list) {
    const grid = document.getElementById('productGrid');
    if (!grid) return;
    grid.innerHTML = list.length
        ? list.map(productCard).join('')
        : `<p class="no-results">${t('shop_no_products')}</p>`;
    initReveal();
    if (window.applyTranslations) applyTranslations();
}

function renderBundles(list) {
    const grid = document.getElementById('bundleGrid');
    if (!grid) return;
    grid.innerHTML = list.length ? list.map(bundleCard).join('') : '';
    initReveal();
    if (window.applyTranslations) applyTranslations();
}

function updateCount(list) {
    const el = document.getElementById('filterInfo');
    if (el) el.textContent = `${list.length} product${list.length !== 1 ? 's' : ''}`;
}

function initReveal() {
    const obs = new IntersectionObserver(
        entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
        { threshold: 0.08 }
    );
    document.querySelectorAll('.reveal:not(.visible)').forEach(el => obs.observe(el));
}

// ── FILTER ────────────────────────────────────────────
function filterProducts(cat) {
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
    const filtered = cat === 'all' ? ALL_PRODUCTS : ALL_PRODUCTS.filter(p => p.category === cat);
    renderProducts(filtered);
    updateCount(filtered);
}
window.filterProducts = filterProducts;

// ── VARIANT ───────────────────────────────────────────
function updatePrice(id, sel) {
    const el = document.getElementById(`price-${id}`);
    const ul = document.getElementById(`unit-${id}`);
    if (el) el.textContent = `€${sel.value}`;
    if (ul) ul.textContent = `/ ${sel.options[sel.selectedIndex].dataset.l}`;
}
window.updatePrice = updatePrice;

// ── CART ──────────────────────────────────────────────
function shopAddToCart(id) {
    if (orderingBlocked()) return;
    const p = ALL_PRODUCTS.find(x => x.id === id);
    if (!p) return;
    const sel = document.getElementById(`var-${id}`);
    const opt = sel ? sel.options[sel.selectedIndex] : null;

    // The chosen option is read the same way whether the product has 1 or 50.
    const variant = opt ? (opt.dataset.l || '') : '';
    const price   = opt ? parseFloat(opt.value) : Number(p.base_price) || 0;

    if ((p.variants || []).length && !variant) {
        if (typeof showToast === 'function') showToast('Please choose an option first.');
        return;
    }
    addToCart({ id: p.id, kind: 'product', name: pName(p), emoji: '🍽️', price, variant });
}
window.shopAddToCart = shopAddToCart;

function bundleAddToCart(id) {
    if (orderingBlocked()) return;
    const b = ALL_BUNDLES.find(x => x.id === id);
    if (!b) return;
    const opts = bundleOptions(b);
    const sel = document.getElementById(`choice-${id}`);
    const choice = sel ? sel.value.trim() : '';

    // If the pack offers any option at all, one must be chosen — no exception
    // for "there's only one".
    if (opts.length && !choice) {
        if (sel) { sel.classList.add('error'); sel.focus(); }
        if (typeof showToast === 'function') showToast('Please choose an option first.');
        return;
    }
    addToCart({ id: b.id, kind: 'bundle', name: bName(b), emoji: '🎁',
                price: Number(b.discount_price) || 0,
                choice, size: b.size_label || '' });
}
window.bundleAddToCart = bundleAddToCart;

// ── BOOT ─────────────────────────────────────────────
// Expose a promise so other pages (index.html) can await shop data
let _shopDataReady = null;
function loadShopData() {
    if (!_shopDataReady) _shopDataReady = _loadShopData();
    return _shopDataReady;
}
document.addEventListener('DOMContentLoaded', loadShopData);

// ── FALLBACK DATA ─────────────────────────────────────
// Display-only: shown if the API is unreachable, with ordering disabled (see
// renderFallbackBanner / orderingBlocked). Kept in step with the live catalogue
// as of 2026-09-12 so the page at least doesn't show wrong prices.
const FALLBACK_PRODUCTS = [
    {
        id: 'syrnyky', name_en: 'Syrnyky', name_ua: 'Сирники', name_nl: 'Syrnyky', category: 'breakfast',
        desc_en: 'Ukrainian cottage cheese pancakes. Warm, real, no fuss.', base_price: 13, unit: '8 pcs', badge: '',
        photo: 'assets/products/syrnyky.png', dietary: ['vegetarian'],
        variants: [{ label: '8 pcs', price: 13 }, { label: '16 pcs', price: 23 }, { label: '24 pcs', price: 31 }]
    },
    {
        id: 'chicken', name_en: 'Kyiv Chicken Balls', name_ua: 'Курячі кульки', name_nl: 'Kyiv Chicken Balls', category: 'snacks',
        desc_en: 'Crispy outside, herb butter inside.', base_price: 15, unit: '8 pcs', badge: 'Popular',
        photo: 'assets/products/chicken.png', dietary: [],
        variants: [{ label: '8 pcs', price: 15 }, { label: '16 pcs', price: 28 }, { label: '20 pcs', price: 34 }]
    },
    {
        id: 'borscht', name_en: 'Borscht', name_ua: 'Борщ', name_nl: 'Borsjt', category: 'soups',
        desc_en: 'Classic Ukrainian beetroot soup. Just heat — 8 min.', base_price: 13, unit: '900ml', badge: '',
        photo: 'assets/products/borscht.png', dietary: ['vegetarian', 'gluten-free'],
        variants: [{ label: '900ml', price: 13 }]
    },
    {
        id: 'solyanka', name_en: 'Solyanka', name_ua: 'Солянка', name_nl: 'Solyanka', category: 'soups',
        desc_en: 'Rich meat soup with olives and lemon.', base_price: 16, unit: '900ml', badge: '',
        photo: 'assets/products/solyanka.png', dietary: ['gluten-free'],
        variants: [{ label: '900ml', price: 16 }]
    },
    {
        id: 'shakshuka', name_en: 'Shakshuka', name_ua: 'Шакшука', name_nl: 'Shakshuka', category: 'mains',
        desc_en: 'Spiced tomato base. 1 portion = 2 hearts × 100g.', base_price: 6, unit: '200g', badge: 'New',
        photo: 'assets/products/shakshuka.png', dietary: ['vegetarian', 'vegan', 'gluten-free'],
        variants: [{ label: '200g (2 hearts)', price: 6 }]
    },
    {
        id: 'zrazy', name_en: 'Zrazy', name_ua: 'Зрази', name_nl: 'Zrazy', category: 'snacks',
        desc_en: 'Pan-fried potato patties with mushroom & cheese.', base_price: 15, unit: '6 pcs', badge: '',
        photo: 'assets/products/zrazy.jpeg', dietary: ['vegetarian'],
        variants: [{ label: 'Mushroom & Cheese · 6 pcs', price: 15 }, { label: 'Mushroom & Cheese · 12 pcs', price: 28 }]
    },
    {
        id: 'julien_balls', name_en: 'Julien Kyiv Meat Balls', name_ua: 'Котлети Жульєн по-Київськи', name_nl: 'Julienne Kyiv Gehaktballen', category: 'mains',
        desc_en: 'Golden crispy chicken balls filled with creamy mushroom & cheese julienne.', base_price: 15, unit: '4 pcs', badge: 'NEW',
        photo: 'assets/products/julien_balls.png', dietary: [],
        variants: [{ label: '4 pcs', price: 15 }, { label: '6 pcs', price: 21 }]
    },
    {
        id: 'mlyntsi', name_en: 'Mlyntsi', name_ua: 'Млинці', name_nl: 'Mlyntsi (Crêpes)', category: 'mains',
        desc_en: 'Thin Ukrainian crêpes — chicken & mushroom or cottage cheese filling.', base_price: 14, unit: '6 pcs', badge: 'NEW',
        photo: 'assets/products/mlyntsi.png', dietary: [],
        variants: [{ label: 'Sweet Cottage Cheese · 6 pcs', price: 14 },
                   { label: 'Chicken, Mushrooms & Cheese · 6 pcs', price: 15 }]
    },
];

const _FALLBACK_CHOICE = {
    en: 'Zrazy 12 pcs OR Chicken balls 16 pcs OR Mlyntsi Sweet (Cottage Cheese) 12 pcs OR Mlyntsi Chicken, Mushrooms & Cheese 12 pcs',
    ua: 'Зрази 12 шт АБО Курячі кульки 16 шт АБО Млинці солодкі (сир) 12 шт АБО Млинці з курком, грибами та сиром 12 шт',
    nl: 'Zrazy 12 st OF Chicken balls 16 st OF Mlyntsi Zoet (Kwark) 12 st OF Mlyntsi Kip, Champignons & Kaas 12 st',
};
const FALLBACK_BUNDLES = [
    {
        id: 'pack-m1',
        name_en: 'Pack M (1) — Syrnyky + Borscht', name_ua: 'Набір M (1) — Сирники + Борщ', name_nl: 'Pack M (1) — Syrnyky + Borsjt',
        size_label: 'Pack M',
        items: [{ product_id: 'syrnyky', qty: 16 }, { product_id: 'borscht', qty: 2 }],
        original_price: 77, discount_price: 72,
        photo: 'assets/Bundles/packM_72euro.png', badge: '',
        choice_en: _FALLBACK_CHOICE.en, choice_ua: _FALLBACK_CHOICE.ua, choice_nl: _FALLBACK_CHOICE.nl,
    },
    {
        id: 'pack-m2',
        name_en: 'Pack M (2) — Syrnyky + Shakshuka + Solyanka', name_ua: 'Набір M (2) — Сирники + Шакшука + Солянка', name_nl: 'Pack M (2) — Syrnyky + Shakshuka + Solyanka',
        size_label: 'Pack M',
        items: [{ product_id: 'syrnyky', qty: 8 }, { product_id: 'shakshuka', qty: 2 }, { product_id: 'solyanka', qty: 2 }],
        original_price: 85, discount_price: 80,
        photo: 'assets/Bundles/packM_80euro.jpeg', badge: 'Most popular',
        choice_en: _FALLBACK_CHOICE.en, choice_ua: _FALLBACK_CHOICE.ua, choice_nl: _FALLBACK_CHOICE.nl,
    },
    {
        id: 'pack-l1',
        name_en: 'Pack L (1) — Syrnyky + Borscht + Solyanka', name_ua: 'Набір L (1) — Сирники + Борщ + Солянка', name_nl: 'Pack L (1) — Syrnyky + Borsjt + Solyanka',
        size_label: 'Pack L',
        items: [{ product_id: 'syrnyky', qty: 24 }, { product_id: 'borscht', qty: 2 }, { product_id: 'solyanka', qty: 1 }],
        original_price: 100, discount_price: 95,
        photo: 'assets/Bundles/packL_95euro.png', badge: '',
        choice_en: _FALLBACK_CHOICE.en, choice_ua: _FALLBACK_CHOICE.ua, choice_nl: _FALLBACK_CHOICE.nl,
    },
    {
        id: 'pack-l2',
        name_en: 'Pack L (2) — Syrnyky + Borscht + Solyanka + Shakshuka', name_ua: 'Набір L (2) — Сирники + Борщ + Солянка + Шакшука', name_nl: 'Pack L (2) — Syrnyky + Borsjt + Solyanka + Shakshuka',
        size_label: 'Pack L',
        items: [{ product_id: 'syrnyky', qty: 16 }, { product_id: 'borscht', qty: 1 }, { product_id: 'solyanka', qty: 2 }, { product_id: 'shakshuka', qty: 2 }],
        original_price: 108, discount_price: 100,
        photo: 'assets/Bundles/packL_100euro.png', badge: '',
        choice_en: _FALLBACK_CHOICE.en, choice_ua: _FALLBACK_CHOICE.ua, choice_nl: _FALLBACK_CHOICE.nl,
    },
];

// ── TAB SWITCHING ─────────────────────────────────────
function switchTab(name, btn) {
  document.querySelectorAll('.shop-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.shop-panel').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(`panel-${name}`).classList.add('active');
}
window.switchTab = switchTab;

// ── PACK IMAGE LIGHTBOX ───────────────────────────────
(function () {
    function createLightbox() {
        if (document.getElementById('packLightbox')) return;
        const el = document.createElement('div');
        el.id = 'packLightbox';
        el.innerHTML = `
          <div id="packLightboxBg"></div>
          <button id="packLightboxClose" aria-label="Close">✕</button>
          <img id="packLightboxImg" src="" alt="">
        `;
        document.body.appendChild(el);

        const style = document.createElement('style');
        style.textContent = `
          #packLightbox {
            display: none; position: fixed; inset: 0; z-index: 9999;
            align-items: center; justify-content: center;
          }
          #packLightbox.open { display: flex; }
          #packLightboxBg {
            position: absolute; inset: 0;
            background: rgba(0,0,0,.85); backdrop-filter: blur(6px);
            cursor: zoom-out;
          }
          #packLightboxImg {
            position: relative; max-width: min(92vw, 560px);
            max-height: 92vh; border-radius: 20px;
            object-fit: contain; box-shadow: 0 24px 80px rgba(0,0,0,.5);
            animation: lbIn .22s ease;
          }
          #packLightboxClose {
            position: absolute; top: 18px; right: 22px;
            background: rgba(255,255,255,.15); border: none;
            color: #fff; font-size: 20px; width: 40px; height: 40px;
            border-radius: 50%; cursor: pointer; z-index: 1;
            display: flex; align-items: center; justify-content: center;
            transition: background .15s;
          }
          #packLightboxClose:hover { background: rgba(255,255,255,.3); }
          @keyframes lbIn {
            from { opacity: 0; transform: scale(.92); }
            to   { opacity: 1; transform: scale(1); }
          }
          .pack-img-wrap { cursor: zoom-in; }
        `;
        document.head.appendChild(style);

        document.getElementById('packLightboxBg').onclick = closeLightbox;
        document.getElementById('packLightboxClose').onclick = closeLightbox;
        document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });
    }

    function closeLightbox() {
        const lb = document.getElementById('packLightbox');
        if (lb) lb.classList.remove('open');
    }

    window.openPackLightbox = function(src, alt) {
        createLightbox();
        const lb  = document.getElementById('packLightbox');
        const img = document.getElementById('packLightboxImg');
        img.src = src;
        img.alt = alt || '';
        lb.classList.add('open');
    };

    window.closePackLightbox = closeLightbox;
})();
