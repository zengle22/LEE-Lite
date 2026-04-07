const DEFAULT_EXPERIENCE = {
  feat_ref: "PRD-001",
  feat_title: "Run Master Coach",
  journey_structural_spec_ref: "journey-ux-ascii.md",
  ui_shell_snapshot_ref: "ui-shell-spec.md",
  ui_shell_version: "1.0.0",
  source_refs: [
    "PRD-001 injury-first / PB-second shell candidate",
    "journey-ux-ascii.md",
    "ui-shell-spec.md",
  ],
  pages: [
    {
      page_id: "setup-wizard",
      title: "Setup Wizard",
      page_goal: "Capture the runner baseline before any plan is activated.",
      page_type_family: "form",
      snapshot_items: [
        "Goal race: half marathon PB in 12 weeks",
        "Current weekly volume: 28-35 km",
        "Risk sensitivity: right knee and calf history",
        "Availability: 4 run slots + 2 strength slots",
      ],
      decision_options: [
        { title: "Activate conservative base", body: "Recommended if baseline is complete and injury history is clear.", tone: "recommended" },
        { title: "Revise baseline", body: "Return to training history or injury inputs before activation.", tone: "caution" },
      ],
      main_path: [
        "Set race goal and event date.",
        "Confirm weekly volume and training history.",
        "Record injury-sensitive zones and constraints.",
        "Activate the first cycle.",
      ],
      branch_paths: [
        { title: "Missing baseline", steps: ["Ask for required fields", "Keep activation blocked"] },
        { title: "Risk-sensitive runner", steps: ["Lower default load", "Flag guardrails"] },
      ],
      states: [
        { name: "baseline_pending", ui_behavior: "The profile is incomplete. Keep the user in setup until the baseline is trustworthy." },
        { name: "ready_to_activate", ui_behavior: "The baseline is complete. Preview the first week and allow activation." },
      ],
      page_sections: ["Goal race", "Current level", "Injury history", "Weekly availability"],
      completion_definition: "User can activate a cycle with a complete and safe baseline.",
      ascii_wireframe: "[top bar]\n[stepper]\n[goal race]\n[training history]\n[injury history]\n[availability]\n[sticky cta]",
      buttons: [
        { label: "Back", action: "page_back", tone: "ghost" },
        { label: "Activate cycle", action: "primary", tone: "primary" },
      ],
    },
    {
      page_id: "today-home",
      title: "Today Home",
      page_goal: "Answer what the runner should do today and why.",
      page_type_family: "dashboard",
      snapshot_items: [
        "Assigned session: aerobic intervals 8 km",
        "Block focus: maintain continuity while nudging threshold",
        "Readiness trend: stable but calf tightness noted yesterday",
        "Coach note: pre-run check required before green-lighting intensity",
      ],
      decision_options: [
        { title: "Start pre-run check", body: "Recommended default path before any quality session begins.", tone: "recommended" },
        { title: "Open plan review", body: "Use only if the runner needs cycle context, not as the first daily action.", tone: "caution" },
      ],
      main_path: [
        "Review the assigned session.",
        "Check readiness and risk trend.",
        "Start pre-run check or inspect the adjusted plan.",
      ],
      branch_paths: [
        { title: "Risk rising", steps: ["Show caution banner", "Offer easier option"] },
      ],
      states: [
        { name: "ready", ui_behavior: "The day is healthy. Keep the interface calm and point to the pre-run check." },
        { name: "degraded", ui_behavior: "Readiness dipped. Surface the lighter option before the original workout." },
      ],
      page_sections: ["Today card", "Readiness banner", "Risk radar", "Plan capsule"],
      completion_definition: "User understands the safest next action for today.",
      ascii_wireframe: "[top bar]\n[today card]\n[risk banner]\n[plan capsule]\n[coach rationale]\n[cta dock]",
      buttons: [
        { label: "View plan", action: "skip", tone: "ghost" },
        { label: "Start pre-run check", action: "primary", tone: "primary" },
      ],
    },
    {
      page_id: "pre-run-decision",
      title: "Pre-run Decision",
      page_goal: "Turn readiness signals into one clear training recommendation.",
      page_type_family: "review",
      snapshot_items: [
        "Sleep: 6h 10m and broken",
        "Fatigue: moderate after last quality session",
        "Pain: calf tightness 3/10 while walking",
        "Confidence: wants to train but accepts downgrade if risk rises",
      ],
      decision_options: [
        { title: "Follow plan", body: "Only valid when readiness stays green and pain is absent.", tone: "recommended" },
        { title: "Switch to easier session", body: "Preferred downgrade when fatigue or soreness is elevated.", tone: "caution" },
        { title: "Take recovery", body: "Use when the shell moves into blocked / stop territory.", tone: "stop" },
      ],
      main_path: [
        "Collect sleep, soreness, fatigue, and confidence.",
        "Judge risk and today's recommendation.",
        "Recommend plan, downgrade, swap, or rest.",
      ],
      branch_paths: [
        { title: "Blocked", steps: ["Recommend no run", "Route to recovery guidance"] },
        { title: "Degraded", steps: ["Swap session", "Explain why the load changed"] },
      ],
      states: [
        { name: "ready", ui_behavior: "Proceed with the planned workout and keep reassurance lightweight." },
        { name: "degraded", ui_behavior: "Reduce the session load or substitute an easier session." },
        { name: "blocked", ui_behavior: "Do not run today. Lead with recovery guidance." },
      ],
      page_sections: ["Readiness inputs", "Risk verdict", "Adjusted session", "Reasoning"],
      completion_definition: "User leaves with one explicit and safe decision.",
      ascii_wireframe: "[header]\n[input stack]\n[risk verdict]\n[adjusted workout]\n[why]\n[sticky cta]",
      buttons: [
        { label: "Reset", action: "reset", tone: "ghost" },
        { label: "Use easier option", action: "skip", tone: "ghost" },
        { label: "Accept recommendation", action: "primary", tone: "primary" },
      ],
    },
    {
      page_id: "plan-review",
      title: "Plan Review",
      page_goal: "Show how today's work fits inside the current cycle without breaking the daily shell.",
      page_type_family: "detail",
      snapshot_items: [
        "Cycle: week 4 of 12",
        "Key session: threshold intervals on Wednesday",
        "Long run: controlled aerobic build on Sunday",
        "Risk rule: maintain continuity over peak intensity",
      ],
      decision_options: [
        { title: "Return to daily home", body: "Preferred path once the runner understands today's place in the cycle.", tone: "recommended" },
      ],
      main_path: [
        "Inspect the current block focus.",
        "Review the week layout and spacing.",
        "Return to home with clearer context for the next run.",
      ],
      branch_paths: [
        { title: "Race approaching", steps: ["Shift to taper", "Highlight execution reminders"] },
      ],
      states: [
        { name: "pass", ui_behavior: "The plan is stable. Keep this surface supportive and secondary to today's execution." },
      ],
      page_sections: ["Cycle overview", "Week structure", "Key workout", "Race context"],
      completion_definition: "User sees how today's recommendation fits the larger cycle.",
      ascii_wireframe: "[header]\n[cycle summary]\n[week cards]\n[key workout]\n[back to home]",
      buttons: [
        { label: "Back to home", action: "page_back", tone: "ghost" },
        { label: "Pin this week", action: "primary", tone: "primary" },
      ],
    },
    {
      page_id: "post-run-feedback",
      title: "Post-run Feedback",
      page_goal: "Capture completion, pain, and effort quickly so tomorrow can adapt.",
      page_type_family: "review",
      snapshot_items: [
        "Completion: finished 7.2 km of planned 8 km",
        "RPE: 7/10",
        "Pain: calf tightness increased to 4/10 late in the run",
        "Tomorrow: likely downgrade to easy recovery",
      ],
      decision_options: [
        { title: "Save review", body: "Recommended path for updating tomorrow's load.", tone: "recommended" },
        { title: "Flag pain for coach review", body: "Use when symptoms are new or clearly trending worse.", tone: "caution" },
      ],
      main_path: [
        "Log completion and deviations.",
        "Record effort and pain.",
        "Preview recovery advice and tomorrow's adjustment.",
      ],
      branch_paths: [
        { title: "Pain logged", steps: ["Raise risk flag", "Reduce next load"] },
      ],
      states: [
        { name: "completed", ui_behavior: "Training is logged. Keep the follow-up recovery-oriented." },
        { name: "warning", ui_behavior: "Pain or fatigue is elevated. Preview a downgraded next step." },
      ],
      page_sections: ["Completion", "Pain and effort", "Coach reflection", "Tomorrow preview"],
      completion_definition: "User finishes the review quickly and gets a clear follow-up.",
      ascii_wireframe: "[sheet header]\n[completion]\n[pain effort]\n[next-day advice]\n[save]",
      buttons: [
        { label: "Skip details", action: "skip", tone: "ghost" },
        { label: "Save review", action: "primary", tone: "primary" },
      ],
    },
  ],
};

