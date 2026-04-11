# ADR-047 双链测试治理 — 使用指南

> **ADR**: ADR-047 (v1.4, Trial Approved)
> **标题**: 测试体系重建——基于双链治理的 API / E2E 测试架构
> **试点状态**: Skills 已创建并安装，Execution 待实施
> **适用范围**: LL / LEE 项目及后续采用 SSOT 驱动研发的项目
> **最近更新**: 2026-04-11 — Phase 6 完成：8 个正式 Skill 入口已创建并安装到 Claude Code

---

## 一、总体架构

```
                    ┌─────────────────────────────────┐
                    │        ADR-047 (治理规则)        │
                    └────────────┬────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
    │ FEAT-SRC-*   │   │ PROTOTYPE-*  │   │ BMAD Skills       │
    │ (API 锚点)    │   │ (E2E 锚点)    │   │ (能力层插件)       │
    └──────┬───────┘   └──────┬───────┘   └──────┬───────────┘
           │                  │                  │
           ▼                  ▼                  │
    ┌──────────────┐  ┌──────────────┐           │
    │  API Chain   │  │  E2E Chain   │           │
    │  plan        │  │  plan        │           │
    │    ↓         │  │    ↓         │           │
    │  manifest    │  │  manifest    │           │
    │    ↓         │  │    ↓         │           │
    │  spec        │  │  spec        │           │
    │    ↓         │  │    ↓         │           │
    │  tests       │  │  tests       │           │
    │    ↓         │  │    ↓         │           │
    │  evidence    │  │  evidence    │           │
    │    ↓         │  │    ↓         │           │
    │  settlement  │  │  settlement  │           │
    └──────┬───────┘  └──────┬───────┘           │
           └────────┬────────┘                   │
                    ▼                            │
           ┌──────────────────┐                  │
           │  Gate Evaluator  │◄─────────────────┘
           └────────┬─────────┘
                    ▼
       ┌──────────────────────────┐
       │  release-gate-input.yaml │
       └────────┬─────────────────┘
                ▼
       ┌──────────────────┐
       │  CI/CD Consumer  │
       │  (pass/fail)     │
       └──────────────────┘
```

---

## 二、正式 Skill 列表（Phase 6 完成）

以下 8 个 Skill 已创建为正式 `skills/ll-qa-*/` 目录结构，并通过 `ll-skill-install` 安装到 Claude Code 全局。每个 Skill 包含 SKILL.md、合约定义、输入输出契约、执行器和监督器代理。

### Skill 1: ll-qa-feat-to-apiplan

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-feat-to-apiplan` |
| **来源** | `ssot/tests/templates/feat-to-api-test-plan.md` 升级 |
| **用途** | 从冻结的 feat 文档提取 capabilities，生成 `api-test-plan.md` |
| **触发场景** | 新 feat 通过 gate 后，需要定义 API 测试范围 |
| **输入** | 冻结的 `feat_freeze_package` + `feat_ref` |
| **输出** | `ssot/tests/api/{feat_id}/api-test-plan.md` |

**工作流**:
```
1. 验证 feat 已冻结 (status = frozen)
2. 从 Scope 提取 API capabilities，分配 capability_id + priority
3. 应用 ADR-047 测试维度矩阵（正常路径、参数校验、边界值、状态约束、权限、异常、幂等、数据副作用）
4. 应用优先级裁剪规则（P0 仅裁剪幂等/边界值，P1 裁剪更多，P2 仅保留正常路径）
5. 生成 api-test-plan.md（含范围定义 + 优先级矩阵）
```

---

### Skill 2: ll-qa-api-manifest-init

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-api-manifest-init` |
| **来源** | ADR-047 新增 |
| **用途** | 根据 api-test-plan 初始化 `api-coverage-manifest.yaml` |
| **输入** | `api-test-plan.md` |
| **输出** | `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml` |

**核心行为**:
- capability × dimension 全量展开为 coverage items
- 初始化四维状态：lifecycle_status=designed, mapping_status=unmapped, evidence_status=missing, waiver_status=none
- 应用裁剪规则，所有 cut 项必须有 cut_record（approver + source_ref）
- 结构约束：item count = capabilities × required dimensions

