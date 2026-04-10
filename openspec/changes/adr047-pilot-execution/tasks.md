# ADR-047 Pilot Execution Tasks

基于 proposal.md 和 design.md，执行 ADR-047 双链测试架构试点。

## 1. 试点准备 (Day 1-2)

### 1.1 候选评估
- [ ] 1.1.1 验证 FEAT-SRC-005-001 满足最小可测试性（能力定义、I/O 合约、业务规则、状态转换、成功/失败标准）
- [ ] 1.1.2 验证 PROTOTYPE-FEAT-SRC-005-001 满足最小可测试性（页面入口、主旅程、异常反馈、状态差异、页面反馈）
- [ ] 1.1.3 确认备用候选（FEAT-SRC-004-001 + PROTOTYPE-FEAT-SRC-002-004）
- [ ] 1.1.4 记录选择理由

### 1.2 目录结构创建
- [ ] 1.2.1 创建 `ssot/tests/api/FEAT-SRC-005-001/`
- [ ] 1.2.2 创建 `ssot/tests/api/FEAT-SRC-005-001/api-test-spec/`
- [ ] 1.2.3 创建 `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-005-001/`
- [ ] 1.2.4 创建 `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-005-001/e2e-journey-spec/`
- [ ] 1.2.5 创建 `ssot/tests/gate/`

### 1.3 试点追踪
- [ ] 1.3.1 创建 pilot-plan.md（范围 + 成功标准）
- [ ] 1.3.2 确认 ADR-047 版本（v1.3, Trial Approved）
- [ ] 1.3.3 确认 BMAD skill 可用性

## 2. API 测试链 (Day 2-4)

### 2.1 API 测试计划
- [ ] 2.1.1 从 FEAT-SRC-005-001 提取 capabilities
- [ ] 2.1.2 创建 `api-test-plan.md`（范围定义 + 优先级矩阵）
- [ ] 2.1.3 定义测试维度（正常流、异常流、边界条件）

### 2.2 API 覆盖清单
- [ ] 2.2.1 初始化 `api-coverage-manifest.yaml`
- [ ] 2.2.2 为每个 capability × dimension 创建 coverage item
- [ ] 2.2.3 所有 items 标记 `lifecycle_status=designed`
- [ ] 2.2.4 验证 item count = capabilities × dimensions（结构约束）
- [ ] 2.2.5 应用覆盖裁剪规则（按优先级矩阵）
- [ ] 2.2.6 每个 cut 项必须有 cut_record（含 approver + source_ref）

### 2.3 API 测试规格
- [ ] 2.3.1 为 AUTH-001（正常登录）创建 spec
- [ ] 2.3.2 为 AUTH-002（微信授权失败）创建 spec
- [ ] 2.3.3 为 AUTH-003（Token 过期刷新）创建 spec
- [ ] 2.3.4 为 AUTH-004（设备绑定校验）创建 spec
- [ ] 2.3.5 为 AUTH-005（JWT Token 生命周期）创建 spec
- [ ] 2.3.6 每个 spec 必须包含 evidence_required 字段
- [ ] 2.3.7 每个 spec 必须包含 anti_false_pass_checks

### 2.4 API 测试执行
- [ ] 2.4.1 编写/生成 API 测试脚本（pytest 或 go test）
- [ ] 2.4.2 执行 AUTH-001 测试，收集 request_log + response_log
- [ ] 2.4.3 执行 AUTH-002 测试，收集 error_response + assertion_result
- [ ] 2.4.4 执行 AUTH-003 测试，收集 token_refresh_log
- [ ] 2.4.5 执行 AUTH-004 测试，收集 device_binding_log
- [ ] 2.4.6 执行 AUTH-005 测试，收集 token_lifecycle_log
- [ ] 2.4.7 验证所有证据文件完整性

### 2.5 API Manifest 更新
- [ ] 2.5.1 更新 lifecycle_status（passed/failed/blocked）
- [ ] 2.5.2 更新 evidence_status（complete/partial/missing）
- [ ] 2.5.3 验证 lifecycle_status=passed 时 evidence_status=complete
- [ ] 2.5.4 记录更新日志

### 2.6 API 结算报告
- [ ] 2.6.1 生成 `api-settlement-report.md`
- [ ] 2.6.2 统计通过率
- [ ] 2.6.3 记录失败项和根因
- [ ] 2.6.4 记录裁剪项和审批链