const STAGES = [
  { key: "setup_wizard", label: "Setup", mode: "setup" },
  { key: "today_home", label: "Today", mode: "home" },
  { key: "pre_run_decision", label: "Decision", mode: "decision" },
  { key: "plan_review", label: "Plan", mode: "plan" },
  { key: "post_run_feedback", label: "Review", mode: "review" },
];

function stateTone(name) {
  const key = String(name || "").toLowerCase();
  if (key.includes("error") || key.includes("blocked") || key.includes("failed")) return "danger";
  if (key.includes("degraded") || key.includes("retry") || key.includes("warning")) return "warn";
  return "ready";
}

function inferMode(page, index) {
  const haystack = `${page.page_id || ""} ${page.title || ""} ${page.page_goal || ""}`.toLowerCase();
  if (haystack.includes("setup") || haystack.includes("profile") || haystack.includes("goal") || haystack.includes("onboard")) return "setup";
  if (haystack.includes("today") || haystack.includes("home") || haystack.includes("daily")) return "home";
  if (haystack.includes("pre-run") || haystack.includes("readiness") || haystack.includes("decision") || haystack.includes("check")) return "decision";
  if (haystack.includes("plan") || haystack.includes("cycle") || haystack.includes("week")) return "plan";
  if (haystack.includes("review") || haystack.includes("post-run") || haystack.includes("feedback")) return "review";
  return (STAGES[index] || STAGES[0]).mode;
}

