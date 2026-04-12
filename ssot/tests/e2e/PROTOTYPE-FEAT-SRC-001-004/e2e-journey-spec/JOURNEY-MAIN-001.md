# E2E Journey Spec — JOURNEY-MAIN-001: 主链 IO 与路径治理

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.main.happy |
| coverage_id | e2e.journey.main.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-001-004.AC-01 |

## Test Contract

### Entry Point

`/io-path-governance/configure` (or equivalent IO path governance configuration UI)

### Preconditions

- 用户已登录 (开发者/operator 角色)
- 系统中存在待配置的主链 IO 路径
- 路径治理模块已初始化

### User Steps

1. 导航至主链 IO 路径配置页面
2. 配置手写入路径: "ssot/handoff/mainline/"
3. 配置目录边界: "ssot/formal/**"
4. 点击 "验证 IO 边界" 按钮
5. 查看 IO 边界验证通过结果
6. 执行正式写入操作
7. 查看写入确认和 path/mode 约束遵守状态

### Expected UI States

- Step 4: 验证按钮变为 loading/disabled 状态
- Step 5: 显示 "IO 边界验证通过" 和受治理路径列表
- Step 6: 写入按钮变为 loading/disabled 状态
- Step 7: 显示 "写入成功，path/mode 约束已遵守" 确认

### Expected Network Events

- POST /api/v1/io-scope/validate called for IO boundary check
- POST /api/v1/io/write called for formal write operation
- GET /api/v1/io/write-status called for write confirmation
- GET /api/v1/path-governance/status called for governance status

### Expected Persistence

- reload_page_keeps_io_config == true
- backend_io_config_exists == true
- formal_write_persisted_with_correct_path == true

### Anti-False-Pass Checks

- no_console_error
- backend_io_config_exists (not just local state)
- write_path_matches_governed_path
- no_pending_network_requests_after_completion

### Evidence Required

- playwright_trace
- screenshot_final
- network_log
- persistence_assertion
- console_error_check_result
