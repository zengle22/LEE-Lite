---
phase: 19
reviewers: [codex, qwen]
reviewed_at: 2026-04-24T23:12:00+08:00
plans_reviewed: [19-01-PLAN.md, 19-02-PLAN.md, 19-03-PLAN.md, 19-04-PLAN.md (draft)]
---

# Cross-AI Plan Review — Phase 19

## Codex Review

### Plan 19-01: independent_verifier.py + step_result.py

**Summary**
方向对：把"独立验收判断（verdict+confidence）"从执行层抽离出来，并按 `scenario_type` 分流，符合 D-01~D-05 的精神；但当前计划里对 **conditional_pass 的判定规则、coverage/failures 的精确定义、以及与既有 `StepResult`/manifest schema 的对齐**都不够明确，存在实现后"能跑但不满足锁定决策/验收口径"的风险。

**Strengths**
- 按 `scenario_type` 分为 main/non-core，直接对齐 D-03
- `confidence` 计算口径与 D-04/D-05 一致（作为参考，不作为主裁决依据）
- 报告结构（run_id、generated_at、details）利于后续 settlement/gate 串联与追溯

**Concerns**
- **HIGH**: 计划未给出 **conditional_pass** 的产生条件；而需求明确 verdict 必须是 `pass/conditional_pass/fail`（GATE-01）
- **HIGH**: D-01/D-02 的 **coverage** 与 **failures** 口径未定义（coverage 分母是 designed？可执行？还是 executed？failures 是否包含 blocked？uncovered？）
- **HIGH**: `Overall verdict = fail if ANY flow fails; otherwise pass` 过于二元，基本吞掉 conditional 的空间
- **MEDIUM**: `_compute_confidence()` 对 "0 executed items" 会有除零风险
- **MEDIUM**: `_categorize_items()` 对未知/缺失 `scenario_type` 的策略未说明
- **MEDIUM**: 新增 `cli/lib/step_result.py` 可能与 Phase 17/18 已有 `StepResult` 重复或路径不一致
- **LOW**: `details: dict` 过于松散；后续 settlement/gate 依赖时容易产生 schema 漂移

**Suggestions**
- 明确判定表：把 D-01/D-02 转成可执行规则，补上 `conditional_pass` 的定义
- 明确指标口径：coverage = executed_designed / designed，failures 是否计入 blocked
- 明确缺省策略：缺失 `scenario_type` 建议默认 non-core
- 结构化 details：把 `details` 升级为稳定 schema（dataclass 皆可）
- 兼容性优先：先确认现有 `StepResult` 与 manifest item 结构

**Risk Assessment: HIGH** — 核心验收口径（conditional_pass、coverage/failures 定义、overall verdict 汇总）未锁定到代码级规则，且存在与既有类型/manifest schema 冲突的潜在破坏面。

---

### Plan 19-02: settlement_integration.py + gate_integration.py

**Summary**
流水线形态符合 D-06~D-08（verifier → settlement → gate），并把 verdict+confidence 注入 settlement，方向正确；但计划对 **manifest 更新点、报告落盘/引用方式、API/E2E 双 settlement 的合并与缺失处理**不够清晰。

**Strengths**
- settlement 明确包含 `verdict` + `confidence`（对齐 D-07）
- gate 由 settlement 推导最终决策（对齐 D-08 的"以 settlement 为准"）
- settlement 统计指标（total/designed/executed/…）与 gap/waiver 有助于形成可审计报告

**Concerns**
- **HIGH**: `generate_settlement(manifest_path, verdict_report, chain)` — verdict_report 可能是外部注入，而不是从 manifest 统一读取
- **HIGH**: gate 逻辑没有说明 **当 API 或 E2E 其中一个 settlement 缺失、或 verdict 为 conditional_pass 时如何对齐**
- **MEDIUM**: settlement 的统计口径与 verifier 的 coverage/failures 口径可能不一致
- **MEDIUM**: 未说明 settlement report / gate 结论的 schema 版本、落盘路径、与 run_id 的关联

**Suggestions**
- 让 settlement "只信 manifest"：把 verifier 输出写回 manifest，`ll-qa-settlement` 仅靠 manifest 生成 settlement
- 明确 gate 合并策略：API/E2E 的组合矩阵（pass/conditional/fail/缺失）明确成表
- 统一 schema：settlement 中固定字段（verdict/confidence/run_id/generated_at/verifier_report_ref）
- 明确错误处理：manifest 不合法、字段缺失时建议 conditional + reason；不可恢复→fail