function normalizeData(raw) {
  const base = raw && Array.isArray(raw.pages) && raw.pages.length ? raw : DEFAULT_EXPERIENCE;
  return {
    feat_ref: base.feat_ref || DEFAULT_EXPERIENCE.feat_ref,
    feat_title: base.feat_title || DEFAULT_EXPERIENCE.feat_title,
    journey_ref: base.journey_structural_spec_ref || base.journey_ascii_ref || DEFAULT_EXPERIENCE.journey_structural_spec_ref,
    shell_ref: base.ui_shell_snapshot_ref || base.ui_shell_ref || DEFAULT_EXPERIENCE.ui_shell_snapshot_ref,
    ui_shell_version: base.ui_shell_version || DEFAULT_EXPERIENCE.ui_shell_version,
    source_refs: Array.isArray(base.source_refs) && base.source_refs.length ? base.source_refs : DEFAULT_EXPERIENCE.source_refs,
    pages: Array.isArray(base.pages) && base.pages.length ? base.pages : DEFAULT_EXPERIENCE.pages,
  };
}

async function loadData() {
  if (window.__LEE_PROTO_DATA__) return window.__LEE_PROTO_DATA__;
  try {
    const response = await fetch("mock-data.json");
    if (response.ok) return await response.json();
  } catch (error) {
    console.warn("mock-data.json unavailable, using default shell demo.", error);
  }
  return DEFAULT_EXPERIENCE;
}