---

### Skill 3: ll-qa-api-spec-gen

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-api-spec-gen` |
| **来源** | ADR-047 新增 |
| **用途** | 为每个 coverage item 生成结构化 `api-test-spec` |
| **输入** | `api-coverage-manifest.yaml` |
| **输出** | `ssot/tests/api/{feat_id}/api-test-spec/SPEC-*.md` |

**每个 spec 包含**: endpoint 定义、request schema、expected response、assertions、evidence_required、anti_false_pass_checks、cleanup

---

### Skill 4: ll-qa-prototype-to-e2eplan

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-prototype-to-e2eplan` |
| **来源** | `ssot/tests/templates/prototype-to-e2e-journey-plan.md` 升级 |
| **用途** | 从 prototype 或 feat 推导用户旅程，生成 `e2e-journey-plan.md` |
| **模式** | A: Prototype-Driven / B: API-Derived（无 prototype 时降级） |
| **输入** | 冻结的 prototype package 或 FEAT |
| **输出** | `ssot/tests/e2e/{prototype_id}/e2e-journey-plan.md` |

**旅程识别规则**:
| 触发条件 | 必须识别的旅程 | 优先级 |
|----------|----------------|--------|
| 每个页面流 | 至少 1 条主旅程 | P0 |
| 每个表单页 | 至少 1 条校验失败异常旅程 | P0 |
| 每个网络请求点 | 至少 1 条网络失败异常旅程 | P1 |

---

### Skill 5: ll-qa-e2e-manifest-init

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-e2e-manifest-init` |
| **来源** | ADR-047 新增 |
| **用途** | 根据 e2e-journey-plan 初始化 `e2e-coverage-manifest.yaml` |
| **输入** | `e2e-journey-plan.md` |
| **输出** | `ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml` |

---

### Skill 6: ll-qa-e2e-spec-gen

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-e2e-spec-gen` |
| **来源** | ADR-047 新增 |
| **用途** | 为每个 journey 生成结构化 `e2e-journey-spec` |
| **输入** | `e2e-coverage-manifest.yaml` |
| **输出** | `ssot/tests/e2e/{prototype_id}/e2e-journey-spec/JOURNEY-*.md` |

**每个 spec 包含**: entry_point、user_steps、expected_ui_states、expected_network_events、expected_persistence、evidence_required（playwright_trace + screenshot 必须）、anti_false_pass_checks

---

