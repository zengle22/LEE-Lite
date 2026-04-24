# ADR-052 双轴测试 — 用户使用指南

> **ADR**: ADR-052（测试体系轴化 — 需求轴与实施轴）
> **文档类型**: 用户操作指南
> **适用范围**: 所有需要通过 Skill 入口完成双链测试的用户
> **创建日期**: 2026-04-23
> **基于里程碑**: v2.1（Phase 12-16 完成）

---

## 一、实施状态总览

> 先看这个表，确认哪些能力当前可用，哪些还在规划中。

### 当前可用（v2.1 已交付）

| 模块/能力 | 状态 |
|-----------|------|
| 需求轴基础设施（Schema / Enum Guard / Governance Validator） | ✓ 完成 |
| 8 个 ADR-047 QA Skills（需求轴生成 + 结算 + Gate） | ✓ 已安装 |
| 测试执行引擎（`ll-test-exec-cli` / `ll-test-exec-web-e2e`） | ✓ 已安装 |

### 尚未实现

| 模块/能力 | 计划阶段 |
|-----------|----------|
| `qa.test-plan` / `qa.test-run`（用户统一入口） | Phase 4 |
| `scenario-spec-compile` / `state-machine-executor` | Phase 1a |
| `environment-provision` / `run-manifest-gen` | Phase 1a-1b |
| `independent-verifier` | Phase 2 |
| `l0-smoke-check` / `accident-package` / `failure-classifier` | Phase 2 |
| `bypass-detector` / `test-data-provision` / `dag-runner` | Phase 3 |

**结论：** 现阶段用户通过 **8 个 ADR-047 QA Skill** 完成双链测试。`qa.test-plan` 和 `qa.test-run` 是 ADR-052 定义的最终入口，尚未实现。

---

## 二、核心理念：两条轴，两条链

| 维度 | 问题 | 管理者 | 资产性质 |
|------|------|--------|----------|
| **需求轴** | "测什么？" | SSOT | 声明性（可重新编译） |
| **实施轴** | "在哪测？怎么跑？结果是否可信？" | Artifact | 证据性（只追加） |

**"链"与"轴"的区别：**
- **链**（API 链 / E2E 链）= 测试覆盖的通道，是水平维度的
- **轴**（需求轴 / 实施轴）= 资产的管理方式，是垂直维度的
- 每条链都有自己的需求轴资产和实施轴资产

---

## 三、快速开始：从零跑通一条黄金路径

> 本节演示从一份冻结的 FEAT 文档出发，跑完双链测试的完整流程。以 `FEAT-SRC-001-001` 为例。

### 前置准备

1. **确认 FEAT 文档已冻结** — 检查你的 FEAT 文档中 `feat_freeze_package.status = "frozen"`。如果尚未冻结，需要先走 FRZ 冻结流程（`ll frz-manage validate` + `ll frz-manage freeze`）。
2. **确认 Skills 已安装** — 在 Claude Code 中运行 `/help` 或直接尝试调用 Skill，如果提示找不到，运行 `ll skill-install ll-qa-feat-to-apiplan` 等安装命令。
3. **准备 Prototype 文件**（E2E 链需要）— 如果还没有原型图，可走 API-Derived 降级模式（Step 4 模式 B）。

### 执行步骤

```
# 第一步：生成 API 测试计划
# 在 Claude Code 对话框中输入：
/ll-qa-feat-to-apiplan
# 然后提供冻结的 FEAT 文档引用

# 第二步：生成覆盖率清单
/ll-qa-api-manifest-init
# Skill 会自动读取上一步生成的 api-test-plan.md

# 第三步：生成 API 测试规范
/ll-qa-api-spec-gen
# Skill 会自动读取上一步生成的 api-coverage-manifest.yaml

# 第四步：生成 E2E 旅程计划（与 1-3 并行）
/ll-qa-prototype-to-e2eplan
# 提供 Prototype 或 FEAT 文档引用

# 第五步：生成 E2E 覆盖率清单
/ll-qa-e2e-manifest-init

# 第六步：生成 E2E 旅程规范
/ll-qa-e2e-spec-gen

# 第七步：执行测试
# 读取：Step 3 的 SPEC 文件 + Step 6 的 JOURNEY 文件
/ll-test-exec-cli        # API 测试
/ll-test-exec-web-e2e    # E2E 测试
# 执行后 manifests 中的 lifecycle_status 和 evidence_status 会被更新

# 第八步：生成结算报告
/ll-qa-settlement

# 第九步：Gate 门禁评估
/ll-qa-gate-evaluate
# 产出：release_gate_input.yaml（pass / conditional_pass / fail）
```

