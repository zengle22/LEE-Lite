# E2E Journey Spec — JOURNEY-EXCEPTION-002: 回流边界违规

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception-reflow.happy |
| coverage_id | e2e.journey.exception-reflow.happy |
| journey_id | JOURNEY-EXCEPTION-002 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-001-001.AC-02 |

## Test Contract

### Entry Point

`/loops/collaboration/verify` (or equivalent loop collaboration verification UI)

### Preconditions

- 用户已登录 (开发者/operator 角色)
- gate loop 已返回 revise decision
- execution loop 处于 completed 状态 (不允许重入)
- 存在待回流的对象

### User Steps

1. 导航至 loop 协作验证页面
2. 查看 gate revise decision 详情
3. 选择回流目标: "loop-exec-completed-001" (处于 completed 状态)
4. 选择回流对象: "pkg-reflow-001"
5. 填写回流原因: "gate_requested_revision"
6. 点击 "发起回流" 按钮
7. 等待系统响应
8. 查看回流边界违规错误
9. 修正回流目标为允许重入的 loop 或重置状态
10. 重新发起回流

### Expected UI States

- Step 6: 提交按钮变为 loading/disabled 状态
- Step 7: 显示 "REENTRY_NOT_ALLOWED" 错误，包含目标 loop 当前状态
- Step 8: 错误面板显示目标 loop 状态和允许重入的状态列表
- Step 9: 修正成功提示
- Step 10: 回流成功提示

### Expected Network Events

- POST /api/v1/loops/reflow/re-enter called once (step 6) — returns 409
- GET /api/v1/loops/execution/status called to verify target loop state
- POST /api/v1/loops/reflow/re-enter called again (step 10) — returns 200

### Expected Persistence

- no_reflow_created_on_invalid_reentry == true
- gate_decision_state_unchanged_after_failed_attempt == true
- successful_reflow_after_correction == true

### Anti-False-Pass Checks

- no_console_error
- reflow_table_has_no_record_for_first_attempt
- error_response_contains_REENTRY_NOT_ALLOWED_code
- target_loop_state_unchanged_after_failed_reentry
- second_reflow_succeeds_with_valid_response

### Evidence Required

- playwright_trace
- screenshot_error_display
- screenshot_success_display
- network_log
- persistence_assertion
- console_error_check_result
