# E2E Journey Plan — FEAT-SRC-005-001 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-005-001 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-10 |
| source | ADR-047 pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-005-001__主链候选提交与交接流.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-005-001 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | 用户提交候选包 -> 系统生成 handoff -> 进入 gate 审核 -> 用户查看结果 |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | 用户提交不完整候选包 -> 系统校验失败 -> 返回错误提示 -> 用户修正后重新提交 |
| 3 | JOURNEY-EXCEPTION-002 | exception | P1 | 用户重复提交同一候选包 -> 系统检测重复 -> 返回幂等响应 -> 不创建新 handoff |
| 4 | JOURNEY-RETRY-001 | retry | P1 | gate 评估失败 -> handoff 回流 -> 用户重新触发提交 -> 系统接受并重新流转 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 完整提交流转

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 用户导航至候选提交入口 | 系统显示提交表单 |
| 2 | 用户填写 candidate package 信息 | 系统实时校验输入 |
| 3 | 用户提交候选包 | 系统校验 package + proposal + evidence 完整性 |
| 4 | 系统生成 authoritative handoff | 用户看到 handoff 创建成功确认 |
| 5 | 系统自动推入 gate 消费链 | 用户看到 "已进入审核" 状态 |
| 6 | 用户刷新查看 gate 结果 | 用户看到 gate decision 结果 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 校验失败

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 用户导航至候选提交入口 | 系统显示提交表单 |
| 2 | 用户提交缺少 proposal 的候选包 | 系统拒绝提交 |
| 3 | 系统返回具体错误字段 | 用户看到错误高亮和修复建议 |
| 4 | 用户补充缺失字段重新提交 | 系统校验通过并进入步骤 4 的主旅程 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 重复提交

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 用户已提交过 candidate package X | 系统已有 handoff for X |
| 2 | 用户再次提交相同的 candidate package X | 系统识别为重复提交 |
| 3 | 系统返回现有 handoff 引用 | 不创建新 handoff，返回已有对象 |

#### JOURNEY-RETRY-001: 重试旅程 — Gate 回流

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 用户之前提交的候选包在 gate 被拒绝 | 系统显示 gate decision = reject |
| 2 | 用户修正 candidate package 后重新提交 | 系统接受修正后的提交 |
| 3 | 系统生成新 handoff 并重新推入 gate | 用户看到新 gate 审核状态 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次提交流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
