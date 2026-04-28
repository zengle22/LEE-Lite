(() => {
  const STORAGE_KEY = 'lee_proto_generic_hifi_state_v1';
  const data = (window.__LEE_PROTO_DATA__ && typeof window.__LEE_PROTO_DATA__ === 'object') ? window.__LEE_PROTO_DATA__ : null;
  const model = (window.__LEE_JOURNEY_MODEL__ && typeof window.__LEE_JOURNEY_MODEL__ === 'object') ? window.__LEE_JOURNEY_MODEL__ : null;

  const els = {
    navTitle: document.getElementById('nav-title'),
    navSub: document.getElementById('nav-sub'),
    navBack: document.getElementById('nav-back'),
    navMenu: document.getElementById('nav-menu'),
    screen: document.getElementById('screen'),
    cta: document.getElementById('cta'),
    sheet: document.getElementById('sheet'),
    sheetScrim: document.getElementById('sheet-scrim'),
    sheetClose: document.getElementById('sheet-close'),
    sheetMeta: document.getElementById('sheet-meta'),
    journey: document.getElementById('journey'),
    debug: document.getElementById('debug'),
    reset: document.getElementById('reset'),
    toast: document.getElementById('toast'),
    modal: document.getElementById('modal'),
    modalScrim: document.getElementById('modal-scrim'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-body'),
    modalActions: document.getElementById('modal-actions'),
    drawer: document.getElementById('drawer'),
    drawerScrim: document.getElementById('drawer-scrim'),
    drawerClose: document.getElementById('drawer-close'),
    drawerTitle: document.getElementById('drawer-title'),
    drawerSub: document.getElementById('drawer-sub'),
    drawerBody: document.getElementById('drawer-body'),
    drawerFoot: document.getElementById('drawer-foot'),
  };

  const safeParse = (t, fb) => { try { return JSON.parse(t); } catch { return fb; } };
  const load = () => safeParse(localStorage.getItem(STORAGE_KEY) || '', null);
  const save = () => localStorage.setItem(STORAGE_KEY, JSON.stringify(state));

  const pageList = Array.isArray(data && data.pages) ? data.pages : [];
  const surfaceList = Array.isArray(model && model.journey_surface_inventory) ? model.journey_surface_inventory : [];
  const bySurfaceId = new Map(surfaceList.map((s) => [String(s.surface_id || ''), s]));

  const surfaceSeq = (() => {
    const main = Array.isArray(model && model.journey_main_path) ? model.journey_main_path : [];
    const seq = [];
    main.forEach((step) => {
      const m = String(step || '').match(/(screen_[a-z0-9_]+|sheet_[a-z0-9_]+|drawer_[a-z0-9_]+|page-\\d+)/i);
      if (m && m[1]) seq.push(m[1]);
    });
    const dedup = [];
    seq.forEach((id) => { if (!dedup.length || dedup[dedup.length - 1] !== id) dedup.push(id); });
    return dedup.length ? dedup : (surfaceList.map((s) => String(s.surface_id || '')).filter(Boolean));
  })();

  const defaults = () => ({
    route: surfaceSeq[0] || (surfaceList[0] && surfaceList[0].surface_id) || 'page-0',
    history: [],
    form: {},
  });

  let state = (load() && typeof load() === 'object') ? load() : defaults();

  function toast(msg) {
    els.toast.textContent = String(msg || '');
    els.toast.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => { els.toast.hidden = true; }, 1700);
  }

  function openSheet() { els.sheet.hidden = false; }
  function closeSheet() { els.sheet.hidden = true; }

  function openModal(title, body, actions) {
    els.modalTitle.textContent = title || '';
    els.modalBody.innerHTML = body || '';
    els.modalActions.innerHTML = '';
    (actions || []).forEach((a) => {
      const btn = document.createElement('button');
      btn.className = `btn ${a.tone || 'ghost'}`;
      btn.textContent = a.label || 'OK';
      btn.addEventListener('click', () => { a.onClick && a.onClick(); closeModal(); });
      els.modalActions.appendChild(btn);
    });
    els.modal.hidden = false;
  }
  function closeModal() { els.modal.hidden = true; }

  function openDrawer({ title, sub, body, actions }) {
    els.drawerTitle.textContent = title || '';
    els.drawerSub.textContent = sub || '';
    els.drawerBody.innerHTML = body || '';
    els.drawerFoot.innerHTML = '';
    (actions || []).forEach((a) => {
      const btn = document.createElement('button');
      btn.className = `btn ${a.tone || 'ghost'}`;
      btn.textContent = a.label || 'OK';
      if (a.disabled) btn.disabled = true;
      btn.addEventListener('click', () => a.onClick && a.onClick());
      els.drawerFoot.appendChild(btn);
    });
    els.drawer.hidden = false;
  }
  function closeDrawer() { els.drawer.hidden = true; }

  function setRoute(route, opts) {
    const next = String(route || '').trim();
    if (!next) return;
    if ((opts || {}).pushHistory && state.route && state.route !== next) {
      state.history = (state.history || []).slice(0, 30);
      state.history.push(state.route);
    }
    state.route = next;
    save();
    render();
  }

  function back() {
    const h = state.history || [];
    const prev = h.length ? h[h.length - 1] : '';
    if (!prev) return;
    state.history = h.slice(0, -1);
    state.route = prev;
    save();
    render();
  }

  function activePage() {
    // If route matches a page id, use it; else fallback to first page.
    const page = pageList.find((p) => String(p.page_id || '') === String(state.route || '')) || pageList[0] || null;
    return page;
  }

  function requiredFields(page) {
    const list = Array.isArray(page && page.required_ui_fields) ? page.required_ui_fields : (Array.isArray(page && page.required_fields) ? page.required_fields : []);
    return list.map((x) => String(x || '').trim()).filter(Boolean);
  }

  function validate(page) {
    const req = requiredFields(page);
    const missing = req.filter((k) => !String((state.form || {})[k] || '').trim());
    return { ok: missing.length === 0, missing };
  }

  function renderFields(page) {
    const fields = Array.isArray(page && page.editable_ui_fields) ? page.editable_ui_fields : [];
    const v = validate(page);
    if (!fields.length) {
      return `<section class="card"><div class="h2">内容</div><div class="p" style="margin-top:8px">该页面未声明可编辑字段（UI SSOT 中可能是纯展示页）。</div></section>`;
    }
    const err = (k) => (v.missing.includes(k) ? '<div class="err">必填</div>' : '');
    const input = (f) => {
      const name = String(f.field_name || f.name || '').trim();
      if (!name) return '';
      const label = String(f.label || name).trim();
      const type = String(f.field_type || '').toLowerCase();
      const val = String((state.form || {})[name] || '');
      const isSelect = type === 'select' || type === 'segmented';
      const isTextArea = type === 'textarea' || type === 'multiline';
      const options = Array.isArray(f.options) ? f.options : [];
      if (isSelect && options.length) {
        return `<div class="field"><label>${label}${requiredFields(page).includes(name) ? ' *' : ''}</label>
          <select name="${name}">
            <option value="">请选择</option>
            ${options.map((o) => `<option value="${String(o)}" ${String(o) === val ? 'selected' : ''}>${String(o)}</option>`).join('')}
          </select>${err(name)}</div>`;
      }
      if (isTextArea) {
        return `<div class="field"><label>${label}${requiredFields(page).includes(name) ? ' *' : ''}</label>
          <textarea name="${name}" placeholder="${label}">${val}</textarea>${err(name)}</div>`;
      }
      return `<div class="field"><label>${label}${requiredFields(page).includes(name) ? ' *' : ''}</label>
        <input name="${name}" value="${val}" placeholder="${label}" />${err(name)}</div>`;
    };
    return `<section class="card"><div class="h2">输入</div><div class="grid" style="margin-top:12px">${fields.map(input).join('')}</div></section>`;
  }

  function renderScreen() {
    const page = activePage();
    const surface = bySurfaceId.get(String(state.route || '')) || null;
    if (!page && !surface) {
      return `<section class="card"><div class="h2">原型初始化失败</div><div class="p" style="margin-top:8px">缺少 UI 数据（mock-data.js）或旅程模型（journey-model.js）。</div></section>`;
    }
    const title = (surface && surface.surface_title) ? String(surface.surface_title) : (page ? String(page.title || page.page_id || 'Page') : String(state.route || ''));
    const family = page ? String(page.page_type_family || '') : '';
    const v = validate(page);
    const head = `
      <section class="card">
        <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
          <div style="min-width:0">
            <div class="h1">${title}</div>
            <div class="p">${family ? `family=${family}` : 'hi-fi interactive prototype'}</div>
          </div>
          ${page ? `<div class="pill ${v.ok ? 'good' : 'warn'}">${v.ok ? '可继续' : `缺 ${v.missing.length} 项`}</div>` : ''}
        </div>
      </section>`;

    const note = page && page.page_goal ? `<section class="card"><div class="h2">目标</div><div class="p" style="margin-top:8px">${String(page.page_goal)}</div></section>` : '';
    const fields = page ? renderFields(page) : '';
    const hint = (surface && Array.isArray(surface.shared_state_refs) && surface.shared_state_refs.length)
      ? `<section class="card"><div class="h2">状态</div><div class="p" style="margin-top:8px">${surface.shared_state_refs.map((x) => `<span class="pill" style="margin-right:8px">${String(x)}</span>`).join('')}</div></section>`
      : '';
    return `${head}${note}${fields}${hint}`;
  }

  function actions() {
    const page = activePage();
    const v = validate(page);
    const idx = surfaceSeq.indexOf(String(state.route || ''));
    const nextId = idx >= 0 && idx + 1 < surfaceSeq.length ? surfaceSeq[idx + 1] : '';
    const prevId = idx > 0 ? surfaceSeq[idx - 1] : '';
    return [
      { label: nextId ? '继续' : '完成', tone: 'primary', disabled: page ? !v.ok : false, onClick: () => {
        if (page && !v.ok) { toast('请先完成必填项'); return; }
        if (!nextId) { toast('已到旅程末尾'); return; }
        setRoute(nextId, { pushHistory: true });
      }},
      { label: prevId ? '返回' : '菜单', tone: 'ghost', onClick: () => (prevId ? setRoute(prevId, { pushHistory: true }) : openSheet()) },
    ];
  }

  function renderMenu() {
    const items = surfaceSeq.length ? surfaceSeq : (surfaceList.map((s) => String(s.surface_id || '')).filter(Boolean));
    const labelFor = (id) => {
      const s = bySurfaceId.get(String(id));
      if (s && s.surface_title) return String(s.surface_title);
      const p = pageList.find((x) => String(x.page_id || '') === String(id));
      if (p && p.title) return String(p.title);
      return String(id);
    };
    els.sheetMeta.textContent = `${String((data && data.feat_ref) || '') || 'Prototype'} · ${String((model && model.journey_id) || '') || 'Generic'}`;
    els.journey.innerHTML = items.map((id) => `<button class="btn ghost" data-jump="${String(id)}">${labelFor(id)}</button>`).join('');
    els.debug.innerHTML = [
      `<button class="btn ghost" data-debug="clear-form">清空输入</button>`,
    ].join('');

    els.journey.querySelectorAll('button[data-jump]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-jump') || '';
        closeSheet();
        setRoute(id, { pushHistory: true });
      });
    });
    els.debug.querySelectorAll('button[data-debug]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const k = btn.getAttribute('data-debug');
        if (k === 'clear-form') { state.form = {}; save(); toast('已清空'); closeSheet(); render(); }
      });
    });
  }

  function bindInputs() {
    els.screen.addEventListener('input', (e) => {
      const el = e.target;
      if (!el || !el.matches) return;
      if (!el.matches('input[name],select[name],textarea[name]')) return;
      const name = el.getAttribute('name');
      if (!name) return;
      state.form = state.form || {};
      state.form[name] = el.value;
      save();
    });
    els.screen.addEventListener('change', () => render());
  }

  function render() {
    const surface = bySurfaceId.get(String(state.route || '')) || null;
    const title = surface && surface.surface_title ? String(surface.surface_title) : String((data && data.feat_title) || 'Prototype');
    els.navTitle.textContent = title;
    els.navSub.textContent = String(state.route || '');
    els.navBack.disabled = (state.history || []).length === 0;

    els.screen.innerHTML = renderScreen();

    const row = document.createElement('div');
    row.className = 'cta-row';
    actions().slice(0, 3).forEach((a) => {
      const b = document.createElement('button');
      b.className = `btn ${a.tone || 'ghost'}`;
      b.textContent = a.label || 'Action';
      if (a.disabled) b.disabled = true;
      b.addEventListener('click', () => a.onClick && a.onClick());
      row.appendChild(b);
    });
    els.cta.innerHTML = '';
    els.cta.appendChild(row);

    renderMenu();
  }

  els.navBack.addEventListener('click', () => back());
  els.navMenu.addEventListener('click', () => openSheet());
  els.sheetClose.addEventListener('click', () => closeSheet());
  els.sheetScrim.addEventListener('click', () => closeSheet());
  els.modalScrim.addEventListener('click', () => closeModal());
  els.drawerClose.addEventListener('click', () => closeDrawer());
  els.drawerScrim.addEventListener('click', () => closeDrawer());
  els.reset.addEventListener('click', () => { state = defaults(); save(); closeSheet(); closeModal(); closeDrawer(); toast('已重置'); render(); });

  bindInputs();
  render();
})();
