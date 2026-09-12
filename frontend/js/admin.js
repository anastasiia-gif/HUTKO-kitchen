/* ── HUTKO — admin.js (v2.0) ──────────────────────────────────
   Self-contained admin client. Products are edited INLINE (expand
   in place); bundles use a modal. Uses its own admin token.

   v2.0 (2026-09-12) — two fixes that between them explain "the panel
   stopped saving variants":

   1. A 403 no longer destroys what you were typing. The old handler called
      showLogin(), which hides #appView — and the expanded product panel lives
      inside it. Everything typed was thrown away, and the error message was
      written into an element that had just been hidden, so all you saw was a
      toast. Now, if an editor is open, the panel stays exactly as it is and a
      re-login bar appears above it: type the password, press Save again, done.
      (The backend now also slides the session on every request, so a 12h
      session means 12h idle rather than 12h from login.)

   2. A variant row with a price but no label is no longer silently dropped.
      fillPanel() seeds a product that has no variants with {label: p.unit},
      so for any product with no `unit` set that seeded row was blank — you
      typed a price into a visible row, pressed Save, and it vanished.
   ───────────────────────────────────────────────────────────── */
const Admin = (() => {
  const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? 'http://localhost:5000' : 'https://hutko-kitchen.onrender.com';
  const TKEY = 'hutko_admin_token';

  let PRODUCTS = [], BUNDLES = [];
  let _editPid = null, _editBid = null;
  let _gallery = [];   // extra photos for the product currently open in the editor

  const $ = id => document.getElementById(id);
  const token = () => localStorage.getItem(TKEY) || '';
  const setToken = t => localStorage.setItem(TKEY, t);
  const clearToken = () => localStorage.removeItem(TKEY);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const mediaUrl = p => !p ? '' : (p.startsWith('/api/') ? API_BASE + p : p);

  function toast(msg) { const el = $('toast'); el.textContent = msg; el.classList.add('show'); clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove('show'), 2600); }
  function err(id, msg) { const el = $(id); if (!el) return; if (!msg) { el.classList.remove('show'); return; } el.textContent = msg; el.classList.add('show'); }

  /* Is there unsaved work on screen right now? */
  function editorOpen() {
    return !!(document.querySelector('tr.expand-row') ||
              document.querySelector('.modal-overlay.show'));
  }

  /* Re-login WITHOUT tearing down the open editor. */
  function showReauthBar() {
    if ($('reauthBar')) return;
    const bar = document.createElement('div');
    bar.id = 'reauthBar';
    bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;padding:12px 16px;'
      + 'background:#FFF3CD;color:#856404;border-bottom:1px solid #FFD761;display:flex;'
      + 'gap:10px;align-items:center;justify-content:center;flex-wrap:wrap;font-size:14px;';
    bar.innerHTML =
      '<span>Your admin session expired. <strong>Nothing you typed has been lost</strong> — '
      + 'log back in here, then press Save again.</span>'
      + '<input id="reauthPass" type="password" placeholder="Admin password" '
      + 'style="padding:8px 12px;border:1.5px solid #E0C97F;border-radius:8px;font-size:14px;">'
      + '<button id="reauthBtn" style="padding:8px 16px;border:none;border-radius:8px;'
      + 'background:#1B3FCE;color:#fff;font-weight:600;cursor:pointer;">Log back in</button>';
    document.body.appendChild(bar);
    const go = async () => {
      const pass = $('reauthPass').value;
      if (!pass) return;
      const r = await api('POST', '/api/admin/login', { password: pass });
      if (!r.ok) { $('reauthPass').value = ''; toast(r.data.error || 'Wrong password.'); return; }
      setToken(r.data.token);
      bar.remove();
      toast('Logged back in — press Save again.');
    };
    $('reauthBtn').onclick = go;
    $('reauthPass').addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
    $('reauthPass').focus();
  }

  async function api(method, path, body, isForm) {
    const headers = {}; const t = token();
    if (t) headers['Authorization'] = 'Bearer ' + t;
    const opts = { method, headers };
    if (body) { if (isForm) opts.body = body; else { headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); } }
    let res, data;
    try { res = await fetch(API_BASE + path, opts); }
    catch (e) { return { ok: false, status: 0, data: { error: 'Network error. Is the server awake?' } }; }
    try { data = await res.json(); } catch (e) { data = {}; }
    if (res.status === 403 && t && !path.endsWith('/api/admin/login')) {
      clearToken();
      if (editorOpen()) {
        // Keep the half-finished product on screen. This is the whole point.
        showReauthBar();
      } else {
        showLogin();
        toast('Session expired — please log in again.');
      }
    }
    return { ok: res.ok, status: res.status, data };
  }

  function showLogin() { $('loginView').style.display = 'flex'; $('appView').classList.remove('show'); }
  function showApp() { $('loginView').style.display = 'none'; $('appView').classList.add('show'); }

  async function login() {
    err('loginErr', '');
    const pass = $('loginPass').value;
    if (!pass) { err('loginErr', 'Enter your password.'); return; }
    const r = await api('POST', '/api/admin/login', { password: pass });
    if (!r.ok) { err('loginErr', r.data.error || 'Login failed.'); return; }
    setToken(r.data.token); $('loginPass').value = '';
    if (r.data.expires_hours) $('tokenNote').textContent = `session ${r.data.expires_hours}h idle`;
    showApp(); boot();
  }
  async function logout() { await api('POST', '/api/admin/logout'); clearToken(); showLogin(); }
  function boot() { loadDashboard(); loadProducts(); loadBundles(); loadSettings(); }

  function tab(name, el) {
    document.querySelectorAll('.admin-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.admin-side a').forEach(a => a.classList.remove('active'));
    $('tab-' + name).classList.add('active');
    if (el) el.classList.add('active');
  }

  // DASHBOARD
  async function loadDashboard() {
    const r = await api('GET', '/api/admin/stats'); if (!r.ok) return;
    const s = r.data;
    const cards = [
      ['Orders', s.total_orders, false], ['Revenue', '€' + Number(s.total_revenue || 0).toFixed(2), true],
      ['Awaiting action', s.pending_orders, true], ['Unpaid / abandoned', s.unpaid_orders ?? 0, false],
      ['Active products', s.active_products, false],
      ['Active bundles', s.active_bundles, false], ['Customers', s.total_users, false],
      ['Subscribers', s.newsletter_subs, false], ['Messages', s.unread_messages, false],
    ];
    $('statGrid').innerHTML = cards.map(([l, n, a]) =>
      `<div class="stat-card ${a ? 'accent' : ''}"><div class="n">${esc(n)}</div><div class="l">${esc(l)}</div></div>`).join('');
    wireExport('exportBtn', '/api/admin/export', 'hutko-data.xlsx');
    wireExport('exportCatBtn', '/api/admin/export-catalogue', 'hutko-catalogue.xlsx');
  }
  function wireExport(id, path, filename) {
    const b = $(id); if (!b) return;
    b.onclick = async () => {
      const r = await fetch(API_BASE + path, { headers: { Authorization: 'Bearer ' + token() } });
      if (!r.ok) { toast('Export failed.'); return; }
      const blob = await r.blob(), u = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = u; a.download = filename; a.click(); URL.revokeObjectURL(u);
    };
  }

  // PRODUCTS (inline expand)
  async function loadProducts() {
    const r = await api('GET', '/api/admin/products'); if (!r.ok) return;
    PRODUCTS = r.data.products || [];
    _editPid = null;
    const rows = PRODUCTS.map(p => `
      <tr class="prow" id="prow-${esc(p.id)}">
        <td><button class="icon-btn" title="Edit" onclick="Admin.toggleProduct('${esc(p.id)}')"><span class="chevron">▸</span></button></td>
        <td onclick="Admin.toggleProduct('${esc(p.id)}')" style="cursor:pointer;">
          <div style="display:flex;align-items:center;gap:12px;">
            <span class="cell-thumb">${p.photo ? `<img src="${mediaUrl(p.photo)}" style="width:100%;height:100%;border-radius:8px;object-fit:cover" onerror="this.replaceWith(document.createTextNode('🍽'))">` : '🍽'}</span>
            <span><span class="cell-name">${esc(p.name_en || '(no name)')}</span><br><span class="cell-id">${esc(p.id)}</span></span>
          </div>
        </td>
        <td>${esc(p.category || '—')}</td>
        <td>€${Number(p.base_price || 0).toFixed(2)}</td>
        <td>${(p.variants || []).length} option${(p.variants || []).length === 1 ? '' : 's'}</td>
        <td><label class="switch"><input type="checkbox" ${p.active ? 'checked' : ''} onchange="Admin.toggleActive('${esc(p.id)}',this.checked)"><span class="track"></span></label></td>
        <td><div class="row-actions">
          <button class="icon-btn" title="Edit" onclick="Admin.toggleProduct('${esc(p.id)}')">✏️</button>
          <button class="icon-btn danger" title="Delete" onclick="Admin.deleteProduct('${esc(p.id)}')">🗑</button>
        </div></td>
      </tr>`).join('');
    $('productRows').innerHTML = rows || `<tr><td colspan="7"><div class="empty-state"><div class="big">🥟</div>No products yet — add your first dish.</div></td></tr>`;
  }

  const LANG_FIELDS = [
    ['name', 'Name'], ['desc', 'Short description'], ['about', 'About this dish'],
    ['prepare', 'How to prepare'], ['ingredients', 'Ingredients'], ['hutko_tip', 'HUTKO tip'], ['storage', 'Storage'],
  ];
  function buildLangPane(lang) {
    return LANG_FIELDS.map(([f, label]) => {
      const id = `pe_${f}_${lang}`; const multi = f !== 'name';
      return `<div class="field"><label>${label}</label>${multi ? `<textarea class="form-control" id="${id}"></textarea>` : `<input class="form-control" id="${id}">`}</div>`;
    }).join('');
  }
  function langTab(prefix, lang, btn) {
    ['en', 'ua', 'nl'].forEach(l => $(`${prefix}-pane-${l}`).classList.toggle('active', l === lang));
    btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }
  function panelHTML() {
    return `
      <div id="peErr" class="inline-err"></div>
      <div class="dropzone" onclick="document.getElementById('pePhotoFile').click()">
        <img id="pePhotoPreview" src="" alt="" style="display:none;">
        <div class="dz-text" id="pePhotoText">📷 Click to upload a photo (PNG/JPG)</div>
        <input type="file" id="pePhotoFile" accept="image/*" style="display:none;" onchange="Admin.uploadPhoto(this,'pe')">
      </div>
      <input type="hidden" id="pePhoto">
      <div>
        <label style="font-size:12px;font-weight:600;opacity:.7;">More photos (gallery — these scroll on the product page, after the main photo)</label>
        <div id="peGallery" class="gallery-grid"></div>
        <input type="file" id="peGalleryFile" accept="image/*" multiple style="display:none;" onchange="Admin.uploadGallery(this)">
        <span class="add-link" onclick="document.getElementById('peGalleryFile').click()">＋ add photos</span>
      </div>
      <div class="field-grid">
        <div class="field"><label>Category</label><input class="form-control" id="peCategory" placeholder="Soups"></div>
        <div class="field"><label>Base price (€)</label><input class="form-control" id="pePrice" type="number" step="0.5"></div>
        <div class="field"><label>Unit</label><input class="form-control" id="peUnit" placeholder="10 pcs / 900 ml"></div>
        <div class="field"><label>Badge (optional)</label><input class="form-control" id="peBadge" placeholder="Bestseller"></div>
      </div>
      <div class="field"><label>Dietary tags (comma-separated)</label><input class="form-control" id="peDietary" placeholder="vegetarian, spicy"></div>
      <div>
        <div class="lang-tabs">
          <button type="button" class="active" onclick="Admin.langTab('pe','en',this)">English</button>
          <button type="button" onclick="Admin.langTab('pe','ua',this)">Українська</button>
          <button type="button" onclick="Admin.langTab('pe','nl',this)">Nederlands</button>
        </div>
        <div id="pe-pane-en" class="lang-pane active"></div>
        <div id="pe-pane-ua" class="lang-pane"></div>
        <div id="pe-pane-nl" class="lang-pane"></div>
      </div>
      <div>
        <label style="font-size:12px;font-weight:600;opacity:.7;">Options (size / flavour — the customer picks one)</label>
        <div class="hint" style="font-size:12px;opacity:.7;margin:4px 0 6px;">
          Every option needs a <strong>name</strong>. The customer's choice is recorded on the order
          by this exact text, so write it the way you want to read it in the kitchen —
          e.g. “Sweet Cottage Cheese · 6 pcs”.
        </div>
        <div id="peVariants" style="display:flex;flex-direction:column;gap:8px;margin-top:6px;"></div>
        <span class="add-link" onclick="Admin.addVariant()">＋ add option</span>
      </div>
      <div class="panel-actions">
        <button class="btn btn-outline" onclick="Admin.closePanel()">Cancel</button>
        <button class="btn btn-primary" onclick="Admin.saveProduct()">Save product</button>
      </div>`;
  }
  function closePanel() {
    document.querySelectorAll('tr.expand-row').forEach(r => r.remove());
    document.querySelectorAll('.prow.open').forEach(r => r.classList.remove('open'));
    _editPid = null;
  }
  function fillPanel(p) {
    ['en', 'ua', 'nl'].forEach(l => { $(`pe-pane-${l}`).innerHTML = buildLangPane(l); });
    $('peVariants').innerHTML = '';
    resetPhoto('pe');
    _gallery = (p && Array.isArray(p.gallery)) ? p.gallery.slice() : [];
    renderGallery();
    $('peCategory').value = p?.category || '';
    $('pePrice').value = p ? (p.base_price || '') : '';
    $('peUnit').value = p?.unit || '';
    $('peBadge').value = p?.badge || '';
    $('peDietary').value = (p?.dietary || []).join(', ');
    if (p) {
      LANG_FIELDS.forEach(([f]) => ['en', 'ua', 'nl'].forEach(l => { const el = $(`pe_${f}_${l}`); if (el) el.value = p[`${f}_${l}`] || ''; }));
      if (p.photo) setPhoto('pe', p.photo);
      if (p.variants && p.variants.length) {
        p.variants.forEach(v => addVariant(v.label, v.price));
      } else {
        // Seed one row from the product's own unit/price. If `unit` is empty the
        // label is blank — which used to mean the row was silently dropped on
        // save. It is now kept and flagged instead.
        addVariant(p.unit || '', p.base_price ?? '');
      }
    } else { addVariant(); }
  }
  function toggleProduct(id) {
    const existing = document.querySelector('tr.expand-row');
    const wasThis = existing && existing.dataset.for === id;
    closePanel();
    if (wasThis) return;
    const prow = $('prow-' + id);
    if (!prow) return;
    prow.classList.add('open');
    prow.insertAdjacentHTML('afterend', `<tr class="expand-row" data-for="${esc(id)}"><td colspan="7"><div class="expand-panel">${panelHTML()}</div></td></tr>`);
    _editPid = id;
    fillPanel(PRODUCTS.find(p => p.id === id));
  }
  function openNewProduct() {
    closePanel();
    const tb = $('productRows');
    tb.insertAdjacentHTML('afterbegin', `<tr class="expand-row" data-for="__new"><td colspan="7"><div class="expand-panel">${panelHTML()}</div></td></tr>`);
    _editPid = null;
    fillPanel(null);
    const el = $('pe_name_en'); if (el) { el.focus(); el.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
  }
  function addVariant(label = '', price = '') {
    const row = document.createElement('div'); row.className = 'builder-row';
    row.innerHTML = `<input class="form-control v-label" placeholder="Option name (e.g. Sweet Cottage Cheese · 6 pcs)" value="${esc(label)}">
      <input class="form-control v-price" type="number" step="0.5" placeholder="€" value="${esc(price)}" style="max-width:110px">
      <button class="icon-btn" onclick="this.parentElement.remove()">✕</button>`;
    $('peVariants').appendChild(row);
  }
  async function saveProduct() {
    err('peErr', '');
    const payload = {
      category: $('peCategory').value.trim(), base_price: parseFloat($('pePrice').value) || 0,
      unit: $('peUnit').value.trim(), badge: $('peBadge').value.trim(),
      dietary: $('peDietary').value.split(',').map(s => s.trim()).filter(Boolean),
      photo: $('pePhoto').value, gallery: _gallery.slice(), variants: [],
    };
    LANG_FIELDS.forEach(([f]) => ['en', 'ua', 'nl'].forEach(l => { payload[`${f}_${l}`] = ($(`pe_${f}_${l}`) || {}).value || ''; }));

    let unnamed = 0;
    document.querySelectorAll('#peVariants .builder-row').forEach(r => {
      const label = r.querySelector('.v-label').value.trim();
      const rawPrice = r.querySelector('.v-price').value.trim();
      const price = parseFloat(rawPrice) || 0;
      if (!label && !rawPrice) return;             // genuinely empty row — ignore
      if (!label) { unnamed++; r.querySelector('.v-label').classList.add('error'); return; }
      payload.variants.push({ label, price });
    });
    // A row with a price but no name used to disappear without a word. Now it
    // stops the save and points at the row, because an unnamed option is
    // exactly how a customer's choice becomes unreadable on the order.
    if (unnamed) {
      err('peErr', `${unnamed} option${unnamed === 1 ? ' has' : 's have'} a price but no name. `
        + 'Give each option a name (the customer sees it, and it is what gets recorded on the order), '
        + 'or remove the row with ✕.');
      return;
    }
    if (!payload.name_en) { err('peErr', 'Please add at least an English name.'); return; }

    let r;
    if (_editPid) r = await api('PUT', `/api/admin/products/${_editPid}`, payload);
    else { payload.active = true; r = await api('POST', '/api/admin/products', payload); }
    if (!r.ok) {
      // If the session expired, the re-login bar is already up and the panel is
      // intact — say so instead of a generic failure.
      if (r.status === 403) { err('peErr', 'Session expired — log back in at the top of the page, then press Save again. Your text is still here.'); return; }
      err('peErr', r.data.error || 'Could not save.');
      return;
    }
    toast('Product saved ✓'); loadProducts(); loadDashboard();
  }
  async function toggleActive(id, active) {
    const r = await api('PUT', `/api/admin/products/${id}`, { active });
    if (!r.ok) { toast('Could not update.'); loadProducts(); return; }
    toast(active ? 'Product visible' : 'Product hidden'); loadDashboard();
  }
  async function deleteProduct(id) {
    if (!confirm(`Delete product "${id}"? This cannot be undone. (Tip: hiding keeps it for later.)`)) return;
    const r = await api('DELETE', `/api/admin/products/${id}`);
    if (!r.ok) { toast('Could not delete.'); return; }
    toast('Product deleted'); loadProducts(); loadDashboard();
  }

  // BUNDLES (modal)
  async function loadBundles() {
    const r = await api('GET', '/api/admin/bundles'); if (!r.ok) return;
    BUNDLES = r.data.bundles || [];
    const rows = BUNDLES.map(b => `
      <tr>
        <td><span class="cell-thumb">${b.photo ? `<img src="${mediaUrl(b.photo)}" style="width:100%;height:100%;border-radius:8px;object-fit:cover" onerror="this.replaceWith(document.createTextNode('📦'))">` : '📦'}</span></td>
        <td><div class="cell-name">${esc(b.name_en || '(no name)')}</div><div class="cell-id">${esc(b.id)}</div></td>
        <td>${(b.items || []).length} items</td>
        <td>€${Number(b.discount_price || 0).toFixed(2)}</td>
        <td><label class="switch"><input type="checkbox" ${b.active ? 'checked' : ''} onchange="Admin.toggleBundle('${esc(b.id)}',this.checked)"><span class="track"></span></label></td>
        <td><div class="row-actions">
          <button class="icon-btn" onclick="Admin.openBundle('${esc(b.id)}')">✏️</button>
          <button class="icon-btn danger" onclick="Admin.deleteBundle('${esc(b.id)}')">🗑</button>
        </div></td>
      </tr>`).join('');
    $('bundleRows').innerHTML = rows || `<tr><td colspan="6"><div class="empty-state"><div class="big">📦</div>No bundles yet.</div></td></tr>`;
  }
  function openBundle(id) {
    _editBid = id || null;
    err('bmErr', '');
    $('bmTitle').textContent = id ? 'Edit bundle' : 'Add bundle';
    resetPhoto('bm'); $('bmItems').innerHTML = '';
    const b = id ? BUNDLES.find(x => x.id === id) : null;
    $('bmNameEn').value = b?.name_en || ''; $('bmNameUa').value = b?.name_ua || ''; $('bmNameNl').value = b?.name_nl || '';
    $('bmSize').value = b?.size_label || ''; $('bmOrig').value = b ? (b.original_price || '') : '';
    $('bmDisc').value = b ? (b.discount_price || '') : ''; $('bmBadge').value = b?.badge || '';
    if ($('bmChoiceEn')) { $('bmChoiceEn').value = b?.choice_en || ''; $('bmChoiceUa').value = b?.choice_ua || ''; $('bmChoiceNl').value = b?.choice_nl || ''; }
    if (b?.photo) setPhoto('bm', b.photo);
    if (b && b.items && b.items.length) b.items.forEach(it => addBundleItem(it.product_id, it.qty)); else addBundleItem();
    openModal('bundleModal');
  }
  function addBundleItem(pid = '', qty = 1) {
    const opts = PRODUCTS.map(p => `<option value="${esc(p.id)}" ${p.id === pid ? 'selected' : ''}>${esc(p.name_en || p.id)}</option>`).join('');
    const row = document.createElement('div'); row.className = 'builder-row';
    row.innerHTML = `<select class="form-control bi-pid">${opts || '<option value="">(add products first)</option>'}</select>
      <input class="form-control bi-qty" type="number" min="1" value="${esc(qty)}" style="max-width:90px">
      <button class="icon-btn" onclick="this.parentElement.remove()">✕</button>`;
    $('bmItems').appendChild(row);
  }
  async function saveBundle() {
    err('bmErr', '');
    const items = [];
    document.querySelectorAll('#bmItems .builder-row').forEach(r => {
      const pid = r.querySelector('.bi-pid').value; const qty = parseInt(r.querySelector('.bi-qty').value) || 1;
      if (pid) items.push({ product_id: pid, qty });
    });
    const payload = {
      name_en: $('bmNameEn').value.trim(), name_ua: $('bmNameUa').value.trim(), name_nl: $('bmNameNl').value.trim(),
      size_label: $('bmSize').value.trim(), badge: $('bmBadge').value.trim(),
      original_price: parseFloat($('bmOrig').value) || 0, discount_price: parseFloat($('bmDisc').value) || 0,
      photo: $('bmPhoto').value, items,
    };
    if ($('bmChoiceEn')) {
      payload.choice_en = $('bmChoiceEn').value.trim();
      payload.choice_ua = $('bmChoiceUa').value.trim();
      payload.choice_nl = $('bmChoiceNl').value.trim();
    }
    if (!payload.name_en) { err('bmErr', 'Please add an English name.'); return; }
    let r;
    if (_editBid) r = await api('PUT', `/api/admin/bundles/${_editBid}`, payload);
    else { payload.active = true; r = await api('POST', '/api/admin/bundles', payload); }
    if (!r.ok) {
      if (r.status === 403) { err('bmErr', 'Session expired — log back in at the top of the page, then press Save again. Your text is still here.'); return; }
      err('bmErr', r.data.error || 'Could not save.'); return;
    }
    closeModal('bundleModal'); toast('Bundle saved ✓'); loadBundles(); loadDashboard();
  }
  async function toggleBundle(id, active) {
    const r = await api('PUT', `/api/admin/bundles/${id}`, { active });
    if (!r.ok) { toast('Could not update.'); loadBundles(); return; }
    toast(active ? 'Bundle visible' : 'Bundle hidden'); loadDashboard();
  }
  async function deleteBundle(id) {
    if (!confirm(`Delete bundle "${id}"?`)) return;
    const r = await api('DELETE', `/api/admin/bundles/${id}`);
    if (!r.ok) { toast('Could not delete.'); return; }
    toast('Bundle deleted'); loadBundles(); loadDashboard();
  }

  // PHOTO
  async function uploadPhoto(input, prefix) {
    const f = input.files[0]; if (!f) return;
    const fd = new FormData(); fd.append('file', f);
    toast('Uploading photo…');
    const r = await api('POST', '/api/admin/media', fd, true); input.value = '';
    if (!r.ok) { toast(r.data.error || 'Upload failed.'); return; }
    setPhoto(prefix, r.data.url); toast('Photo uploaded ✓');
  }
  function setPhoto(prefix, url) { $(prefix + 'Photo').value = url; const img = $(prefix + 'PhotoPreview'); img.src = mediaUrl(url); img.style.display = 'block'; $(prefix + 'PhotoText').textContent = 'Change photo'; }
  function resetPhoto(prefix) { $(prefix + 'Photo').value = ''; const img = $(prefix + 'PhotoPreview'); img.src = ''; img.style.display = 'none'; $(prefix + 'PhotoText').textContent = '📷 Click to upload a photo (PNG/JPG)'; }

  // GALLERY (extra product photos)
  function renderGallery() {
    const el = $('peGallery'); if (!el) return;
    el.innerHTML = _gallery.map((url, i) => `
      <div class="gthumb">
        <img src="${mediaUrl(url)}" alt="" onerror="this.style.opacity=.3">
        <button class="gthumb-x" title="Remove" onclick="Admin.removeGallery(${i})">✕</button>
      </div>`).join('') || '<span class="hint">No extra photos yet — add up to a few.</span>';
  }
  async function uploadGallery(input) {
    const files = Array.from(input.files || []); input.value = '';
    if (!files.length) return;
    toast('Uploading ' + files.length + ' photo' + (files.length > 1 ? 's' : '') + '…');
    for (const f of files) {
      const fd = new FormData(); fd.append('file', f);
      const r = await api('POST', '/api/admin/media', fd, true);
      if (r.ok && r.data.url) _gallery.push(r.data.url);
      else toast(r.data.error || 'A photo failed to upload.');
    }
    renderGallery(); toast('Photos added ✓');
  }
  function removeGallery(i) { _gallery.splice(i, 1); renderGallery(); }

  // SETTINGS
  async function loadSettings() {
    const r = await api('GET', '/api/admin/settings'); if (!r.ok) return;
    const { rules, site } = r.data;
    $('s_local').value = rules.fee_local || '';
    $('s_reg').value = rules.fee_regional || '';
    $('s_free').value = rules.free_delivery_over || '';
    $('s_cap').value = rules.max_per_day || '';
    $('s_days').value = rules.delivery_days || '';
    renderSite(site || {});
  }
  function renderSite(site) {
    $('siteFields').innerHTML = Object.keys(site).sort().map(k =>
      `<div class="field"><label>${esc(k)}</label><input class="form-control" data-key="${esc(k)}" value="${esc(site[k])}"></div>`).join('')
      || `<div class="hint">No contact settings yet — add one below.</div>`;
  }
  function addSiteField() {
    const k = $('newKey').value.trim(); const v = $('newVal').value;
    if (!k) { toast('Enter a field name.'); return; }
    const wrap = document.createElement('div'); wrap.className = 'field';
    wrap.innerHTML = `<label>${esc(k)}</label><input class="form-control" data-key="${esc(k)}" value="${esc(v)}">`;
    if ($('siteFields').querySelector('.hint')) $('siteFields').innerHTML = '';
    $('siteFields').appendChild(wrap); $('newKey').value = ''; $('newVal').value = '';
  }
  async function saveRules() {
    err('rulesErr', '');
    const updates = {
      fee_local: $('s_local').value, fee_regional: $('s_reg').value,
      free_delivery_over: $('s_free').value,
      max_per_day: $('s_cap').value, delivery_days: $('s_days').value.trim(),
    };
    const r = await api('PUT', '/api/admin/settings', updates);
    if (!r.ok) { err('rulesErr', r.data.error || 'Could not save.'); return; }
    toast('Delivery fees saved ✓');
  }
  async function saveSite() {
    const updates = {};
    document.querySelectorAll('#siteFields [data-key]').forEach(i => updates[i.dataset.key] = i.value);
    if (!Object.keys(updates).length) { toast('Nothing to save.'); return; }
    const r = await api('PUT', '/api/admin/settings', updates);
    if (!r.ok) { toast(r.data.error || 'Could not save.'); return; }
    toast('Contact details saved ✓');
  }
  async function changePassword() {
    err('pwErr', '');
    const cur = $('pwCur').value, nw = $('pwNew').value;
    if (nw.length < 8) { err('pwErr', 'New password must be at least 8 characters.'); return; }
    const r = await api('PUT', '/api/admin/password', { current_password: cur, new_password: nw });
    if (!r.ok) { err('pwErr', r.data.error || 'Could not update.'); return; }
    $('pwCur').value = ''; $('pwNew').value = ''; toast('Password updated ✓');
  }

  function openModal(id) { $(id).classList.add('show'); }
  function closeModal(id) { $(id).classList.remove('show'); }

  document.addEventListener('DOMContentLoaded', async () => {
    $('loginPass').addEventListener('keydown', e => { if (e.key === 'Enter') login(); });
    if (token()) { const r = await api('GET', '/api/admin/stats'); if (r.ok) { showApp(); boot(); return; } }
    showLogin();
  });

  return {
    login, logout, tab, toggleProduct, openNewProduct, closePanel, saveProduct, toggleActive, deleteProduct,
    addVariant, langTab, uploadPhoto, uploadGallery, removeGallery, openBundle, saveBundle, toggleBundle, deleteBundle, addBundleItem,
    saveRules, saveSite, addSiteField, changePassword, closeModal,
  };
})();
