# Roadmap: v2.0 ADR-050/051 SSOT 语义治理升级

**Created:** 2026-04-18
**Milestone:** v2.0
**Granularity:** Standard (5 phases)
**Total Requirements:** 24 (21 active + 3 deferred to v2.1)

---

## Phase 7: FRZ 冻结层基础设施

**Goal:** 交付 FRZ 包结构定义、MSC 验证、注册表，以及 `ll-frz-manage` 新技能（冻结模式 + 查询模式）。

**Requirements:** FRZ-01, FRZ-02, FRZ-03, FRZ-04, FRZ-05, FRZ-06

**Plans:** 3 plans

- [x] 07-01-PLAN.md — FRZ 包结构定义 + MSC 5维 schema + 单元测试 (FRZ-01, FRZ-02)
- [x] 07-02-PLAN.md — 锚点 ID 注册表 + FRZ 注册表文件 + 版本追踪 (FRZ-03, EXTR-03)
- [x] 07-03-PLAN.md — ll-frz-manage 技能（冻结模式 validate + freeze + list）(FRZ-04, FRZ-05, FRZ-06)

**Success Criteria:**
1. `cli/lib/frz_schema.py` 定义 FRZPackage dataclass + MSCValidator，5维校验通过
2. 人工输入 PRD/UX/Arch 文档 → `ll frz-manage validate` 输出 MSC 报告
3. `ll frz-manage freeze --id FRZ-xxx` 将验证通过的 FRZ 写入注册表，状态 frozen
4. `ll frz-manage list` 列出所有已注册 FRZ 包及状态
5. `ssot/registry/frz-registry.yaml` 记录版本、状态、创建时间

**UI hint:** no

---

## Phase 8: FRZ->SRC 语义抽取链

**Goal:** 交付 `ll-frz-manage` 抽取模式 + SRC/EPIC/FEAT 级联抽取引擎 + 投影不变性守卫 + 漂移检测。

**Requirements:** EXTR-01, EXTR-02, EXTR-03, EXTR-04, EXTR-05

**Plans:**

- [x] 08-01 — `cli/lib/drift_detector.py`: 语义漂移检测器
- [x] 08-02 — `skills/ll-frz-manage` 抽取模式: FRZ -> SRC 抽取 + 投影守卫 + 锚点注册 + 漂移检测
- [x] 08-03 — `skills/ll-product-src-to-epic`: 改为 FRZ 抽取 EPIC 模式
- [x] 08-04 — `skills/ll-product-epic-to-feat`: 改为 FRZ 抽取 FEAT 模式

**Success Criteria:**
1. `ll frz-manage extract --frz FRZ-xxx` 输出 SRC candidate，不超出 `derived_allowed` 范围
2. `ll src-to-epic extract --src <dir> --frz FRZ-xxx` 输出 EPIC，锚点 ID 已注册
3. `ll epic-to-feat extract --epic <dir> --frz FRZ-xxx` 输出 FEAT
4. 漂移检测器比对抽取结果与 FRZ 原始语义，漂移 >0 则拦截
5. 完整链路跑通: FRZ -> SRC -> EPIC -> FEAT，所有锚点可追溯

**UI hint:** no

---

## Phase 9: 执行语义稳定 + impl-spec-test 增强

**Goal:** 在 `ll-qa-impl-spec-test` 中集成语义稳定性检查，交付静默覆盖防护。

**Requirements:** STAB-01, STAB-02, STAB-03, STAB-04

**Plans:**

- [x] 09-01 — `cli/lib/silent_override.py`: 静默覆盖检测器
- [x] 09-02 — `skills/ll-qa-impl-spec-test`: 加第9维度 `semantic_stability` (含 drift_detector 调用 + verdict 字段)
- [x] 09-03 — 所有 `ll-dev-*` 技能的 `validate_output.sh`: 加 `silent_override.py` 校验

**Success Criteria:**
1. `ll-qa-impl-spec-test` deep mode 包含 `semantic_stability` 维度，verdict 含 `semantic_drift` 字段
2. impl-spec-test 对漂移的 FEAT/TECH/UI 返回 `block` verdict
3. `ll-dev-feat-to-tech` 等技能的 `validate_output.sh` 检测静默改写 FRZ 语义的行为
4. 变更 vs 补全分类在 impl-spec-test 中正确工作 (clarification 放行，semantic_change 标记漂移)

**UI hint:** no

---

## Phase 10: 变更分级协同

**Goal:** 集成三分类到 Patch 层，交付 Minor/Major 分流处理，Major 回流 FRZ。