function currentStateName(page, stateByPage) {
  return stateByPage[page.page_id] || ((page.states || [])[0] || {}).name || "initial";
}

function targetStateName(page, action) {
  const states = page.states || [];
  const lookup = {
    primary: ["ready", "pass", "completed", "success", "activate"],
    skip: ["degraded", "warning", "retry", "skip"],
    error: ["blocked", "error", "failed"],
    reset: [],
  };
  if (action === "reset") return (states[0] || {}).name || "initial";
  for (const state of states) {
    const name = String(state.name || "").toLowerCase();
    if ((lookup[action] || []).some((token) => name.includes(token))) {
      return state.name;
    }
  }
  return (states[Math.min(1, Math.max(states.length - 1, 0))] || states[0] || {}).name || "initial";
}

function stateLabel(stateName, mode) {
  const tone = stateTone(stateName);
  if (mode === "setup") return tone === "danger" ? "Complete baseline before activation." : "Build a trustworthy baseline.";
  if (mode === "home") return tone === "warn" ? "Daily load should be reduced." : "Return anchor for today's decision.";
  if (mode === "decision") return tone === "danger" ? "Recommend no run or recovery." : "Turn readiness into one clear choice.";
  if (mode === "plan") return "Keep plan context secondary to today's execution.";
  return "Capture feedback fast so tomorrow can adapt.";
}

function coachIntro(page, stateObj, mode) {
  const label = {
    setup: "Setup shell",
    home: "Daily home shell",
    decision: "Pre-run shell",
    plan: "Plan shell",
    review: "Review shell",
  }[mode];
  const body = stateObj.ui_behavior || page.completion_definition || page.page_goal || "Keep the next action obvious.";
  return { label, body };
}

function containerHint(mode) {
  return {
    setup: "page + sticky CTA",
    home: "page + inline banner",
    decision: "page or bottom_sheet",
    plan: "page",
    review: "bottom_sheet or page",
  }[mode];
}

function actionRule(mode, tone) {
  if (mode === "setup") return "Use one forward CTA per step. Back or exit must remain subordinate.";
  if (mode === "home") return "Primary CTA answers what to do today, not where to navigate.";
  if (mode === "decision") return tone === "danger"
    ? "Downgrade the CTA to recovery or rest guidance."
    : "Recommend exactly one of plan, downgrade, swap, or rest.";
  if (mode === "plan") return "Keep plan actions supportive so they do not outrank today's decision.";
  return "Save feedback fast; optional detail stays secondary.";
}

function focusItems(page, stateName, mode) {
  const items = [];
  items.push(`Mode: ${mode}`);
  if (page.page_type_family) items.push(`Family: ${page.page_type_family}`);
  if (stateName) items.push(`State: ${stateName}`);
  (page.page_sections || []).slice(0, 2).forEach((section) => items.push(section));
  return items.slice(0, 4);
}

function snapshotTitle(mode) {
  return {
    setup: "Baseline Snapshot",
    home: "Today's Session Snapshot",
    decision: "Readiness Inputs",
    plan: "Cycle Snapshot",
    review: "Review Snapshot",
  }[mode];
}

function snapshotMeta(mode) {
  return {
    setup: "Activation context",
    home: "Coach-assigned workload",
    decision: "Runner-reported signals",
    plan: "Week and cycle context",
    review: "Training completion capture",
  }[mode];
}

function defaultSnapshot(mode, stateName) {
  if (mode === "setup") {
    return [
      "Goal race and target date are required.",
      "Training history must be credible enough to seed the first cycle.",
      "Injury-sensitive zones drive the initial load ceiling.",
      "Weekly time budget constrains session placement.",
    ];
  }
  if (mode === "home") {
    return [
      "Today's workout and block focus should be visible above the fold.",
      "Readiness trend should summarize yesterday's review.",
      "Risk banner should stay quiet unless risk is trending up.",
      `Current state: ${stateName || "ready"}.`,
    ];
  }
  if (mode === "decision") {
    return [
      "Sleep, soreness, fatigue, and confidence should be collected together.",
      "Pain and readiness must be judged before any ambitious workout path.",
      "The shell should make one recommendation, not a menu of equal choices.",
      `Current state: ${stateName || "ready"}.`,
    ];
  }
  if (mode === "plan") {
    return [
      "Cycle context should explain why today's session exists.",
      "Key workout spacing matters more than decorative schedule detail.",
      "Taper and recovery rules belong in the same planning frame.",
      `Current state: ${stateName || "pass"}.`,
    ];
  }
  return [
    "Completion, RPE, and pain should be fast to capture.",
    "Feedback should shape tomorrow's recommendation.",
    "Pain trend is more important than motivational copy.",
    `Current state: ${stateName || "completed"}.`,
  ];
}

