# ADR-047 Pilot Retrospective

## Pilot Summary

| 字段 | 值 |
|------|-----|
| **Pilot Scope** | FEAT-SRC-005-001 (主链候选提交与交接流) |
| **ADR Version** | v1.4 (Trial Approved) |
| **Start Date** | 2026-04-10 |
| **Status** | Design Complete, Execution Pending |

## What Was Accomplished

### Completed

| 交付物 | 状态 | 说明 |
|--------|------|------|
| pilot-plan.md | DONE | 候选评估 + 试点范围定义 |
| api-test-plan.md | DONE | 8 capabilities, 3 优先级矩阵, 裁剪规则 |
| api-coverage-manifest.yaml | DONE | 19 coverage items, 4 维状态字段 |
| api-test-spec (5 files) | DONE | CAND-SUBMIT, CAND-VALIDATE, HANDOFF-CREATE, HANDOFF-TRANSITION, GATE-EVAL |
| e2e-journey-plan.md | DONE | 4 journeys (1 main + 2 exception + 1 retry), API-derived mode |
| e2e-coverage-manifest.yaml | DONE | 4 journey items |
| e2e-journey-spec (4 files) | DONE | MAIN-001, EXCEPTION-001, EXCEPTION-002, RETRY-001 |
| gate-evaluator.py | DONE | 双链评估 + 防偷懒验证 (7/7 pass) |
| release_gate_input.yaml | DONE | 机器可读, YAML 可解析 |
| ci-gate-consumer.py | DONE | YAML 消费验证通过 |
| api-settlement-report | DONE | YAML + Markdown |
| e2e-settlement-report | DONE | YAML + Markdown |

### Not Completed (Intentionally Deferred)

| 交付物 | 原因 |
|--------|------|
| 测试脚本执行 | 需要实际后端服务或 mock server |
| Evidence 收集 | 依赖测试执行结果 |
| Manifest 状态更新 | 依赖执行结果 |

## What Worked Well

1. **四层资产分离**: plan/manifest/spec/settlement 职责清晰, 避免了相互污染
2. **Manifest 状态机**: lifecycle/mapping/evidence/waiver 四维分离有效防止状态伪造
3. **Gate Evaluator**: 自动化评估 + 防偷懒验证机制工作良好
4. **API-derived E2E 模式**: 在无 prototype 资产时, 从 feat 推导用户旅程的方案可行
5. **YAML 消费链**: release_gate_input.yaml 格式正确, CI 消费验证通过

## ADR vs Actual Gaps

| ADR 定义 | 实际情况 | 改进建议 |
|----------|----------|----------|
| E2E 锚定 prototype | 无 PROTOTYPE-FEAT-SRC-005-001 | ADR 应补充 "API-derived" 降级模式 |
| 测试脚本自动生成 | 手动创建 spec, 脚本生成待实现 | 需要接入 BMAD 或自研脚本生成器 |
| Evidence 收集 | 框架已就位, 实际收集待执行 | 定义最小证据 schema 模板 |

## Friction Points

1. **Prototype 缺失**: 试点 feat 没有对应的 prototype 资产, E2E 链被迫采用降级方案
2. **后端服务不可用**: 无法真实执行 API 测试, 只能验证设计和框架
3. **YAML 路径解析**: 初始 gate evaluator 路径有误, 需要修复
4. **128 个任务粒度**: 部分任务粒度过细, 实际执行时可合并

## Unforeseen Issues

1. 未预料到 `datetime.utcnow()` 在 Python 3.12+ 的 deprecation warning
2. `load_manifest_items` 的 `or` 逻辑在 API manifest 返回空列表时会 fallback 到 E2E

## Improvement Suggestions

### Schema
- 在 ADR 中明确 "API-derived E2E" 模式的适用范围和限制
- Manifest 增加 `derivation_mode` 字段标记 API-derived 来源

### Template
- 提供 manifest 初始化模板 (空结构), 减少手写 YAML 的工作量
- 提供 spec 模板文件, 避免重复编写元数据表格

### Process
- Phase 2-3 可并行执行 (API 链和 E2E 链独立)
- 测试脚本生成应在 spec 冻结后立即触发, 而非手动

### Anti-Laziness
- 7 项验证全部通过, 机制有效
- 建议增加 "spec 必须有至少 N 个断言" 的结构约束

## Promotion Recommendation

### Verdict: GO (with conditions)

**条件**:
1. 补充 ADR-047 的 "API-derived E2E" 降级模式定义
2. 在下一个试点中选择有真实 prototype 资产的 feat
3. 接入真实的后端服务或 mock server 以验证执行链路
4. 实现测试脚本自动生成 (BMAD 或自研)

**理由**:
- 四层资产结构设计合理, 职责分离清晰
- 防偷懒机制 7/7 验证通过, 有效防止 AI 偷懒
- Gate evaluator 正确识别 "未执行 = fail", 决策逻辑正确
- 整体架构可扩展到全量 feat

## Pilot Status Update

| 阶段 | 状态 | 完成度 |
|------|------|--------|
| Phase 1: 试点准备 | DONE | 100% |
| Phase 2: API 测试链 | DESIGN_COMPLETE | 80% (设计完成, 执行待完成) |
| Phase 3: E2E 测试链 | DESIGN_COMPLETE | 75% (设计完成, 执行待完成) |
| Phase 4: Gate 集成 | DONE | 100% |
| Phase 5: 试点总结 | DONE | 100% |
