# E2E Journey Plan — FEAT-SRC-003-008 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-003-008 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-003-008__governed-skill-接入与-pilot-验证流.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-003-008 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | Operator 定义接入范围和 migration waves -> 系统验证 scope 合规 -> 执行 pilot 链 (producer -> consumer -> audit -> gate) -> 收集 pilot evidence -> 生成 cutover decision |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | Pilot 链仅通过组件级测试（非真实链路）-> 系统拒绝 -> 要求真实端到端链路验证 |
| 3 | JOURNEY-EXCEPTION-002 | exception | P1 | 接入范围试图扩展到 warehouse-wide 治理 -> 系统拒绝 -> 限制在 governed skill 范围 |
| 4 | JOURNEY-EXCEPTION-003 | exception | P1 | Pilot evidence 无法绑定到真实 approve->runner->next-skill 链路 -> 系统标记 evidence 无效 |
| 5 | JOURNEY-RETRY-001 | retry | P1 | Pilot 链执行失败（如某个环节 skill 不可用）-> 修复后重试 -> 完整链路通过 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 完整 Pilot 验证

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 定义 onboarding scope 和 migration waves | 系统验证 scope 合规 |
| 2 | Operator 定义 cutover/fallback 规则 | 规则存储确认 |
| 3 | Operator 执行 pilot 链 | 系统开始 producer -> consumer -> audit -> gate 流程 |
| 4 | Producer 生成 job | job 进入 ready queue |
| 5 | Runner 自动取件并 claim | job 进入 running |
| 6 | Runner 派发至 next skill | skill 开始执行 |
| 7 | Skill 执行完成，结果回写 | outcome 写入 done |
| 8 | Gate 评估 pilot 结果 | gate 生成 decision |
| 9 | 系统收集 pilot evidence | evidence 绑定完整链路 |
| 10 | 系统生成 integration matrix 和 cutover decision | 输出 adoption 报告 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 仅组件级测试

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 尝试用组件测试替代真实链路 | 系统检测链路类型 |
| 2 | 系统返回 COMPONENT_TEST_ONLY_REJECTED 错误 | 说明需要真实端到端链路 |
| 3 | pilot 不标记为通过 | pilot 状态保持 pending |
| 4 | Operator 看到需执行真实链路的指导 | 错误信息说明真实链路要求 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 越界接入范围

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 尝试将接入范围扩展到所有 repository skills | 系统校验 scope |
| 2 | 系统返回 SCOPE_OVERFLOW_REJECTED 错误 | 说明限制在 governed skill 范围 |
| 3 | onboarding scope 不更新 | 范围保持不变 |

#### JOURNEY-EXCEPTION-003: 异常旅程 — Pilot Evidence 无法绑定

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Pilot 链执行完成但某个环节（如 runner）的记录丢失 | 链路存在断裂 |
| 2 | 系统尝试绑定 evidence 到 approve->runner->next-skill 链 | 发现断裂 |
| 3 | 系统返回 BROKEN_EVIDENCE_CHAIN 警告 | 列出断裂的环节 |
| 4 | pilot evidence 标记为 incomplete | adoption 报告标记为 partial |

#### JOURNEY-RETRY-001: 重试旅程 — Pilot 链失败后重试

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Pilot 链执行中某个 skill 不可用 | 链执行失败 |
| 2 | Operator 修复 skill 可用性 | skill 恢复 |
| 3 | Operator 重试 pilot 链 | 系统从头执行完整链路 |
| 4 | Pilot 链完成 | evidence 收集成功 |
| 5 | 系统生成完整的 cutover decision | adoption 报告完成 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为一次性验证，回访场景由主链覆盖 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002, JOURNEY-EXCEPTION-003 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
