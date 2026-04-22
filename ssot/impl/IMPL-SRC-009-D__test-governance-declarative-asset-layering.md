---
id: IMPL-SRC-009-D
ssot_type: IMPL
impl_ref: IMPL-SRC-009-D
tech_ref: TECH-009
feat_ref: FEAT-009-D
title: 测试需求轴治理 — 声明性资产分层与枚举冻结 Implementation Task Package
status: active
version: v2
schema_version: 0.1.0
impl_root_id: impl-root-src-009-d
parent_id: FEAT-009-D
source_refs:
  - FEAT-009-D
  - EPIC-009
  - SRC-009
  - ADR-052
  - ADR-047
  - ADR-050
  - ADR-051
  - TECH-009
owner: dev-owner
workflow_key: manual.impl.from-tech
workflow_instance_id: manual-impl-src-009-d-20260422
package_semantics: canonical_execution_package
authority_scope: execution_input_only
selected_upstream_refs:
  feat_ref: FEAT-009-D
  tech_ref: TECH-009
  authority_refs:
    - SRC-009
    - EPIC-009
task_pack_ref: ssot/testset/TASK-PACK-009-D__test-governance-declarative-task-pack.yaml
created_at: '2026-04-22T00:00:00+08:00'
---

# IMPL-SRC-009-D

## 1. 任务标识

- impl_ref: `IMPL-SRC-009-D`
- title: 测试需求轴治理 — 声明性资产分层与枚举冻结 Implementation Task Package
- workflow_key: `manual.impl.from-tech`
- workflow_run_id: `manual-impl-src-009-d-20260422`
- status: `execution_ready`
- derived_from: `FEAT-009-D`, `TECH-009`
- package role: canonical execution package / execution-time single entrypoint

## 2. 本次目标

- 覆盖目标: 实现需求轴（SSOT）治理基础设施，包括 Schema 定义层、枚举守卫模块、治理对象验证器和 Frozen Contract 追溯。
- 完成标准: 4 个 implementation unit、7 条 Frozen Contracts 可追溯、5 个枚举守卫、11 个治理对象验证器全部齐备。
- 完成条件: coder/tester 可直接消费本契约，按有序主序列实施，不必打开上游 TECH/SRC 文档捞关键约束。

## 3. 范围与非目标

### In Scope

- TESTSET YAML schema（forbidden: test_case_pack, script_pack）
- Environment YAML schema（required: base_url, browser, timeout, headless; optional: managed, account_runner, account_verifier）
- Gate verdict YAML schema（4 verdicts: pass/conditional_pass/fail/provisional_pass）
- `cli/lib/enum_guard.py`: 5 个枚举字段的 allowed_values / forbidden_semantics 校验
- `cli/lib/governance_validator.py`: 11 个治理对象的 required/optional/forbidden fields 校验
- Frozen Contract 追溯集成到 TESTSET/Environment/Gate 定义
- 所有 schema 顶层元字段：`axis: requirement`（标识需求轴资产）、`compiled_from`（来源 FEAT/TECH/UI 引用）、`compilation_timestamp`（编译时间追溯）
- 分层规则元字段：`governance.axis`（requirement|implementation）、`governance.mutable`（true=声明可覆盖, false=证据只追加）、`governance.cross_axis_ref`（实施轴引用需求轴的 _ref 字段）

### Out of Scope

- Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.
- Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.
- Do not expand touch set beyond declared modules without re-derive or revision review.
- Do not implement execution engine, state machine, or verifier — those belong to other FEATs.

## 4. 上游收敛结果

- ADR refs: ADR-052, ADR-047, ADR-050, ADR-051 -> Freeze test governance dual-axis architecture under ADR-052; ADR-047/050/051 provide foundation constraints.
- SRC / EPIC / FEAT: `SRC-009` / `EPIC-009` / `FEAT-009-D` -> 测试需求轴治理，声明性资产分层与枚举冻结。
- TECH: `TECH-009` -> 4-layer architecture: (1) 需求轴 schema, (2) 实施轴 artifact, (3) 执行引擎, (4) Skill 编排。本 IMPL 覆盖 Layer 1 需求轴 schema 及全局枚举守卫。
- ARCH: none selected for this FEAT.
- API: none selected for this FEAT.
- UI: none selected for this FEAT.
- TESTSET: `TESTSET-009` -> Acceptance and evidence must remain mapped to TESTSET-009.
- provisional_refs: none

