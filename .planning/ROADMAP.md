# Roadmap: v2.2 双链执行闭环

**Created:** 2026-04-24
**Milestone:** v2.2
**Granularity:** Standard (3 phases)
**Total Requirements:** 17 (15 active + 2 integration test phases that span)

---

## Phases

- [x] **Phase 17: 双链统一入口 + spec 桥接跑通** — 废弃 TESTSET，统一入口 Skill 编排，spec adapter 桥接，ll-qa-test-run 用户入口
- [ ] **Phase 18: 实施轴 P0 模块** — run_manifest_gen, scenario_spec_compile, state_machine_executor 3状态模型
- [ ] **Phase 19: 验收闭环** — independent_verifier, settlement 集成, gate-evaluate 集成

---

## Phase Details

### Phase 17: 双链统一入口 + spec 桥接跑通 ✓ COMPLETE

**Goal:** 构建需求轴统一入口 Skill（ll-qa-api-from-feat, ll-qa-e2e-from-proto），废弃 TESTSET 策略层，补齐 SPEC_ADAPTER_COMPAT 桥接，打通 spec → 实施的完整路径，ll-qa-test-run 用户入口就绪。

**Depends on:** Phase 16 (v2.1 complete — schema/enum_guard/governance_validator 已交付)

**Requirements:** ENTRY-01, ENTRY-02, ENTRY-03, ENTRY-04, BRIDGE-01, BRIDGE-02, BRIDGE-03, BRIDGE-04, BRIDGE-05, BRIDGE-06, BRIDGE-07, BRIDGE-08, ENV-01, ENV-02, TEST-01