### Skill 7: ll-qa-gate-evaluate

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-gate-evaluate` |
| **来源** | `gate-evaluator.py` 升级 |
| **用途** | 执行放行门评估，读取双链 manifests + settlements + waivers |
| **输入** | API/E2E manifests + settlements + waiver records |
| **输出** | `.artifacts/tests/settlement/release_gate_input.yaml` |

**输出包含**: API 链状态、E2E 链状态、7 项防偷懒验证、evidence_hash (SHA-256)、pass/fail/conditional_pass 决策 + 原因

---

### Skill 8: ll-qa-settlement

| 属性 | 值 |
|------|-----|
| **名称** | `ll-qa-settlement` |
| **来源** | ADR-047 新增 |
| **用途** | 生成 API/E2E 结算报告（统计通过率、gap list、waiver list） |
| **输入** | 执行后更新的 API/E2E manifests |
| **输出** | `api-settlement-report.yaml` + `e2e-settlement-report.yaml` |

---

## 二.1、遗留模板与工具（保留参考）

以下模板文件和脚本仍保留在 `ssot/tests/templates/` 和 `ssot/tests/gate/` 中，作为 skill 输出格式的参考和独立脚本工具。

### Template: feat-to-api-test-plan（参考）

> 已升级为 `skills/ll-qa-feat-to-apiplan/`。模板文件保留供参考。

### Template: prototype-to-e2e-journey-plan（参考）

> 已升级为 `skills/ll-qa-prototype-to-e2eplan/`。模板文件保留供参考。

### Template: evidence-collection（独立规范）

| 属性 | 值 |
|------|-----|
| **文件** | `ssot/tests/templates/evidence-collection.md` |
| **用途** | 定义 API 和 E2E 测试的证据收集规范 |

**API 证据要求**:
| 证据类型 | 格式 | 何时需要 |
|---------|------|---------|
| request_snapshot | YAML/JSON | 所有 API 测试 |
| response_snapshot | YAML/JSON | 所有 API 测试 |
| assertion_result | YAML | 所有 API 测试 |
| db_assertion_result | YAML | 有 side_effect_assertions 时 |

**E2E 证据要求**:
| 证据类型 | 格式 | 何时需要 |
|---------|------|---------|
| playwright_trace | ZIP | 所有 E2E 测试 |
| network_log | JSON | 所有 E2E 测试 |
| screenshot_final | PNG | 所有 E2E 测试 |
| console_error_check_result | YAML | 所有 E2E 测试 (anti-false-pass) |

---

## 三、已有工具（脚本）

### Tool 1: Gate Evaluator（脚本版）

> 已升级为 `skills/ll-qa-gate-evaluate/`。脚本仍保留供独立使用。

| 属性 | 值 |
|------|-----|
| **路径** | `ssot/tests/gate/gate-evaluator.py` |
| **用途** | 读取双链 manifest + settlement + waiver，生成 `release-gate-input.yaml` |
| **命令** | `python ssot/tests/gate/gate-evaluator.py` |
| **输出** | `.artifacts/tests/settlement/release-gate-input.yaml` |

**评估规则** (ADR-047 Section 9.4):

- `lifecycle_status=passed` 要求 `evidence_status=complete`
- `waiver_status=pending` 仍计入 failed 统计
- `waiver_status=approved` 从分母排除
- `waiver_status=rejected` 强制 fail，必须修复
- `obsolete=true` 从所有统计排除
- `lifecycle_status=cut` 从分母排除 (有意不测试)
- 空 manifest 会报错退出，不会静默 pass

**防偷懒验证** (7 项运行时检查):

1. Manifest items 执行前已冻结
2. 所有 cut 项有 cut_record with approver
3. Pending waiver 计入 failed
4. lifecycle_status=passed 要求 evidence_status=complete
5. 最小异常旅程覆盖 >= 1
6. 无证据 = 未通过
7. 证据哈希绑定存在

---

### Tool 2: CI Consumer

| 属性 | 值 |
|------|-----|
| **路径** | `ssot/tests/gate/ci-gate-consumer.py` |
| **用途** | 消费 `release-gate-input.yaml`，模拟 CI pass/fail 决策 |
| **命令** | `python ssot/tests/gate/ci-gate-consumer.py` |
| **退出码** | 0 = 通过 (release/conditional_release), 1 = 阻断 (block) |

---

## 四、使用场景（已更新为 Skill 触发方式）

### 场景 1: 新 feat 上线 — API 测试链

```
前置条件: feat 已通过 gate 并冻结 (status = frozen)

1. 运行 /ll-qa-feat-to-apiplan:
   输入: feat_freeze_package
   输出: ssot/tests/api/FEAT-XXX/api-test-plan.md

2. 运行 /ll-qa-api-manifest-init:
   输入: api-test-plan.md
   输出: ssot/tests/api/FEAT-XXX/api-coverage-manifest.yaml

3. 运行 /ll-qa-api-spec-gen:
   输入: api-coverage-manifest.yaml
   输出: ssot/tests/api/FEAT-XXX/api-test-spec/SPEC-*.md

4. 根据 spec 生成/编写测试脚本 (pytest / go test)

5. 执行测试 → 收集证据 (request/response snapshots, assertion results)

6. 更新 manifest 状态:
   - lifecycle_status: designed → executed → passed/failed
   - evidence_status: missing → complete

7. 运行 /ll-qa-settlement 生成 api-settlement-report

8. 运行 /ll-qa-gate-evaluate 查看结果
```

---

### 场景 2: 有 prototype — E2E 测试链（驱动模式）

```
前置条件: prototype 已冻结

1. 运行 /ll-qa-prototype-to-e2eplan (模式 A):
   输入: prototype package
   输出: ssot/tests/e2e/PROTO-XXX/e2e-journey-plan.md

2. 运行 /ll-qa-e2e-manifest-init:
   输入: e2e-journey-plan.md
   输出: ssot/tests/e2e/PROTO-XXX/e2e-coverage-manifest.yaml

