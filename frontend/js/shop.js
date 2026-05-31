let ALL_PRODUCTS = [];
let ALL_BUNDLES = [];

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
        } else {
            throw new Error('API returned error');
        }
    } catch (e) {
        console.warn('[SHOP] API failed, using fallback data', e);
        ALL_PRODUCTS = FALLBACK_PRODUCTS;
        ALL_BUNDLES = FALLBACK_BUNDLES;
    }

    renderProducts(ALL_PRODUCTS);
    renderBundles(ALL_BUNDLES);
    updateCount(ALL_PRODUCTS);
}

// ── LANG ─────────────────────────────────────────────
function lang() { try { return localStorage.getItem('hutko_lang') || 'en'; } catch { return 'en'; } }
function pName(p) { return p[`name_${lang()}`] || p.name_en || p.id; }
function pDesc(p) { return p[`desc_${lang()}`] || p.desc_en || ''; }
function bName(b) { return b[`name_${lang()}`] || b.name_en || b.id; }

const DIETARY_ICONS = {
    'vegetarian': '🌿', 'vegan': '🌱',
    'gluten-free': '🌾', 'gluten-free option': '🌾', 'halal option': '✅'
};

// ── PRODUCT CARD ──────────────────────────────────────
function productCard(p) {
    const hasVar = p.variants && p.variants.length > 1;
    const price = p.variants?.[0]?.price ?? p.base_price;
    const dietary = (p.dietary || []).map(t => DIETARY_ICONS[t] ? `<span class="dietary-tag" title="${t}">${DIETARY_ICONS[t]}</span>` : '').join('');

    const variants = hasVar
        ? `<select class="variant-select" id="var-${p.id}" onchange="updatePrice('${p.id}',this)">
        ${p.variants.map(v => `<option value="${v.price}" data-l="${v.label}">${v.label} — €${v.price}</option>`).join('')}
       </select>`
        : '';

    return `<div class="prod-card reveal" data-cat="${p.category}">
    ${p.badge ? `<span class="prod-badge">${p.badge}</span>` : ''}
    <div class="prod-img-wrap">
      <img src="${p.photo}" alt="${pName(p)}" loading="lazy" onerror="this.onerror=null;this.src='assets/products/syrnyky.png'">
    </div>
    <div class="prod-body">
      <div class="prod-cat">${p.category}</div>
      <div class="prod-name">${pName(p)}</div>
      <div class="prod-desc">${pDesc(p)}</div>
      ${dietary ? `<div class="dietary-tags">${dietary}</div>` : ''}
      <div class="prod-price">${t('shop_from')} <strong id="price-${p.id}">€${price}</strong> <span id="unit-${p.id}">/ ${p.unit}</span></div>
      ${variants}
    </div>
    <div class="prod-footer">
      <button class="btn-view-product" onclick="location.href='product.html?id=${p.id}'">${t('btn_details')}</button>
      <button class="btn btn-dark" style="flex:2;justify-content:center;font-size:12px;"
        onclick="shopAddToCart('${p.id}')">${t('btn_add_cart')}</button>
    </div>
  </div>`;
}

// ── BUNDLE CARD ───────────────────────────────────────
function buildChoiceDropdown(b) {
    var raw = b['choice_' + lang()] || b.choice_en || '';
    if (!raw) return '';
    var parts = raw.split(/\s+OR\s+/i).join('|SPLIT|')
                   .split(/\s+АБО\s+/i).join('|SPLIT|')
                   .split(/\s+OF\s+/i).join('|SPLIT|')
                   .split('|SPLIT|')
                   .map(function(s){ return s.trim(); })
                   .filter(function(s){ return s.length > 0; });
    if (parts.length < 2) return '';
    var opts = parts.map(function(p){
        return '<option value="' + p + '">' + p + '</option>';
    }).join('');
    return '<div class="pack-choice-row">'
         + '<div class="pack-choice-label">Choose one ↓</div>'
         + '<select class="pack-choice-select" id="choice-' + b.id + '" onchange="this.classList.remove(\'error\')">'
         + '<option value="">— select an option —</option>'
         + opts
         + '</select>'
         + '</div>';
}

