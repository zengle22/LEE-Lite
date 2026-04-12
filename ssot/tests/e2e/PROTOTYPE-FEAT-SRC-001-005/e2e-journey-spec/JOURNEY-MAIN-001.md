# E2E Journey Spec — JOURNEY-MAIN-001: 技能接入与跨 skill E2E 闭环

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.main.happy |
| coverage_id | e2e.journey.main.happy |
| journey_id | JOURNEY-MAIN-001 |
| journey_type | main |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-001-005.AC-02 |

## Test Contract

### Entry Point

`/skill-onboarding/e2e-pilot` (or equivalent skill onboarding and E2E pilot UI)

### Preconditions

- 用户已登录 (开发者/operator 角色)
- 系统中存在至少一个 governed skill 待注册
- foundation FEAT 能力已建立
- pilot 链路所需的 producer、consumer、audit、gate 组件可用

### User Steps

1. 导航至技能接入与 E2E pilot 页面
2. 注册 governed skill: "skill-planner-001"
3. 配置接入矩阵，定义 producer/consumer/gate consumer 角色
4. 点击 "验证接入矩阵" 按钮
5. 查看 onboarding 验证通过结果
6. 配置迁移波次和 cutover/fallback 规则
7. 点击 "执行 E2E pilot 链" 按钮
8. 等待 pilot 链执行完成
9. 查看 E2E evidence 报告

### Expected UI States

- Step 4: 验证按钮变为 loading/disabled 状态
- Step 5: 显示 "Onboarding 验证通过" 和接入矩阵详情
- Step 6: 显示迁移波次配置界面
- Step 7: 执行按钮变为 loading/disabled 状态，显示进度条
- Step 8: 显示 "E2E pilot 链执行完成" 提示
- Step 9: 显示完整的 E2E evidence 报告，包含 producer -> consumer -> audit -> gate 完整链路

### Expected Network Events

- POST /api/v1/skills/onboard called for skill registration
- POST /api/v1/skills/matrix/verify called for matrix validation
- POST /api/v1/migration/wave/execute called for migration wave execution
- POST /api/v1/e2e-pilot/execute called for pilot chain execution
- GET /api/v1/e2e-pilot/evidence called for evidence report retrieval

### Expected Persistence

- reload_page_keeps_pilot_results == true
- backend_skill_registration_exists == true
- backend_e2e_evidence_exists == true

### Anti-False-Pass Checks

- no_console_error
- backend_e2e_evidence_exists (not just local state)
- pilot_chain_complete (all 4 steps executed: producer, consumer, audit, gate)
- no_pending_network_requests_after_completion

### Evidence Required

- playwright_trace
- screenshot_final
- network_log
- persistence_assertion
- console_error_check_result
- e2e_evidence_report