3. 运行 /ll-qa-e2e-spec-gen:
   输入: e2e-coverage-manifest.yaml
   输出: ssot/tests/e2e/PROTO-XXX/e2e-journey-spec/JOURNEY-*.md

4. 生成 Playwright 脚本 (或手动编写)

5. 执行测试 → 收集证据 (trace, network_log, screenshots)

6. 更新 manifest 状态

7. 运行 /ll-qa-settlement 生成 e2e-settlement-report

8. 运行 /ll-qa-gate-evaluate 查看结果
```

---

### 场景 3: 无 prototype — E2E 测试链（API-derived 降级模式）

```
前置条件: feat 已冻结，但无对应 prototype 资产

1. 运行 /ll-qa-prototype-to-e2eplan (模式 B):
   输入: feat package (prototype 留空)
   输出: ssot/tests/e2e/PROTO-XXX/e2e-journey-plan.md (标注 derivation_mode: api-derived)

2. Skill 从 feat 的 Scope/Acceptance Checks 推导用户旅程

3. 后续流程同场景 2

注意: pilot-retrospective.md 建议下次选择有真实 prototype 的 feat 进行试点
```

---

### 场景 4: 双链合并 — Release Gate

```
前置条件: API 链和 E2E 链的 settlement 报告均已生成

1. 确保以下文件存在:
   - ssot/tests/api/FEAT-XXX/api-coverage-manifest.yaml
   - ssot/tests/e2e/PROTO-XXX/e2e-coverage-manifest.yaml
   - .artifacts/tests/settlement/api-settlement-report.yaml
   - .artifacts/tests/settlement/e2e-settlement-report.yaml
   - .artifacts/tests/settlement/waiver.yaml (可为空)

2. 运行 /ll-qa-gate-evaluate
   输出: .artifacts/tests/settlement/release_gate_input.yaml

3. 或使用独立脚本:
   python ssot/tests/gate/gate-evaluator.py
   python ssot/tests/gate/ci-gate-consumer.py
   退出码: 0 = 通过, 1 = 阻断

4. 检查防偷懒验证结果 (7 项必须全 PASS)

Gate 决策逻辑:
  API pass + E2E pass → release (放行)
  API pass + E2E conditional_pass → conditional_release (条件放行)
  API conditional_pass + E2E pass → conditional_release (条件放行)
  任何链 fail → block (阻断)
```

2. 运行: python ssot/tests/gate/gate-evaluator.py
   输出: .artifacts/tests/settlement/release-gate-input.yaml

3. 运行: python ssot/tests/gate/ci-gate-consumer.py
   退出码: 0 = 通过, 1 = 阻断

4. 检查防偷懒验证结果 (7 项必须全 PASS)

Gate 决策逻辑:
  API pass + E2E pass → release (放行)
  API pass + E2E conditional_pass → conditional_release (条件放行)
  API conditional_pass + E2E pass → conditional_release (条件放行)
  任何链 fail → block (阻断)
```

---

### 场景 5: 裁剪审批

```
当需要裁剪某个测试维度时:

1. 在 manifest 中设置该 item 的 lifecycle_status = "cut"

2. 添加 cut_record:
   cut_record:
     cut_target: "裁剪的维度名称"
     cut_reason: "裁剪原因"
     source_ref: "ADR-047 Section X.X 或 feat.rationale.xxx"
     approver: "审批人姓名/角色"
     approved_at: "ISO8601 时间戳"

3. Gate evaluator 会自动排除 cut 项 (不计入分母)

注意: P0 裁剪必须有 approver + source_ref
```

---

### 场景 6: Waiver 审批

```
当测试失败但需要豁免时:

1. 在 .artifacts/tests/settlement/waiver.yaml 中添加:
   waivers:
     - coverage_id: "api.xxx.yyy"
       status: "pending"          # 初始状态
       reason: "豁免原因"
       requested_by: "申请人"
       requested_at: "ISO8601"
       approved_by: null
       approved_at: null

2. Gate evaluator 将 waiver_status=pending 的项仍计入 failed

3. 审批后更新 status 为 "approved" 或 "rejected"
   - approved: 从分母排除，gate 可能通过
   - rejected: 必须修复，gate 强制 fail
```