执行完成后，查看 `ssot/tests/.artifacts/tests/settlement/release_gate_input.yaml` 中的 `final_decision` 字段即可得知测试结果。

---

## 四、当前可用：8 个 Skill 详细说明

### 需求轴 — API 链

#### Step 1: `/ll-qa-feat-to-apiplan`

**你得到什么：** 一份定义"测哪些 API、测什么维度、优先级如何"的测试计划。

**前置条件：** FEAT 文档已冻结（`status = frozen`）

**用法：** 在 Claude Code 中调用 `/ll-qa-feat-to-apiplan`，然后提供冻结的 FEAT 文档引用（包含 `feat_id`、`feat_ref`、Scope 定义）。

**这一步发生了什么：**
1. 验证 FEAT 文档处于冻结状态 — 未冻结会被拒绝
2. 从 Scope 中提取 API 相关 capabilities，分配唯一 ID 和优先级（P0/P1/P2）
3. 对每个 capability 应用 8 维测试矩阵（正常路径、参数校验、边界值、状态约束、权限、异常、幂等/重试/并发、数据副作用）
4. 根据优先级裁剪低优先级维度
5. 生成测试计划

**产出：** `ssot/tests/api/{feat_id}/api-test-plan.md`

**常见问题：**
- **FEAT 未冻结怎么办？** 先运行 `ll frz-manage validate` 验证，再运行 `ll frz-manage freeze` 冻结。
- **Skill 报错 "capabilities not found"？** 检查 FEAT 文档的 Scope 部分是否明确定义了 API 相关能力。

---

#### Step 2: `/ll-qa-api-manifest-init`

**你得到什么：** 一份覆盖清单（manifest），把测试计划中的每个能力×维度组合展开为可追踪的独立测试项，每项都有四维状态字段。

**前置条件：** `api-test-plan.md` 已存在（由 Step 1 生成）

**用法：** `/ll-qa-api-manifest-init`，无需额外参数。

**这一步发生了什么：**
1. 读取 api-test-plan.md，验证结构完整
2. 将每个 `capability × dimension` 组合展开为一个 coverage item
3. 初始化四维状态（详见第五节）：`lifecycle_status=designed`、`mapping_status=unmapped`、`evidence_status=missing`、`waiver_status=none`
4. 对裁剪项生成 `cut_record`（必须含 approver + source_ref）

**产出：** `ssot/tests/api/{feat_id}/api-coverage-manifest.yaml`

**常见问题：**
- **报错 "plan not found"？** 确认 Step 1 已成功执行且文件在 `ssot/tests/api/` 下。
- **item 数量太多？** 这是正常的 — 每个 capability 可能展开出 5-8 个测试维度。可在 Step 1 中调整优先级来裁剪。

---

#### Step 3: `/ll-qa-api-spec-gen`

**你得到什么：** 每个测试项对应一份独立的测试规范文件，定义了"调什么接口、发什么请求、期望什么响应、需要什么证据"。

**前置条件：** `api-coverage-manifest.yaml` 已存在（由 Step 2 生成）

**用法：** `/ll-qa-api-spec-gen`，无需额外参数。

**这一步发生了什么：**
1. 读取 manifest，筛选出所有 `lifecycle_status = designed` 的测试项
2. 为每个测试项生成一份 SPEC 文件，包含：Endpoint 定义、Request/Response schema、Assertions、证据要求、防假通过检查（P0 至少 3 条）、Cleanup 步骤

**产出：** `ssot/tests/api/{feat_id}/api-test-spec/SPEC-*.md`（多个文件）

**常见问题：**
- **SPEC 文件为空或断言缺失？** 检查 manifest 中对应 item 的优先级 — P2 能力可能只有最基本的测试维度。

---

### 需求轴 — E2E 链（可与 API 链并行执行）

