# E2E Journey Plan — FEAT-SRC-003-001 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-003-001 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-003-001__批准后-ready-job-生成流.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-003-001 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | Operator 触发 approve 后 job 生成 -> 系统检测 progression_mode=auto-continue -> 写入 artifacts/jobs/ready -> 验证 job 可被 runner 取件 |
| 2 | JOURNEY-MAIN-002 | main | P0 | Operator 触发 approve 后 job 生成 -> 系统检测 progression_mode=hold -> 路由到 hold 队列 -> 验证不泄漏到 ready queue |
| 3 | JOURNEY-EXCEPTION-001 | exception | P0 | Operator 对 revise 决策尝试生成 job -> 系统拒绝 -> 返回 DECISION_NOT_APPROVED 错误 -> 无副作用 |
| 4 | JOURNEY-EXCEPTION-002 | exception | P1 | Operator 提交非法 progression_mode -> 系统校验失败 -> 返回参数校验错误 |
| 5 | JOURNEY-RETRY-001 | retry | P1 | Job 生成失败（如目录不存在）-> Operator 修复后重试 -> 系统成功生成 job |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — Auto-Continue Job 生成

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 确认 gate approve | 系统接收 approve 决策 |
| 2 | 系统检测 progression_mode=auto-continue | 准备生成 ready job |
| 3 | 系统写入 artifacts/jobs/ready | 用户看到 job 创建成功确认 |
| 4 | Operator 验证 ready job 存在 | 文件存在且内容完整 |
| 5 | Operator 验证 job 可被 runner 取件 | job 包含 next_skill_target 和 authoritative refs |

#### JOURNEY-MAIN-002: 主旅程 — Hold Job 路由

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 确认 gate approve with progression_mode=hold | 系统接收 hold 决策 |
| 2 | 系统路由到 hold/waiting-human 队列 | 用户看到 hold job 创建成功确认 |
| 3 | Operator 验证 hold job 未泄漏到 ready queue | artifacts/jobs/ready 中无该 job |
| 4 | Operator 验证 hold job 在 hold 队列 | artifacts/jobs/hold 中存在该 job |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 非 Approve 决策被拒绝

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 尝试对 revise 决策生成 job | 系统拒绝请求 |
| 2 | 系统返回 DECISION_NOT_APPROVED 错误 | 用户看到明确错误信息和决策状态 |
| 3 | 用户确认无文件被创建 | artifacts/jobs/ready 和 hold 均无新文件 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 非法 Progression Mode

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 提交 progression_mode=invalid-mode | 系统校验参数 |
| 2 | 系统返回 INVALID_PROGRESSION_MODE 错误 | 用户看到合法枚举值列表 |
| 3 | 无 job 被生成 | artifacts/jobs/ 目录无变化 |

#### JOURNEY-RETRY-001: 重试旅程 — 生成失败后重试

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 触发 approve job 生成但 artifacts/jobs/ready 不存在 | 系统返回写入失败错误 |
| 2 | Operator 创建 artifacts/jobs/ready 目录 | 目录就绪 |
| 3 | Operator 重试 job 生成请求 | 系统成功生成 ready job |
| 4 | Operator 验证 job 文件存在 | 文件存在且内容完整 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次生成流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001, JOURNEY-MAIN-002 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
