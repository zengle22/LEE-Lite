# E2E Journey Spec — JOURNEY-EXCEPTION-002: 重复提交

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.duplicate-submit |
| coverage_id | e2e.journey.exception.duplicate-submit |
| journey_id | JOURNEY-EXCEPTION-002 |
| journey_type | exception |
| priority | P1 |
| source_prototype_ref | FEAT-SRC-005-001.Scope.authoritative-handoff |

## Test Contract

### Entry Point

`/candidate-submit`

### Preconditions

- 用户已登录
- 系统中已存在 candidate package "pkg-dup-001" 的 handoff

### User Steps

1. 导航至候选提交页面
2. 填写已存在的 candidate package ID: "pkg-dup-001"
3. 填写 proposal reference
4. 点击 "提交候选包" 按钮
5. 观察系统响应

### Expected UI States

- Step 5: 显示 "该候选包已提交" 提示
- Step 5: 显示已有 handoff 的引用链接
- 不应创建新的 handoff

### Expected Network Events

- POST /api/v1/candidate-packages/submit called (returns 200 or 409 with existing handoff ref)
- GET /api/v1/handoffs/{existing_handoff_id} called to fetch existing data

### Expected Persistence

- 系统中仅存在 1 个 handoff for "pkg-dup-001"
- handoff 的 created_at 未变化

### Anti-False-Pass Checks

- no_console_error
- only_one_handoff_exists_for_package
- handoff_created_at_not_modified

### Evidence Required

- playwright_trace
- screenshot_final
- network_log
- persistence_assertion

---

# E2E Journey Spec — JOURNEY-RETRY-001: Gate 回流重试

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.retry.gate-rejection |
| coverage_id | e2e.journey.retry.gate-rejection |
| journey_id | JOURNEY-RETRY-001 |
| journey_type | retry |
| priority | P1 |
| source_prototype_ref | FEAT-SRC-005-001.Scope.gate-consumption |

## Test Contract

### Entry Point

`/candidate-submit` (with rejected handoff context)

### Preconditions

- 用户已登录
- Mock backend 配置：handoff "handoff-rejected-001" 状态为 "rejected"

### User Steps

1. 导航至候选提交页面
2. 系统显示已有被拒绝的 handoff
3. 用户修改 candidate package 信息
4. 点击 "重新提交" 按钮
5. 等待系统响应
6. 确认新 handoff 创建并进入 gate 审核

### Expected UI States

- Step 2: 显示被拒绝 handoff 的详情和拒绝原因
- Step 4: 提交按钮变为 loading
- Step 5: 显示 "重新提交成功" 提示
- Step 6: 显示新 handoff 的 gate 审核状态

### Expected Network Events

- GET /api/v1/handoffs/handoff-rejected-001 (returns rejected status)
- POST /api/v1/candidate-packages/resubmit called
- GET /api/v1/handoffs/{new_handoff_id} called after resubmission

### Expected Persistence

- 新 handoff 在 backend 存在
- 原 rejected handoff 保持不变

### Anti-False-Pass Checks

- no_console_error
- new_handoff_id_differs_from_old
- original_handoff_status_unchanged

### Evidence Required

- playwright_trace
- screenshot_final
- network_log
- persistence_assertion