#### Step 4: `/ll-qa-prototype-to-e2eplan`

**你得到什么：** 一份定义"用户走哪些旅程、每个旅程的操作步骤和预期结果"的 E2E 测试计划。

**前置条件：** Prototype 流程图或 FEAT 文档已就绪

**用法：** `/ll-qa-prototype-to-e2eplan`，提供 Prototype 或 FEAT 文档引用。

**两种模式：**
- **模式 A（Prototype-Driven）：** 有完整 Prototype 流程图时，从页面流自动提取用户旅程
- **模式 B（API-Derived）：** 没有 Prototype 时，从 FEAT 的用户可见能力推导旅程（降级模式，计划中会标注 `derivation_mode: api-derived`）

**产出：** `ssot/tests/e2e/{prototype_id}/e2e-journey-plan.md`

**常见问题：**
- **报错 "no journeys identified"？** 至少需要 1 个 main journey + 1 个 exception journey。检查 FEAT 中是否定义了可感知的用户操作。

---

#### Step 5: `/ll-qa-e2e-manifest-init`

**你得到什么：** E2E 覆盖清单，与 Step 2 的 API manifest 结构类似，但针对用户旅程。

**前置条件：** `e2e-journey-plan.md` 已存在（由 Step 4 生成）

**用法：** `/ll-qa-e2e-manifest-init`

**这一步发生了什么：** 与 Step 2 类似 — 将每个 journey 展开为 coverage item，初始化四维状态。P0 main journey 不可裁剪。

**产出：** `ssot/tests/e2e/{prototype_id}/e2e-coverage-manifest.yaml`

---

#### Step 6: `/ll-qa-e2e-spec-gen`

**你得到什么：** 每个旅程对应一份 Journey Spec，定义了"从哪个页面进入、用户做什么操作、期望看到什么 UI 变化、期望触发什么网络请求、数据是否持久化"。

**前置条件：** `e2e-coverage-manifest.yaml` 已存在（由 Step 5 生成）

**用法：** `/ll-qa-e2e-spec-gen`

**这一步发生了什么：** 为每个 designed item 生成 Journey Spec，包含：Entry point、User steps、Expected UI states、Expected network events、Expected persistence、Evidence required（playwright_trace + screenshot 必须）、防假通过检查。

**产出：** `ssot/tests/e2e/{prototype_id}/e2e-journey-spec/JOURNEY-*.md`（多个文件）

---

### 实施轴 — 测试执行

#### Step 7: 运行测试

> **这是"生成测试计划"和"生成结算报告"之间的关键衔接步骤。** 前面的 6 个 Skill 产出的是"测试要测什么"的声明，这一步才是真正的执行。

| 引擎 | 触发命令 | 读取 | 做什么 |
|------|----------|------|--------|
| API 测试 | `/ll-test-exec-cli` | `SPEC-*.md` | 发送 HTTP 请求、验证响应、收集证据 |
| E2E 测试 | `/ll-test-exec-web-e2e` | `JOURNEY-*.md` | Playwright 浏览器自动化、页面交互、截图/录屏 |

**执行完成后：** 两个 manifest 文件中的 `lifecycle_status`（designed → passed/failed）和 `evidence_status`（missing → complete）会被更新。

**收集的证据：**
- API：request/response snapshots、assertion results（YAML/JSON）
- E2E：playwright_trace（ZIP）、network_log（JSON）、screenshot（PNG）、console_log

**常见问题：**
- **执行引擎找不到 Spec 文件？** 确认 Step 3 / Step 6 已成功产出文件。
- **执行中途失败？** 查看 `ssot/tests/.artifacts/` 下的执行日志，已执行的用例状态会被保存，可从断点继续。
- **所有用例都失败？** 先检查目标环境是否可达 — 可能是 base_url 配置错误或服务未启动。

---

### 实施轴 — 结算与 Gate

#### Step 8: `/ll-qa-settlement`

**你得到什么：** 两条链各自的统计报告 — 多少通过、多少失败、多少未覆盖、通过率多少。

**前置条件：** 两个 manifests 都已执行更新

**用法：** `/ll-qa-settlement`

**产出：**
- `ssot/tests/.artifacts/settlement/api-settlement-report.yaml`
- `ssot/tests/.artifacts/settlement/e2e-settlement-report.yaml`

