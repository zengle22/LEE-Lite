# E2E Journey Plan — FEAT-SRC-003-005 (API-Derived)

## Plan Metadata

| 字段 | 值 |
|------|-----|
| prototype_id | PROTOTYPE-FEAT-SRC-003-005 (API-Derived) |
| plan_version | v1.0 |
| created_at | 2026-04-11 |
| source | ADR-047 pilot execution — API-derived mode |
| anchor_type | feat (derived) |

## Source References

- `ssot/feat/FEAT-SRC-003-005__下游-skill-自动派发流.md`
- NOTE: 无独立 prototype 资产，旅程从 feat 功能契约推导

## Derived Journeys

从 FEAT-SRC-003-005 的功能行为推导以下用户旅程：

### Journey 列表

| # | Journey ID | Type | Priority | Description |
|---|-----------|------|----------|-------------|
| 1 | JOURNEY-MAIN-001 | main | P0 | Runner claim job -> 检测 progression_mode=auto-continue -> 自动派发到下游 skill -> 验证输入包完整 -> skill 执行启动 |
| 2 | JOURNEY-EXCEPTION-001 | exception | P0 | Runner 尝试派发 progression_mode=hold 的 job -> 系统阻止自动派发 -> job 保留 |
| 3 | JOURNEY-EXCEPTION-002 | exception | P0 | 下游 skill 不存在 -> 派发失败 -> 系统回写 execution outcome -> 不静默丢失 |
| 4 | JOURNEY-EXCEPTION-003 | exception | P1 | 输入包引用缺失或不可达 -> 系统校验失败 -> 返回参数错误 |
| 5 | JOURNEY-RETRY-001 | retry | P1 | 派发因网络/依赖失败 -> 修复后重试 -> 派发成功 |

### Journey 详情

#### JOURNEY-MAIN-001: 主旅程 — 自动派发

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Runner 已 claim job-ready-001 | job 处于 running 状态 |
| 2 | 系统检测 job 的 progression_mode=auto-continue | 确认允许自动派发 |
| 3 | 系统以 authoritative input package 调用 next skill | 调用目标 skill |
| 4 | 系统保留上游 refs 和 target-skill lineage | lineage 记录写入 |
| 5 | 下游 skill 开始执行 | skill 执行确认输出 |
| 6 | Operator 验证 invocation 记录 | invocation 文件存在且包含完整 refs |

#### JOURNEY-EXCEPTION-001: 异常旅程 — Hold Job 被阻止自动派发

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Runner 尝试处理 progression_mode=hold 的 job | 系统检测到 hold 模式 |
| 2 | 系统阻止自动派发 | 不调用下游 skill |
| 3 | 系统返回 HOLD_NOT_DISPATCHABLE 信息 | job 保持当前状态 |
| 4 | job 不被从 ready queue 移除 | job 仍在队列中等待 operator |

#### JOURNEY-EXCEPTION-002: 异常旅程 — 下游 Skill 不存在

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Runner 尝试派发 job 到不存在的 next skill | 系统查找 skill 失败 |
| 2 | 派发失败 | 返回 SKILL_NOT_FOUND 错误 |
| 3 | 系统回写 execution outcome | failure reason 记录到 job outcome |
| 4 | 验证 outcome 文件存在且包含失败信息 | 不静默丢失 |

#### JOURNEY-EXCEPTION-003: 异常旅程 — 输入包引用无效

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Runner 尝试派发 job 但 input refs 中的文件不存在 | 系统校验输入包 |
| 2 | 系统返回 MISSING_INPUT_REF 错误 | 列出缺失的引用 |
| 3 | 不执行派发 | 不调用下游 skill |
| 4 | Operator 看到具体缺失文件信息 | 错误信息指出哪些 ref 不可达 |

#### JOURNEY-RETRY-001: 重试旅程 — 派发失败后重试

| Step | User Action | Expected System Response |
|------|------------|------------------------|
| 1 | Runner 派发失败（如 skill 依赖未安装） | 返回依赖缺失错误 |
| 2 | Operator 安装缺失依赖 | 依赖就绪 |
| 3 | Operator 触发重试 | 系统重新尝试派发 |
| 4 | 派发成功 | skill 开始执行 |

## Journey Cut Records

| Cut Target | Cut Reason | Source Ref | Approver |
|------------|------------|------------|----------|
| journey_type.revisit | 试点 feat 为单次派发流程，无回访场景 | ADR-047 Section 4.2.3 | qa-lead |

## Minimum Journey Validation

| 规则 | 状态 | 说明 |
|------|------|------|
| 至少 1 条主旅程 | PASS | JOURNEY-MAIN-001 |
| 至少 1 条异常旅程 | PASS | JOURNEY-EXCEPTION-001, JOURNEY-EXCEPTION-002, JOURNEY-EXCEPTION-003 |
| 至少 1 条重试/回访旅程 | PASS | JOURNEY-RETRY-001 |