## 3. E2E 测试链 (Day 4-7)

### 3.1 E2E 旅程计划
- [ ] 3.1.1 从 PROTOTYPE-FEAT-SRC-005-001 提取 journeys
- [ ] 3.1.2 应用旅程识别规则（主旅程 + 最小异常旅程枚举）
- [ ] 3.1.3 创建 `e2e-journey-plan.md`
- [ ] 3.1.4 验证满足最小旅程数（≥1 主旅程 + ≥1 异常旅程）

### 3.2 E2E 覆盖清单
- [ ] 3.2.1 初始化 `e2e-coverage-manifest.yaml`
- [ ] 3.2.2 为每个 journey 创建 coverage item
- [ ] 3.2.3 所有 items 标记 `lifecycle_status=designed`
- [ ] 3.2.4 验证 item count >= plan journeys
- [ ] 3.2.5 应用覆盖裁剪规则
- [ ] 3.2.6 每个 cut 项必须有 cut_record

### 3.3 E2E 旅程规格
- [ ] 3.3.1 为 JOURNEY-001（主旅程）创建 spec
- [ ] 3.3.2 为 JOURNEY-002（登录失败→重试→成功）创建 spec
- [ ] 3.3.3 为 JOURNEY-003（手机号绑定失败→重试）创建 spec
- [ ] 3.3.4 为 JOURNEY-004（Token 过期→自动刷新）创建 spec
- [ ] 3.3.5 每个 spec 必须包含 anti_false_pass_checks
- [ ] 3.3.6 每个 spec 必须包含 evidence_required（playwright_trace + network_log）

### 3.4 E2E 测试执行
- [ ] 3.4.1 生成 Playwright 测试脚本
- [ ] 3.4.2 执行 JOURNEY-001，收集 playwright_trace + screenshot
- [ ] 3.4.3 执行 JOURNEY-002，收集 trace + network_log
- [ ] 3.4.4 执行 JOURNEY-003，收集 trace + network_log
- [ ] 3.4.5 执行 JOURNEY-004，收集 trace + network_log
- [ ] 3.4.6 验证所有 evidence_refs 非空且包含 required 类型

### 3.5 E2E Manifest 更新
- [ ] 3.5.1 更新 lifecycle_status
- [ ] 3.5.2 更新 evidence_status
- [ ] 3.5.3 验证证据完整性（playwright_trace + network_log 必须存在）
- [ ] 3.5.4 记录更新日志

### 3.6 E2E 结算报告
- [ ] 3.6.1 生成 `e2e-settlement-report.md`
- [ ] 3.6.2 统计通过率
- [ ] 3.6.3 记录失败项和根因
- [ ] 3.6.4 记录异常旅程覆盖率

## 4. Gate 集成 (Day 7-8)

### 4.1 Gate Evaluator
- [ ] 4.1.1 实现 gate evaluator 脚本（Python 或 Go）
- [ ] 4.1.2 读取 API manifest + settlement
- [ ] 4.1.3 读取 E2E manifest + settlement
- [ ] 4.1.4 读取 waiver 记录
- [ ] 4.1.5 计算通过率（排除 obsolete 和 approved waiver）
- [ ] 4.1.6 验证 waiver_status=pending 仍计入 failed
- [ ] 4.1.7 验证 lifecycle_status vs evidence_status 一致性

### 4.2 Release Gate Input
- [ ] 4.2.1 生成 `release_gate_input.yaml`
- [ ] 4.2.2 包含 API 链状态汇总
- [ ] 4.2.3 包含 E2E 链状态汇总
- [ ] 4.2.4 包含执行日志哈希（evidence_hash）
- [ ] 4.2.5 包含 gate 评估结果（pass/fail + 原因）

### 4.3 CI 消费验证
- [ ] 4.3.1 创建 CI 消费脚本（模拟）
- [ ] 4.3.2 验证 YAML 格式可解析
- [ ] 4.3.3 验证 pass/fail 决策逻辑
- [ ] 4.3.4 记录 CI 消费结果