### Authority Binding Status

- `ADR` status=`bound` ref=`ADR-052, ADR-047, ADR-050, ADR-051` | required_for: test governance dual-axis architecture and constraint inheritance | execution_effect: coder/tester inherit 7 Frozen Contracts and enum definitions from SRC-009 | follow_up: none
- `TECH` status=`bound` ref=`TECH-009` | required_for: 4-layer architecture and module interface definitions | execution_effect: IMPL implements Layer 1 schema + enum guard layer per TECH-009 | follow_up: none
- `TESTSET` status=`bound` ref=`TESTSET-009` | required_for: acceptance truth, evidence collection, and tester alignment | execution_effect: acceptance trace maps to TESTSET-009 observation points | follow_up: none
- `ARCH` status=`missing` ref=`none` | required_for: architecture layering constraints | execution_effect: TECH-009 provides sufficient architectural guidance; no separate ARCH required for schema/guard IMPL | follow_up: none
- `API` status=`missing` ref=`none` | required_for: API contract definitions | execution_effect: this FEAT is infrastructure-level (schemas, validators), no external API surface | follow_up: none
- `UI` status=`missing` ref=`none` | required_for: UI entry/exit constraints | execution_effect: this FEAT has no user-facing UI surface; it is CLI/library-level infrastructure | follow_up: none

### Controlled Authority Gaps

- `UI` status=`missing` ref=`none` | required_for: N/A — this FEAT has no user-facing UI surface | execution_effect: no UI constraints needed; all outputs are schema/validation artifacts | follow_up: none
- `API` status=`missing` ref=`none` | required_for: N/A — this FEAT exposes no external API | execution_effect: no API contracts needed; module interfaces are internal library calls | follow_up: none

### TECH Contract Snapshot

- 4-layer architecture: Layer 1 = 需求轴 schema, Layer 2 = 实施轴 artifact, Layer 3 = 执行引擎, Layer 4 = Skill 编排
- 本 IMPL 覆盖 Layer 1: TESTSET/Environment/Gate schema 定义 + 枚举守卫 + 治理对象验证器
- 7 Frozen Contracts (FC-001 ~ FC-007) 必须在所有产出中可追溯
- 5 个枚举字段（skill_id, assertion_layer, failure_class, gate_verdict, phase）的 allowed_values 和 forbidden_semantics 必须强制执行
- 枚举字段以 TECH-009 Layer 1 定义为准（5 个），ADR-052 原文"6 个"含 module_id 但 module_id 不在冻结范围内

### State Model Snapshot

- `schema_draft` -> `schema_validated` -> `enum_guard_integrated` -> `contracts_traceable` -> `ready_for_test`
- `validation_failed` -> `schema_revised` -> `schema_validated` (retry loop, max 3 revisions)
- Schema 未通过 validate 时不得进入 enum_guard_integrated 状态
- Frozen Contract 追溯未完成时不得进入 ready_for_test 状态

### Main Sequence Snapshot

- 1. Define TESTSET YAML schema with forbidden field guards (test_case_pack, script_pack)
- 2. Define Environment YAML schema with required field guards
- 3. Define Gate verdict YAML schema with 4-verdict enum
- 4. Implement `cli/lib/enum_guard.py`: allowed_values + forbidden_semantics validator for 5 enum fields
- 5. Implement `cli/lib/governance_validator.py`: 11 governance object field validator
- 6. Integrate enum_guard into all SSOT write paths
- 7. Wire Frozen Contract traceability into TESTSET/Environment/Gate definitions
- 8. Run validation tests and produce evidence artifacts

### Integration Points Snapshot

- 调用方: `ll-frz-manage` freeze/extract 路径产出 FRZ/SRC，本 IMPL 的 schema 和验证器消费这些产出
- 挂接点: enum_guard 集成到 `cli/lib/` 写入路径，在所有 SSOT YAML/JSON 产出时自动校验
- 旧系统兼容: 已有 `cli/lib/frz_schema.py` 的 MSC 验证器不受影响；新增 enum_guard 作为额外验证层

### Implementation Unit Mapping Snapshot