**Success Criteria** (what must be TRUE):
1. `ll-qa-api-from-feat` 执行后产出 api-test-plan, api-manifest, api-spec 三段产物，含 acceptance → capability 追溯表
2. `ll-qa-e2e-from-proto` 执行后产出 e2e-plan, e2e-manifest, e2e-spec，含 acceptance → journey 追溯表
3. `ll-qa-feat-to-testset` 已从 ll.contract.yaml 移除，ADR-053 §2.1 废弃声明可见
4. `spec_adapter.py api` 对 api-test-spec/*.md 输出 SPEC_ADAPTER_COMPAT YAML，含 `_source_coverage_id`
5. `spec_adapter.py e2e` 对 e2e-journey-spec/*.md 输出 SPEC_ADAPTER_COMPAT YAML，含 `_source_coverage_id` + `_e2e_extension`，target_format 字段有效
6. `test_orchestrator.py` 线性编排 env → adapter → exec → manifest update，StepResult 数据正确传递并更新 manifest
7. `ll-qa-test-run --app-url X --api-url Y --chain api` 端到端跑通 manifest 更新
8. `ll-qa-test-run --resume` 重跑失败用例正确执行

**Plans:** 4/4 ✓ Complete
- [x] 17-01: ll-qa-api-from-feat + ll-qa-e2e-from-proto Skill 创建 + ll-qa-feat-to-testset 废弃
- [x] 17-02: cli/lib/contracts.py + spec_adapter.py + environment_provision.py
- [x] 17-03: test_orchestrator.py + SPEC_ADAPTER_COMPAT 分支 + ll-qa-test-run Skill + CLI 注册
- [x] 17-04: 集成测试（24 tests passed）

**UI hint:** no

---

### Phase 18: 实施轴 P0 模块

**Goal:** 交付实施轴 P0 组件：run-manifest 生成、scenario spec 编译、3-state 状态机执行器，E2E chain 端到端测试。

**Depends on:** Phase 17 (orchestrator + spec adapter 就绪)

**Requirements:** EXEC-01, EXEC-02, EXEC-03, TEST-02, TEST-03

**Success Criteria** (what must be TRUE):
1. `run_manifest_gen.py` 每次执行生成 run-manifest.yaml，含 git sha / frontend build / backend build / base_url / browser / accounts 字段
2. `scenario_spec_compile.py` 将 e2e spec 编译为 scenario spec，A 层断言完整，B 层有 fallback，C 层标记 `C_MISSING`
3. `state_machine_executor.py` 3-state 模型（SETUP → EXECUTE → VERIFY → COLLECT → DONE）正确流转，非 DONE 失败进入 COLLECT
4. `qa test-run --proto-ref XXX --app-url http://localhost:3000 --api-url http://localhost:8000` E2E chain 端到端跑通
5. `--resume` 从失败的 step 继续执行，不重复已完成步骤

**Plans:** 4 plans
- [ ] 18-01-PLAN.md — run_manifest_gen.py + unit tests (Wave 1, EXEC-01)
- [ ] 18-02-PLAN.md — scenario_spec_compile.py + unit tests (Wave 1, EXEC-02)
- [ ] 18-03-PLAN.md — state_machine_executor.py + unit tests (Wave 1, EXEC-03, depends on 18-01, 18-02)
- [ ] 18-04-PLAN.md — integration tests (Wave 2, TEST-02, TEST-03, depends on 18-01, 18-02, 18-03)

**UI hint:** no

---

### Phase 19: 验收闭环

**Goal:** 交付 independent_verifier 独立验证报告 + settlement 集成 + gate-evaluate 集成，打通从 feat 到 gate 的完整闭环。

**Depends on:** Phase 17 (spec adapter + orchestrator) and Phase 18 (execution layer)

**Requirements:** GATE-01, GATE-02, GATE-03, TEST-04

**Success Criteria** (what must be TRUE):
1. `independent_verifier.py` 对执行结果产出验证报告，verdict 为 pass / conditional_pass / fail，含置信度字段
2. `ll-qa-settlement` 消费更新后的 manifest，产出 settlement report
3. `ll-qa-gate-evaluate` 基于 manifest 产出 gate 结论，与 settlement report 对齐
4. `pytest tests/cli/lib/test_spec_adapter.py tests/cli/lib/test_environment_provision.py tests/cli/lib/test_step_result.py` 单元测试套件全部通过

**Plans:** 3 plans
- [ ] 19-01-PLAN.md — independent_verifier.py + step_result.py (Wave 1)
- [ ] 19-02-PLAN.md — settlement + gate-evaluate integration (Wave 2)
- [ ] 19-03-PLAN.md — unit tests + minimal spec_adapter/environment_provision (Wave 3)

**UI hint:** no

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 17. 双链统一入口 + spec 桥接跑通 | 4/4 | ✓ Complete | 2026-04-24 |
| 18. 实施轴 P0 模块 | 0/4 | Planned | - |
| 19. 验收闭环 | 0/3 | Planned | - |

---

## Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENTRY-01 | Phase 17 | ✓ Done |
| ENTRY-02 | Phase 17 | ✓ Done |
| ENTRY-03 | Phase 17 | ✓ Done |
| ENTRY-04 | Phase 17 | ✓ Done |
| BRIDGE-01 | Phase 17 | ✓ Done |
| BRIDGE-02 | Phase 17 | ✓ Done |
| BRIDGE-03 | Phase 17 | ✓ Done |
| BRIDGE-04 | Phase 17 | ✓ Done |
| BRIDGE-05 | Phase 17 | ✓ Done |
| BRIDGE-06 | Phase 17 | ✓ Done |
| BRIDGE-07 | Phase 17 | ✓ Done |
| BRIDGE-08 | Phase 17 | ✓ Done |
| ENV-01 | Phase 17 | ✓ Done |
| ENV-02 | Phase 17 | ✓ Done | |
| EXEC-01 | Phase 18 | Planned |
| EXEC-02 | Phase 18 | Planned |
| EXEC-03 | Phase 18 | Planned |
| GATE-01 | Phase 19 | Pending |
| GATE-02 | Phase 19 | Pending |
| GATE-03 | Phase 19 | Pending |
| TEST-01 | Phase 17 | ✓ Done |
| TEST-02 | Phase 18 | Planned |
| TEST-03 | Phase 18 | Planned |
| TEST-04 | Phase 19 | Pending |

**Coverage:**
- v2.2 requirements: 24 total
- Mapped to phases: 24 (100%)
- Planned: 5 (Phase 18)
- Pending: 19

---

## Phase Dependency Map

```
Phase 16 (v2.1 done)
    │
    ▼
Phase 17 ──> Phase 18 ──> Phase 19
(spec bridge)   (exec P0)    (gate闭环)
    │               │            │
    └── ENV-01/02 ──┘            │
    └── TEST-01 (api chain)      │
                                 │
                   TEST-02, TEST-03 (E2E chain)
                                 │
                   TEST-04 (unit tests)
```

---

*Roadmap created: 2026-04-24*
*Last updated: 2026-04-24 — Phase 17 complete (14 commits, 238 tests passed)*
