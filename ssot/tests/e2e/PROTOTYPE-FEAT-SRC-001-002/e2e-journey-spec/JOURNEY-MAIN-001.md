# E2E Journey Spec — JOURNEY-MAIN-001: 正式升级路径

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.main.happy |
| coverage_id | e2e.journey.main.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-001-002.AC-01 |

## Test Contract

### Entry Point

`/handoff/upgrade/verify` (or equivalent formal upgrade verification UI)

### Preconditions

- 用户已登录 (开发者/operator 角色)
- 存在有效的 handoff 对象，状态为 gate-approved
- gate decision 已生成且为 approve
- 系统中不存在相同 handoff 的已有 formal materialization

### User Steps

1. 导航至正式升级验证页面
2. 选择 handoff 对象: "handoff-e2e-001"
3. 确认 gate decision 存在且为 approve
4. 点击 "发起正式升级" 按钮
5. 等待系统响应
6. 查看 formal materialization 创建成功确认
7. 验证无并行 shortcut 存在

### Expected UI States

- Step 4: 升级按钮变为 loading/disabled 状态
- Step 5: 显示 "升级成功" 提示和 formal_materialization_id
- Step 6: 显示 handoff -> gate decision -> formal materialization 完整链路
- Step 7: 显示 "唯一路径验证通过" 确认

### Expected Network Events

- POST /api/v1/handoff/upgrade called once
- GET /api/v1/handoffs/{handoff_id} called to verify gate decision
- GET /api/v1/formal-materializations/{formal_id} called after create
- GET /api/v1/upgrade-path/verify called to confirm single path

### Expected Persistence

- reload_page_keeps_upgrade_status == true
- backend_formal_materialization_exists == true
- handoff_marked_as_upgraded == true

### Anti-False-Pass Checks

- no_console_error
- backend_formal_materialization_exists (not just local state)
- upgrade_path_is_unique (no parallel shortcuts)
- no_pending_network_requests_after_completion

### Evidence Required

- playwright_trace
- screenshot_final
- network_log
- persistence_assertion
- console_error_check_result