- `cli/lib/testset_schema.py` (new): TESTSET YAML schema 定义，含 forbidden field guards
- `cli/lib/environment_schema.py` (new): Environment YAML schema 定义，含 required field guards
- `cli/lib/gate_schema.py` (new): Gate verdict YAML schema 定义，含 4-verdict enum
- `cli/lib/enum_guard.py` (new): 5 个枚举字段的 allowed_values / forbidden_semantics 校验器
- `cli/lib/governance_validator.py` (new): 11 个治理对象的 required/optional/forbidden fields 校验器
- `cli/lib/protocol.py` (extend): 集成 enum_guard 到 SSOT 写入路径

### Governance Objects清单（11 个）

以下 11 个治理对象必须在 `governance_validator.py` 中各有 required/optional/forbidden fields 定义：

| # | 对象 | 来源 | 关键字段示例 |
|---|------|------|-------------|
| 1 | Skill | ADR-052 §2.5 | skill_id, user_intent, orchestrates[] |
| 2 | Module | ADR-052 §2.3/§2.4/§2.5 | module_id, input[], output[], storage_path |
| 3 | AssertionLayer | ADR-052 §2.5 三层断言模型 | layer(A/B/C), proves, example, phase_requirement |
| 4 | FailureClass | ADR-052 §2.5 模块8 | failure_class, meaning, common_manifest, post_process_rule |
| 5 | GoldenPath | ADR-052 §6 | path_id, priority, title, rationale |
| 6 | Gate | ADR-052 §7.4 | gate_verdict, dimensions[], weights[], verifier_veto_rule |
| 7 | StateMachine | ADR-052 §2.5 模块4 / §2.9.8 | state_name, allowed_next[], on_fail, covers[] |
| 8 | RunManifest | ADR-052 §2.5 模块2 | run_id, app_commit, base_url, browser, generated_at |
| 9 | Environment | ADR-052 §2.5 模块1 / §2.8 | base_url, browser, timeout, headless, managed |
| 10 | Accident | ADR-052 §2.5 模块7 | case_id, manifest, screenshots[], traces[], classification |
| 11 | Verifier | ADR-052 §2.5 模块6 | verdict, confidence, c_layer_verdict, independence_rule |

### API Contract Snapshot

- No external API surface. All modules expose Python library interfaces:
  - `validate_testset(yaml_path) -> ValidationResult`
  - `validate_environment(yaml_path) -> ValidationResult`
  - `validate_gate_verdict(yaml_path) -> ValidationResult`
  - `check_enum_field(field_name, value) -> bool`
  - `validate_governance_object(object_name, data) -> ValidationResult`

### UI Constraint Snapshot

- No user-facing UI surface. This FEAT is CLI/library-level infrastructure.
- CLI entry: `ll frz-manage validate --type testset|environment|gate <path>` (future, not in this IMPL scope)

## 5. 规范性约束

### Normative / MUST

- TESTSET schema 必须拒绝 test_case_pack / script_pack 字段（FC-006）
- 5 个枚举字段必须强制执行 allowed_values，forbidden_semantics 值必须拦截
- 11 个治理对象必须通过 required_fields 校验
- 7 条 Frozen Contracts 必须在所有产出中可追溯
- Schema 未通过 validate 时不得进入下游

### Informative / Context Only

- None.

## 6. 实施要求

### Touch Set / Module Plan

- `cli/lib/testset_schema.py` [backend | new | no_existing_match] <- TESTSET YAML schema 定义
- `cli/lib/environment_schema.py` [backend | new | no_existing_match] <- Environment YAML schema 定义
- `cli/lib/gate_schema.py` [backend | new | no_existing_match] <- Gate verdict YAML schema 定义
- `cli/lib/enum_guard.py` [backend | new | no_existing_match] <- 枚举守卫校验器
- `cli/lib/governance_validator.py` [backend | new | no_existing_match] <- 治理对象字段校验器
- `cli/lib/protocol.py` [backend | extend | existing_match] <- 集成 enum_guard 到 SSOT 写入路径; nearby matches: cli/lib/fs.py, cli/lib/errors.py

### Repo Touch Points

- `cli/lib/testset_schema.py` [backend | new | no_existing_match] <- TESTSET YAML schema 定义
- `cli/lib/environment_schema.py` [backend | new | no_existing_match] <- Environment YAML schema 定义
- `cli/lib/gate_schema.py` [backend | new | no_existing_match] <- Gate verdict YAML schema 定义
- `cli/lib/enum_guard.py` [backend | new | no_existing_match] <- 枚举守卫校验器
- `cli/lib/governance_validator.py` [backend | new | no_existing_match] <- 治理对象字段校验器
- `cli/lib/protocol.py` [backend | extend | existing_match] <- 集成 enum_guard 到 SSOT 写入路径

