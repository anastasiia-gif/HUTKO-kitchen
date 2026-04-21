let ALL_PRODUCTS = [];
let ALL_BUNDLES = [];

async function _loadShopData() {
    const grid = document.getElementById('productGrid');
    const bgrid = document.getElementById('bundleGrid');
    if (grid) grid.innerHTML = '<div class="shop-loading">Loading…</div>';
    if (bgrid) bgrid.innerHTML = '<div class="shop-loading">Loading…</div>';

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
      <img src="${p.photo}" alt="${pName(p)}" loading="lazy" onerror="this.src='assets/IMG_7982.JPEG'">
    </div>
    <div class="prod-body">
      <div class="prod-cat">${p.category}</div>
      <div class="prod-name">${pName(p)}</div>
      <div class="prod-desc">${pDesc(p)}</div>
      ${dietary ? `<div class="dietary-tags">${dietary}</div>` : ''}
      <div class="prod-price">from <strong id="price-${p.id}">€${price}</strong> <span id="unit-${p.id}">/ ${p.unit}</span></div>
      ${variants}
    </div>
    <div class="prod-footer">
      <button class="btn-view-product" onclick="location.href='product.html?id=${p.id}'">Details</button>
      <button class="btn btn-dark" style="flex:2;justify-content:center;font-size:12px;"
        onclick="shopAddToCart('${p.id}')">Add to cart</button>
    </div>
  </div>`;
}

// ── BUNDLE CARD ───────────────────────────────────────
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
    <div class="pack-img-wrap">
      <img src="${b.photo}" alt="${bName(b)}" loading="lazy" onerror="this.onerror=null;this.src='assets/IMG_7982.JPEG'">
    </div>
    <div class="pack-body">
      <div class="pack-size-badge">${b.size_label}${b.badge ? ' · ' + b.badge : ''}</div>
      <div class="pack-name">${bName(b)}</div>
      <div class="pack-items">${items}</div>
      <div class="pack-price-row">${oldPriceHtml}<span class="pack-price-new">€${b.discount_price}</span></div>
      ${portions ? `<div class="pack-per">~€${(b.discount_price / portions).toFixed(1)} per portion</div>` : ''}
    </div>
    <div class="pack-footer">
      <button class="btn ${featured ? 'btn-primary' : 'btn-blue'}" style="width:100%;justify-content:center;"
        onclick="bundleAddToCart('${b.id}')">Order this pack</button>
    </div>
  </div>`;
}

// ── RENDER ────────────────────────────────────────────
function renderProducts(list) {
    const grid = document.getElementById('productGrid');
    if (!grid) return;
    grid.innerHTML = list.length
        ? list.map(productCard).join('')
        : '<p class="no-results">No products found.</p>';
    initReveal();
}

