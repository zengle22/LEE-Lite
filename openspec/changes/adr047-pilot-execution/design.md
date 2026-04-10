# ADR-047 Pilot Execution Design

## Context

**背景**: ADR-047 (v1.4, Trial Approved) 定义了双链测试治理架构，需要通过实际试点验证其可行性。

**约束**:
- 遵循 ADR-047 定义的四层资产结构
- 实现 6 层防偷懒机制
- 试点范围限定在单个 feat + prototype 对
- 产出可复用的测试工作流 skill

## Goals / Non-Goals

### Goals
- 完成 API 和 E2E 双链的完整流程试点
- 验证 manifest 状态机（lifecycle/mapping/evidence/waiver）
- 验证 gate evaluator 的机器可读决策
- 验证防偷懒机制的有效性
- 产出可复用的 skill 模板

### Non-Goals
- 不覆盖所有 23 个 feat（仅试点 1 个）
- 不实现完整的 CI/CD 流水线（仅验证 yaml 消费）
- 不处理 AI 非确定性测试（微信登录是确定性流程）
- 不处理性能测试（属于 NFR，后续补充）

## Architecture

### 四层资产流转

```
                    ┌──────────────┐
                    │   ADR-047    │
                    │ (治理规则)    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
    ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
    │    FEAT     │ │  Prototype  │ │  BMAD Skills  │
    │ SRC-005-001 │ │ SRC-005-001 │ │ (能力层)      │
    └──────┬──────┘ └──────┬──────┘ └──────┬───────┘
           │               │               │
           ▼               ▼               │
    ┌─────────────┐ ┌─────────────┐        │
    │  API Chain  │ │  E2E Chain  │        │
    │             │ │             │        │
    │  plan       │ │  plan       │        │
    │    ↓        │ │    ↓        │        │
    │  manifest   │ │  manifest   │        │
    │    ↓        │ │    ↓        │        │
    │  spec       │ │  spec       │        │
    │    ↓        │ │    ↓        │        │
    │  tests      │ │  tests      │        │
    │    ↓        │ │    ↓        │        │
    │  evidence   │ │  evidence   │        │
    │    ↓        │ │    ↓        │        │
    │  settlement │ │  settlement │        │
    └──────┬──────┘ └──────┬──────┘        │
           │               │               │
           └───────┬───────┘               │
                   ▼                       │
          ┌────────────────┐               │
          │ Gate Evaluator │◄──────────────┘
          └───────┬────────┘
                  ▼
     ┌────────────────────────┐
     │ release_gate_input.yaml│
     └───────┬────────────────┘
             ▼
     ┌────────────────┐
     │ CI/CD Consumer │
     │ (pass/fail)    │
     └────────────────┘
```

### 目录结构

```
ssot/tests/
├── api/
│   └── FEAT-SRC-005-001/
│       ├── api-test-plan.md              # 测试范围定义
│       ├── api-coverage-manifest.yaml    # 覆盖项追踪
│       ├── api-test-spec/                # 测试合约
│       │   ├── SPEC-AUTH-LOGIN-001.md
│       │   ├── SPEC-AUTH-LOGIN-002.md
│       │   └── SPEC-AUTH-DEVICE-001.md
│       └── api-settlement-report.md      # 结算报告
├── e2e/
│   └── PROTOTYPE-FEAT-SRC-005-001/
│       ├── e2e-journey-plan.md           # 旅程范围定义
│       ├── e2e-coverage-manifest.yaml    # 旅程覆盖追踪
│       ├── e2e-journey-spec/             # 旅程合约
│       │   ├── JOURNEY-MAIN-001.md       # 主旅程
│       │   ├── JOURNEY-EXCEPTION-001.md  # 异常旅程
│       │   └── JOURNEY-RETRY-001.md      # 重试旅程
│       └── e2e-settlement-report.md      # 结算报告
└── gate/
    ├── release_gate_input.yaml           # 放行输入
    └── gate-evaluator.py                 # 评估器脚本
```