### 4.4 防偷懒机制验证
- [ ] 4.4.1 验证：manifest items 执行前已冻结
- [ ] 4.4.2 验证：所有 cut 有 cut_record with approver
- [ ] 4.4.3 验证：waiver_status=pending 计入 failed 统计
- [ ] 4.4.4 验证：lifecycle_status=passed 但 evidence_status=missing 时 gate 拒绝
- [ ] 4.4.5 验证：只跑主旅程时 gate 因异常旅程覆盖不足失败
- [ ] 4.4.6 验证：无 evidence 的 case 不算 executed
- [ ] 4.4.7 验证：执行日志哈希绑定存在

## 5. 试点总结 (Day 8-9)

### 5.1 经验捕获
- [ ] 5.1.1 记录成功经验（what worked well）
- [ ] 5.1.2 记录 ADR 与实际的差距
- [ ] 5.1.3 记录流程中的摩擦点
- [ ] 5.1.4 记录未预料到的问题

### 5.2 改进建议
- [ ] 5.2.1 识别 schema 改进点
- [ ] 5.2.2 识别 template 改进点
- [ ] 5.2.3 识别流程改进点
- [ ] 5.2.4 识别防偷懒机制改进点

### 5.3 可复用资产
- [ ] 5.3.1 创建可复用的测试工作流 skill 模板
- [ ] 5.3.2 创建 gate evaluator 通用脚本
- [ ] 5.3.3 创建 manifest 初始化模板
- [ ] 5.3.4 创建 evidence 收集模板

### 5.4 试点回顾
- [ ] 5.4.1 生成 `pilot-retrospective.md`
- [ ] 5.4.2 给出推广建议（go/no-go）
- [ ] 5.4.3 如需要，更新 ADR-047
- [ ] 5.4.4 更新试点状态

## 任务依赖关系

```
Phase 1 (试点准备) ✅
  ├── Phase 2 (API 测试链)
  │     ├── 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6
  │     └── 防偷懒检查点: 2.2.4, 2.2.6, 2.3.6-7, 2.5.3
  │
  ├── Phase 3 (E2E 测试链)
  │     ├── 3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6
  │     └── 防偷懒检查点: 3.1.4, 3.2.4, 3.3.5-6, 3.4.6
  │
  ├── Phase 4 (Gate 集成)
  │     ├── 4.1 → 4.2 → 4.3 → 4.4
  │     └── 防偷懒检查点: 4.4.1-7
  │
  └── Phase 5 (试点总结)
        └── 依赖 Phase 2-4 完成
```

## 验收标准

### API 链验收
- [ ] api-test-plan.md 已创建且范围定义清晰
- [ ] api-coverage-manifest.yaml 所有 items 状态正确
- [ ] 至少 5 个 api-test-spec 已创建
- [ ] 测试脚本执行通过，证据完整
- [ ] api-settlement-report.md 已生成

### E2E 链验收
- [ ] e2e-journey-plan.md 已创建且旅程定义清晰
- [ ] e2e-coverage-manifest.yaml 所有 items 状态正确
- [ ] 至少 4 个 e2e-journey-spec 已创建（含主旅程 + 异常旅程）
- [ ] Playwright 测试执行通过，evidence_refs 完整
- [ ] e2e-settlement-report.md 已生成

### Gate 验收
- [ ] release_gate_input.yaml 已生成且格式正确
- [ ] Gate evaluator 正确计算通过率
- [ ] 防偷懒机制 7 项验证全部通过

### 交付物验收
- [ ] pilot-retrospective.md 已生成
- [ ] 可复用的 skill 模板已创建
- [ ] 推广建议已给出

## 估算时间

- **总计**: 9 个工作日
- **试点准备**: 2 天
- **API 测试链**: 3 天
- **E2E 测试链**: 4 天
- **Gate 集成**: 1-2 天（与 E2E 链有重叠）
- **试点总结**: 1-2 天

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| FEAT-SRC-005-001 不满足最小可测试性 | 高 | 切换到备用候选 |
| BMAD skill 不可用 | 中 | 手动编写测试脚本 |
| Gate evaluator 逻辑复杂 | 中 | 从简单版本开始，迭代 |
| 证据收集标准不明确 | 低 | 阶段 2 早期定义最小 schema |
| AI 执行代理跳过边界测试 | 高 | 6 层防偷懒约束 |
| 试点周期超预期 | 低 | 每阶段限时，捕获部分经验 |