---

## 五、产出物对照表

| 层级 | API 链 | E2E 链 | Gate |
|------|--------|--------|------|
| **Plan** | `api-test-plan.md` | `e2e-journey-plan.md` | — |
| **Manifest** | `api-coverage-manifest.yaml` | `e2e-coverage-manifest.yaml` | — |
| **Spec** | `api-test-spec/` 目录 | `e2e-journey-spec/` 目录 | — |
| **Settlement** | `api-settlement-report` | `e2e-settlement-report` | — |
| **Gate Input** | — | — | `release-gate-input.yaml` |
| **Evidence** | `.artifacts/tests/api/evidence/` | `.artifacts/tests/e2e/evidence/` | — |
| **Reports** | `.artifacts/tests/api/reports/` | `.artifacts/tests/e2e/reports/` | — |

---

## 六、关键规则速查

| 规则 | 说明 |
|------|------|
| **裁剪必须有审批** | 所有 `cut_record` 必须含 `approver` + `source_ref` |
| **Pending 不等于豁免** | `waiver_status=pending` 仍计入 failed 统计 |
| **Passed 必须有证据** | `lifecycle_status=passed` 时 `evidence_status` 必须为 `complete` |
| **E2E 最少异常旅程** | 全局至少 1 条 exception journey，否则 gate 拒绝 |
| **无证据 = 未执行** | `evidence_status=missing` 的 case 不算 executed |
| **证据哈希绑定** | 每次 gate 评估生成 evidence_hash，防止伪造 |
| **Rejected 必须修复** | `waiver_status=rejected` 或 `lifecycle_status=rejected` 强制 gate fail |
| **Cut 不计入分母** | `lifecycle_status=cut` 的项从统计中排除 |
| **Obsolete 全部排除** | `obsolete=true` 的项从所有统计中排除 |

---

## 七、目录结构一览

### 测试资产目录

```
ssot/tests/
├── pilot-plan.md                              # 试点范围 + 候选评估
├── pilot-retrospective.md                     # 试点回顾 + 推广建议
├── INDEX.md                                   # 资产索引
├── templates/                                 # 可复用 Skill 模板（参考）
│   ├── feat-to-api-test-plan.md
│   ├── prototype-to-e2e-journey-plan.md
│   └── evidence-collection.md
├── api/FEAT-SRC-005-001/
│   ├── api-test-plan.md                       # 8 capabilities, 3 优先级矩阵
│   ├── api-coverage-manifest.yaml             # 19 coverage items
│   └── api-test-spec/                         # 5 spec 文件
├── e2e/PROTOTYPE-FEAT-SRC-005-001/
│   ├── e2e-journey-plan.md                    # 4 journeys (API-derived)
│   ├── e2e-coverage-manifest.yaml             # 4 journey items
│   └── e2e-journey-spec/                      # 4 spec 文件
├── gate/
│   ├── gate-evaluator.py                      # Gate 评估器
│   ├── ci-gate-consumer.py                    # CI 消费验证
│   └── release_gate_input.yaml                # 放行输入 (当前: block)
└── .artifacts/                                # 内部结算报告 (副本)

.artifacts/tests/
├── api/reports/api-settlement-report.md
├── e2e/reports/e2e-settlement-report.md
└── settlement/
    ├── api-settlement-report.yaml
    ├── e2e-settlement-report.yaml
    ├── release-gate-input.yaml                # CI 读取的最终输出
    └── waiver.yaml
```

### 正式 Skill 目录

```
skills/
├── ll-qa-feat-to-apiplan/                     # FEAT → api-test-plan
├── ll-qa-api-manifest-init/                   # plan → api-coverage-manifest
├── ll-qa-api-spec-gen/                        # manifest → api-test-spec
├── ll-qa-prototype-to-e2eplan/                # prototype → e2e-journey-plan
├── ll-qa-e2e-manifest-init/                   # plan → e2e-coverage-manifest
├── ll-qa-e2e-spec-gen/                        # manifest → e2e-journey-spec
├── ll-qa-gate-evaluate/                       # manifests+settlements → gate decision
└── ll-qa-settlement/                          # post-exec manifests → settlement reports

每个 skill 包含:
├── SKILL.md                                   # 主技能定义（含 ADR-047 治理规则引用）
├── ll.contract.yaml                           # 合约元数据
├── input/
│   ├── contract.yaml                          # 输入契约定义
│   └── semantic-checklist.md                  # 输入语义检查清单
├── output/
│   ├── contract.yaml                          # 输出契约定义
│   └── semantic-checklist.md                  # 输出语义检查清单
└── agents/
    ├── executor.md                            # 执行器代理
    └── supervisor.md                          # 监督器代理
```

