# Requirements — v2.1 双链双轴测试强化

> Derived from: IMPL-SRC-009-D, SRC-009 v1.1 (frozen), EPIC-009, FEAT-009-D, TECH-009
> Milestone: v2.1 | FEAT: FEAT-009-D only

## Schema Definitions

### TESTSET Schema
- [ ] **SCHEMA-01**: Define TESTSET YAML schema with forbidden field guards (test_case_pack, script_pack per FC-006)
- [ ] **SCHEMA-02**: TESTSET schema accepts valid input and rejects invalid input with clear error messages

### Environment Schema
- [ ] **SCHEMA-03**: Define Environment YAML schema with required field guards (base_url, browser, timeout, headless)
- [ ] **SCHEMA-04**: Environment schema accepts valid input and rejects invalid input

### Gate Verdict Schema
- [ ] **SCHEMA-05**: Define Gate verdict YAML schema with 4-verdict enum (pass, conditional_pass, fail, provisional_pass)
- [ ] **SCHEMA-06**: Gate schema rejects unknown verdict values

## Enum Guard Module

- [ ] **ENUM-01**: Implement `cli/lib/enum_guard.py` with allowed_values validation for 6 enum fields:
  - skill_id: ["qa.test-plan", "qa.test-run"]
  - module_id: ["feat-to-testset", "api-plan-compile", "api-manifest-compile", "api-spec-compile", "e2e-plan-compile", "e2e-manifest-compile", "e2e-spec-compile", "environment-provision", "run-manifest-gen", "scenario-spec-compile", "state-machine-executor", "bypass-detector", "independent-verifier", "accident-package", "failure-classifier", "test-data-provision", "l0-smoke-check", "test-exec-web-e2e", "test-exec-cli", "settlement", "gate-evaluation"]
  - assertion_layer: ["A", "B", "C"]
  - failure_class: ["ENV", "DATA", "SCRIPT", "ORACLE", "BYPASS", "PRODUCT", "FLAKY", "TIMEOUT"]
  - gate_verdict: ["pass", "conditional_pass", "fail", "provisional_pass"]
  - phase: ["1a", "1b", "2", "3", "4"]
- [ ] **ENUM-02**: enum_guard rejects forbidden_semantics values for all 6 enum fields
- [ ] **ENUM-03**: enum_guard provides clear error messages with field name, value, and allowed values

## Governance Validator

- [ ] **GOV-01**: Implement `cli/lib/governance_validator.py` with required/optional/forbidden fields validation for all 11 governance objects:
  - Skill, Module, AssertionLayer, FailureClass, GoldenPath, Gate, StateMachine, RunManifest, Environment, Accident, Verifier
- [ ] **GOV-02**: Field definitions match SRC-009 object contracts exactly (no additions or deletions)
- [ ] **GOV-03**: Governance validator provides clear error messages for missing required fields, unexpected optional fields, and forbidden fields

## Frozen Contract Traceability

- [x] **FC-01**: All outputs reference FC-001 ~ FC-007 with explicit traceability
- [x] **FC-02**: FC-006 enforcement: TESTSET schema rejects test_case_pack / script_pack fields
- [x] **FC-03**: FC-007 enforcement: Verifier schema marks shared_context_with_runner as forbidden field

## SSOT Write Path Integration

- [x] **INT-01**: Integrate enum_guard into `cli/lib/protocol.py` SSOT write paths
- [x] **INT-02**: Existing FRZ/MSC validation flow remains unaffected by enum_guard integration
- [x] **INT-03**: SSOT writes invoke enum_guard validation automatically before persisting

## Testing

- [ ] **TEST-01**: Schema validation tests for all 3 schemas (TESTSET, Environment, Gate)
- [ ] **TEST-02**: Enum guard tests for all 6 fields (allowed_values + forbidden_semantics)
- [ ] **TEST-03**: Governance validator tests for all 11 objects
- [ ] **TEST-04**: Integration tests confirming enum_guard is invoked on SSOT writes
- [ ] **TEST-05**: Frozen Contract traceability tests

## Future Requirements (Deferred)

### FEAT-009-E: 测试执行框架 (Deferred to v2.2+)
- StateMachine 有限状态执行器
- 三层断言模型 (A/B/C)
- 8 类故障分类
- L0-L3 分层执行模型
- RunManifest 生成器
- 黄金路径 (G1-G6)

### FEAT-009-A: 独立验证与审计 (Deferred to v2.2+)
- Verifier 独立认证上下文
- bypass-detector 违规检测
- Accident 标准化失败取证包
- failure-classifier 后处理路由

### FEAT-009-S: Skill 编排 (Deferred to v2.2+)
- qa.test-plan Skill DAG
- qa.test-run Skill DAG
- 17+ 内部模块接口契约
- DAG 解析器

## Out of Scope

| Feature | Reason |
|---------|--------|
| FRZ 生成工具实现 | 本轮仅定义治理规则 |
| 复杂 DAG 调度 | ADR-050/051 明确采用顺序 loop |
| 执行引擎/状态机/验证器 | 属于其他 FEAT (FEAT-009-E, FEAT-009-A) |
| Skill 编排实现 | 属于 FEAT-009-S |
| UI 界面 | 本 FEAT 为 CLI/library-level 基础设施 |

## Traceability

| Requirement | Mapped to | Task Pack |
|-------------|-----------|-----------|
| SCHEMA-01 ~ SCHEMA-06 | AC-SCHEMA-001 | TASK-001 |
| ENUM-01 ~ ENUM-03 | AC-ENUM-001, AC-ENUM-002 | TASK-002 |
| GOV-01 ~ GOV-03 | AC-OBJECT-001 | TASK-003 |
| FC-01 ~ FC-03 | AC-FC-001, AC-FC006-001 | TASK-004, TASK-006 |
| INT-01 ~ INT-03 | AC-FC-001 | TASK-007 |
| TEST-01 ~ TEST-05 | All ACs | TASK-004 ~ TASK-006 |

---
*Requirements defined: 2026-04-22*