function bundleCard(b) {
    const featured = b.badge === 'Most popular';
    const items = b.items.map(item => {
        const prod = ALL_PRODUCTS.find(p => p.id === item.product_id);
        return `<span class="pack-item-chip">${prod ? pName(prod) : item.product_id} ×${item.qty}</span>`;
    }).join('');
    const oldPriceHtml = b.original_price !== b.discount_price
        ? `<span class="pack-price-old">€${b.original_price}</span>` : '';
    const portions = b.items.reduce((s, i) => s + i.qty, 0);

    return `<div class="pack-card ${featured ? 'featured' : ''} reveal">
    <div class="pack-img-wrap" onclick="openPackLightbox('${b.photo}','${bName(b).replace(/'/g,"\\'")}')">
      <img src="${b.photo}" alt="${bName(b)}" loading="lazy" onerror="this.onerror=null;this.src='assets/Bundles/s_pack_orange.png'">
    </div>
    <div class="pack-body">
      <div class="pack-size-badge">${b.size_label}${b.badge ? ' · ' + b.badge : ''}</div>
      <div class="pack-name">${bName(b)}</div>
      <div class="pack-items">${items}</div>
      ${buildChoiceDropdown(b)}
      <div class="pack-price-row">${oldPriceHtml}<span class="pack-price-new">€${b.discount_price}</span></div>
      ${portions ? `<div class="pack-per">~€${(b.discount_price / portions).toFixed(1)} per portion</div>` : ''}
    </div>
    <div class="pack-footer">
      <button class="btn ${featured ? 'btn-primary' : 'btn-blue'}" style="width:100%;justify-content:center;"
        onclick="bundleAddToCart('${b.id}')">${t('btn_order_pack')}</button>
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
    const p = ALL_PRODUCTS.find(x => x.id === id);
    if (!p) return;
    const sel = document.getElementById(`var-${id}`);
    const price = sel ? parseFloat(sel.value) : p.base_price;
    const label = sel ? sel.options[sel.selectedIndex].dataset.l : p.unit;
    addToCart(id, pName(p), '🍽️', price, label);
}
window.shopAddToCart = shopAddToCart;

function bundleAddToCart(id) {
    const b = ALL_BUNDLES.find(x => x.id === id);
    if (!b) return;
    const sel = document.getElementById(`choice-${id}`);
    if (sel) {
        const choiceText = sel.value.trim();
        if (!choiceText) {
            sel.classList.add('error');
            sel.focus();
            if (typeof showToast === 'function') showToast('Please choose an option first.');
            return;
        }
        addToCart(id, bName(b), '🎁', b.discount_price, `${b.size_label} · ${choiceText}`);
    } else {
        addToCart(id, bName(b), '🎁', b.discount_price, b.size_label);
    }
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

// ── FALLBACK DATA (shown if API unreachable) ──────────
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
        variants: [{ label: '200g', price: 6 }]
    },
    {
        id: 'zrazy', name_en: 'Zrazy', name_ua: 'Зрази', name_nl: 'Zrazy', category: 'snacks',
        desc_en: 'Pan-fried potato patties with mushroom & cheese.', base_price: 15, unit: '6 pcs', badge: '',
        photo: 'assets/products/zrazy.png', dietary: ['vegetarian'],
        variants: [{ label: '6 pcs', price: 15 }, { label: '12 pcs', price: 28 }]
    },
];
const FALLBACK_BUNDLES = [
    {
        id: 'pack-m1',
        name_en: 'Pack M (1) — Syrnyky + Borscht', name_ua: 'Набір M (1) — Сирники + Борщ', name_nl: 'Pack M (1) — Syrnyky + Borsjt',
        size_label: 'Pack M',
        items: [{ product_id: 'syrnyky', qty: 16 }, { product_id: 'borscht', qty: 2 }],
        original_price: 77, discount_price: 72,
        photo: 'assets/Bundles/packM_72euro.png', badge: '',
        choice_en: 'Zrazy 12 pcs OR Chicken balls 16 pcs OR Mlyntsi 12 pcs',
        choice_ua: 'Зрази 12 шт АБО Курячі кульки 16 шт АБО Млинці 12 шт',
        choice_nl: 'Zrazy 12 st OF Chicken balls 16 st OF Mlyntsi 12 st',
    },
    {
        id: 'pack-m2',
        name_en: 'Pack M (2) — Syrnyky + Shakshuka + Solyanka', name_ua: 'Набір M (2) — Сирники + Шакшука + Солянка', name_nl: 'Pack M (2) — Syrnyky + Shakshuka + Solyanka',
        size_label: 'Pack M',
        items: [{ product_id: 'syrnyky', qty: 8 }, { product_id: 'shakshuka', qty: 2 }, { product_id: 'solyanka', qty: 2 }],
        original_price: 85, discount_price: 80,
        photo: 'assets/Bundles/packM_80euro.jpeg', badge: 'Most popular',
        choice_en: 'Zrazy 12 pcs OR Chicken balls 16 pcs OR Mlyntsi 12 pcs',
        choice_ua: 'Зрази 12 шт АБО Курячі кульки 16 шт АБО Млинці 12 шт',
        choice_nl: 'Zrazy 12 st OF Chicken balls 16 st OF Mlyntsi 12 st',
    },
    {
        id: 'pack-l1',
        name_en: 'Pack L (1) — Syrnyky + Borscht + Solyanka', name_ua: 'Набір L (1) — Сирники + Борщ + Солянка', name_nl: 'Pack L (1) — Syrnyky + Borsjt + Solyanka',
        size_label: 'Pack L',
        items: [{ product_id: 'syrnyky', qty: 24 }, { product_id: 'borscht', qty: 2 }, { product_id: 'solyanka', qty: 1 }],
        original_price: 100, discount_price: 95,
        photo: 'assets/Bundles/packL_95euro.png', badge: '',
        choice_en: 'Zrazy 12 pcs OR Chicken balls 16 pcs OR Mlyntsi 12 pcs',
        choice_ua: 'Зрази 12 шт АБО Курячі кульки 16 шт АБО Млинці 12 шт',
        choice_nl: 'Zrazy 12 st OF Chicken balls 16 st OF Mlyntsi 12 st',
    },
    {
        id: 'pack-l2',
        name_en: 'Pack L (2) — Syrnyky + Borscht + Solyanka + Shakshuka', name_ua: 'Набір L (2) — Сирники + Борщ + Солянка + Шакшука', name_nl: 'Pack L (2) — Syrnyky + Borsjt + Solyanka + Shakshuka',
        size_label: 'Pack L',
        items: [{ product_id: 'syrnyky', qty: 16 }, { product_id: 'borscht', qty: 1 }, { product_id: 'solyanka', qty: 2 }, { product_id: 'shakshuka', qty: 2 }],
        original_price: 108, discount_price: 100,
        photo: 'assets/Bundles/packL_100euro.png', badge: '',
        choice_en: 'Zrazy 12 pcs OR Chicken balls 16 pcs OR Mlyntsi 12 pcs',
        choice_ua: 'Зрази 12 шт АБО Курячі кульки 16 шт АБО Млинці 12 шт',
        choice_nl: 'Zrazy 12 st OF Chicken balls 16 st OF Mlyntsi 12 st',
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
