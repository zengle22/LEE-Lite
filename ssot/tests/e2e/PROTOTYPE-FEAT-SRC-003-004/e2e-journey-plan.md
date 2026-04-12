# E2E Journey Plan — FEAT-SRC-003-004 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-003-004 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FECT-SRC-003-004__execution-runner-自动取件流.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-003-004 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | Runner 自动扫描 ready queue -> 发现 job -> claim 成功 -> 状态转为 running -> 验证 ownership |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | 两个 Runner 同时 claim 同一 job -> 仅一个成功 -> 另一个返回 ALREADY_CLAIMED -> 验证 single-owner |
| 3 | JOURNEY-EXCEPTION-002 | exception | P0 | Ready queue 为空 -> Runner 扫描无 job -> 系统正确处理空队列 -> 不报错或优雅处理 |
| 4 | JOURNEY-EXCEPTION-003 | exception | P1 | Ready queue 不存在 -> Runner 扫描失败 -> 返回队列不存在错误 |
| 5 | JOURNEY-RETRY-001 | retry | P1 | Runner claim 失败（如权限问题）-> 修复后重试 -> claim 成功 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 自动取件

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Operator 放置 job 到 artifacts/jobs/ready | job 文件存在 |
| 2 | Runner 自动扫描 ready queue | 发现新 job |
| 3 | Runner 执行 claim | 输出 claim 成功确认 |
| 4 | 系统转移 job 状态: ready -> running | 状态更新确认 |
| 5 | Operator 验证 ownership 记录 | ownership 文件/日志存在 |
| 6 | Operator 验证 job 不在 ready queue | 文件已从 ready 移除或标记 |

#### JOURNEY-EXCEPTION-001: 异常旅程 — 并发 Claim 竞争

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 两个 Runner 实例同时发现同一 job | 两者都尝试 claim |
| 2 | Runner A 执行 claim 先到达 | 系统接受 claim，标记 owner=Runner-A |
| 3 | Runner B 执行 claim 到达 | 系统返回 ALREADY_CLAIMED 错误，拒绝 |
| 4 | 验证仅 Runner A 拥有 ownership | 只有 Runner A 的 ownership 记录存在 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 空队列

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | artifacts/jobs/ready 目录存在但无 job 文件 | 目录为空 |
| 2 | Runner 扫描 ready queue | 扫描完成，发现 0 个 job |
| 3 | 系统不报错，正常等待 | 无错误输出 |
| 4 | Runner 进入等待/轮询状态 | 准备下次扫描 |

#### JOURNEY-EXCEPTION-003: 异常旅程 — 队列不存在

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | artifacts/jobs/ready 目录不存在 | 路径无效 |
| 2 | Runner 尝试扫描 | 系统返回 QUEUE_NOT_FOUND 错误 |
| 3 | Runner 停止自动取件 | 不继续尝试 |
| 4 | Operator 看到明确的修复指导 | 错误消息说明需创建目录 |

#### JOURNEY-RETRY-001: 重试旅程 — Claim 失败后重试

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Runner 尝试 claim job 但目录权限不足 | 系统返回 PERMISSION_DENIED 错误 |
| 2 | Operator 修复目录权限 | 权限已更正 |
| 3 | Runner 重试 claim | claim 成功 |
| 4 | 验证 ownership 已建立 | ownership 记录存在 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次取件流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002, JOURNEY-EXCEPTION-003 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
