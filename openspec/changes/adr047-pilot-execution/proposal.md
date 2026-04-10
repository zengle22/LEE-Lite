# Change: ADR-047 Pilot Execution - Dual-Chain Testing Architecture

## Why

ADR-047 (v1.4, Trial Approved) 定义了双链测试治理架构：
- **API 测试链**锚定 feat，确保功能覆盖完整
- **E2E 测试链**锚定 prototype，确保用户旅程覆盖
- **BMAD** 作为能力层集成，非治理层
- **放行门**基于 manifest + evidence，非叙述性报告

当前项目的测试体系存在以下问题：
- 单一 testset 无法区分 API 功能测试和 E2E 用户旅程测试
- 测试覆盖定义权在执行阶段，导致范围漂移
- 放行依据是叙述性报告，无法机器消费
- AI 执行代理可能用 happy path 跳过边界测试

ADR-047 通过四层资产结构（plan → manifest → spec → settlement）和 6 层防偷懒机制，从根本上解决这些问题。

**试点范围**:
- 选择 `FEAT-SRC-005-001__微信登录核心流程` 作为 API 链试点
- 选择 `PROTOTYPE-FEAT-SRC-005-001__微信登录核心流程` 作为 E2E 链试点
- 验证完整流程：plan → manifest → spec → tests → evidence → settlement → release_gate_input
- 产出可复用的测试工作流 skill

**试点选择理由**:
- 微信登录流程边界清晰，I/O 合约明确
- 有 3 个验收检查，覆盖主流程和异常流程
- 已有 12 个 UI 状态定义，适合 E2E 验证
- 已有 PRD-001 的 6/6 通过测试报告，可作为基线

## What Changes

### 新增四层测试资产

#### API 测试链
1. **api-test-plan**: 从 feat 提取的测试范围定义
2. **api-coverage-manifest**: 覆盖项追踪（含 lifecycle/mapping/evidence/waiver 四维度状态）
3. **api-test-spec**: 每个覆盖项的测试合约定义
4. **api-settlement-report**: API 测试结算结果

#### E2E 测试链
1. **e2e-journey-plan**: 从 prototype 提取的用户旅程定义
2. **e2e-coverage-manifest**: 旅程覆盖项追踪（含分层状态字段）
3. **e2e-journey-spec**: 每个旅程的测试合约定义
4. **e2e-settlement-report**: E2E 测试结算结果

### 新增 Gate 集成
1. **release_gate_input.yaml**: 机器可读的放行输入文件
2. **Gate Evaluator**: 基于 manifest + settlement 的自动评估器
3. **CI 消费流水线**: 消费 release_gate_input.yaml 的 pass/fail 决策

### 新增 Skill 入口
1. **/ll-qa-feat-to-apiplan**: 从 feat 生成 API 测试计划
2. **ll-qa-prototype-to-e2eplan**: 从 prototype 生成 E2E 测试计划
3. **ll-qa-api-manifest-init**: 初始化 API 覆盖清单
4. **ll-qa-e2e-manifest-init**: 初始化 E2E 覆盖清单
5. **ll-qa-api-spec-gen**: 生成 API 测试规格
6. **ll-qa-e2e-spec-gen**: 生成 E2E 旅程规格
7. **ll-qa-gate-evaluate**: 执行放行门评估
8. **ll-qa-settlement**: 生成测试结算报告

### 新增防偷懒机制
1. **结构约束**: manifest items 在执行前冻结
2. **制度约束**: 所有裁剪必须带 cut_record（含 approver 和 source_ref）
3. **计算约束**: waiver_status=pending 仍计入 failed 统计
4. **Schema 约束**: lifecycle_status 与 evidence_status 一致性检查
5. **规则约束**: E2E 最小异常旅程覆盖要求
6. **证据约束**: 执行日志哈希绑定 + CI 真实执行验证

## Impact

### Affected Directories
- `openspec/changes/adr047-pilot-execution/` - 新增 openspec 变更
- `ssot/adr/ADR-047-测试体系重建 - 双链治理.md` - 参考文档（已存在）

### Pilot Artifacts (will be created during execution)
- `ssot/tests/api/FEAT-SRC-005-001/` - API 测试资产
  - `api-test-plan.md`
  - `api-coverage-manifest.yaml`
  - `api-test-spec/` (per capability)
  - `api-settlement-report.md`
- `ssot/tests/e2e/PROTOTYPE-FEAT-SRC-005-001/` - E2E 测试资产
  - `e2e-journey-plan.md`
  - `e2e-coverage-manifest.yaml`
  - `e2e-journey-spec/` (per journey)
  - `e2e-settlement-report.md`
- `ssot/tests/gate/release_gate_input.yaml` - 放行输入

### Dependencies
- ADR-047 (v1.4, Trial Approved) - 治理规则定义
- `FEAT-SRC-005-001` - API 测试锚点
- `PROTOTYPE-FEAT-SRC-005-001` - E2E 测试锚点
- BMAD skills: `/bmad-testarch-framework`, `/bmad-qa-generate-e2e-tests`
- 现有测试基础设施: pytest, go test, Playwright

## Success Criteria

### 功能验收
- [ ] API 测试链完整走完（plan → manifest → spec → tests → evidence → settlement）
- [ ] E2E 测试链完整走完（plan → manifest → spec → tests → evidence → settlement）
- [ ] Gate evaluator 正确生成 release_gate_input.yaml
- [ ] 裁剪记录带审批链路（cut_record with approver + source_ref）
- [ ] 分层状态字段（lifecycle/mapping/evidence/waiver）正确追踪

### 防偷懒机制验收
- [ ] **结构约束**: manifest item count = plan capabilities × required dimensions
- [ ] **制度约束**: 所有 cut 记录有 approver 和 source_ref
- [ ] **计算约束**: waiver_status=pending 不计入 waiver，仍反映在统计中
- [ ] **Schema 约束**: lifecycle_status=passed 但 evidence_status=missing 时 gate 拒绝
- [ ] **规则约束**: 只跑主旅程时，gate 因异常旅程覆盖不足而失败
- [ ] **证据约束**: 无 evidence 的 case 不算 executed
- [ ] **剩余风险缓解**: 至少实施一项（执行日志哈希绑定 / CI 真实执行验证 / 抽样回放）

### 交付物验收
- [ ] 试点回顾报告（pilot-retrospective.md）
- [ ] 可复用的测试工作流 skill 模板
- [ ] ADR-047 试点发现更新（如需要）
- [ ] 推广建议（go/no-go for broader adoption）

## Migration Plan

### 阶段顺序执行
1. **试点准备** (1-2 天): 候选评估 + 目录结构创建
2. **API 测试链** (2-3 天): 从 plan 到 settlement 的完整链路
3. **E2E 测试链** (2-3 天): 从 plan 到 settlement 的完整链路
4. **Gate 集成** (1 天): 双链合并 + release_gate_input 生成
5. **试点总结** (1 天): 经验捕获 + skill 模板化

### 回滚策略
- 试点不影响现有测试体系，是新增验证
- 如试点失败，保留所有资产作为改进参考
- ADR-047 状态从 "Trial Approved" 可退回为 "Draft"
