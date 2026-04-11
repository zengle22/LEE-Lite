# E2E Journey Spec — JOURNEY-MAIN-001: 完整提交流转

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.main.happy |
| coverage_id | e2e.journey.main.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-005-001.Scope.candidate-package-submission |

## Test Contract

### Entry Point

`/candidate-submit` (or equivalent candidate submission UI)

### Preconditions

- 用户已登录
- 系统中不存在相同 candidate package 的已有 handoff
- Mock backend 可用

### User Steps

1. 导航至候选提交页面
2. 填写 candidate package ID: "pkg-e2e-001"
3. 填写 proposal reference: "adr011-raw2src-fix-20260327-r1"
4. 上传/确认 evidence references
5. 点击 "提交候选包" 按钮
6. 等待系统响应
7. 查看 handoff 创建成功确认
8. 刷新页面查看 gate 审核状态

### Expected UI States

- Step 5: 提交按钮变为 loading/disabled 状态
- Step 6: 显示 "提交成功" 提示
- Step 7: 显示 handoff_id 和 status = "pending-intake"
- Step 8: 显示 gate 审核状态（试点阶段可为 mock "approved"）

### Expected Network Events

- POST /api/v1/candidate-packages/submit called once
- GET /api/v1/handoffs/{handoff_id} called after create
- GET /api/v1/gate/evaluate/{handoff_id} called for status check

### Expected Persistence

- reload_page_keeps_handoff_status == true
- backend_handoff_exists_for_user == true

### Anti-False-Pass Checks

- no_console_error
- backend_handoff_exists (not just local state)
- submission_id_matches_response_id
- no_pending_network_requests_after_completion

### Evidence Required

- playwright_trace
- screenshot_final
- network_log
- persistence_assertion
- console_error_check_result