**Risk Assessment: MEDIUM-HIGH** — 整体链路合理，但数据契约（manifest↔verifier↔settlement↔gate）的"单一真源"与合并规则不清晰。

---

### Plan 19-03: Unit tests

**Summary**
把 Phase 17 的三组单测作为回归门槛是好的，但它们并不覆盖 Phase 19 新增的 verifier/settlement/gate 关键逻辑；即使所有测试通过，也可能完全没验证到本 phase 的核心交付（GATE-01~03）。

**Strengths**
- 有明确的 pytest 命令与回归范围，能防止 adapter/environment/step_result 退化
- 作为依赖相位（17/18）的回归门槛合理

**Concerns**
- **HIGH**: 缺少对 `independent_verifier.verify()` 的单测：阈值边界、conditional_pass、confidence 除零
- **HIGH**: 缺少对 settlement 注入 verdict/confidence、以及 gate 合并矩阵的单测
- **MEDIUM**: 如果 `step_result.py` 在 Phase 19 有新增/迁移，现有测试可能不足以覆盖导入路径兼容性问题

**Suggestions**
- 增加 `tests/cli/lib/test_independent_verifier.py`：覆盖 D-01/D-02/D-04 的关键边界
- 增加 `tests/cli/lib/test_settlement_integration.py`：verdict/confidence 透传 + 统计口径一致性
- 增加 `tests/cli/lib/test_gate_integration.py`：API/E2E verdict 合并矩阵（含缺失输入）

**Risk Assessment: HIGH** — 新代码无测试覆盖，回归风险高。

---

## Qwen Review

### Plan 19-01: independent_verifier.py + step_result.py

**Summary**
Plan 19-01 设计了验证层的核心数据结构和逻辑，将 manifest items 按 scenario_type 分类，计算覆盖率/失败率，并产出带置信度的 VerdictReport。整体架构清晰，与已锁定的 D-01~D-08 决策一致。

**Strengths**
- **决策对齐**: verdict 逻辑与 D-01/D-02 的覆盖率阈值要求一致
- **职责分离**: `_categorize_items()` 和 `_compute_confidence()` 职责单一，易于测试
- **数据结构清晰**: VerdictReport 结构明确，包含 run_id、verdict、confidence、details
- **可追溯性**: details 字段保留 main_flow/non_core_flow 详细状态，便于调试

**Concerns**
- **[HIGH] scenario_type 缺失/未知的处理**: `_categorize_items()` 会如何处理缺失 scenario_type 的 item？
- **[MEDIUM] 边界条件: 零 items 情况**: 如果 manifest_items 为空，confidence 计算会产生除零错误 (0/0)
- **[MEDIUM] evidence_refs 验证不充分**: 仅检查 existence，不验证 evidence_refs 内容有效性
- **[LOW] verdict 枚举一致性**: GateVerdict 枚举是否包含 `conditional_pass`？

**Suggestions**
- 明确 scenario_type 默认值策略：建议 `scenario_type not in ['main'] → non_core_flow`，并记录 warning
- 在 `_compute_confidence()` 中添加 `executed_items_count == 0` 的保护分支
- 考虑添加 evidence_refs 格式校验

**Risk Assessment: MEDIUM** — 核心逻辑清晰，但边界条件处理不足。

---

### Plan 19-02: settlement_integration.py + gate_integration.py

**Summary**
Plan 19-02 将验证结果串联到 settlement 和 gate 阶段，实现了 D-06~D-08 定义的数据流。两文件职责分明，但存在接口契约不够明确的问题。

**Strengths**
- **数据流清晰**: verifier → settlement → gate 链路符合 D-06/D-07/D-08
- **统计全面**: settlement report 包含完整指标
- **gate 逻辑简单**: 基于 API + E2E 双 settlement 的结论，逻辑直观易懂

**Concerns**
- **[HIGH] chain 参数用途不明**: `generate_settlement(manifest_path, verdict_report, chain)` 中 chain 是什么？
- **[HIGH] settlement 与 verdict_report 同步风险**: 如果 manifest 更新但 verdict_report 未更新，数据不一致
- **[MEDIUM] gate 条件逻辑不完整**: (PASS, CONDITIONAL_PASS)、(CONDITIONAL_PASS, CONDITIONAL_PASS) 等组合未明确
- **[MEDIUM] 错误处理缺失**: 如果 settlement 文件不存在或格式错误，`evaluate_gate()` 如何处理？

