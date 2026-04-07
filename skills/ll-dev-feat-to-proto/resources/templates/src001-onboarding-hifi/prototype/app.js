(() => {
  const STORAGE_KEY = 'lee_proto_src001_ux1_state';
  const els = {
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

  const defaults = () => ({
    route: 'screen_onboarding_minimal',
    history: [],
    minProfile: { gender: '', age: '', height: '', weight: '', marathon_goal: '' },
    suggestion: { risk_band: 'low' },
    home: { profile_completion: 30, device_connected: false },
    overlay: '',
    tasks: { weekly_volume: '', injury_status: '', preferred_days: 'Tue/Thu/Sat', notes: '' },
    device: { selected: '' },
  });

  let state = (load() && typeof load() === 'object') ? load() : defaults();

  function toast(msg) {
    els.toast.textContent = String(msg || '');
    els.toast.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => { els.toast.hidden = true; }, 1900);
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
  function closeDrawer() { els.drawer.hidden = true; state.overlay = ''; save(); render(); }

  function setRoute(route, opts) {
    const next = String(route || '').trim();
    if (!next) return;
    if ((opts || {}).pushHistory && state.route && state.route !== next) {
      state.history = (state.history || []).slice(0, 30);
      state.history.push(state.route);
    }
    state.route = next;
    state.overlay = '';
    save();
    render();
  }

  function back() {
    const h = state.history || [];
    const prev = h.length ? h[h.length - 1] : '';
    if (!prev) return;
    state.history = h.slice(0, -1);
    state.route = prev;
    state.overlay = '';
    save();
    render();
  }

  const minRequiredKeys = () => ['gender', 'age', 'height', 'weight', 'marathon_goal'];
  const validateMin = () => {
    const missing = minRequiredKeys().filter((k) => !String(state.minProfile[k] || '').trim());
    return { ok: missing.length === 0, missing };
  };

  function riskCompute() {
    const age = Number(state.minProfile.age || 0);
    const weight = Number(state.minProfile.weight || 0);
    const goal = String(state.minProfile.marathon_goal || '');
    if (age >= 50 || weight >= 90 || goal.includes('破三')) return 'medium';
    return 'low';
  }

  function bindDelegates(root) {
    if (!root) return;
    root.addEventListener('input', (e) => {
      const el = e.target;
      if (!el || !el.matches) return;
      if (!el.matches('input[name],select[name],textarea[name]')) return;
      const name = el.getAttribute('name');
      if (!name) return;
      if (state.route === 'screen_onboarding_minimal') state.minProfile[name] = el.value;
      if (state.overlay === 'sheet_profile_tasks') state.tasks[name] = el.value;
      save();
    });
    root.addEventListener('change', () => render());
  }

  function openProfileTasks() {
    state.overlay = 'sheet_profile_tasks';
    save();
    openDrawer({
      title: '渐进补全画像',
      sub: '任务卡 · 可随时保存返回首页',
      body: `
        <section class="card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
            <div style="min-width:0">
              <div class="h2">补全项（推荐）</div>
              <div class="p" style="margin-top:8px">只补你愿意补的，首日体验不阻塞。</div>
            </div>
            <div class="tag ${state.home.profile_completion >= 70 ? 'good' : 'warn'}">完成度 ${state.home.profile_completion || 0}%</div>
          </div>
        </section>
        <section class="card">
          <div class="grid">
            <div class="field">
              <label>近 4 周周跑量（km）</label>
              <input name="weekly_volume" value="${String(state.tasks.weekly_volume || '')}" placeholder="例如 25" />
            </div>
            <div class="field">
              <label>近期伤痛/疲劳</label>
              <select name="injury_status">
                <option value="">请选择</option>
                ${['无明显问题', '轻微不适', '恢复中', '有急性伤痛'].map((o) => `<option value="${o}" ${o === String(state.tasks.injury_status || '') ? 'selected' : ''}>${o}</option>`).join('')}
              </select>
            </div>
            <div class="field">
              <label>偏好训练日</label>
              <input name="preferred_days" value="${String(state.tasks.preferred_days || '')}" placeholder="例如 Tue/Thu/Sat" />
            </div>
            <div class="field">
              <label>备注（可选）</label>
              <textarea name="notes" placeholder="任何你希望教练知道的事情">${String(state.tasks.notes || '')}</textarea>
            </div>
          </div>
        </section>`,
      actions: [
        { label: '保存并返回首页', tone: 'primary', onClick: () => {
          state.home.profile_completion = Math.min(100, Math.max(40, Number(state.home.profile_completion || 30) + 20));
          save();
          toast('已保存补全（原型模拟）');
          closeDrawer();
        }},
        { label: '稍后再说', tone: 'ghost', onClick: () => { toast('已稍后'); closeDrawer(); } },
      ],
    });
    bindDelegates(els.drawerBody);
  }

  function openDeviceConnect() {
    state.overlay = 'sheet_device_connect';
    save();
    const connected = !!state.home.device_connected;
    openDrawer({
      title: '连接设备（可选）',
      sub: connected ? '已连接 · 可更换/解绑' : '首日体验不阻塞，可跳过',
      body: `
        <section class="card">
          <div class="h2">设备列表</div>
          <div class="p" style="margin-top:8px">用于自动同步跑步记录与心率。</div>
          <div class="grid" style="margin-top:12px">
            ${['Apple Health', 'Garmin', 'COROS', 'Suunto'].map((d) => `
              <button class="btn ghost" data-device="${d}" style="text-align:left">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
                  <div style="font-weight:800">${d}</div>
                  <div class="tag ${String(state.device.selected||'')===d ? 'good' : ''}">${String(state.device.selected||'')===d ? '已选择' : '选择'}</div>
                </div>
              </button>`).join('')}
          </div>
        </section>
        <section class="card">
          <div class="h2">连接说明</div>
          <ul class="list" style="margin-top:10px">
            <li>连接失败不会影响你继续体验。</li>
            <li>后续可在首页随时重新连接。</li>
          </ul>
        </section>`,
      actions: [
        { label: connected ? '已连接' : '开始连接', tone: 'primary', disabled: connected || !String(state.device.selected || '').trim(), onClick: () => {
          state.home.device_connected = true;
          save();
          toast('连接成功（原型模拟）');
          closeDrawer();
        }},
        { label: '跳过', tone: 'ghost', onClick: () => { toast('已跳过'); closeDrawer(); } },
      ],
    });
    els.drawerBody.querySelectorAll('button[data-device]').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.device.selected = btn.getAttribute('data-device') || '';
        save();
        openDeviceConnect();
      });
    });
  }

  function renderOnboarding() {
    const v = validateMin();
    const err = (k) => (v.missing.includes(k) ? '<div class="err">必填</div>' : '');
    const input = (k, label, type) => `<div class="field"><label>${label} *</label>
      <input name="${k}" type="${type}" value="${String(state.minProfile[k] || '')}" placeholder="${label}" />
      ${err(k)}</div>`;
    const select = (k, label, opts) => {
      const val = String(state.minProfile[k] || '');
      return `<div class="field"><label>${label} *</label>
        <select name="${k}">
          <option value="">请选择</option>
          ${opts.map((o) => `<option value="${o}" ${o === val ? 'selected' : ''}>${o}</option>`).join('')}
        </select>${err(k)}</div>`;
    };
    return `
      <section class="card">
        <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
          <div style="min-width:0">
            <div class="h1">最小建档</div>
            <div class="p">目标：1 分钟内完成最小画像，立刻放出首轮建议。</div>
          </div>
          <div class="pill ${v.ok ? 'good' : 'warn'}">${v.ok ? '可继续' : `缺 ${v.missing.length} 项`}</div>
        </div>
      </section>
      <section class="card">
        <div class="h2">基本信息</div>
        <div class="grid" style="margin-top:12px">
          <div class="grid two">
            ${select('gender', '性别', ['女', '男'])}
            ${input('age', '年龄', 'number')}
          </div>
          <div class="grid two">
            ${input('height', '身高（cm）', 'number')}
            ${input('weight', '体重（kg）', 'number')}
          </div>
          <div class="field">
            <label>目标（示例：完赛 / 破四 / 破三） *</label>
            <input name="marathon_goal" value="${String(state.minProfile.marathon_goal || '')}" placeholder="完赛 / 破四 / 破三" />
            ${err('marathon_goal')}
          </div>
        </div>
      </section>
    `;
  }

  function renderSuggestion() {
    const band = String(state.suggestion.risk_band || 'low');
    const tag = band === 'low' ? 'good' : band === 'medium' ? 'warn' : 'danger';
    const label = band === 'low' ? '低风险' : band === 'medium' ? '需谨慎' : '高风险';
    return `
      <section class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
          <div style="min-width:0">
            <div class="h1">首轮 AI 建议</div>
            <div class="p">先给出一条“能执行”的建议，再逐步补齐更多信息。</div>
          </div>
          <div class="tag ${tag}">${label}</div>
        </div>
      </section>
      <section class="card">
        <div class="h2">今日推荐</div>
        <ul class="list" style="margin-top:10px">
          <li>轻松跑 25–35 分钟（RPE 3–4）</li>
          <li>跑前 5 分钟热身 + 动态拉伸</li>
          <li>跑后补水 + 走 5 分钟放松</li>
        </ul>
      </section>
      <section class="card">
        <div class="h2">下一步</div>
        <div class="p" style="margin-top:8px">进入首页后，你可以通过任务卡补全画像，或连接设备。</div>
      </section>
    `;
  }

  function renderHome() {
    const pc = Math.min(100, Math.max(0, Number(state.home.profile_completion || 0)));
    const dc = !!state.home.device_connected;
    return `
      <section class="card">
        <div class="h1">首页</div>
        <div class="p">建议可执行、补全不阻塞、设备后置增强。</div>
        <div class="grid" style="margin-top:12px">
          <div class="grid two">
            <div class="card" style="padding:12px">
              <div class="h2">画像完成度</div>
              <div class="p" style="margin-top:6px">${pc}%</div>
              <div class="bar" style="margin-top:10px"><div style="width:${pc}%"></div></div>
            </div>
            <div class="card" style="padding:12px">
              <div class="h2">设备</div>
              <div class="p" style="margin-top:6px">${dc ? '已连接' : '未连接'}</div>
              <div class="p" style="margin-top:10px">${dc ? '已准备好同步记录。' : '可跳过，不影响体验。'}</div>
            </div>
          </div>
          <button class="btn ghost" data-action="open-tasks" style="text-align:left">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
              <div>
                <div style="font-weight:800">任务卡：补全画像</div>
                <div class="p" style="margin-top:4px">让后续建议更准（不阻塞）。</div>
              </div>
              <div class="tag ${pc >= 70 ? 'good' : 'warn'}">${pc >= 70 ? '已较完整' : '建议补全'}</div>
            </div>
          </button>
          <button class="btn ghost" data-action="open-device" style="text-align:left">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
              <div>
                <div style="font-weight:800">设备连接（可选）</div>
                <div class="p" style="margin-top:4px">用于自动同步记录与心率。</div>
              </div>
              <div class="tag ${dc ? 'good' : 'warn'}">${dc ? '已连接' : '未连接'}</div>
            </div>
          </button>
        </div>
      </section>
      <section class="card">
        <div class="h2">状态模型（冻结边界）</div>
        <div class="p" style="margin-top:8px">展示“单一事实源”与同步状态，但不把它做成独立页面。</div>
        <ul class="list" style="margin-top:10px">
          <li>画像数据：本地增量保存 + 云端最终一致。</li>
          <li>设备绑定：后置增强，不影响建议可用性。</li>
          <li>建议/风险：可回溯到冻结的输出契约。</li>
        </ul>
      </section>
    `;
  }

  function actions() {
    if (state.route === 'screen_onboarding_minimal') {
      const v = validateMin();
      return [
        { label: '继续', tone: 'primary', disabled: !v.ok, onClick: () => {
          if (!v.ok) { toast('请先完成必填项'); return; }
          state.suggestion.risk_band = riskCompute();
          save();
          setRoute('screen_first_suggestion', { pushHistory: true });
        }},
      ];
    }
    if (state.route === 'screen_first_suggestion') {
      return [
        { label: '接受并进入首页', tone: 'primary', onClick: () => setRoute('screen_home_entry', { pushHistory: true }) },
        { label: '返回修改', tone: 'ghost', onClick: () => setRoute('screen_onboarding_minimal', { pushHistory: true }) },
      ];
    }
    if (state.route === 'screen_home_entry') {
      return [
        { label: '开始今日训练', tone: 'primary', onClick: () => toast('训练执行闭环在 SRC002（原型模拟）') },
        { label: '补全画像', tone: 'ghost', onClick: () => openProfileTasks() },
      ];
    }
    return [{ label: '返回', tone: 'ghost', onClick: () => back() }];
  }

  function renderMenu() {
    const items = [
      { id: 'screen_onboarding_minimal', label: '最小建档', run: () => { setRoute('screen_onboarding_minimal'); closeSheet(); } },
      { id: 'screen_first_suggestion', label: '首轮建议', run: () => { setRoute('screen_first_suggestion'); closeSheet(); } },
      { id: 'screen_home_entry', label: '首页', run: () => { setRoute('screen_home_entry'); closeSheet(); } },
      { id: 'sheet_profile_tasks', label: '补全画像（抽屉）', run: () => { setRoute('screen_home_entry'); closeSheet(); openProfileTasks(); } },
      { id: 'sheet_device_connect', label: '设备连接（抽屉）', run: () => { setRoute('screen_home_entry'); closeSheet(); openDeviceConnect(); } },
    ];
    els.sheetMeta.textContent = 'SRC001 · 新用户旅程';
    els.journey.innerHTML = items.map((it) => `<button class="btn ghost" data-jump="${it.id}">${it.label}</button>`).join('');
    els.debug.innerHTML = [
      `<button class="btn ghost" data-debug="risk-low">风险=低</button>`,
      `<button class="btn ghost" data-debug="risk-medium">风险=中</button>`,
      `<button class="btn ghost" data-debug="risk-high">风险=高</button>`,
      `<button class="btn ghost" data-debug="toggle-device">切换设备连接</button>`,
      `<button class="btn ghost" data-debug="profile-plus">画像完成度 +20%</button>`,
    ].join('');

    els.journey.querySelectorAll('button[data-jump]').forEach((btn) => {
      const item = items.find((it) => it.id === btn.getAttribute('data-jump'));
      item && btn.addEventListener('click', item.run);
    });
    els.debug.querySelectorAll('button[data-debug]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const k = btn.getAttribute('data-debug');
        if (k === 'risk-low') state.suggestion.risk_band = 'low';
        if (k === 'risk-medium') state.suggestion.risk_band = 'medium';
        if (k === 'risk-high') state.suggestion.risk_band = 'high';
        if (k === 'toggle-device') state.home.device_connected = !state.home.device_connected;
        if (k === 'profile-plus') state.home.profile_completion = Math.min(100, Number(state.home.profile_completion || 0) + 20);
        save();
        closeSheet();
        render();
      });
    });
  }

  function render() {
    els.navBack.disabled = (state.history || []).length === 0;
    const dc = !!state.home.device_connected;
    const pc = Math.min(100, Math.max(0, Number(state.home.profile_completion || 0)));
    els.navSub.textContent = state.route === 'screen_onboarding_minimal'
      ? '最小建档 · 1 分钟完成'
      : state.route === 'screen_first_suggestion'
        ? `首轮建议 · 风险=${String(state.suggestion.risk_band || '')}`
        : `首页 · 画像${pc}% · 设备${dc ? '已连接' : '未连接'}`;

    if (state.route === 'screen_onboarding_minimal') els.screen.innerHTML = renderOnboarding();
    if (state.route === 'screen_first_suggestion') els.screen.innerHTML = renderSuggestion();
    if (state.route === 'screen_home_entry') els.screen.innerHTML = renderHome();

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

    els.screen.querySelectorAll('button[data-action]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const act = btn.getAttribute('data-action');
        if (act === 'open-tasks') openProfileTasks();
        if (act === 'open-device') openDeviceConnect();
      });
    });

    bindDelegates(els.screen);
    renderMenu();
  }

  // nav bindings
  els.navBack.addEventListener('click', () => back());
  els.navMenu.addEventListener('click', () => openSheet());
  els.sheetClose.addEventListener('click', () => closeSheet());
  els.sheetScrim.addEventListener('click', () => closeSheet());
  els.drawerClose.addEventListener('click', () => closeDrawer());
  els.drawerScrim.addEventListener('click', () => closeDrawer());
  els.modalScrim.addEventListener('click', () => closeModal());
  els.reset.addEventListener('click', () => { state = defaults(); save(); closeSheet(); closeDrawer(); closeModal(); toast('已重置'); render(); });

  render();
})();