**Requirements:** GRADE-01, GRADE-02, GRADE-03, GRADE-04

**Plans:** 4/4 plans complete

Plans:
- [x] 10-01-PLAN.md — `skills/ll-patch-capture`: 集成三分类 (visual->Minor, interaction->Minor, semantic->Major) + GradeLevel enum (GRADE-01)
- [x] 10-02-PLAN.md — `skills/ll-experience-patch-settle`: Minor settle 逻辑 (backwrite UI/TESTSET) (GRADE-02, GRADE-04)
- [x] 10-03-PLAN.md — `skills/ll-frz-manage`: 冻结模式加 `--type revise` 参数 (Major 回流) (GRADE-03)
- [x] 10-04-PLAN.md — `skills/ll-patch-aware-context`: 注入时检测 Minor/Major 变更 (GRADE-04)

**Success Criteria:**
1. `ll-patch-capture` 捕获变更时自动分类，visual/interaction -> Minor patch
2. semantic 变更触发 Major 回流: `ll frz-manage freeze --type revise --previous-frz FRZ-xxx`
3. FRZ 注册表记录 revision chain（parent_frz_ref, reason, status）
4. Minor Patch 验证通过后 backwrite 到 UI Spec / Flow Spec
5. `ll-patch-aware-context` 注入时正确标记 Patch 类型

**UI hint:** no

---

## Phase 11: Task Pack 结构（执行循环延期到 v2.1）

**Goal:** 交付 Task Pack YAML schema + depends_on 解析。v2.0 手动按顺序执行 task。

**Requirements:** PACK-01, PACK-02, [PACK-03, PACK-04, PACK-05 deferred to v2.1]

**Plans:** 2/2 plans complete

- [x] 11-01-PLAN.md — `ssot/schemas/qa/task_pack.yaml` + `cli/lib/task_pack_schema.py` + tests (PACK-01)
- [x] 11-02-PLAN.md — `cli/lib/task_pack_resolver.py` + tests + sample Task Pack (PACK-02)

**Success Criteria:**
1. `task_pack.yaml` schema 定义 pack_id, feat_ref, tasks (task_id, type, depends_on, status, verifies)
2. `validate(pack_yaml)` 拒绝非法结构（缺少 task_id, depends_on 引用不存在等）
3. `resolve_order(pack_yaml)` 返回拓扑排序后的可执行顺序
4. 手工创建一个样例 Task Pack 并通过 schema 验证 + 依赖解析
5. PACK-03/04/05 明确标记 deferred，在 v2.1 Requirements 中追踪

**UI hint:** no

---

## Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FRZ-01 | Phase 7 | Satisfied |
| FRZ-02 | Phase 7 | Satisfied |
| FRZ-03 | Phase 7 | Satisfied |
| FRZ-04 | Phase 7 | Satisfied |
| FRZ-05 | Phase 7 | Satisfied |
| FRZ-06 | Phase 7 | Satisfied |
| EXTR-01 | Phase 8 | Pending |
| EXTR-02 | Phase 8 | Pending |
| EXTR-03 | Phase 7 | Satisfied |
| EXTR-04 | Phase 8 | Pending |
| EXTR-05 | Phase 8 | Pending |
| STAB-01 | Phase 9 | Pending |
| STAB-02 | Phase 9 | Pending |
| STAB-03 | Phase 9 | Pending |
| STAB-04 | Phase 9 | Pending |
| GRADE-01 | Phase 10 | Pending |
| GRADE-02 | Phase 10 | Pending |
| GRADE-03 | Phase 10 | Pending |
| GRADE-04 | Phase 10 | Pending |
| PACK-01 | Phase 11 | Pending |
| PACK-02 | Phase 11 | Pending |
| PACK-03 | Phase 11 | Deferred to v2.1 |
| PACK-04 | Phase 11 | Deferred to v2.1 |
| PACK-05 | Phase 11 | Deferred to v2.1 |

**Coverage:**
- v2.0 requirements: 24 total
- Active (v2.0 in scope): 21
- Deferred to v2.1: 3 (PACK-03, PACK-04, PACK-05)
- Mapped to phases: 21 active + 3 deferred
- Unmapped: 0

---
*Roadmap created: 2026-04-18*
*Last updated: 2026-04-20 after Phase 11 planning*

---

## Phase 12: Schema 定义层 (v2.1)

**Goal:** 定义 TESTSET、Environment、Gate 三个 YAML schema，含 forbidden/required field guards。