**Suggestions**
- 添加 chain 参数文档或重命名为 `test_type` (api/e2e)
- 实现 settlement 文件校验函数
- 完善 gate 评估真值表，覆盖所有 3×3 组合（PASS/CONDITIONAL_PASS/FAIL）
- 添加 try-except 包装文件读取

**Risk Assessment: HIGH** — 接口契约模糊，错误处理缺失。

---

### Plan 19-03: Unit tests

**Summary**
复用 Phase 17 已有测试文件，覆盖 step_result、spec_adapter、environment_provision。但 Plan 未明确是否需要为新增的 independent_verifier、settlement_integration、gate_integration 补充测试。

**Concerns**
- **[HIGH] 新模块缺乏单元测试**: independent_verifier.py、settlement_integration.py、gate_integration.py 无对应测试文件
- **[MEDIUM] 覆盖率目标不明**: Phase 要求 TEST-04 单元测试套件，但未定义覆盖率阈值
- **[LOW] 集成测试缺失**: verifier→settlement→gate 链路的端到端测试在哪里？

**Suggestions**
- 新增 `tests/cli/lib/test_independent_verifier.py`
- 新增 `tests/cli/lib/test_settlement_integration.py`
- 新增 `tests/cli/lib/test_gate_integration.py`

**Risk Assessment: HIGH** — 新代码无测试覆盖，回归风险高。

---

## Consensus Summary

### Agreed Strengths
- Architecture aligns with D-01~D-08 locked decisions
- Data flow (verifier → settlement → gate) direction is correct
- Responsibility separation is clear (_categorize_items, _compute_confidence)
- Settlement statistics coverage is comprehensive

### Agreed Concerns (Highest Priority)

1. **conditional_pass criteria undefined** (BOTH reviewers: HIGH)
   - GATE-01 requires verdict to be pass/conditional_pass/fail, but conditional_pass generation condition not defined
   - Suggestion: Define explicit rule table: main flow fails condition → conditional_pass; non-core flow fails → conditional_pass

2. **coverage/failures definition unclear** (BOTH reviewers: HIGH)
   - Coverage denominator ambiguous (designed? executable? executed?)
   - Whether failures include blocked/uncovered items unclear
   - Suggestion: Define exact formula in code comments: `coverage = executed / designed`, `failures = count(lifecycle_status == 'failed')`

3. **New modules lack unit tests** (BOTH reviewers: HIGH)
   - independent_verifier, settlement_integration, gate_integration have no tests
   - TEST-04 requirement only covers Phase 17 tests
   - Suggestion: Add minimal test files for each new module covering key boundary conditions

4. **scenario_type default strategy undefined** (BOTH reviewers: HIGH/MEDIUM)
   - What to do when scenario_type is missing/empty?
   - Suggestion: Default to non_core_flow with warning log

5. **Zero-division risk in confidence calculation** (BOTH reviewers: MEDIUM)
   - `_compute_confidence()` when no executed items → divide by zero
   - Suggestion: Add guard: `if not total_executed: return 0.0`

6. **Gate merge logic incomplete** (BOTH reviewers: HIGH/MEDIUM)
   - Missing handling for conditional_pass, missing settlement
   - Suggestion: Define complete truth table for all 3x3 combinations

### Divergent Views
- **Codex**: Concerned about step_result.py creating duplicate with Phase 17 existing StepResult
- **Qwen**: More focused on error handling missing for file operations
- **Qwen**: Suggests evidence_refs format validation (Codex did not raise)
- **Codex**: Suggests making settlement "trust manifest only" (not raised by Qwen)

## Recommendations for Plan Update

Based on cross-reviewer consensus:

1. **Add conditional_pass logic** to independent_verifier.py:
   - main flow fails condition → FAIL (D-01 says 0 tolerance)
   - non-core flow fails condition → conditional_pass (flexible tolerance met but not exceeded)

2. **Document exact coverage formula**:
   - coverage = executed (lifecycle_status in passed/failed/blocked) / total (all items)
   - failures = count where lifecycle_status == 'failed'

3. **Add boundary unit tests** for new modules:
   - test_independent_verifier.py: coverage boundary, zero-division, conditional_pass
   - test_settlement_integration.py: verdict/confidence passthrough
   - test_gate_integration.py: merge matrix with all 9 combinations

4. **Define scenario_type default**: missing → non_core_flow + warning

5. **Complete gate truth table**: Document all 9 verdict combinations
