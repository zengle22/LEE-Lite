# Phase 18: 实施轴 P0 模块 - Context

**Gathered:** 2026-04-24
**Status:** Ready for planning

<domain>
## Phase Boundary

交付实施轴 P0 组件：run-manifest 生成、scenario spec 编译、3-state 状态机执行器，E2E chain 端到端测试。

- `run_manifest_gen.py` — 每次执行生成唯一 run-manifest.yaml
- `scenario_spec_compile.py` — e2e spec → scenario spec，含 A/B/C 层断言
- `state_machine_executor.py` — 3-state 模型 (SETUP → EXECUTE → VERIFY → COLLECT → DONE)
- E2E chain E2E 测试 (TEST-02, TEST-03)
- `--resume` 支持

</domain>

<decisions>
## Implementation Decisions

### run-manifest Storage (EXEC-01)
- **D-01:** Dedicated `ssot/tests/.artifacts/runs/{run_id}/` directory
- **D-02:** Append-only storage — full audit trail, never delete

### scenario spec A/B/C Layers (EXEC-02)
- **D-03:** C-layer assertions marked `C_MISSING` with placeholder + evidence collection
- **D-04:** C_MISSING placeholders collect both HAR + screenshot for manual review

### State Machine Persistence (EXEC-03, TEST-03)
- **D-05:** Separate `{run_id}-state.yaml` file for state persistence (not embedded in run-manifest)
- **D-06:** Step-level tracking within journeys (per-step granularity)

### Step Execution & Error Handling
- **D-07:** Per-step within journey as atomic unit
- **D-08:** On step failure: stop journey, go to COLLECT state, collect evidence

### CLI Interface
- **D-09:** `qa test-run --proto-ref XXX --app-url http://localhost:3000 --api-url http://localhost:8000`
- **D-10:** `--resume` reads from `{run_id}-state.yaml` to continue from last completed step

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §实施轴补全 — EXEC-01, EXEC-02, EXEC-03
- `.planning/REQUIREMENTS.md` §集成测试 — TEST-02, TEST-03
- `.planning/ROADMAP.md` §Phase 18 — Phase goal and success criteria

### ADR-054 Implementation Plan
- `ssot/adr/ADR-054-实施轴接入需求轴-双链桥接与执行闭环.md` §3 Phase 2 — run-manifest-gen, scenario-spec-compile, state-machine-executor

### Prior Phase Context
- `.planning/phases/16-test-validation/16-CONTEXT.md` — pytest patterns, evidence collection
- `.planning/phases/17-*-CONTEXT.md` — orchestrator patterns (Phase 17)

### Existing Code (reference)
- `cli/lib/test_exec_runtime.py` — existing execution runtime patterns
- `cli/lib/execution_runner.py` — job state transitions
- `cli/lib/test_exec_playwright.py` — Playwright execution patterns
- `ssot/tests/.artifacts/evidence/` — existing evidence structure

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `test_exec_playwright.py` — existing Playwright execution, can be extended
- `test_exec_reporting.py` — evidence collection patterns
- `execution_runner.py` — state transition patterns

### Established Patterns
- Artifact paths: `ssot/tests/.artifacts/evidence/{run_id}/`
- run_id format: `e2e.run-{timestamp}-{random}`

### Integration Points
- Connects to Phase 17 orchestrator (`test_orchestrator.py`)
- Reads from `e2e-journey-spec/*.md` (output from Phase 17)
- Updates `e2e-coverage-manifest.yaml` with lifecycle_status

</code_context>

<specifics>
## Specific Ideas

- run_id naming: `e2e.run-{timestamp}-{random_suffix}`
- state file format: YAML with `completed_steps: [{journey_id, step_index, step_name}]`
- HAR capture: Use Playwright's built-in `page.route` interception

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 18-execution-axis*
*Context gathered: 2026-04-24*
