/* ── HUTKO — search.js ───────────────────────────────
   Global navbar search:
   - Dropdown preview of matching products
   - Enter / click navigates to shop.html?q=…
   - shop.js reads the ?q= param on load
   ─────────────────────────────────────────────────── */

const SEARCH_PRODUCTS = [
  { id:1, name:'Syrnyky',            nameUa:'Сирники',    nameNl:'Syrnyky',            emoji:'🥞', cat:'breakfast' },
  { id:2, name:'Kyiv Chicken Balls', nameUa:'Котлети по-київськи', nameNl:'Kyiv kippenballen', emoji:'🍗', cat:'snacks' },
  { id:3, name:'Borscht',            nameUa:'Борщ',       nameNl:'Borsjt',             emoji:'🫕', cat:'soups' },
  { id:4, name:'Solyanka',           nameUa:'Солянка',    nameNl:'Soljanka',           emoji:'🍲', cat:'soups' },
  { id:5, name:'Shakshuka',          nameUa:'Шакшука',    nameNl:'Shakshuka',          emoji:'🍳', cat:'mains' },
  { id:6, name:'Zrazy',              nameUa:'Зрази',      nameNl:'Zrazy',              emoji:'🥟', cat:'snacks' },
];

function getProductName(p) {
  const lang = typeof getLang === 'function' ? getLang() : 'en';
  if (lang === 'ua') return p.nameUa;
  if (lang === 'nl') return p.nameNl;
  return p.name;
}

function initSearch() {
  /* Find all search inputs (navbar + mobile) */
  document.querySelectorAll('.nav-search input, #globalSearch').forEach(input => {
    if (input._searchInit) return;
    input._searchInit = true;

    /* Create dropdown */
    const wrap = input.closest('.nav-search') || input.parentElement;
    wrap.style.position = 'relative';

    const dropdown = document.createElement('div');
    dropdown.className = 'search-dropdown';
    dropdown.style.cssText = `
      display:none; position:absolute; top:calc(100% + 8px); left:0; right:0;
      background:#fff; border:1px solid rgba(26,35,86,0.12); border-radius:12px;
      box-shadow:0 8px 24px rgba(0,0,0,0.1); z-index:500; overflow:hidden; min-width:260px;
    `;
    wrap.appendChild(dropdown);

    input.addEventListener('input', () => {
      const q = input.value.trim().toLowerCase();
      if (!q) { dropdown.style.display = 'none'; return; }

      const matches = SEARCH_PRODUCTS.filter(p =>
        p.name.toLowerCase().includes(q) ||
        p.nameUa.toLowerCase().includes(q) ||
        p.nameNl.toLowerCase().includes(q) ||
        p.cat.toLowerCase().includes(q)
      );

      if (!matches.length) {
        dropdown.innerHTML = `<div style="padding:1rem 1.25rem;font-size:13px;color:rgba(26,35,86,0.5);">${typeof t === 'function' ? t('search_none') : 'No results for'} "${input.value}"</div>`;
      } else {
        dropdown.innerHTML = matches.map(p => `
          <a href="shop.html?q=${encodeURIComponent(input.value)}" class="search-result-item" style="
            display:flex;align-items:center;gap:12px;padding:10px 1.25rem;
            text-decoration:none;color:inherit;transition:background 0.15s;
          " onmouseover="this.style.background='#F2EDE4'" onmouseout="this.style.background='transparent'">
            <span style="font-size:24px;width:32px;text-align:center;">${p.emoji}</span>
            <div>
              <div style="font-size:13px;font-weight:500;color:#1a2356;">${getProductName(p)}</div>
              <div style="font-size:11px;color:rgba(26,35,86,0.45);text-transform:uppercase;letter-spacing:0.8px;">${p.cat}</div>
            </div>
          </a>`).join('') +
          `<a href="shop.html?q=${encodeURIComponent(input.value)}" style="
            display:block;padding:10px 1.25rem;font-size:12px;font-weight:500;
            color:#E8622A;border-top:1px solid rgba(26,35,86,0.07);text-decoration:none;
          ">See all results →</a>`;
      }
      dropdown.style.display = 'block';
    });

    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && input.value.trim()) {
        window.location.href = `shop.html?q=${encodeURIComponent(input.value.trim())}`;
      }
      if (e.key === 'Escape') { dropdown.style.display = 'none'; input.value = ''; }
    });

    document.addEventListener('click', e => {
      if (!wrap.contains(e.target)) dropdown.style.display = 'none';
    });
  });
}

/* Init after components render */
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(initSearch, 100);
});

/* Also expose for re-init after lang switch re-renders navbar */
window.initSearch = initSearch;