function decisionOptionsTitle(mode) {
  return mode === "decision" ? "Recommended Paths" : "Action Posture";
}

function decisionOptionsMeta(mode) {
  return mode === "decision" ? "Primary + downgrade" : "Shell-guided choices";
}

function defaultDecisionOptions(mode, tone) {
  if (mode === "setup") {
    return [
      { title: "Activate cycle", body: "Proceed only when baseline and injury inputs are complete.", tone: "recommended" },
      { title: "Fix missing data", body: "Stay in setup if the shell cannot trust the baseline.", tone: "caution" },
    ];
  }
  if (mode === "home") {
    return [
      { title: "Start pre-run check", body: "Default daily CTA before intensity work begins.", tone: "recommended" },
      { title: "Open plan review", body: "Secondary path for context, not the first daily action.", tone: "caution" },
    ];
  }
  if (mode === "decision") {
    return [
      { title: tone === "danger" ? "Take recovery" : "Accept recommendation", body: "Keep exactly one dominant next action.", tone: tone === "danger" ? "stop" : "recommended" },
      { title: "Use easier option", body: "Preferred downgrade when the runner is trainable but not fully green.", tone: "caution" },
    ];
  }
  if (mode === "plan") {
    return [
      { title: "Return to daily home", body: "Plan review supports the loop; it does not replace it.", tone: "recommended" },
    ];
  }
  return [
    { title: "Save review", body: "Primary action for updating tomorrow's coaching decision.", tone: "recommended" },
    { title: "Flag pain", body: "Raise a caution path when symptoms trend up.", tone: "caution" },
  ];
}

function decisionOptionsMarkup(options) {
  return options
    .map((option) => `<div class="decision-option ${option.tone || "recommended"}"><strong>${option.title}</strong><p>${option.body}</p></div>`)
    .join("");
}

function decisionCards(page, stateName, stateObj, mode) {
  const tone = stateTone(stateName);
  const cards = [
    {
      title: "Current recommendation",
      body: stateObj.ui_behavior || page.page_goal || "Keep the safest next action visible.",
      tone,
    },
    {
      title: "Container family",
      body: containerHint(mode),
      tone: "ready",
    },
    {
      title: "CTA posture",
      body: actionRule(mode, tone),
      tone: tone === "danger" ? "danger" : "ready",
    },
  ];
  return cards;
}

function branchMarkup(branches) {
  if (!branches.length) {
    return "<div class=\"branch-item\"><strong>No explicit branch</strong><p>Keep a degrade and retry route available for safety.</p></div>";
  }
  return branches
    .map((branch) => {
      const steps = Array.isArray(branch.steps) ? branch.steps.join(" -> ") : "No recorded steps.";
      return `<div class="branch-item"><strong>${branch.title || "Branch"}</strong><p>${steps}</p></div>`;
    })
    .join("");
}

function stageTabsMarkup(activeMode) {
  return STAGES.map((stage) => `<button type="button" class="stage-tab ${stage.mode === activeMode ? "is-active" : ""}" data-mode="${stage.mode}">${stage.label}</button>`).join("");
}

function journeyMarkup(pages, activeIndex) {
  return pages
    .map((page, index) => {
      const active = index === activeIndex ? "active" : "";
      const meta = inferMode(page, index);
      return `<li><a href="#" class="journey-link ${active}" data-page="${index}">${page.title || `Page ${index + 1}`}<span>${meta}</span></a></li>`;
    })
    .join("");
}