---

## 八、Manifest 状态机

```
drafted → designed → generated → executable → executed → {passed | failed | blocked}
                                                              ↓
                                                      blocked → waived (审批后)
                                                      failed  → waived (审批后)
                                                      any     → obsolete (上游变更)
                                                      any     → cut (裁剪审批)
```

| 状态 | 含义 | 计入分母 |
|------|------|---------|
| `designed` | 测试已设计，待生成脚本 | 是 (算 uncovered) |
| `generated` | 测试脚本已生成，待执行 | 是 (算 uncovered) |
| `executable` | 测试可执行，待运行 | 是 (算 uncovered) |
| `executed` | 测试已执行，待验证证据 | 是 (证据完整=pass，否则=uncovered) |
| `passed` | 测试通过 | 是 (要求 evidence_status=complete) |
| `failed` | 测试失败 | 是 |
| `blocked` | 测试被阻塞 | 是 |
| `waived` | 测试已豁免 | 否 |
| `cut` | 测试已裁剪 | 否 |
| `obsolete` | 上游变更导致失效 | 否 |

---

## 九、常见问题

### Q: 我应该选择哪个 feat 作为下一个试点?

**A**: 推荐标准:
1. feat 已冻结 (status = accepted)
2. capabilities 定义清晰，I/O 合约明确
3. 有对应的 prototype 资产 (避免 API-derived 降级)
4. 验收标准可量化 (Acceptance Checks >= 2)

### Q: Gate 返回 block 时怎么办?

**A**:
1. 查看 `release-gate-input.yaml` 中的 `decision_reason`
2. 检查是 failed / uncovered / blocked 哪种状态
3. 对于 uncovered: 执行对应测试
4. 对于 failed: 修复被测系统或修正测试
5. 对于确实无法执行的项: 申请 waiver (需审批)
6. 重新运行 gate-evaluator.py

### Q: 如何添加新的测试用例?

**A**:
1. 在 `api-coverage-manifest.yaml` / `e2e-coverage-manifest.yaml` 中添加新 item
2. 设置 `lifecycle_status: designed`, `mapping_status: unmapped`, `evidence_status: missing`
3. 创建对应的 spec 文件
4. 生成测试脚本并执行
5. 执行后更新 manifest 状态

### Q: BMAD Skills 如何接入?

**A**: BMAD 作为能力层插件，角色限定为:
- `/bmad-testarch-framework`: 测试底座初始化 (draft only)
- `/bmad-testarch-test-design`: 测试设计草稿生成 (draft only)
- `/bmad-qa-generate-e2e-tests`: E2E 脚本生成 (需 journey-spec 驱动)
- `/bmad-testarch-ci`: CI/CD 配置生成

BMAD **不得**定义覆盖边界、替代 SSOT 作为真理源、或独立决定 release gate。

### Q: ADR-047 正式 Skill 和模板文件有什么区别?

**A**: Phase 6 之前，测试设计依赖 `ssot/tests/templates/` 下的 Markdown 模板手动操作。
Phase 6 完成后，3 个模板升级为 8 个正式 Skill，具有以下优势:
- **自动化**: 输入 → 输出全链路自动化，不再手动编写
- **治理**: 每个 Skill 包含 ADR-047 治理规则引用（四维状态、防偷懒、evidence 要求）
- **合约**: 正式的 input/output contract 定义，保证技能间互操作
- **验证**: executor + supervisor 双代理架构，确保输出质量
- **全局可用**: 通过 `ll-skill-install` 安装到 Claude Code 全局，跨项目使用

模板文件仍保留在 `ssot/tests/templates/` 作为参考。