### Allowed

- Implement only the declared repo touch points and governed evidence/handoff artifacts.
- Create new modules at the declared repo touch points.
- Add validation hooks into existing SSOT write paths in protocol.py.

### Forbidden

- Modify modules outside the declared repo touch points without re-derive or explicit revision approval.
- Invent new requirements or redefine design truth in IMPL.
- Use repo current shape as silent override of upstream frozen objects.
- Do not implement execution engine, state machine, or verifier logic — those belong to other FEATs.

### Execution Boundary

- 继承规则: 上游冻结决策只能被实现和验证，不能在 IMPL 中被改写。
- discrepancy handling: 若 repo 现状与上游冻结对象冲突，不得默认以代码现状为准。

## 7. 交付物要求

- 说明: 本切片的主要实现对象是上文 `Repo Touch Points` 列出的代码/配置路径。
- 说明: 下面列出 workflow 流程产物（evidence / review / handoff），用于审计与交接，不应替代工程对象本身的交付。
- impl-bundle.md
- impl-bundle.json
- impl-task.md
- upstream-design-refs.json
- integration-plan.md
- dev-evidence-plan.json
- smoke-gate-subject.json
- impl-review-report.json
- impl-acceptance-report.json
- impl-defect-list.json
- handoff-to-feature-delivery.json
- execution-evidence.json
- supervision-evidence.json

### Handoff Artifacts

- impl-bundle.md, impl-bundle.json, impl-task.md
- upstream-design-refs.json, integration-plan.md
- dev-evidence-plan.json, smoke-gate-subject.json
- impl-review-report.json, impl-acceptance-report.json, impl-defect-list.json
- handoff-to-feature-delivery.json
- execution-evidence.json, supervision-evidence.json

## 8. 验收标准与 TESTSET 映射

- testset_ref: `TESTSET-009`
- mapping_policy: `TESTSET_over_IMPL_when_present`

### Acceptance Trace

- AC-SCHEMA-001: TESTSET schema 拒绝嵌入 test_case_pack / script_pack -> Schema defines forbidden fields; validator rejects any TESTSET containing these fields. | mapping_status: `mapped` | mapped_test_units: `TESTSET-009 assertion_requirements` | mapped_to: `TESTSET-009`
- AC-ENUM-001: 所有 5 个枚举字段校验通过 allowed_values -> enum_guard.py enforces allowed_values for skill_id, assertion_layer, failure_class, gate_verdict, phase. | mapping_status: `mapped` | mapped_test_units: `TESTSET-009 failure_classification_test` | mapped_to: `TESTSET-009`
- AC-ENUM-002: forbidden_semantics 值被正确拦截 -> enum_guard.py rejects forbidden_semantics values with clear error. | mapping_status: `mapped` | mapped_test_units: `TESTSET-009 risk_focus` | mapped_to: `TESTSET-009`
- AC-OBJECT-001: 11 个治理对象均通过 required_fields 校验 -> governance_validator.py validates all 11 objects with required/optional/forbidden fields. | mapping_status: `mapped` | mapped_test_units: `TESTSET-009 coverage_scope` | mapped_to: `TESTSET-009`
- AC-FC006-001: TESTSET 不含执行产物的 schema 测试通过 -> Schema forbids test_case_pack/script_pack; validation test confirms rejection. | mapping_status: `mapped` | mapped_test_units: `TESTSET-009 preconditions` | mapped_to: `TESTSET-009`
- AC-FC-001: 7 条 Frozen Contracts 在产出中可追溯 -> All outputs reference FC-001 ~ FC-007; traceability report confirms coverage. | mapping_status: `mapped` | mapped_test_units: `TESTSET-009 assertion_requirements` | mapped_to: `TESTSET-009`

### Acceptance-to-Task Mapping

- AC-SCHEMA-001 | implemented_by: TASK-001 | evidence: TESTSET schema with forbidden field definitions; validation test confirms rejection.
- AC-ENUM-001, AC-ENUM-002 | implemented_by: TASK-002, TASK-005 | evidence: enum_guard.py enforces allowed_values and rejects forbidden_semantics.
- AC-OBJECT-001 | implemented_by: TASK-003, TASK-006 | evidence: governance_validator.py validates all 11 governance objects.
- AC-FC006-001 | implemented_by: TASK-004 | evidence: Schema test confirms TESTSET cannot contain execution artifacts.
- AC-FC-001 | implemented_by: TASK-006, TASK-007 | evidence: All outputs reference FC-001 ~ FC-007 with traceability report.

