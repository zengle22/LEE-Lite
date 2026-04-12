# E2E Journey Spec — JOURNEY-MAIN-001: 对象分层与准入

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.main.happy |
| coverage_id | e2e.journey.main.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-001-003.Scope |

## Test Contract

### Entry Point

`/object-layering/verify` (or equivalent object layering verification UI)

### Preconditions

- 用户已登录 (开发者/operator 角色)
- 系统中同时存在 candidate 和 formal-stage 对象
- 业务 skill 未持有 gate 或 formal admission 权限

### User Steps

1. 导航至对象分层验证页面
2. 选择 candidate layer 对象: "cand-layer-001"
3. 选择 formal layer 对象: "formal-layer-001"
4. 点击 "验证分层分离" 按钮
5. 查看分层验证通过结果
6. 配置 consumer 基于 formal refs 的准入规则
7. 点击 "验证准入规则" 按钮
8. 查看完整的分层状态报告

### Expected UI States

- Step 4: 验证按钮变为 loading/disabled 状态
- Step 5: 显示 "分层分离验证通过" 和 formal layer 权威性确认
- Step 6: 显示 consumer 准入配置界面
- Step 7: 验证按钮变为 loading/disabled 状态
- Step 8: 显示完整的分层状态和准入验证结果

### Expected Network Events

- POST /api/v1/layers/verify called for layer separation check
- GET /api/v1/layers/{layer_id} called for each layer
- POST /api/v1/consumer/admission/verify called for admission rule check
- GET /api/v1/layers/status called for final status report

### Expected Persistence

- reload_page_keeps_layering_status == true
- backend_layer_configuration_exists == true

### Anti-False-Pass Checks

- no_console_error
- backend_layer_config_exists (not just local state)
- layer_separation_result_matches_displayed_state
- no_pending_network_requests_after_completion

### Evidence Required

- playwright_trace
- screenshot_final
- network_log
- persistence_assertion
- console_error_check_result
