# E2E Journey Spec — JOURNEY-RETRY-001: 下游规则违规

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.retry.happy |
| coverage_id | e2e.journey.retry.happy |
| journey_id | JOURNEY-RETRY-001 |
| journey_type | retry |
| priority | P1 |
| source_prototype_ref | FEAT-SRC-001-001.AC-03 |

## Test Contract

### Entry Point

`/loops/collaboration/verify` (or equivalent loop collaboration verification UI)

### Preconditions

- 用户已登录 (开发者/operator 角色)
- execution loop 处于 active 状态
- 下游 workflow "workflow-dev-feat-to-tech" 已注册
- 下游 workflow 注册了平行 handoff 规则 (违规状态)

### User Steps

1. 导航至 loop 协作验证页面
2. 选择 execution loop: "loop-exec-001"
3. 触发继承验证检查
4. 查看违规检测结果
5. 查看平行 handoff 规则违规详情
6. 移除下游平行规则，改为继承模式
7. 重新触发继承验证
8. 查看验证通过结果

### Expected UI States

- Step 3: 验证按钮变为 loading/disabled 状态
- Step 4: 显示 "PARALLEL_RULE_VIOLATION" 错误
- Step 5: 违规详情面板显示冲突规则名称、冲突对象和严重级别
- Step 6: 规则修正成功提示
- Step 7: 重新验证按钮可用
- Step 8: 验证通过，显示已继承规则列表

### Expected Network Events

- GET /api/v1/loops/inheritance/verify?downstream=workflow-dev-feat-to-tech called (step 3) — returns 409
- PUT /api/v1/loops/inheritance/fix called (step 6) — corrects the downstream rules
- GET /api/v1/loops/inheritance/verify called again (step 7) — returns 200

### Expected Persistence

- violation_record_exists == true
- downstream_compliance_status_updated_after_fix == true
- inheritance_rules_correctly_applied == true

### Anti-False-Pass Checks

- no_console_error
- violation_actually_detected (not pre-existing pass)
- downstream_workflow_compliance_status_changes_from_non-compliant_to_compliant
- inherited_rules_match_parent_configuration_after_fix

### Evidence Required

- playwright_trace
- screenshot_violation_display
- screenshot_success_display
- network_log
- persistence_assertion
- console_error_check_result