---

#### Step 9: `/ll-qa-gate-evaluate`

**你得到什么：** 最终的 pass / conditional_pass / fail 决策 + 7 项防偷懒检查结果。

**前置条件：** 两个 settlement reports + waiver records 已就绪

**用法：** `/ll-qa-gate-evaluate`

**这一步发生了什么：**
1. 读取 5 个输入文件（两个 manifests + 两个 settlements + waiver.yaml），缺少任何一个会拒绝执行
2. 计算双链指标，执行 7 项防偷懒检查（详见第五节）
3. 生成门禁决策

| 决策 | 条件 |
|------|------|
| `pass` | 双链 pass_rate ≥ 80% + 7 项检查全通过 + 证据完整 |
| `conditional_pass` | 一条链达标，另一链有微小差距且 waiver 覆盖 |
| `fail` | 任何链低于阈值 或 任何防偷懒检查失败 |

**产出：** `ssot/tests/.artifacts/tests/settlement/release_gate_input.yaml`

**常见问题：**
- **Gate 返回 `fail` 怎么办？** 查看 `decision_reason` 字段，确定是链失败还是防偷懒检查失败。对于 uncovered 项执行测试，对于 failed 项修复后重跑。
- **`provisional_pass` 是什么？** 仅 A+B 层断言时（C 层未验证）的临时通过结论，不作为质量决策依据。

---

### 完整调用顺序一览

```
需求轴（API 链）              需求轴（E2E 链）
─────────────                ─────────────
1. /ll-qa-feat-to-apiplan    4. /ll-qa-prototype-to-e2eplan
   ↓                            ↓
2. /ll-qa-api-manifest-init   5. /ll-qa-e2e-manifest-init
   ↓                            ↓
3. /ll-qa-api-spec-gen        6. /ll-qa-e2e-spec-gen
   ↓                            ↓
   ───────→ 测试执行 ←──────────
     /ll-test-exec-cli
     /ll-test-exec-web-e2e
              ↓
   7. /ll-qa-settlement
              ↓
   8. /ll-qa-gate-evaluate
              ↓
   release_gate_input.yaml
```

---

## 五、关键规则速查

### 四维状态字段

| 状态维度 | 取值流转 | 关键规则 |
|----------|----------|----------|
| `lifecycle_status` | designed → executing → passed/failed/blocked | passed 必须有完整证据 |
| `mapping_status` | unmapped → mapped → verified | 映射后填入 mapped_case_ids |
| `evidence_status` | missing → partial → complete | missing ≠ executed |
| `waiver_status` | none → pending → approved/rejected | pending 仍计为 failed |

### 裁剪与豁免

| 规则 | 说明 |
|------|------|
| 裁剪必须审批 | 所有 `cut_record` 必须含 `approver` + `source_ref` |
| P0 不可裁剪 | 核心路径永远保留 |
| Pending ≠ 豁免 | `waiver_status=pending` 的 item 在 pass rate 中计为 failed |
| Rejected 必须修复 | 被拒绝的豁免对应项强制 fail |
| Cut 不计入分母 | 已裁剪项从 pass rate 分母排除 |

### 7 项防偷懒检查

| # | 检查项 | 验证什么 |
|---|--------|----------|
| 1 | manifest_frozen | 执行前清单已冻结，防止执行后添加通过项 |
| 2 | cut_records_valid | 所有裁剪项有合法审批记录 |
| 3 | pending_waivers_counted | 待审批豁免仍计为失败 |
| 4 | evidence_consistent | 通过的测试必须有完整证据 |
| 5 | min_exception_coverage | E2E 至少 1 条异常旅程被执行 |
| 6 | no_evidence_not_executed | 无证据的 item 不算已执行 |
| 7 | evidence_hash_binding | 证据 SHA-256 哈希已记录，防止篡改 |

---

## 六、产出物路径参考

