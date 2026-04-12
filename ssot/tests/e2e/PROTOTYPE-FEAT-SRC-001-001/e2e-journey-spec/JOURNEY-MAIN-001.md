# E2E Journey Spec — JOURNEY-MAIN-001: 完整协作闭环

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.main.happy |
| coverage_id | e2e.journey.main.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-001-001.Scope |

## Test Contract

### Entry Point

`/loops/collaboration/verify` (or equivalent loop collaboration verification UI)

### Preconditions

- 用户已登录 (开发者/operator 角色)
- execution loop 处于 active 状态
- gate loop 处于 ready 状态
- human loop 可用
- 存在有效的 candidate package 对象

### User Steps

1. 导航至 loop 协作验证页面
2. 选择 execution loop: "loop-exec-001"
3. 填写候选对象引用: "pkg-e2e-001"
4. 选择目标 gate: "gate-mainline-001"
5. 选择 transition intent: "revision"
6. 点击 "提交执行循环对象" 按钮
7. 等待系统响应
8. 查看 gate-human 交接确认
9. 查看 loop 责任分离验证结果
10. 查看协作闭环完整状态

### Expected UI States

- Step 6: 提交按钮变为 loading/disabled 状态
- Step 7: 显示 "提交成功" 提示和 submission_id
- Step 8: 显示 handoff_id 和 gate-human 交接状态
- Step 9: 显示责任分离验证通过，无重叠检测
- Step 10: 显示完整的协作闭环状态汇总

### Expected Network Events

- POST /api/v1/loops/execution/submit called once
- POST /api/v1/loops/gate-human/handoff called after submission
- GET /api/v1/loops/responsibility/verify called for validation
- GET /api/v1/loops/collaboration/status called for final status display

### Expected Persistence

- reload_page_keeps_collaboration_status == true
- backend_submission_exists == true
- handoff_record_persisted == true

### Anti-False-Pass Checks

- no_console_error
- backend_submission_exists (not just local state)
- submission_id_matches_response_id
- no_pending_network_requests_after_completion
- responsibility_verification_result_matches_displayed_state

### Evidence Required

- playwright_trace
- screenshot_final
- network_log
- persistence_assertion
- console_error_check_result