**Requirements:** SCHEMA-01 ~ SCHEMA-06

**Success Criteria:**
1. TESTSET schema 拒绝 test_case_pack / script_pack 字段（FC-006）
2. Environment schema 要求 base_url / browser / timeout / headless 字段
3. Gate schema 仅接受 pass / conditional_pass / fail / provisional_pass 四个 verdict
4. 所有 schema 对合法输入返回成功，对非法输入返回清晰错误信息

**Deliverables:**
- [x] `cli/lib/testset_schema.py` (new)
- [x] `cli/lib/environment_schema.py` (new)
- [x] `cli/lib/gate_schema.py` (new)
- [x] `ssot/schemas/qa/testset.yaml` (new)
- [x] `ssot/schemas/qa/environment.yaml` (new)
- [x] `ssot/schemas/qa/gate.yaml` (new)
- [x] `tests/cli/lib/test_testset_schema.py` (12 tests, all passing)
- [x] `tests/cli/lib/test_environment_schema.py` (16 tests, all passing)
- [x] `tests/cli/lib/test_gate_schema.py` (21 tests, all passing)

**State transition:** schema_draft -> schema_validated

**Plans:** 3/3 plans complete

Plans:
- [x] 12-01-PLAN.md — TESTSET schema with forbidden field guards (FC-006)
- [x] 12-02-PLAN.md — Environment schema with required field guards
- [x] 12-03-PLAN.md — Gate schema with 4-verdict enum guard

**Success Criteria:**
1. [x] TESTSET schema 拒绝 test_case_pack / script_pack 字段（FC-006）
2. [x] Environment schema 要求 base_url / browser / timeout / headless 字段
3. [x] Gate schema 仅接受 pass / conditional_pass / fail / provisional_pass 四个 verdict
4. [x] 所有 schema 对合法输入返回成功，对非法输入返回清晰错误消息

---

## Phase 13: 枚举守卫 (v2.1)

**Goal:** 实现 enum_guard.py，覆盖 6 个枚举字段（skill_id, module_id, assertion_layer, failure_class, gate_verdict, phase）。

**Requirements:** ENUM-01 ~ ENUM-03

**Success Criteria:**
1. allowed_values 白名单严格校验所有 6 个枚举字段
2. forbidden_semantics 值被正确拦截
3. 错误消息包含字段名、非法值、允许值列表

**Deliverables:**
- [x] `cli/lib/enum_guard.py` (new) — 227 lines, 6 enums, 4 functions, CLI
- [x] `tests/cli/lib/test_enum_guard.py` (new) — 41 tests, all passing

**Dependencies:** Phase 12 (enum values defined in schemas)
**State transition:** schema_validated -> enum_guard_integrated

**Plans:** 1 plan

Plans:
- [x] 13-01-PLAN.md -- Centralized enum_guard.py with 6 governance enums, validation, and CLI (ENUM-01, ENUM-02, ENUM-03) ✓ commit 4f90aa1

---

## Phase 14: 治理对象验证器 (v2.1)

**Goal:** 实现 governance_validator.py，覆盖 SRC-009 定义的 11 个治理对象。

**Requirements:** GOV-01 ~ GOV-03

**Success Criteria:**
1. 11 个治理对象（Skill, Module, AssertionLayer, FailureClass, GoldenPath, Gate, StateMachine, RunManifest, Environment, Accident, Verifier）均通过字段校验
2. required_fields / optional_fields / forbidden_fields 与 SRC-009 完全一致
3. 错误消息清晰指出缺失/多余/禁止字段

**Deliverables:**
- `cli/lib/governance_validator.py` (new)
- `tests/cli/lib/test_governance_validator.py` (new)

**Dependencies:** Phase 12 (schema definitions inform field constraints)

**Plans:** 1/1 plans complete

Plans:
- [x] 14-01-PLAN.md — governance_validator.py with all 11 object validators, enum integration, CLI (GOV-01, GOV-02, GOV-03) ✓ commit 972ee41

---

## Phase 15: 集成与追溯 (v2.1)

**Goal:** enum_guard 集成到 SSOT 写入路径，Frozen Contract 追溯集成到所有产出。

**Requirements:** FC-01 ~ FC-03, INT-01 ~ INT-03

**Success Criteria:**
1. SSOT 写入路径（cli/lib/protocol.py）自动调用 enum_guard 校验
2. 现有 FRZ/MSC 验证流程不受影响
3. 所有产出文件显式引用 FC-001 ~ FC-007