```
ssot/tests/
├── api/{feat_id}/
│   ├── api-test-plan.md              ← Step 1
│   ├── api-coverage-manifest.yaml    ← Step 2
│   └── api-test-spec/                ← Step 3
│       └── SPEC-*.md
├── e2e/{proto_id}/
│   ├── e2e-journey-plan.md           ← Step 4
│   ├── e2e-coverage-manifest.yaml    ← Step 5
│   └── e2e-journey-spec/             ← Step 6
│       └── JOURNEY-*.md
└── .artifacts/
    ├── settlement/
    │   ├── api-settlement-report.yaml       ← Step 8
    │   ├── e2e-settlement-report.yaml       ← Step 8
    │   └── release_gate_input.yaml          ← Step 9
    └── evidence/                            ← Step 7 收集
```

---

## 七、常见问题

### Q: 我应该先跑 API 链还是 E2E 链？

**A:** 两条链是并行的，可以交错执行。但通常建议先跑 API 链（步骤更少，能快速验证接口），再跑 E2E 链（依赖前端环境）。

### Q: 如何冻结一份 FEAT 文档？

**A:** 运行 `ll frz-manage validate` 验证 FRZ 包，验证通过后运行 `ll frz-manage freeze --id FRZ-xxx`。冻结后的 FEAT 文档状态变为 `frozen`，可作为测试计划的输入。

### Q: Skill 找不到怎么办？

**A:** 运行 `ll skill-install ll-qa-feat-to-apiplan`（按需替换 Skill 名称）安装到 Claude Code 全局。8 个 QA Skill 都需要单独安装。

### Q: Gate 返回 `fail` 时怎么办？

**A:**
1. 查看 `release_gate_input.yaml` 中的 `decision_reason`
2. 检查是哪条链失败、哪项防偷懒检查不通过
3. 对于 uncovered 项：执行对应测试
4. 对于 failed 项：修复被测系统或修正测试
5. 对于 PRODUCT 类故障：走 bug 修复流程
6. 重新执行后重跑 settlement + gate

### Q: `provisional_pass` 是什么意思？

**A:** 表示测试暂时通过，但 C 层（业务状态断言）尚未验证。这意味着"页面操作看起来成功，但业务实体是否真正落库还未确认"。`provisional_pass` 仅供技术团队内部参考，不能作为发布决策。

### Q: 如何添加新的测试用例？

**A:** 在对应的 manifest YAML 中添加新 item，设置 `lifecycle_status: designed`，然后重新跑 spec-gen skill 生成新的 spec 文件。

### Q: 8 类故障分类是什么？

**A:** 当测试失败时，`failure-classifier` 模块（待实现）会自动将故障分为 8 类：

| 类别 | 含义 | 常见表现 |
|------|------|----------|
| ENV | 环境不一致 | 手工验收不复现 |
| DATA | 测试数据脏 | 同账号第二次跑失败 |
| SCRIPT | 脚本问题 | 选择器不对/等待条件错 |
| ORACLE | 断言太弱 | 有 toast 就算成功 |
| BYPASS | 绕过 UI | 直调 API 创建实体 |
| PRODUCT | 真实产品 bug | 人手也跑不通 |
| FLAKY | 非确定性/时序竞争 | 偶发失败 |
| TIMEOUT | 业务处理超时 | 超过等待上限 |

---

## 八、未来目标：`qa.test-plan` 和 `qa.test-run`

> 以下是 ADR-052 定义的最终用户入口（Phase 4 交付）。现阶段请使用第四节描述的 8 个独立 Skill。

### `qa.test-plan`：一句话生成全部测试计划

用户只需指向一个已冻结的 FEAT 文档，Skill 内部自动编排 7 个需求轴模块（feat-to-testset → api-plan/manifest/spec → e2e-plan/manifest/spec），一次性产出全套测试计划。

**支持选项：** `--preview`（预览不落盘）、`--target G1`（仅指定黄金路径）

### `qa.test-run`：一句话跑完测试并出报告

用户只需指定目标环境和测试集引用，Skill 内部自动完成：环境供给 → L0 冒烟 → 运行清单生成 → 场景规范编译 → 状态机执行 → 独立验证 → 结算 → Gate 评估 → 报告渲染。

**支持选项：** `--last-failed`（仅重跑失败用例）、`--report-only`（仅生成已有报告）、`--target G1`

> 详细架构说明见 ADR-052 原文 `ssot/adr/ADR-052-测试体系轴化-需求轴与实施轴.md`。
