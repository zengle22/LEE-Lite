# E2E Journey Spec — JOURNEY-EXCEPTION-001: 无效状态提交

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception-state.happy |
| coverage_id | e2e.journey.exception-state.happy |
| journey_id | JOURNEY-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-001-001.Constraints |

## Test Contract

### Entry Point

`/loops/collaboration/verify` (or equivalent loop collaboration verification UI)

### Preconditions

- 用户已登录 (开发者/operator 角色)
- execution loop 处于 completed 状态 (非 active)
- gate loop 处于 ready 状态
- 存在 candidate package 对象

### User Steps

1. 导航至 loop 协作验证页面
2. 选择 execution loop: "loop-exec-completed-001" (处于 completed 状态)
3. 填写候选对象引用: "pkg-e2e-001"
4. 选择目标 gate: "gate-mainline-001"
5. 选择 transition intent: "revision"
6. 点击 "提交执行循环对象" 按钮
7. 等待系统响应
8. 查看错误提示详情
9. 重置 loop 状态为 active
10. 重新提交

### Expected UI States

- Step 6: 提交按钮变为 loading/disabled 状态
- Step 7: 显示 "LOOP_STATE_INVALID" 错误，包含当前状态 "completed"
- Step 8: 错误详情面板显示当前 loop 状态和允许提交的状态列表
- Step 9: 状态重置成功提示
- Step 10: 提交成功提示，进入正常流程

### Expected Network Events

- POST /api/v1/loops/execution/submit called once (step 6) — returns 409
- GET /api/v1/loops/execution/status called to verify current state
- POST /api/v1/loops/execution/reset-state called (step 9)
- POST /api/v1/loops/execution/submit called again (step 10) — returns 201

### Expected Persistence

- no_submission_created_on_invalid_state == true
- state_reset_record_exists == true
- successful_submission_after_reset == true

### Anti-False-Pass Checks

- no_console_error
- submission_table_has_no_record_for_first_attempt
- error_response_contains_LOOP_STATE_INVALID_code
- state_reset_actually_occurred_in_persistence_layer
- second_submission_succeeds_with_valid_response

### Evidence Required

- playwright_trace
- screenshot_error_display
- screenshot_success_display
- network_log
- persistence_assertion
- console_error_check_result
