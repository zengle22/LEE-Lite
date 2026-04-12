# E2E Journey Plan — FEAT-SRC-003-006 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-003-006 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-003-006__执行结果回写与重试边界流.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-003-006 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | 下游 skill 执行完成 -> Runner 记录 done 结果 -> 验证 outcome 文件和证据 -> 验证状态转移 (running -> done) |
| 2 | JOURNEY-MAIN-002 | main | P0 | 下游 skill 执行失败 -> Runner 记录 failed 结果及 failure reason -> 验证失败证据与 attempt 绑定 |
| 3 | JOURNEY-EXCEPTION-001 | exception | P0 | 技能执行返回 retry-reentry -> Runner 记录 retry directive -> job 回到 execution semantics |
| 4 | JOURNEY-EXCEPTION-002 | exception | P1 | 尝试将 retry 结果写为 publish-only 状态 -> 系统拒绝 -> 要求回到 execution semantics |
| 5 | JOURNEY-RETRY-001 | retry | P1 | 结果回写失败（如磁盘满）-> 修复后重试 -> 回写成功 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — Done 结果回写

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 下游 skill 执行完成并返回结果 | skill 输出完成信号 |
| 2 | Runner 接收完成信号 | 准备回写结果 |
| 3 | Runner 记录 done outcome 和证据 | 写入 outcome 文件 |
| 4 | Job 状态从 running 转移到 done | 状态文件更新 |
| 5 | Operator 验证 outcome 文件存在 | 文件包含完成时间、证据引用 |

#### JOURNEY-MAIN-002: 主旅程 — Failed 结果回写

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 下游 skill 执行失败 | skill 输出错误信号 |
| 2 | Runner 接收失败信号 | 准备记录失败 |
| 3 | Runner 记录 failed outcome + failure reason + 证据 | 写入 outcome 文件 |
| 4 | Job 状态从 running 转移到 failed | 状态文件更新 |
| 5 | Operator 验证失败证据与 attempt 绑定 | outcome 文件包含 attempt_id |

#### JOURNEY-EXCEPTION-001: 异常旅程 — Retry/Reentry

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 技能执行返回 retry-reentry 指令 | runner 接收 retry 指令 |
| 2 | Runner 记录 retry-reentry outcome | 写入 retry outcome 文件 |
| 3 | Job 回到 execution semantics（非 publish-only） | job 状态指示需重新执行 |
| 4 | Operator 验证 retry directive 存在 | outcome 文件包含 retry 信息 |

#### JOURNEY-EXCEPTION-002: 异常旅程 — Retry 被错误改写为 Publish

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | 系统尝试将 retry 结果标记为 publish-only | 操作不符合规范 |
| 2 | 系统拒绝该状态转移 | 返回 INVALID_STATE_TRANSITION 错误 |
| 3 | job 不被标记为 published | 保持 execution 语义 |

#### JOURNEY-RETRY-001: 重试旅程 — 结果回写失败后重试

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Runner 尝试回写结果但磁盘满/权限不足 | 系统返回 WRITE_FAILED 错误 |
| 2 | Operator 修复磁盘空间/权限 | 存储就绪 |
| 3 | Operator 触发结果回写重试 | 系统重新回写 |
| 4 | 回写成功 | outcome 文件存在 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 结果回写为终态操作，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001, JOURNEY-MAIN-002 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