**Deliverables:**
- `cli/lib/fs.py` (extend — write_json enum_guard wrapping + fc_refs injection)
- `cli/lib/protocol.py` (verify — no changes needed, inherits via write_json)
- `tests/cli/lib/test_fs.py` (new — integration tests)

**Dependencies:** Phase 12, Phase 13, Phase 14
**State transition:** enum_guard_integrated -> contracts_traceable

**Plans:** 1/1 plans complete

Plans:
- [x] 15-01-PLAN.md — enum_guard integration into write_json + FC traceability + integration tests (FC-01, FC-02, FC-03, INT-01, INT-02, INT-03) ✓ commit a1aa585

---

## Phase 16: 测试验证 (v2.1)

**Goal:** 完整测试套件运行，产出证据，达到 ready_for_test 状态。

**Requirements:** TEST-01 ~ TEST-05

**Success Criteria:**
1. 所有 schema 测试通过
2. 所有 enum guard 测试通过
3. 所有 governance validator 测试通过
4. 集成测试确认 enum_guard 在 SSOT 写入时自动触发
5. Frozen Contract 追溯测试通过

**Dependencies:** Phase 12, Phase 13, Phase 14, Phase 15
**State transition:** contracts_traceable -> ready_for_test

**Plans:** 3/3 plans complete

Plans:
- [x] 16-01-PLAN.md — Test infrastructure: pytest-cov, pytest.ini, test_manifests.json update
- [x] 16-02-PLAN.md — Full test suite execution with evidence collection (JUnit XML + coverage)
- [x] 16-03-PLAN.md — CI workflow update (pytest-cov) + phase completion + state transition

**Success Criteria:**
1. [x] 所有 schema 测试通过 (49 tests)
2. [x] 所有 enum guard 测试通过 (41 tests)
3. [x] 所有 governance validator 测试通过 (99 tests)
4. [x] 集成测试确认 enum_guard 在 SSOT 写入时自动触发 (18 tests)
5. [x] Frozen Contract 追溯测试通过 (included in test_fs.py)

**Evidence:**
- test-results.xml: 207 tests, 0 failures (JUnit XML)
- coverage.xml: line-rate 0.057 (full cli.lib module, v2.1 tested files have strong coverage)
- htmlcov/index.html: Interactive HTML coverage report
- test-output.log: Full test run output

**State transition:** contracts_traceable -> ready_for_test [COMPLETE]

---

## v2.1 Task Pack Mapping

| Phase | Task Pack | Acceptance Criteria |
|-------|-----------|---------------------|
| Phase 12 | TASK-001 | AC-SCHEMA-001 |
| Phase 13 | TASK-002, TASK-005 | AC-ENUM-001, AC-ENUM-002 |
| Phase 14 | TASK-003, TASK-006 | AC-OBJECT-001 |
| Phase 15 | TASK-007 | AC-FC-001 |
| Phase 16 | TASK-004 | AC-FC006-001 |

## v2.1 Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCHEMA-01 | Phase 12 | Satisfied |
| SCHEMA-02 | Phase 12 | Satisfied |
| SCHEMA-03 | Phase 12 | Satisfied |
| SCHEMA-04 | Phase 12 | Satisfied |
| SCHEMA-05 | Phase 12 | Satisfied |
| SCHEMA-06 | Phase 12 | Satisfied |
| ENUM-01 | Phase 13 | Satisfied |
| ENUM-02 | Phase 13 | Satisfied |
| ENUM-03 | Phase 13 | Satisfied |
| GOV-01 | Phase 14 | Satisfied |
| GOV-02 | Phase 14 | Satisfied |
| GOV-03 | Phase 14 | Satisfied |
| INT-01 | Phase 15 | Satisfied |
| INT-02 | Phase 15 | Satisfied |
| INT-03 | Phase 15 | Satisfied |
| FC-01 | Phase 15 | Satisfied |
| FC-02 | Phase 15 | Satisfied |
| FC-03 | Phase 15 | Satisfied |
| TEST-01 | Phase 16 | Satisfied |
| TEST-02 | Phase 16 | Satisfied |
| TEST-03 | Phase 16 | Satisfied |
| TEST-04 | Phase 16 | Satisfied |
| TEST-05 | Phase 16 | Satisfied |

**Coverage:**
- v2.1 requirements: 22 total
- Mapped to phases: 22 (100%)
- Satisfied: 22 (100%)
- Unmapped: 0

---
*Last updated: 2026-04-23 — Phase 16 complete (test validation, 207 tests passed, ready_for_test)*
