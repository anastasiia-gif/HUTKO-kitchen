/* ── SHOP — shop.js ──────────────────────────────── */
const PRODUCTS = [
  { id: 1, name: 'Syrnyky',            cat: 'breakfast', emoji: '🥞', desc: 'Ukrainian cottage cheese pancakes, golden and fluffy',         basePrice: 13, unit: '8 pcs',  badge: '',        variants: [{l:'8 pcs',p:13},{l:'16 pcs',p:23},{l:'24 pcs',p:31}] },
  { id: 2, name: 'Kyiv Chicken Balls', cat: 'snacks',    emoji: '🍗', desc: 'Crispy breaded balls with herb butter inside',                 basePrice: 15, unit: '8 pcs',  badge: 'Popular', variants: [{l:'8 pcs',p:15},{l:'16 pcs',p:28},{l:'20 pcs',p:34}] },
  { id: 3, name: 'Borscht',            cat: 'soups',     emoji: '🫕', desc: 'Classic Ukrainian beetroot soup, rich and hearty',             basePrice: 13, unit: '900 ml', badge: '',        variants: [{l:'900 ml',p:13}] },
  { id: 4, name: 'Solyanka',           cat: 'soups',     emoji: '🍲', desc: 'Thick meat & vegetable soup with lemon twist',                 basePrice: 16, unit: '900 ml', badge: '',        variants: [{l:'900 ml',p:16}] },
  { id: 5, name: 'Shakshuka',          cat: 'mains',     emoji: '🍳', desc: 'Spiced tomato egg dish with Mediterranean flavour',            basePrice:  6, unit: '200g',   badge: 'New',     variants: [{l:'200g',p:6}] },
  { id: 6, name: 'Zrazy',             cat: 'snacks',    emoji: '🥟', desc: 'Pan-fried stuffed patties with mushrooms & cheese',            basePrice: 15, unit: '6 pcs',  badge: '',        variants: [{l:'6 pcs',p:15},{l:'12 pcs',p:28}] },
];

let currentCat = 'all';

function renderGrid(list) {
  const grid = document.getElementById('shopGrid');
  const rc   = document.getElementById('resultCount');
  const fi   = document.getElementById('filterInfo');
  if (rc) rc.textContent = `${list.length} product${list.length !== 1 ? 's' : ''}`;
  if (fi) fi.textContent = `Showing ${list.length} result${list.length !== 1 ? 's' : ''}`;

  if (!list.length) {
    grid.innerHTML = '<p class="no-results">No products found.</p>';
    return;
  }

  grid.innerHTML = list.map(p => {
    const variantSel = p.variants.length > 1
      ? `<select class="shop-card-variant" id="v${p.id}">${p.variants.map(v => `<option value="${v.p}" data-l="${v.l}">€${v.p} — ${v.l}</option>`).join('')}</select>`
      : '';
    return `
    <div class="shop-card reveal">
      ${p.badge ? `<span class="shop-card-badge">${p.badge}</span>` : ''}
      <div class="shop-card-img">${p.emoji}</div>
      <div class="shop-card-body">
        <div class="shop-card-cat">${p.cat}</div>
        <div class="shop-card-name">${p.name}</div>
        <div class="shop-card-desc">${p.desc}</div>
        ${variantSel}
      </div>
      <div class="shop-card-footer">
        <div class="shop-price">
          <div class="shop-price-from">${p.variants.length > 1 ? 'from' : ''}</div>
          <span class="shop-price-val">€${p.basePrice}</span>
          <span class="shop-price-unit"> / ${p.unit}</span>
        </div>
        <button class="shop-add-btn" id="ab${p.id}" onclick="shopAdd(${p.id})">Add to cart</button>
      </div>
    </div>`;
  }).join('');

  // trigger reveal on new cards
  document.querySelectorAll('.shop-card.reveal').forEach(el => {
    setTimeout(() => el.classList.add('visible'), 50);
  });
}

function shopAdd(id) {
  const p = PRODUCTS.find(x => x.id === id);
  const sel = document.getElementById(`v${id}`);
  const price = sel ? parseInt(sel.value) : p.basePrice;
  const label = sel ? sel.options[sel.selectedIndex].dataset.l : p.unit;
  addToCart(id, p.name, p.emoji, price, label);
  const btn = document.getElementById(`ab${id}`);
  if (btn) { btn.textContent = 'Added ✓'; btn.classList.add('added'); setTimeout(() => { btn.textContent = 'Add to cart'; btn.classList.remove('added'); }, 2000); }
}
window.shopAdd = shopAdd;

function filter() {
  const q    = document.getElementById('shopSearch')?.value.toLowerCase() || '';
  const sort = document.getElementById('sortSelect')?.value || 'default';
  let list = PRODUCTS.filter(p =>
    (currentCat === 'all' || p.cat === currentCat) &&
    (p.name.toLowerCase().includes(q) || p.desc.toLowerCase().includes(q))
  );
  if (sort === 'price-asc')  list.sort((a, b) => a.basePrice - b.basePrice);
  if (sort === 'price-desc') list.sort((a, b) => b.basePrice - a.basePrice);
  if (sort === 'name-asc')   list.sort((a, b) => a.name.localeCompare(b.name));
  renderGrid(list);
}

document.addEventListener('DOMContentLoaded', () => {
  renderGrid(PRODUCTS);

  document.querySelectorAll('.cat-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCat = btn.dataset.cat;
      filter();
    });
  });

  document.getElementById('sortSelect')?.addEventListener('change', filter);
  document.getElementById('shopSearch')?.addEventListener('input', filter);
});

/* ── URL search param (?q=...) ────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const q = params.get('q');
  if (q) {
    const searchEl = document.getElementById('shopSearch');
    if (searchEl) { searchEl.value = q; }
    /* slight delay to let filter() be available */
    setTimeout(filter, 50);
  }
});
