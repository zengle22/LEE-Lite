# Phase 19: 验收闭环 - Context

**Gathered:** 2026-04-24
**Status:** Ready for planning

<domain>
## Phase Boundary

交付 independent_verifier 独立验证报告 + settlement 集成 + gate-evaluate 集成，打通从 feat 到 gate 的完整验收闭环。

**Success Criteria:**
1. `independent_verifier.py` 对执行结果产出验证报告，verdict 为 pass / conditional_pass / fail，含置信度字段
2. `ll-qa-settlement` 消费更新后的 manifest，产出 settlement report
3. `ll-qa-gate-evaluate` 基于 manifest 产出 gate 结论，与 settlement report 对齐
4. `pytest tests/cli/lib/test_spec_adapter.py tests/cli/lib/test_environment_provision.py tests/cli/lib/test_step_result.py` 单元测试套件全部通过

</domain>

<decisions>
## Implementation Decisions

### Verdict Strategy (分层判定)
- **D-01:** 主流程判定规则：
  - 覆盖率必须 100%（可灵活配置）
  - 失败容忍 0 个（主流程 1 个失败 = verdict fail）
- **D-02:** 非核心流程判定规则：
  - 覆盖率 ≥ 80%（可灵活配置）
  - 失败容忍 3-5 个（可灵活配置）
- **D-03:** scenario_type 区分主/非核心流程：
  - `main` = 主流程
  - `exception` / `branch` = 非核心流程
  - `retry` / `state` = 非核心流程（默认）

### Confidence Calculation
- **D-04:** 置信度 = 有 `evidence_refs` 的用例占比
- **D-05:** 置信度作为参考指标列出，不作为 verdict 的主要依据

### Integration Strategy (链式传递)
- **D-06:** 数据流：`independent_verifier.verdict` → `ll-qa-settlement` → `ll-qa-gate-evaluate.final_decision`
- **D-07:** settlement report 包含 verdict 和 confidence
- **D-08:** gate-evaluate 基于 settlement report 产出最终判定

### Unit Test Scope (TEST-04)
- **D-09:** 覆盖所有相关模块：
  - `spec_adapter.py` — API/E2E spec 解析
  - `environment_provision.py` — ENV 文件生成
  - `StepResult` dataclass — 数据传递契约
  - `ll-qa-settlement` — settlement report 生成
  - `ll-qa-gate-evaluate` — gate 判定逻辑
  - `independent_verifier.py` — verdict 计算逻辑

### Claude's Discretion
- confidence 的灵活阈值（具体百分比）
- failure_tolerance 的精确容忍数量（3-5 之间选哪个）
- verdict 灵活性配置的具体值

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §验收闭环 — GATE-01, GATE-02, GATE-03, TEST-04
- `.planning/ROADMAP.md` §Phase 19 — Phase goal and success criteria
- `.planning/REQUIREMENTS.md` §实施轴补全 — EXEC-01, EXEC-02, EXEC-03 (Phase 18 dependencies)

### ADR
- `ssot/adr/ADR-054-实施轴接入需求轴-双链桥接与执行闭环.md` §3 Phase 3 — GATE-01~03, TEST-04 定义
- `ssot/adr/ADR-047-双链测试架构与防偷懒治理框架.MD` — settlement 和 gate-evaluate 的原始规范

### Existing Skills
- `skills/ll-qa-settlement/SKILL.md` — settlement report 生成规范
- `skills/ll-qa-gate-evaluate/SKILL.md` — gate evaluate 判定逻辑规范

### Implementation (to implement)
- `cli/lib/spec_adapter.py` — Phase 17 交付，需单元测试
- `cli/lib/environment_provision.py` — Phase 17 交付，需单元测试
- `cli/lib/contracts.py` — StepResult dataclass 定义，需单元测试
- `cli/lib/independent_verifier.py` — Phase 19 新建

### Existing Tests (baseline)
- `tests/cli/lib/test_enum_guard.py` — 41 passing tests, pytest-based structure
- `tests/cli/lib/test_environment_schema.py` — schema test pattern
- `tests/cli/lib/test_testset_schema.py` — schema test pattern

### Gate Schema
- `cli/lib/gate_schema.py` — gate schema definition
- `tests/cli/lib/test_gate_schema.py` — gate schema tests

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `skills/ll-qa-gate-evaluate/SKILL.md` — existing gate evaluate skill (do not rewrite, integrate)
- `skills/ll-qa-settlement/SKILL.md` — existing settlement skill (do not rewrite, integrate)
- `tests/cli/lib/test_*.py` — pytest-based test structure pattern to follow
- `cli/lib/gate_schema.py` — gate schema definition to reference

### Established Patterns
- pytest-based test structure (tests/cli/lib/ directory)
- Test files follow `test_<module>.py` naming convention
- Tests use dataclass fixtures for test data

### Integration Points
- test_orchestrator → settlement: updated manifests
- settlement → gate-evaluate: settlement report
- independent_verifier → settlement: verdict report

</code_context>

<specifics>
## Specific Ideas

### Verdict Report Format
```yaml
verification_report:
  run_id: {run_id}
  generated_at: {timestamp}
  verdict: pass|conditional_pass|fail
  confidence: 0.XX
  details:
    main_flow:
      coverage: 100%
      failures: 0
      status: pass|fail
    non_core_flow:
      coverage: 80%
      failures: 3
      status: conditional_pass
```

### Confidence = Evidence Completeness
```python
confidence = count(executed_items with evidence_refs) / count(executed_items)
```

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 19-验收闭环*
*Context gathered: 2026-04-24*