## Decisions

### D1: Manifest 状态字段设计

**决策**: 使用四维分离的状态字段，防止状态伪造

```yaml
coverage_items:
  - capability: "POST /v1/auth/login/wechat"
    lifecycle_status: designed | in_progress | passed | failed | blocked | obsolete
    mapping_status: linked | unlinked
    evidence_status: complete | partial | missing
    waiver_status: none | pending | approved | rejected
    cut_record:        # 仅当 lifecycle_status=cut 时存在
      cut_reason: "低优先级，试点范围外"
      source_ref: "ADR-047 Section 4.1.3"
      approver: "qa-lead"
      approved_at: "2026-04-10T10:00:00Z"
```

**原因**: 单一 status 字段容易被伪造（如 lifecycle_status=passed 但实际无证据），四维分离确保：
- lifecycle_status 反映测试生命周期进度
- evidence_status 强制证据收集
- waiver_status 区分豁免状态
- mapping_status 确保与 feat 关联

### D2: Gate 统计口径

**决策**: 明确定义 pass rate 计算公式

```
总覆盖项 = manifest.items 中 lifecycle_status != obsolete 的数量
已豁免项 = waiver_status == approved 的数量
有效分母 = 总覆盖项 - 已豁免项
通过项 = lifecycle_status == passed && evidence_status == complete
通过率 = 通过项 / 有效分母

# 注意: waiver_status=pending 不计入已豁免项
# 仍作为 failed/blocked 统计
```

**原因**: 防止通过 pending waiver 人为降低分母来"通过" gate

### D3: 证据要求

**决策**: 不同类型的测试要求不同的证据类型

| 测试类型 | 必需证据 |
|---------|---------|
| API 测试 | request_log, response_log, assertion_result |
| E2E 测试 | playwright_trace, network_log, screenshot_on_failure |
| 集成测试 | db_state_before, db_state_after, api_call_log |

**原因**: 防止仅凭 "测试通过" 的文字描述作为证据

### D4: 防偷懒机制实施

**决策**: 6 层约束 + 剩余风险缓解

| 约束层 | 实施点 | 验证方式 |
|--------|--------|---------|
| 结构约束 | manifest 初始化后冻结 | item count = plan × dimensions |
| 制度约束 | cut_record 必填 | 审计 cut_record 完整性 |
| 计算约束 | gate 统计排除逻辑 | 手工验证公式 |
| Schema 约束 | lifecycle vs evidence 一致性 | gate 拒绝不一致项 |
| 规则约束 | 最小旅程枚举 | 检查异常旅程覆盖率 |
| 证据约束 | evidence_required 字段 | spec 必须有此字段 |
| 剩余风险 | 执行日志哈希绑定 | CI 重新执行抽样验证 |

### D5: 试点测试用例选择

**决策**: 微信登录核心流程的测试覆盖

**API 链 (FEAT-SRC-005-001)**:
- AUTH-001: POST /v1/auth/login/wechat 正常登录
- AUTH-002: POST /v1/auth/login/wechat 微信授权失败
- AUTH-003: POST /v1/auth/login/wechat Token 过期刷新
- AUTH-004: 设备绑定校验
- AUTH-005: JWT Token 生命周期管理

**E2E 链 (PROTOTYPE-FEAT-SRC-005-001)**:
- JOURNEY-001: 微信登录 → 手机号绑定 → 进入首页 (主旅程)
- JOURNEY-002: 微信登录失败 → 重试 → 成功 (异常→恢复)
- JOURNEY-003: 手机号绑定失败 → 修改 → 重试 (异常→恢复)
- JOURNEY-004: Token 过期 → 自动刷新 → 继续操作 (后台异常)

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 选定 feat/prototype 不满足最小可测试性 | 高 | 阶段 1 严格评估，有备用候选 |
| BMAD skill 集成失败 | 中 | 有手动生成脚本的降级方案 |
| Gate evaluator 逻辑复杂 | 中 | 从简单 YAML 生成开始，迭代 |
| 证据收集标准不明确 | 低 | 在阶段 2 早期定义最小证据 schema |
| AI 执行代理跳过边界测试 | 高 | 6 层防偷懒约束 + 证据哈希绑定 |
| 试点周期超预期 | 低 | 每阶段限时，捕获部分经验 |