function renderBundles(list) {
    const grid = document.getElementById('bundleGrid');
    if (!grid) return;
    grid.innerHTML = list.length ? list.map(bundleCard).join('') : '';
    initReveal();
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
    addToCart(id, bName(b), '🎁', b.discount_price, b.size_label);
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
        photo: 'assets/nobg/syrnyky.png', dietary: ['vegetarian'],
        variants: [{ label: '8 pcs', price: 13 }, { label: '16 pcs', price: 23 }, { label: '24 pcs', price: 31 }]
    },
    {
        id: 'chicken', name_en: 'Kyiv Chicken Balls', name_ua: 'Курячі кульки', name_nl: 'Kyiv Chicken Balls', category: 'snacks',
        desc_en: 'Crispy outside, herb butter inside.', base_price: 15, unit: '8 pcs', badge: 'Popular',
        photo: 'assets/nobg/chicken.png', dietary: [],
        variants: [{ label: '8 pcs', price: 15 }, { label: '16 pcs', price: 28 }, { label: '20 pcs', price: 34 }]
    },
    {
        id: 'borscht', name_en: 'Borscht', name_ua: 'Борщ', name_nl: 'Borsjt', category: 'soups',
        desc_en: 'Classic Ukrainian beetroot soup. Just heat — 8 min.', base_price: 13, unit: '900ml', badge: '',
        photo: 'assets/nobg/borscht.png', dietary: ['vegetarian', 'gluten-free'],
        variants: [{ label: '900ml', price: 13 }]
    },
    {
        id: 'solyanka', name_en: 'Solyanka', name_ua: 'Солянка', name_nl: 'Solyanka', category: 'soups',
        desc_en: 'Rich meat soup with olives and lemon.', base_price: 16, unit: '900ml', badge: '',
        photo: 'assets/nobg/solyanka.png', dietary: ['gluten-free'],
        variants: [{ label: '900ml', price: 16 }]
    },
    {
        id: 'shakshuka', name_en: 'Shakshuka', name_ua: 'Шакшука', name_nl: 'Shakshuka', category: 'mains',
        desc_en: 'Spiced tomato base. 1 portion = 2 hearts × 100g.', base_price: 6, unit: '200g', badge: 'New',
        photo: 'assets/nobg/shakshuka.png', dietary: ['vegetarian', 'vegan', 'gluten-free'],
        variants: [{ label: '200g', price: 6 }]
    },
    {
        id: 'zrazy', name_en: 'Zrazy', name_ua: 'Зрази', name_nl: 'Zrazy', category: 'snacks',
        desc_en: 'Pan-fried potato patties with mushroom & cheese.', base_price: 15, unit: '6 pcs', badge: '',
        photo: 'assets/nobg/zrazy.png', dietary: ['vegetarian'],
        variants: [{ label: '6 pcs', price: 15 }, { label: '12 pcs', price: 28 }]
    },
];
const FALLBACK_BUNDLES = [
    {
        id: 'pack-s1', name_en: 'Starter Pack — Borscht', name_ua: 'Стартовий набір — Борщ', name_nl: 'Starterpakket — Borsjt',
        size_label: 'Pack S', items: [{ product_id: 'syrnyky', qty: 8 }, { product_id: 'borscht', qty: 1 }, { product_id: 'zrazy', qty: 6 }, { product_id: 'chicken', qty: 8 }],
        original_price: 41, discount_price: 37, photo: 'hf_20260308_101724_332ed7b633c04af6be57da9339c4624d.jpeg', badge: ''
    },
    {
        id: 'pack-s2', name_en: 'Starter Pack — Solyanka', name_ua: 'Стартовий набір — Солянка', name_nl: 'Starterpakket — Solyanka',
        size_label: 'Pack S', items: [{ product_id: 'syrnyky', qty: 8 }, { product_id: 'solyanka', qty: 1 }, { product_id: 'zrazy', qty: 6 }, { product_id: 'chicken', qty: 8 }],
        original_price: 44, discount_price: 39, photo: 'hf_20260308_101754_0817f1096b73448d87eb3531e411155b.png', badge: ''
    },
    {
        id: 'pack-m1', name_en: 'Family Pack — Classic', name_ua: 'Сімейний набір — Класик', name_nl: 'Familiepakket — Klassiek',
        size_label: 'Pack M', items: [{ product_id: 'syrnyky', qty: 16 }, { product_id: 'borscht', qty: 2 }, { product_id: 'zrazy', qty: 12 }, { product_id: 'chicken', qty: 16 }],
        original_price: 77, discount_price: 69, photo: 'hf_20260308_102232_0b1e6e0deade4ce2934cc28ee2635165.png', badge: 'Most popular'
    },
    {
        id: 'pack-l1', name_en: 'Big Pack', name_ua: 'Великий набір', name_nl: 'Groot pakket',
        size_label: 'Pack L', items: [{ product_id: 'syrnyky', qty: 24 }, { product_id: 'borscht', qty: 2 }, { product_id: 'solyanka', qty: 1 }, { product_id: 'zrazy', qty: 16 }, { product_id: 'chicken', qty: 20 }],
        original_price: 107, discount_price: 97, photo: 'hf_20260308_102551_7e65581e179545a7a46d6504b44e7e7b.png', badge: ''
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