## 9. 执行顺序建议

### Required

- 1. Define schemas (TESTSET, Environment, Gate) — foundation layer
- 2. Implement enum_guard — depends on schema definitions for enum values
- 3. Implement governance_validator — depends on SRC-009 domain object definitions
- 4. Write schema validation tests — depends on schema + enum_guard
- 5. Write enum_guard tests — depends on enum_guard implementation
- 6. Write governance_validator tests — depends on governance_validator implementation
- 7. Integrate enum_guard into SSOT write paths — depends on all validators passing tests
- 8. Produce evidence artifacts and run full validation suite

### Suggested

- Run tests after each module; do not batch all testing to the end.

### Ordered Task Breakdown

- TASK-001 Define TESTSET/Environment/Gate YAML schemas | depends_on: none | parallel: none | touch_points: cli/lib/testset_schema.py, cli/lib/environment_schema.py, cli/lib/gate_schema.py | outputs: 3 schema files with forbidden/required field guards | acceptance: AC-SCHEMA-001 | done_when: All 3 schemas reject invalid input and accept valid input
- TASK-002 Implement enum_guard.py | depends_on: TASK-001 | parallel: none | touch_points: cli/lib/enum_guard.py | outputs: allowed_values + forbidden_semantics validator for 5 enum fields | acceptance: AC-ENUM-001, AC-ENUM-002 | done_when: All 5 enum fields enforce allowed_values and reject forbidden_semantics
- TASK-003 Implement governance_validator.py | depends_on: TASK-001 | parallel: TASK-002 | touch_points: cli/lib/governance_validator.py | outputs: 11 governance object field validator | acceptance: AC-OBJECT-001 | done_when: All 11 objects validate required/optional/forbidden fields correctly
- TASK-004 Write TESTSET schema tests | depends_on: TASK-001, TASK-002 | parallel: none | touch_points: tests/ | outputs: test file for TESTSET forbidden field rejection | acceptance: AC-SCHEMA-001, AC-FC006-001 | done_when: Tests confirm TESTSET rejects test_case_pack/script_pack
- TASK-005 Write enum_guard tests | depends_on: TASK-002 | parallel: TASK-003 | touch_points: tests/ | outputs: test file for enum field validation | acceptance: AC-ENUM-001, AC-ENUM-002 | done_when: Tests confirm all 5 enum fields validate correctly
- TASK-006 Write governance_validator tests | depends_on: TASK-003 | parallel: none | touch_points: tests/ | outputs: test file for governance object validation | acceptance: AC-OBJECT-001 | done_when: Tests confirm all 11 objects validate correctly
- TASK-007 Integrate enum_guard into SSOT write paths | depends_on: TASK-004, TASK-005, TASK-006 | parallel: none | touch_points: cli/lib/protocol.py | outputs: enum_guard wired into SSOT write pipeline | acceptance: AC-FC-001 | done_when: All SSOT writes invoke enum_guard validation

## 10. 风险与注意事项

- Schema 定义不完整可能导致下游 TESTSET 产出无效 — 必须在 Phase 1a 完成所有 schema 定义
- enum_guard 的 forbidden_semantics 拦截可能误杀合法值 — 需要明确的 allowed_values 白名单
- governance_validator 的 11 个对象字段定义必须与 SRC-009 完全一致，不得自行增删
- Frozen Contract 追溯可能遗漏 — 需要在每个产出文件中显式引用 FC 编号
- 集成 enum_guard 到 SSOT 写入路径时不得破坏现有 FRZ/MSC 验证流程
- 本 IMPL 不实现执行引擎、状态机或验证器 — 这些属于其他 FEAT 的职责范围

## 附录：版本历史

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-04-22 | Initial draft |
| v2 | 2026-04-22 | ADR-052 gap fix: (1) 枚举守卫 6→5 修正, (2) 11 个治理对象清单补齐, (3) Environment schema 增加 managed 字段, (4) 分层规则/编译追溯元字段纳入 In Scope, (5) TECH-009 接口签名核对确认一致 |