## Migration Plan

### 阶段 1: 试点准备 (1-2 天)

1. 评估候选 feat/prototype 的最小可测试性
2. 确认试点对：FEAT-SRC-005-001 + PROTOTYPE-FEAT-SRC-005-001
3. 创建测试资产目录结构
4. 创建试点追踪文档

**产出**:
- 选定的 feat + prototype 对及选择理由
- 目录结构已创建

### 阶段 2: API 测试链试点 (2-3 天)

1. 从 feat 提取生成 `api-test-plan.md`
2. 初始化 `api-coverage-manifest.yaml`（所有 coverage items，lifecycle_status=designed）
3. 应用覆盖裁剪规则，每个 cut 必须有 cut_record
4. 为每个 coverage item 创建 `api-test-spec`
5. 生成/编写 API 测试脚本
6. 执行 API 测试
7. 收集证据（request_log, response_log, assertion_result）
8. 更新 manifest 状态
9. 生成 `api-settlement-report.md`

**防偷懒检查点**:
- [ ] manifest item count = plan capabilities × required dimensions
- [ ] 所有 cut 有 cut_record with approver
- [ ] spec 有 evidence_required 字段
- [ ] lifecycle_status=passed 时 evidence_status=complete

### 阶段 3: E2E 测试链试点 (2-3 天)

1. 从 prototype 提取生成 `e2e-journey-plan.md`
2. 应用旅程识别规则（主旅程 + 最小异常旅程）
3. 初始化 `e2e-coverage-manifest.yaml`
4. 为每个 journey 创建 `e2e-journey-spec`
5. 生成 Playwright E2E 测试脚本
6. 执行 E2E 测试
7. 收集证据（playwright_trace, network_log, screenshot_on_failure）
8. 更新 manifest 分层状态
9. 生成 `e2e-settlement-report.md`

**防偷懒检查点**:
- [ ] 满足最小旅程数（主旅程 + 至少 1 个异常旅程）
- [ ] manifest item count >= plan journeys
- [ ] spec 有 anti_false_pass_checks 字段
- [ ] evidence_refs 包含 playwright_trace + network_log

### 阶段 4: Gate 集成 (1 天)

1. 实现 gate evaluator 脚本
2. 从 manifests + settlements 生成 `release_gate_input.yaml`
3. 验证 gate 规则
4. 测试 CI 消费流程
5. 记录 gate 评估结果

**防偷懒检查点**:
- [ ] 分母统计排除 obsolete 和 waiver_status=approved
- [ ] waiver_status=pending 仍计入 failed
- [ ] 包含 execution_metadata.evidence_hash
- [ ] CI 重新执行抽样验证

### 阶段 5: 试点总结 (1 天)

1. 记录成功经验
2. 记录 ADR 与实际的差距
3. 识别 schema/template 改进点
4. 创建可复用的测试工作流 skill
5. 更新 ADR-047（如需要）
6. 给出推广建议（go/no-go）

## Rollback Plan

1. **试点不影响现有测试**: 所有资产在独立目录，不影响 tests/ 目录
2. **ADR 状态回退**: 如试点失败，ADR-047 从 "Trial Approved" 回退为 "Draft"
3. **资产保留**: 即使试点失败，保留所有资产作为改进参考

## Open Questions

1. BMAD 的 `/bmad-qa-generate-api-tests` skill 是否可用？（需要确认）
2. Gate evaluator 是用 Python 脚本还是 Go 工具实现？
3. 是否需要为试点创建独立的分支？
4. CI 消费环节是模拟验证还是接入真实 CI？