function statePillsMarkup(states, activeName) {
  return states
    .map((state, index) => {
      const active = state.name === activeName ? "is-active" : "";
      const tone = stateTone(state.name) === "ready" ? "" : stateTone(state.name);
      const className = ["pill", active, tone].filter(Boolean).join(" ");
      return `<button type="button" class="${className}" data-state="${index}">${state.name}</button>`;
    })
    .join("");
}

async function boot() {
  const data = normalizeData(await loadData());
  let pageIndex = 0;
  const stateByPage = {};

  const els = {
    featTitle: document.getElementById("feat-title"),
    featRef: document.getElementById("feat-ref"),
    journeyNav: document.getElementById("journey-nav"),
    statePills: document.getElementById("state-pills"),
    sourceRefs: document.getElementById("source-refs"),
    pageTitle: document.getElementById("page-title"),
    pageGoal: document.getElementById("page-goal"),
    shellStage: document.getElementById("shell-stage"),
    stageTabs: document.getElementById("stage-tabs"),
    readinessStrip: document.getElementById("readiness-strip"),
    screenTitle: document.getElementById("screen-title"),
    containerHint: document.getElementById("container-hint"),
    coachCopy: document.getElementById("coach-copy"),
    planFocus: document.getElementById("plan-focus"),
    snapshotTitle: document.getElementById("snapshot-title"),
    snapshotMeta: document.getElementById("snapshot-meta"),
    trainingSnapshot: document.getElementById("training-snapshot"),
    decisionOptionsTitle: document.getElementById("decision-options-title"),
    decisionOptionsMeta: document.getElementById("decision-options-meta"),
    decisionOptions: document.getElementById("decision-options"),
    stateSummary: document.getElementById("state-summary"),
    mainPath: document.getElementById("main-path"),
    pageSections: document.getElementById("page-sections"),
    wireframeLabel: document.getElementById("wireframe-label"),
    wireframe: document.getElementById("wireframe"),
    actionHint: document.getElementById("action-hint"),
    actions: document.getElementById("actions"),
    decisionSummary: document.getElementById("decision-summary"),
    branchPaths: document.getElementById("branch-paths"),
    journeyRef: document.getElementById("journey-ref"),
    shellRef: document.getElementById("shell-ref"),
  };

  function currentPage() {
    return data.pages[pageIndex];
  }

  function render() {
    const page = currentPage();
    const mode = inferMode(page, pageIndex);
    const stateName = currentStateName(page, stateByPage);
    const stateObj = (page.states || []).find((item) => item.name === stateName) || (page.states || [])[0] || {};
    const tone = stateTone(stateName);
    const intro = coachIntro(page, stateObj, mode);

    els.featTitle.textContent = data.feat_title || "Run Master Coach";
    els.featRef.textContent = `${data.feat_ref || "prototype"} · shell v${data.ui_shell_version || "1.0.0"}`;
    els.journeyNav.innerHTML = journeyMarkup(data.pages, pageIndex);
    els.statePills.innerHTML = statePillsMarkup(page.states || [], stateName);
    els.sourceRefs.innerHTML = (data.source_refs || []).map((ref) => `<li>${ref}</li>`).join("");

    els.pageTitle.textContent = page.title || "Running coach shell";
    els.pageGoal.textContent = page.page_goal || "Use a fixed shell to hold the coaching journey together.";
    els.shellStage.textContent = STAGES.find((stage) => stage.mode === mode)?.label || mode;
    els.stageTabs.innerHTML = stageTabsMarkup(mode);

    els.readinessStrip.className = `readiness-strip ${tone}`.trim();
    els.readinessStrip.innerHTML = `
      <h4>${stateName || "initial"}</h4>
      <p>${stateLabel(stateName, mode)}</p>
    `;

    els.screenTitle.textContent = page.title || "Primary screen";
    els.containerHint.textContent = containerHint(mode);
    els.coachCopy.innerHTML = `<strong>${intro.label}</strong><p>${intro.body}</p>`;
    els.planFocus.innerHTML = focusItems(page, stateName, mode).map((item) => `<span class="chip">${item}</span>`).join("");
    els.snapshotTitle.textContent = snapshotTitle(mode);
    els.snapshotMeta.textContent = snapshotMeta(mode);
    const snapshotItems = page.snapshot_items || defaultSnapshot(mode, stateName);
    els.trainingSnapshot.innerHTML = snapshotItems.map((item) => `<li>${item}</li>`).join("");
    els.decisionOptionsTitle.textContent = decisionOptionsTitle(mode);
    els.decisionOptionsMeta.textContent = decisionOptionsMeta(mode);
    const decisionOptions = page.decision_options || defaultDecisionOptions(mode, tone);
    els.decisionOptions.innerHTML = decisionOptionsMarkup(decisionOptions);

    els.stateSummary.innerHTML = `
      <div class="summary-meta">
        <span class="badge ${tone === "ready" ? "" : tone}">${stateName || "initial"}</span>
        <span>${page.completion_definition || "Keep the shell focused on the safest next action."}</span>
      </div>
      <p>${page.page_goal || stateObj.ui_behavior || "The shell should keep the coaching answer coherent across screens."}</p>
    `;

    els.mainPath.innerHTML = (page.main_path || []).map((item) => `<li>${item}</li>`).join("") || "<li>No main path recorded.</li>";
    els.pageSections.innerHTML = (page.page_sections || []).map((item) => `<li>${item}</li>`).join("") || "<li>No sections recorded.</li>";
    els.wireframeLabel.textContent = mode;
    els.wireframe.textContent = page.ascii_wireframe || "No ASCII wireframe available.";

    els.actionHint.textContent = `Journey: ${data.journey_ref} | Shell: ${data.shell_ref}`;
    els.actions.innerHTML = (page.buttons || [])
      .map((button) => `<button type="button" data-action="${button.action}" data-tone="${button.tone || "primary"}">${button.label}</button>`)
      .join("");

    els.decisionSummary.innerHTML = decisionCards(page, stateName, stateObj, mode)
      .map((card) => `<div class="decision-callout ${card.tone === "ready" ? "" : card.tone}"><strong>${card.title}</strong><p>${card.body}</p></div>`)
      .join("");
    els.branchPaths.innerHTML = branchMarkup(page.branch_paths || []);
    els.journeyRef.textContent = `Journey Structural Spec: ${data.journey_ref}`;
    els.shellRef.textContent = `UI Shell Snapshot: ${data.shell_ref}`;
  }

  document.addEventListener("click", (event) => {
    const pageLink = event.target.closest("[data-page]");
    if (pageLink) {
      event.preventDefault();
      pageIndex = Number(pageLink.getAttribute("data-page"));
      render();
      return;
    }

    const stateButton = event.target.closest("[data-state]");
    if (stateButton) {
      const page = currentPage();
      const state = (page.states || [])[Number(stateButton.getAttribute("data-state"))];
      if (state && state.name) stateByPage[page.page_id] = state.name;
      render();
      return;
    }

    const stageButton = event.target.closest("[data-mode]");
    if (stageButton) {
      const targetMode = stageButton.getAttribute("data-mode");
      const targetIndex = data.pages.findIndex((page, index) => inferMode(page, index) === targetMode);
      if (targetIndex >= 0) {
        pageIndex = targetIndex;
        render();
      }
      return;
    }

    const actionButton = event.target.closest("[data-action]");
    if (!actionButton) return;
    const action = actionButton.getAttribute("data-action");
    if (action === "page_next" && pageIndex < data.pages.length - 1) {
      pageIndex += 1;
      render();
      return;
    }
    if (action === "page_back" && pageIndex > 0) {
      pageIndex -= 1;
      render();
      return;
    }
    const page = currentPage();
    stateByPage[page.page_id] = targetStateName(page, action);
    render();
  });

  render();
}

boot();
