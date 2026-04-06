(() => {
  const STORAGE_KEY = 'lee_proto_src002_ux1_state';
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
    route: 'setup', // setup | today
    step: 0, // 0 input | 1 gate | 2 draft
    gate: { status: 'assessing', degradedAccepted: false },
    plan: { weekExpanded: false, activated: false },
    today: { status: 'planned', weekExpanded: false, adjustmentApplied: false },
    form: {
      gender: '',
      birthdate: '',
      height: '',
      weight: '',
      running_level: '',
      recent_injury_status: '',
      current_weekly_volume: '',
      recent_race_pace: '',
      readiness_to_train: '',
      pain_trend: '',
      sleep_quality: '3',
      fatigue_level: '3',
      muscle_soreness: '3',
      mood_state: '3',
      completed: '',
      deviation_reason: '',
      notes: '',
    },
  });

  let state = (load() && typeof load() === 'object') ? load() : defaults();

  function toast(msg) {
    els.toast.textContent = String(msg || '');
    els.toast.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => { els.toast.hidden = true; }, 1900);
  }

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

  function openSheet() { els.sheet.hidden = false; }
  function closeSheet() { els.sheet.hidden = true; }

  function openDrawer({ title, sub, body, actions }) {
    els.drawerTitle.textContent = title || '';
    els.drawerSub.textContent = sub || '';
    els.drawerBody.innerHTML = body || '';
    els.drawerFoot.innerHTML = '';
    (actions || []).forEach((a) => {
      const btn = document.createElement('button');
      btn.className = `btn ${a.tone || 'ghost'}`;
      btn.textContent = a.label || 'OK';
      btn.addEventListener('click', () => a.onClick && a.onClick());
      els.drawerFoot.appendChild(btn);
    });
    els.drawer.hidden = false;
  }
  function closeDrawer() { els.drawer.hidden = true; }

  function setSetupStep(step) {
    state.route = 'setup';
    state.step = Math.max(0, Math.min(Number(step) || 0, 2));
    save();
    render();
  }

  function setForm(key, value) {
    if (!key) return;
    state.form = state.form || {};
    state.form[key] = value;
    save();
  }

  const requiredKeys = () => ['gender', 'birthdate', 'height', 'weight', 'running_level', 'recent_injury_status', 'current_weekly_volume', 'readiness_to_train'];
  const validate = () => {
    const missing = requiredKeys().filter((k) => !String(state.form[k] || '').trim());
    return { ok: missing.length === 0, missing };
  };
  const gateCompute = () => {
    const injury = String(state.form.recent_injury_status || '');
    const readiness = String(state.form.readiness_to_train || '');
    const volume = Number(state.form.current_weekly_volume || 0);
    const level = String(state.form.running_level || '');
    if (injury === 'active' || readiness === 'no') return 'blocked';
    if (injury === 'recovering' || readiness === 'uncertain') return 'degraded';
    if (level === 'beginner' && volume < 20) return 'degraded';
    return 'pass';
  };

  function bindDelegates(root) {
    if (!root) return;

    root.addEventListener('click', (e) => {
      const btn = e.target && e.target.closest ? e.target.closest('button[data-seg][data-val]') : null;
      if (!btn) return;
      const key = btn.getAttribute('data-seg');
      const val = btn.getAttribute('data-val');
      if (!key) return;
      setForm(key, val);
      render();
    });

    const onValue = (e, rerender) => {
      const el = e.target;
      if (!el || !el.matches) return;
      if (!el.matches('input[name],select[name],textarea[name]')) return;
      const name = el.getAttribute('name');
      if (!name) return;
      setForm(name, el.value);
      if (rerender) render();
    };

    root.addEventListener('input', (e) => onValue(e, false));
    root.addEventListener('change', (e) => onValue(e, true));
  }

  const stepper = () => {
    const s = state.step;
    const node = (idx, label) => `<div class="step ${idx < s ? 'done' : ''} ${idx === s ? 'active' : ''}"><div class="dot"></div><div>${label}</div></div>`;
    return `<div class="stepper">${node(0, '输入')}<div class="sep"></div>${node(1, '风险')}<div class="sep"></div>${node(2, '草案')}</div>`;
  };

  function renderInput() {
    const v = validate();
    const err = (k) => (v.missing.includes(k) ? '<div class="err">必填</div>' : '');
    const select = (k, label, opts) => {
      const val = String(state.form[k] || '');
      return `<div class="field"><label>${label} *</label>
        <select name="${k}">
          <option value="">请选择</option>
          ${opts.map((o) => `<option value="${o}" ${o === val ? 'selected' : ''}>${o}</option>`).join('')}
        </select>${err(k)}</div>`;
    };
    const input = (k, label, type, hint) => `<div class="field"><label>${label} *</label>
      <input name="${k}" type="${type}" value="${String(state.form[k] || '')}" placeholder="${label}" />
      ${err(k)}${hint ? `<div class="p">${hint}</div>` : ''}</div>`;
    const two = (a, b) => `<div class="grid two">${a}${b}</div>`;

    return `
      <section class="card">
        <div class="grid" style="gap:10px">
          <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
            <div style="min-width:0">
              <div class="h1">生成训练计划（1/3）</div>
              <div class="p">完成最小画像与能力基线，才能进入风险评估并生成计划。</div>
            </div>
            <div class="pill ${v.ok ? 'good' : 'warn'}">${v.ok ? '可进入下一步' : `缺 ${v.missing.length} 项`}</div>
          </div>
          ${stepper()}
        </div>
      </section>

      <section class="card">
        <div class="h2">最小画像（Min Profile）</div>
        <div class="p" style="margin-top:8px">这些信息用于确定训练负荷与风险边界。</div>
        <div class="grid" style="margin-top:12px">
          ${select('gender', '性别', ['male', 'female', 'non_binary', 'prefer_not_to_say'])}
          ${two(input('birthdate', '出生日期', 'date', 'canonical：必须用出生日期'), input('height', '身高（cm）', 'number', ''))}
          ${two(input('weight', '体重（kg）', 'number', ''), select('running_level', '跑步水平', ['beginner', 'intermediate', 'advanced', 'elite']))}
          ${select('recent_injury_status', '近期伤病', ['none', 'mild', 'recovering', 'active'])}
        </div>
      </section>

      <section class="card">
        <div class="h2">训练能力基线（Current Training State）</div>
        <div class="p" style="margin-top:8px">能力基线缺失会阻断计划生成。</div>
        <div class="grid" style="margin-top:12px">
          ${two(input('current_weekly_volume', '当前周跑量（km）', 'number', ''), `<div class="field"><label>近期比赛配速（可选）</label><input name="recent_race_pace" type="text" value="${String(state.form.recent_race_pace || '')}" placeholder="例如：5:30/km" /><div class="p">例如：5:30/km</div></div>`)}
          ${select('readiness_to_train', '今天准备训练吗', ['yes', 'uncertain', 'no'])}
        </div>
      </section>

      <section class="card">
        <div class="h2">后置操作（不阻塞）</div>
        <div class="p" style="margin-top:8px">设备绑定/历史同步不会阻塞计划生成，可在后续完成。</div>
        <div style="display:flex;gap:10px;margin-top:12px;flex-wrap:wrap">
          <button class="btn ghost" data-action="device">设备绑定（可选）</button>
          <button class="btn ghost" data-action="sync">历史同步（可选）</button>
        </div>
      </section>
    `;
  }

  function renderGate() {
    const s = state.gate.status;
    const banner = s === 'assessing'
      ? { pill: 'warn', title: '评估中…', body: '我们会检查伤病风险、目标合理性、当前训练负荷与恢复情况。' }
      : s === 'pass'
        ? { pill: 'good', title: 'PASS：可以生成计划', body: '未发现明显风险，可继续生成草案。' }
        : s === 'degraded'
          ? { pill: 'warn', title: 'DEGRADED：建议降级方案', body: '为了降低风险，我们建议降低目标与训练负荷。需要你明确接受后继续。' }
          : { pill: 'danger', title: 'BLOCKED：暂不满足生成条件', body: '当前风险过高或准备度不足，需先修改输入或暂不生成。' };

    const degraded = `
      <div class="card" style="margin-top:12px">
        <div class="h2">影响摘要</div>
        <div class="p" style="margin-top:8px">原目标 vs 建议目标（示例）</div>
        <div class="split" style="margin-top:12px">
          <div class="card" style="padding:12px"><div class="kv"><b>目标</b><span>半马完赛</span></div><div class="kv"><b>频次</b><span>4 次/周</span></div><div class="kv"><b>强度</b><span>间歇 + 阈值</span></div></div>
          <div class="card" style="padding:12px"><div class="kv"><b>目标</b><span>半马完赛（更保守）</span></div><div class="kv"><b>频次</b><span>3 次/周</span></div><div class="kv"><b>强度</b><span>更多有氧</span></div></div>
        </div>
      </div>`;

    const blocked = `
      <div class="card" style="margin-top:12px">
        <div class="h2">原因与建议</div>
        <ul class="list" style="margin-top:10px">
          <li>近期伤病状态为 <b>${String(state.form.recent_injury_status || '(unknown)')}</b> 或 readiness_to_train=no</li>
          <li>建议：先完成恢复评估 / 或降低目标为健康跑维持</li>
        </ul>
      </div>`;

    return `
      <section class="card">
        <div class="grid" style="gap:10px">
          <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
            <div style="min-width:0">
              <div class="h1">生成训练计划（2/3）</div>
              <div class="p">风险 Gate（内联）</div>
            </div>
            <div class="pill ${banner.pill}">${s.toUpperCase()}</div>
          </div>
          ${stepper()}
        </div>
      </section>
      <section class="card"><div class="h2">${banner.title}</div><div class="p" style="margin-top:8px">${banner.body}</div></section>
      ${s === 'degraded' ? degraded : ''}
      ${s === 'blocked' ? blocked : ''}
    `;
  }

  function renderDraft() {
    const activated = !!state.plan.activated;
    return `
      <section class="card">
        <div class="grid" style="gap:10px">
          <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
            <div style="min-width:0">
              <div class="h1">生成训练计划（3/3）</div>
              <div class="p">草案审查与激活</div>
            </div>
            <div class="pill ${activated ? 'good' : 'warn'}">${activated ? 'ACTIVE' : 'DRAFT'}</div>
          </div>
          ${stepper()}
        </div>
      </section>

      <section class="card">
        <div class="h2">Guardrail</div>
        <div class="p" style="margin-top:8px">✅ 校验通过（示例：如训练负荷偏高会自动修正并提示）</div>
      </section>

      <section class="card">
        <div class="h2">计划摘要</div>
        <div class="p" style="margin-top:8px">目标：半马完赛（${state.gate.status === 'degraded' ? '降级路径' : '标准路径'}）${activated ? ' · 已激活（只读）' : ''}</div>
        <div class="card" style="margin-top:12px;padding:12px">
          <div class="kv"><b>周期</b><span>12 周</span></div>
          <div class="kv"><b>频次</b><span>${state.gate.status === 'degraded' ? '3 次/周' : '3-4 次/周'}</span></div>
          <div class="kv"><b>强度</b><span>有氧 70% / 阈值 20% / 间歇 10%</span></div>
        </div>
      </section>

      <section class="card">
        <div class="h2">周计划概览</div>
        <div class="p" style="margin-top:8px">默认只展示概览；可展开查看完整周表。</div>
        <div style="display:flex;gap:10px;margin-top:12px;flex-wrap:wrap">
          <span class="pill">Week 1 基础期</span><span class="pill">Week 2 基础期</span><span class="pill">Week 3 进展期</span><span class="pill">…</span><span class="pill">Week 12 taper</span>
        </div>
        <div style="margin-top:12px"><button class="btn ghost" data-action="toggle-week">${state.plan.weekExpanded ? '收起完整周表' : '查看完整周表'}</button></div>
        ${state.plan.weekExpanded ? `<div class="card" style="margin-top:12px;padding:12px"><div class="p">（示例）完整周表在最终产品会是可滚动周历/列表，这里用简表替代。</div><ul class="list" style="margin-top:10px"><li>周二：间歇训练（短）</li><li>周四：阈值跑</li><li>周六：LSD 长距离</li></ul></div>` : ''}
      </section>

      <section class="card">
        <div class="h2">关键训练日（本周）</div>
        <ul class="list" style="margin-top:10px"><li>Tue：间歇训练</li><li>Thu：阈值跑</li><li>Sat：长距离慢跑</li></ul>
      </section>
    `;
  }

  function renderToday() {
    const adjusted = state.today.adjustmentApplied;
    const t = {
      date: '2026-04-06',
      week: '第 3 周 · 第 2 天',
      sessionType: adjusted ? '恢复跑（已调整）' : '阈值跑',
      intensity: adjusted ? '低强度' : '中等偏高',
      goal: adjusted ? '降低负荷，促进恢复，为后续训练留余量。' : '提升乳酸阈值配速，增强持续快速奔跑能力。',
      execution: adjusted
        ? ['热身：10 分钟轻松走/慢跑', '主训练：30 分钟轻松跑', '冷身：5 分钟 + 拉伸']
        : ['热身：15 分钟轻松跑', '主训练：20 分钟阈值配速跑（可 2×10 分钟）', '配速区间：5:30–5:45 / km', '冷身：10 分钟轻松跑 + 拉伸'],
      safety: ['如感觉心率异常升高，请降低配速或停止。', '如肌肉疼痛加剧，请跳过本次训练。'],
    };
    const statusPill = state.today.status === 'planned'
      ? '<span class="pill warn">未开始</span>'
      : state.today.status === 'in_progress'
        ? '<span class="pill warn">进行中</span>'
        : '<span class="pill good">已完成</span>';

    return `
      <section class="card">
        <div class="grid" style="gap:10px">
          <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
            <div style="min-width:0"><div class="h1">今日训练 · ${t.date}</div><div class="p">${t.week}</div></div>
            ${statusPill}
          </div>
          <div style="display:flex;gap:10px;flex-wrap:wrap">
            <span class="pill">${t.sessionType}</span>
            <span class="pill">${t.intensity}</span>
            ${adjusted ? '<span class="pill warn">已调整</span>' : ''}
          </div>
        </div>
      </section>
      <section class="card"><div class="h2">训练目标</div><div class="p" style="margin-top:8px">${t.goal}</div></section>
      <section class="card"><div class="h2">执行方式</div><ul class="list" style="margin-top:10px">${t.execution.map((x) => `<li>${x}</li>`).join('')}</ul></section>
      <section class="card"><div class="h2">安全提示</div><ul class="list" style="margin-top:10px">${t.safety.map((x) => `<li>${x}</li>`).join('')}</ul></section>
      <section class="card">
        <div class="h2">完整周表</div>
        <div class="p" style="margin-top:8px">用于理解“今日训练”在整周中的位置。</div>
        <div style="margin-top:12px"><button class="btn ghost" data-action="toggle-today-week">${state.today.weekExpanded ? '收起周表' : '查看完整周表'}</button></div>
        ${state.today.weekExpanded ? `<div class="card" style="margin-top:12px;padding:12px"><ul class="list"><li>Tue：${adjusted ? '恢复跑 30min（已调整）' : '间歇训练 8×400m'}</li><li>Thu：阈值跑 20min</li><li>Sat：LSD 12km</li></ul></div>` : ''}
      </section>
    `;
  }

  function actions() {
    if (state.route === 'setup') {
      if (state.step === 0) {
        const v = validate();
        return [
          { label: '下一步：风险评估', tone: 'primary', disabled: !v.ok, onClick: () => { if (!v.ok) return toast('请先完成必填项'); enterGate(); } },
          { label: '返回', tone: 'ghost', disabled: true, onClick: () => {} },
        ];
      }
      if (state.step === 1) {
        if (state.gate.status === 'assessing') return [
          { label: '评估中…', tone: 'primary', disabled: true, onClick: () => {} },
          { label: '返回修改输入', tone: 'ghost', disabled: false, onClick: () => { state.step = 0; save(); render(); } },
        ];
        if (state.gate.status === 'pass') return [
          { label: '继续生成草案', tone: 'primary', onClick: () => setSetupStep(2) },
          { label: '返回修改输入', tone: 'ghost', onClick: () => setSetupStep(0) },
        ];
        if (state.gate.status === 'degraded') return [
          { label: state.gate.degradedAccepted ? '继续生成草案' : '接受降级并继续', tone: 'primary', onClick: () => { state.gate.degradedAccepted = true; save(); setSetupStep(2); } },
          { label: '返回修改输入', tone: 'ghost', onClick: () => setSetupStep(0) },
        ];
        return [
          { label: '返回修改输入', tone: 'primary', onClick: () => setSetupStep(0) },
          { label: '暂不生成', tone: 'ghost', onClick: () => toast('已暂不生成（原型模拟）') },
        ];
      }
      if (state.plan.activated) return [
        { label: '进入今日训练', tone: 'primary', onClick: () => { state.route = 'today'; save(); render(); } },
        { label: '重新生成草案', tone: 'ghost', onClick: () => { state.plan.activated = false; save(); toast('已重置为草案（原型模拟）'); render(); } },
      ];
      return [
        { label: '激活计划', tone: 'primary', onClick: () => activate() },
        { label: '拒绝并重新生成', tone: 'ghost', onClick: () => toast('已重新生成草案（原型模拟）') },
      ];
    }

    if (state.today.status === 'planned') return [
      { label: '开始训练', tone: 'primary', onClick: () => { state.today.status = 'in_progress'; save(); toast('训练开始（原型模拟）'); render(); } },
      { label: '训练前检查', tone: 'ghost', onClick: () => openCheckin() },
      { label: '改期', tone: 'ghost', onClick: () => toast('已改期（原型模拟）') },
    ];
    if (state.today.status === 'in_progress') return [
      { label: '结束训练', tone: 'primary', onClick: () => { state.today.status = 'completed'; save(); toast('训练已完成'); render(); } },
      { label: '暂停', tone: 'ghost', onClick: () => toast('已暂停（原型模拟）') },
      { label: '返回', tone: 'ghost', onClick: () => toast('已在今日训练页') },
    ];
    return [
      { label: '训练后反馈', tone: 'primary', onClick: () => openFeedback() },
      { label: '查看调整', tone: 'ghost', onClick: () => openAdjustment(true) },
      { label: '返回', tone: 'ghost', onClick: () => toast('已在今日训练页') },
    ];
  }

  function enterGate() {
    setSetupStep(1);
    state.gate.status = 'assessing';
    save();
    render();
    setTimeout(() => {
      state.gate.status = gateCompute();
      save();
      render();
    }, 650);
  }

  function activate() {
    openModal(
      '激活计划？',
      '激活后将进入日常训练闭环，并生成“今日训练”。你仍可通过训练反馈触发微调。',
      [
        { label: '确认激活', tone: 'primary', onClick: () => { state.plan.activated = true; state.route = 'today'; save(); toast('计划已激活'); render(); } },
        { label: '取消', tone: 'ghost', onClick: () => {} },
      ],
    );
  }

  function openCheckin() {
    openDrawer({
      title: '训练前检查',
      sub: 'Pre-run Checkin',
      body: `
        <section class="card"><div class="h2">训练前检查</div><div class="p" style="margin-top:8px">用于判断今天是否适合训练，避免伤病风险。</div></section>
        <section class="card">
          <div class="field"><label>准备训练吗？ *</label>
            <div class="seg">
              <button data-seg="readiness_to_train" data-val="yes" class="${state.form.readiness_to_train === 'yes' ? 'active' : ''}">是</button>
              <button data-seg="readiness_to_train" data-val="uncertain" class="${state.form.readiness_to_train === 'uncertain' ? 'active' : ''}">不确定</button>
              <button data-seg="readiness_to_train" data-val="no" class="${state.form.readiness_to_train === 'no' ? 'active' : ''}">否</button>
            </div>
          </div>
          <div class="field" style="margin-top:12px"><label>疼痛趋势（过去 48h） *</label>
            <div class="seg">
              <button data-seg="pain_trend" data-val="none" class="${state.form.pain_trend === 'none' ? 'active' : ''}">无</button>
              <button data-seg="pain_trend" data-val="mild" class="${state.form.pain_trend === 'mild' ? 'active' : ''}">轻微</button>
              <button data-seg="pain_trend" data-val="recovering" class="${state.form.pain_trend === 'recovering' ? 'active' : ''}">恢复中</button>
              <button data-seg="pain_trend" data-val="worse" class="${state.form.pain_trend === 'worse' ? 'active' : ''}">加重</button>
            </div>
          </div>
        </section>
        <section class="card">
          <div class="h2">其他（可选）</div>
          <div class="grid two" style="margin-top:12px">
            <div class="field"><label>睡眠质量（1-5）</label><input name="sleep_quality" type="number" min="1" max="5" value="${state.form.sleep_quality}" /></div>
            <div class="field"><label>疲劳程度（1-5）</label><input name="fatigue_level" type="number" min="1" max="5" value="${state.form.fatigue_level}" /></div>
            <div class="field"><label>肌肉酸痛（1-5）</label><input name="muscle_soreness" type="number" min="1" max="5" value="${state.form.muscle_soreness}" /></div>
            <div class="field"><label>心情状态（1-5）</label><input name="mood_state" type="number" min="1" max="5" value="${state.form.mood_state}" /></div>
          </div>
        </section>`,
      actions: [
        { label: '提交身体检查', tone: 'primary', onClick: () => submitCheckin() },
        { label: '取消', tone: 'ghost', onClick: () => closeDrawer() },
      ],
    });
  }

  function submitCheckin() {
    const r = String(state.form.readiness_to_train || '');
    const p = String(state.form.pain_trend || '');
    if (!r || !p) return toast('请先完成必填项（准备度 / 疼痛趋势）。');
    if (r === 'no') {
      return openModal('准备度偏低', 'readiness_to_train=no。建议改期或跳过。', [
        { label: '改期', tone: 'primary', onClick: () => { closeDrawer(); toast('已改期（原型模拟）'); } },
        { label: '跳过', tone: 'danger', onClick: () => { closeDrawer(); toast('已跳过（原型模拟）'); } },
        { label: '仍要继续', tone: 'ghost', onClick: () => { closeDrawer(); toast('继续训练（需二次确认，原型模拟）'); } },
      ]);
    }
    closeDrawer();
    toast('身体检查已提交');
  }

  function openFeedback() {
    openDrawer({
      title: '训练后反馈',
      sub: 'Post-run Feedback',
      body: `
        <section class="card"><div class="h2">训练后反馈</div><div class="p" style="margin-top:8px">你的反馈会影响未来 3 天的训练安排。</div></section>
        <section class="card">
          <div class="field"><label>是否完成训练？ *</label>
            <div class="seg">
              <button data-seg="completed" data-val="true" class="${state.form.completed === 'true' ? 'active' : ''}">是</button>
              <button data-seg="completed" data-val="false" class="${state.form.completed === 'false' ? 'active' : ''}">否</button>
            </div>
          </div>
          <div class="field" style="margin-top:12px"><label>偏离原因（未完成时必填）</label>
            <select name="deviation_reason">
              <option value="">请选择</option>
              ${['伤病/不适', '时间不足', '天气原因', '动力不足', '其他'].map((o) => `<option value="${o}" ${state.form.deviation_reason === o ? 'selected' : ''}>${o}</option>`).join('')}
            </select>
          </div>
          <div class="field" style="margin-top:12px"><label>备注（可选）</label>
            <textarea name="notes" placeholder="例如：腿部酸痛、心率偏高、天气闷热…">${String(state.form.notes || '')}</textarea>
          </div>
        </section>`,
      actions: [
        { label: '提交训练反馈', tone: 'primary', onClick: () => submitFeedback() },
        { label: '取消', tone: 'ghost', onClick: () => closeDrawer() },
      ],
    });
  }

  function submitFeedback() {
    const c = String(state.form.completed || '');
    if (!c) return toast('请先确认是否完成训练。');
    if (c === 'false' && !String(state.form.deviation_reason || '').trim()) return toast('未完成训练时必须选择偏离原因。');
    closeDrawer();
    toast('训练反馈已提交');
    openAdjustment(false);
  }

  function openAdjustment(readOnly) {
    const c = String(state.form.completed || '');
    const r = String(state.form.readiness_to_train || '');
    const p = String(state.form.pain_trend || '');
    const propose = c === 'false' || r === 'no' || p === 'worse';
    const action = propose ? 'DOWNGRADE（降级）' : 'KEEP（保持原计划）';
    const reasonList = [
      c === 'false' ? `未完成训练：deviation_reason=${state.form.deviation_reason || '（未填）'}` : null,
      r === 'no' ? 'readiness_to_train=no' : null,
      p ? `疼痛趋势：${p}` : null,
    ].filter(Boolean);

    openDrawer({
      title: '近端微调',
      sub: 'Adjustment Decision',
      body: `
        <section class="card"><div class="h2">近端训练微调审查</div><div class="p" style="margin-top:8px">范围：未来 3 天 · 动作：${action}</div></section>
        <section class="card"><div class="h2">调整原因</div>
          ${reasonList.length ? `<ul class="list" style="margin-top:10px">${reasonList.map((x) => `<li>${x}</li>`).join('')}</ul>` : `<div class="p" style="margin-top:10px">未发现需要调整的明显信号。</div>`}
        </section>
        <section class="card">
          <div class="h2">原计划 vs 调整后（未来 3 天）</div>
          <div class="split" style="margin-top:12px">
            <div class="card" style="padding:12px"><div class="h2">原计划</div><ul class="list" style="margin-top:10px"><li>Tue：间歇跑 8×400m</li><li>Thu：阈值跑 20min</li><li>Sat：LSD 12km</li></ul></div>
            <div class="card" style="padding:12px"><div class="h2">调整后</div>
              ${propose ? `<ul class="list" style="margin-top:10px"><li>Tue：恢复跑 30min 轻松</li><li>Thu：休息/交叉训练</li><li>Sat：LSD 缩短为 8km 轻松</li></ul>` : `<div class="p" style="margin-top:10px">保持原计划，无需调整。</div>`}
            </div>
          </div>
        </section>`,
      actions: readOnly
        ? [{ label: '关闭', tone: 'primary', onClick: () => closeDrawer() }]
        : [
          { label: '确认调整', tone: propose ? 'primary' : 'ghost', onClick: () => { state.today.adjustmentApplied = propose; save(); closeDrawer(); toast(propose ? '已执行微调' : '无需调整'); render(); } },
          { label: '保持原计划', tone: 'ghost', onClick: () => { state.today.adjustmentApplied = false; save(); closeDrawer(); toast('保持原计划'); render(); } },
        ],
    });
  }

  function renderMenu() {
    const items = [
      { id: 'setup-0', label: '计划设置（输入）', run: () => { state.route = 'setup'; state.step = 0; save(); closeSheet(); render(); } },
      { id: 'setup-1', label: '计划设置（风险 Gate）', run: () => { state.route = 'setup'; enterGate(); closeSheet(); } },
      { id: 'setup-2', label: '计划设置（草案审查）', run: () => { state.route = 'setup'; state.step = 2; save(); closeSheet(); render(); } },
      { id: 'today', label: '今日训练', run: () => { state.route = 'today'; save(); closeSheet(); render(); } },
    ];
    els.sheetMeta.textContent = `SRC002 · ${state.route === 'setup' ? `计划设置 ${state.step + 1}/3` : '今日训练'}`;
    els.journey.innerHTML = items.map((it) => `<button class="btn ghost" data-jump="${it.id}">${it.label}</button>`).join('');
    els.debug.innerHTML = [
      `<button class="btn ghost" data-debug="reset-today">重置今日训练状态</button>`,
      `<button class="btn ghost" data-debug="force-pass">Gate=pass</button>`,
      `<button class="btn ghost" data-debug="force-degraded">Gate=degraded</button>`,
      `<button class="btn ghost" data-debug="force-blocked">Gate=blocked</button>`,
    ].join('');

    els.journey.querySelectorAll('button[data-jump]').forEach((btn) => {
      const item = items.find((it) => it.id === btn.getAttribute('data-jump'));
      item && btn.addEventListener('click', item.run);
    });
    els.debug.querySelectorAll('button[data-debug]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const k = btn.getAttribute('data-debug');
        if (k === 'reset-today') {
          state.today.status = 'planned';
          state.today.adjustmentApplied = false;
          save();
          toast('已重置今日训练状态');
          closeSheet();
          render();
          return;
        }
        if (k === 'force-pass') state.gate.status = 'pass';
        if (k === 'force-degraded') state.gate.status = 'degraded';
        if (k === 'force-blocked') state.gate.status = 'blocked';
        save();
        closeSheet();
        render();
      });
    });
  }

  function render() {
    els.navBack.disabled = (state.route === 'setup' && state.step === 0) || state.route === 'today';
    els.navSub.textContent = state.route === 'setup'
      ? `计划设置 · ${state.step + 1}/3`
      : `日常训练闭环 · ${state.today.status === 'planned' ? '未开始' : state.today.status === 'in_progress' ? '进行中' : '已完成'}`;

    if (state.route === 'setup') {
      els.screen.innerHTML = state.step === 0 ? renderInput() : state.step === 1 ? renderGate() : renderDraft();
    } else {
      els.screen.innerHTML = renderToday();
    }

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
        if (act === 'device') toast('设备绑定：后置（原型模拟）');
        if (act === 'sync') toast('历史同步：后置（原型模拟）');
        if (act === 'toggle-week') { state.plan.weekExpanded = !state.plan.weekExpanded; save(); render(); }
        if (act === 'toggle-today-week') { state.today.weekExpanded = !state.today.weekExpanded; save(); render(); }
      });
    });

    renderMenu();
  }

  // nav bindings
  els.navBack.addEventListener('click', () => {
    if (state.route === 'today') return;
    if (state.route === 'setup') {
      if (state.step > 0) setSetupStep(state.step - 1);
      return;
    }
    state.route = 'setup';
    state.step = 2;
    save();
    render();
  });
  els.navMenu.addEventListener('click', openSheet);
  els.sheetScrim.addEventListener('click', closeSheet);
  els.sheetClose.addEventListener('click', closeSheet);
  els.modalScrim.addEventListener('click', closeModal);
  els.drawerScrim.addEventListener('click', closeDrawer);
  els.drawerClose.addEventListener('click', closeDrawer);
  els.reset.addEventListener('click', () => {
    state = defaults();
    save();
    closeSheet();
    closeDrawer();
    closeModal();
    toast('Prototype state reset');
    render();
  });

  closeSheet();
  closeModal();
  closeDrawer();

  bindDelegates(els.screen);
  bindDelegates(els.drawerBody);

  render();
})();
