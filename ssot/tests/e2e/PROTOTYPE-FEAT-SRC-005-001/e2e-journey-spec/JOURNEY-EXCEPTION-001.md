# E2E Journey Spec — JOURNEY-EXCEPTION-001: 校验失败

## Case Metadata

| 字段 | 值 |
|------|-----|
| case_id | e2e_case.journey.exception.validation-fail |
| coverage_id | e2e.journey.exception.validation-fail |
| journey_id | JOURNEY-EXCEPTION-001 |
| journey_type | exception |
| priority | P0 |
| source_prototype_ref | FEAT-SRC-005-001.Constraints.candidate-validation |

## Test Contract

### Entry Point

`/candidate-submit`

### Preconditions

- 用户已登录
- Mock backend 配置为对缺少 proposal 的请求返回 400

### User Steps

1. 导航至候选提交页面
2. 仅填写 candidate package ID，不填写 proposal reference
3. 点击 "提交候选包" 按钮
4. 观察错误提示
5. 补充 proposal reference
6. 再次点击 "提交候选包"
7. 确认提交成功

### Expected UI States

- Step 3: 提交按钮变为 loading
- Step 4: 显示红色错误提示，高亮缺失的 proposal 字段
- Step 5: 错误提示消失，表单可重新提交
- Step 7: 显示提交成功和 handoff 信息

### Expected Network Events

- POST /api/v1/candidate-packages/submit called (returns 400)
- POST /api/v1/candidate-packages/submit called again (returns 201)

### Expected Persistence

- 第二次提交后 handoff 在 backend 存在
- 第一次失败提交未创建 handoff

### Anti-False-Pass Checks

- no_console_error
- first_request_actually_failed (status 400)
- second_request_actually_succeeded (status 201)
- no_handoff_created_from_failed_submission

### Evidence Required

- playwright_trace
- screenshot_final
- network_log
- persistence_assertion
- console_error_check_result
