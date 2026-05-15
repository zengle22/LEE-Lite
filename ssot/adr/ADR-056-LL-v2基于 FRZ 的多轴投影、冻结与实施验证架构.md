# ADR-056：LL v2 基于 FRZ 的 SSOT 编译与实施验收架构

> 状态：Revised v2 (based on brainstorming session 2026-05-08/09 + adversarial review 2026-05-09)
> 日期：2026-05-09
> 决策者：Le Zeng
> 适用范围：LEE Lite / LL Skill-First Governed Development Framework
> 相关对象：FRZ、SRC、EPIC、FEAT、UI、TECH、ARCH、API、TESTSET、IMPL、GSD、Gate、Patch、Bug Registry
> 关联文档：`docs/ai-infra/ITERATION-DOCUMENT-CHECKLIST.md`

---

## 1. 背景

当前 LL 框架已经形成了较完整的 Skill-First 治理式开发体系，包括 SSOT 推导链、Skill 输入/输出契约、Executor/Supervisor 分离、Freeze Guard、Gate 决策层、API/E2E 双链测试、Experience Patch、Bug Registry，以及与 GSD 等执行框架的潜在集成。

原有 LL 主流程为线性推导模式：

```text
Raw Input → SRC → EPIC → FEAT → TECH → IMPL → Test Plan → Test Execution → Gate Review → Release
```

但随着实际研发流程演进，LL 的定位需要调整。核心洞察：

1. **治理是 AI 能力不足的临时成本**。核心需求是 AI 提高生产效率，治理是手段而非目标。随着 AI 能力增长，治理应自动收缩。
2. **BMAD 等工具做需求分析已经很完善**，且越来越多，但工具输出格式不一致。LL 应聚焦于"标准化"而非"生成"。
3. **LL 的本质定位是项目级粘合层** — 管事实源、验收成品；需求生产和代码生产外包给专业工具。LL 跟着项目走，工具可替换。
4. **核心原则是"抓两头"** — 一边需求卡死，一边交付卡死。只要需求和交付完全匹配，工程就可控。

因此，LL v2 从"需求分析师"转型为"SSOT 编译器 + 验收官"。

### 1.1 与现有 ADR 的关系

本 ADR 与以下 ADR 保持一致：

| ADR | 关系 |
|-----|------|
| ADR-050 (SSOT 语义治理总纲) | 本 ADR 的漂移防控机制继承 ADR-050 的治理原则 |
| ADR-052 (测试体系轴化) | 本 ADR 的测试模型兼容 ADR-052 的双轴测试结构 |
| ADR-049 (Experience Patch) | 本 ADR 的问题回流机制复用 ADR-049 的 Patch 定义 |
| ADR-055 (Bug 流转闭环) | 本 ADR 的 Bug Fix 流程与 ADR-055 一致 |

### 1.2 完整性验证的执行方式

§6 定义的 Complete Design Package 完整性检查，可通过以下方式执行：

```yaml
validation_enforcement:
  options:
    - ci_check: 独立脚本验证 YAML/JSON 结构完整性
    - skill_inline: frz-ingest 内部 step_1 执行（当前方式）
    - hybrid: CI 脚本检查结构 + frz-ingest 检查语义完整性
  current_approach: skill_inline
  # frz-ingest step_1 负责完整性判定
  # 不依赖外部 CI，但可选的 CI 预检可提前发现结构问题
```

---

## 2. 问题

### 2.1 旧流程的问题

1. **链式推导导致语义漂移**
   FEAT、TECH、UI、TEST 逐层生成时，每一层都有机会引入新的 AI 推测语义。

2. **FEAT 被迫承载过多信息**
   原流程中 TECH / UI / TEST 多数从 FEAT 向下推导，导致 FEAT 可能被迫承载产品、UI、技术、测试等多类信息。

3. **上游已完成设计时，LL 仍重复设计**
   当 Pre-SSOT 已经有完整 UX/UI、TECH、API、TEST 设计时，再通过 FEAT 重新推导这些对象，会造成重复推导和不一致。

4. **LL 承担了不该承担的职责**
   LL 试图做需求分析、智能补全、设计推导，但这些工作 BMAD 等工具已经做得更好。LL 应该聚焦于标准化和验证。

### 2.2 v1 与 v2 的本质区别

| | v1 | v2 |
|---|---|---|
| **输入** | 任意信息（完整或不完整） | 必须是完整的 Design Package |
| **生成能力** | 智能补全 + 标准准化转换 | 只有标准化转换（编译） |
| **拆解能力** | 智能拆解 | 机械式拆解 |
| **冻结** | 无 | 有 |
| **验证** | 无闭环 | 有验收测试 |
| **核心价值** | 从模糊到清晰 | 从完整到标准化 + 冻结 + 验收 |

v2 砍掉了"AI 发明内容"的能力，保留了"AI 格式化内容"的能力。v2 的增量是**冻结 + 验收**，不是"生成"。

---

## 3. 决策

### 3.1 总体决策

LL v2 从 8 个暴露 Skill 精简为 **2 个暴露 Skill**：

```text
LL v2 = v1（保持不变）+ frz-ingest（编译+冻结）+ impl-verify（版本验收）
```

LL v2 的核心定位：

```text
LL 是 SSOT 编译器、语义冻结器和版本验收官。
```

核心原则 — **抓两头**：

```text
入口卡死：Complete Design Package → 编译 → 冻结的 SSOT 链
出口卡死：冻结的 SSOT 链 vs GSD 交付物 → 文档符合性报告
中间层：GSD 执行 + v1 测试 Skill（独立不动）
```

### 3.2 分工原则

| 角色 | 职责 | 类比 |
|---|---|---|
| **LL（发包方）** | 编译 SSOT、冻结语义、验收交付 | 甲方 |
| **GSD（外包方）** | 执行 FEAT 任务包、自测、交付代码+证据 | 乙方 |
| **BMAD 等工具** | 需求分析、设计产出 | 专业分包商 |

### 3.3 LL 不再承担的职责

- 不从模糊需求中主动发明需求
- 不静默补全业务设计缺口
- 不从 FEAT 重新推导已经存在的 UI / TECH / TEST 设计
- 不做需求质量门控（太重，做不好，且超出工程框架职责）
  > 注：§6.3 的完整性检查 ≠ 需求质量门控。完整性检查只验证"输入是否存在"（结构检查），不评估"需求是否正确"（质量评估）。缺失维度 → 拒绝编译；维度存在但内容有误 → 不在 frz-ingest 职责范围内。

### 3.4 LL 主要承担的职责

- 接收 Complete Design Package，检查完整性
- 对完整设计包进行编译（映射+拆解+格式标准化），生成 SSOT 链
- 对 SSOT 链进行冻结
- 生成验收测试用例（从 FEAT.AC + test_design + prototype）
- GSD 交付后，两条线路并行验收：
  - 线路 1: v1 test_execution 跑验收测试
  - 线路 2: impl-verify 检查功能完成度、工程资料、范围合规、溯源
- 将问题分流到 Bug Fix、Experience Patch 或 FRZ Revise

---

## 4. 新架构

### 4.1 主流程

```text
Complete Design Package (来自 BMAD 等工具)
        │
        ▼
    frz-ingest ──── 编译 + 冻结
        │
        ├──→ 冻结的 SSOT 链
        │    (SRC/EPIC/FEAT/TECH/ARCH/API/UI/IMPL)
        │
        └──→ 验收测试用例 (v1 test_generation)
             (可执行，不冻结为 SSOT 对象)
        │
        ▼
    FRZ Package (SSOT 链 + 验收测试用例)
        │
        ▼
    GSD 执行
    - 看 SSOT → 编码
    - 自己跑测试 (v1 Skill, LL 不关心)
    - 交付: 代码 + 测试证据 + 工程资料
        │
        ├──────────────────────────────────┐
        ▼                                  ▼
    线路 1: v1 test_execution         线路 2: impl-verify
    - 跑 FRZ Package 中的验收测试     - 功能完成度检查
    - 收集测试证据                    - 工程资料检查
    - 输出测试报告                    - 范围合规检查
                                      - 溯源验证
                                      - 输出验收报告
        │                                  │
        └──────────┬───────────────────────┘
                   ▼
          dual_track_convergence:
            inputs:
              - track_1_verdict: 线路 1 (v1 test_execution) 的测试报告 verdict
              - track_2_verdict: 线路 2 (impl-verify) 的验收报告 verdict
            gate: AND
            rules:
              both_pass:
                meaning: 两条线路都通过
                action: 冻结生效，可发布
                state: frozen (confirmed)
              any_fail:
                meaning: 任一或两条线路失败
                action: 问题分流
                routing:
                  - 如果是实现未满足需求: Bug Fix / GSD Remediation
                  - 如果是 UI/Interaction 小问题: Experience Patch
                  - 如果是需求本身有误: FRZ Revise
              partial_delivery:
                meaning: GSD 仅交付了部分 FEAT
                action: 只对已交付部分执行双线路验收
                constraint: conditional_pass 仅对已交付部分有效
                deadline: 截止时间超过且未完成时，verdict 降级为 fail
            output: final_verdict (pass | fail | conditional_pass)
```

### 4.2 从链式生成改为编译+冻结

旧模式：

```text
SRC → EPIC → FEAT → TECH / UI (逐层推导，有语义漂移风险)
```

新模式：

```text
Complete Design Package
    ↓ (标准化编译，映射+拆解，无推导)
SSOT 链 (SRC/EPIC/FEAT/TECH/ARCH/API/UI/IMPL)
    ↓ (冻结)
冻结的 SSOT 链 + 验收测试用例
```

关键变化：
- 不再从模糊需求推导，而是从完整设计包编译
- 编译 = 映射（大部分字段直接映射）+ 拆解（EPIC/FEAT/IMPL 按规则拆分）+ 格式标准化
- 复用 v1 的标准化转换和机械式拆解逻辑
- 新增冻结能力
- TEST 不冻结为 SSOT 对象，测试是实施产物

### 4.3 测试模型：发包方-外包方

```text
LL frz-ingest                GSD                    LL 并行验收
    │                          │                        │
    │ 1. 编译 SSOT             │                        │
    │    + 生成验收测试用例     │                        │
    │                          │                        │
    │ 2. FRZ Package ────────→ │                        │
    │   (SSOT + 验收测试用例)  │                        │
    │                          │                        │
    │                          │ 3. GSD 编码+自测       │
    │                          │   (LL 不关心)          │
    │                          │                        │
    │                          │ 4. 交付 ──────────────→│
    │                          │   代码                 │
    │                          │   测试证据             │
    │                          │   工程资料             │
    │                          │                        │
    │                          │    ┌──────────────────┐│
    │                          │    │ 线路1: v1 测试验收 ││
    │                          │    │ v1 test_execution ││
    │                          │    │ → 测试报告        ││
    │                          │    ├──────────────────┤│
    │                          │    │ 线路2: impl-verify ││
    │                          │    │ 功能完成度检查    ││
    │                          │    │ 工程资料检查      ││
    │                          │    │ 范围合规检查      ││
    │                          │    │ 溯源验证          ││
    │                          │    │ → 验收报告        ││
    │                          │    └──────────────────┘│
    │                          │                        │
    │                          │    5. AND gate 收敛    │
    │                          │    两条线都通过 → 生效  │
```

协作原则：**frz-ingest 的输出给 GSD，GSD 的输出给两条验收线，中间没有多余的交互。**

LL 验收分两条独立线路：

| | 线路 1: v1 测试验收 | 线路 2: impl-verify |
|---|---|---|
| **检查什么** | 测试用例是否通过 | 功能有没有做完 + 工程资料齐不齐 |
| **输入** | FRZ Package 中的验收测试用例 + GSD 代码 | FRZ Package 中的 SSOT 链 + GSD 交付物 |
| **谁执行** | v1 test_execution Skill | impl-verify Skill |
| **产出** | 测试报告 | 验收报告 |
| **关注点** | 测试通过/失败 | 任务完成度、工程资料、范围合规、溯源 |

---

## 5. 术语定义

为消除歧义，本 ADR 统一使用以下术语：

| 术语 | 定义 | 别名 |
|------|------|------|
| **FRZ (Freeze)** | SSOT 链的冻结状态，冻结后不允许静默修改 | 冻结 |
| **FRZ Package** | frz-ingest 的输出，包含冻结的 SSOT 链 + 验收测试用例 | 冻结包 |
| **Complete Design Package** | frz-ingest 的输入，来自上游工具的完整设计文档集 | 设计包 |
| **SSOT 链** | 从 SRC 到 IMPL 的完整文档链（不含 TEST） | SSOT |
| **FRZ Revise** | 冻结后发现需求错误/遗漏时的修订流程 | 需求修订 |
| **验收测试用例** | 从 FEAT.AC + test_design 生成的可执行测试用例，由 LL 在验收时执行 | 验收用例 |
| **GSD 交付物** | GSD 执行 FEAT 后交付的代码和工程资料。LL 独立执行验收测试（线路 1），不依赖 GSD 的测试证据作为验收输入。GSD 的test_evidence 作为参考信息，不作为验收判定依据。 | 交付物 |
| **Prototype** | HTML 高保真交互原型，E2E 测试的前置依赖 | 原型 |
| **invented semantics** | 编译过程中引入的、在原始 Complete Design Package 中不存在的业务语义。包括：新增的业务规则、未定义的状态转换、未授权的验收条件、额外的用户场景。判定标准：编译产物中任何无法追溯到 §6 定义的输入维度中某个具体字段的内容，即为 invented semantics。计数方式：每次编译后，对编译产物进行逐项溯源，统计无法追溯的语义内容项数。阈值：0（不允许任何 invented semantics）。 | 语义发明 |
| **alignment** | SSOT 链内部各对象之间的一致性。检查范围：FEAT 是否覆盖 SRC 需求、TECH/ARCH/API/UI 是否与 FEAT 对齐、source_refs 是否完整。检查时机：frz-ingest step_3。 | 对齐 |
| **drift** | 编译产物相对于原始输入的偏差。检查范围：来源追溯、范围漂移、意图漂移、技术漂移、设计漂移。检查时机：frz-ingest step_4。与 alignment 的区别：alignment 检查 SSOT 链内部一致性（产物之间），drift 检查编译产物与原始输入的偏差（产物 vs 输入）。 | 漂移 |

---

## 6. 输入定义：Complete Design Package

### 6.1 定义

Complete Design Package 是 frz-ingest 的输入，包含来自上游工具的完整设计文档。

### 6.2 结构定义

```yaml
complete_design_package:
  # 维度 1: 商业设计 (必填)
  business_design:
    product_vision:        # 产品愿景/产品简报
    scope_declaration:     # 需求范围声明 (In Scope / Out of Scope)
    success_metrics:       # 成功指标
    user_personas:         # 用户画像
    priority:              # 优先级划分

  # 维度 2: 产品设计 (必填)
  product_design:
    prd:                   # PRD 文档
    user_journey_map:      # 用户旅程地图
    business_rules:        # 业务规则
    exception_flows:       # 异常流程
    state_transitions:     # 状态转换

  # 维度 3: UX 设计 (有 UI 的项目必填)
  ux_design:
    design_principles:     # 设计原则 (≥3 条)
    interaction_flow:      # 核心页面交互流程
    state_expression:      # 状态表达规则
    design_tokens:         # 设计令牌引用
    copy_style:           # 文案风格指南
    platform_strategy:    # 平台差异策略
    error_state_ux:       # 错误状态 UX 规范
    prototype:            # HTML 高保真交互原型 (有 UI 时必填)
      format: static_html # 固定格式：静态 HTML
      scope: journey_level # 粒度：journey 级别（一个 journey 一个原型）
      includes:           # 原型必须包含的交互
        - button_responses   # 按钮交互响应
        - page_navigation    # 页面跳转
        - happy_path         # 主流程可走通
        - error_retry_paths  # 错误/重试路径
      source: string      # HTML 文件路径或引用

  # 维度 4: 架构设计 (必填)
  architecture_design:
    tech_stack:            # 技术选型 → 编译为 TECH
    layering:              # 架构分层与职责边界 → 编译为 ARCH
    sync_async_strategy:   # 同步/异步策略 → 编译为 TECH
    data_flow:             # 核心数据流 → 编译为 ARCH
    api_contract:          # API 端点定义 → 编译为 API
    sequence_diagrams:     # 前后端交互时序图 → 编译为 API
    storage_design:        # 存储方案 → 编译为 ARCH
    non_functional:        # 非功能性需求 → 编译为 TECH
    integration_points:    # 集成点与外部依赖 → 编译为 ARCH

  # 维度 5: 测试设计 (可选，用于生成验收测试用例)
  test_design:
    acceptance_criteria:   # 可测试的 AC (Given-When-Then)
    happy_path:            # 关键路径
    boundary_conditions:   # 边界条件
    ai_uncertainty:        # AI 不确定性场景
    test_strategy:         # 测试分层策略
    testability_review:    # 可测性评审结论
  # 注：test_design 不冻结为 SSOT 对象
  # 它是 frz-ingest 生成验收测试用例的参考输入
  # AC 主要来自 product_design，test_design 补充测试视角

  # 维度 6: 工程实施设计 (必填)
  engineering_design:
    implementation_scope:  # 实施范围边界
    key_decisions:         # 关键实现决策
    dependencies:          # 依赖关系
    rollback_strategy:     # 回滚与降级策略
    capacity_estimate:     # 性能与容量预估
```

### 6.3 完整性检查规则

frz-ingest 使用以下规则判断输入是否完整：

```yaml
completeness_rules:
  # 必填维度 - 缺少任一则拒绝编译
  required_dimensions:
    - business_design
    - product_design
    - architecture_design
    - engineering_design

  # 有条件必填维度
  conditional_dimensions:
    ux_design:
      condition: "complete_design_package.product_design.prd 中包含前端/UI 相关需求，或 complete_design_package.architecture_design.tech_stack 中包含前端技术栈（如 React/Vue/Angular/HTML/CSS），或 complete_design_package.test_design 中包含 e2e 测试策略"
      required_when: 满足上述任一条件
      required_fields: [design_principles, interaction_flow, prototype]

  # 可选维度 - 缺少时标记警告但不阻断
  optional_dimensions:
    - test_design  # 不冻结为 SSOT 对象，仅作为验收测试用例生成的参考

  # 每个维度内的必填字段
  required_fields:
    business_design: [product_vision, scope_declaration]
    product_design: [prd, user_journey_map, business_rules, exception_flows, acceptance_criteria]
    architecture_design: [tech_stack, api_contract]
    engineering_design: [implementation_scope, key_decisions]
```

### 6.4 完整性判定

```yaml
completeness_verdict:
  pass:
    meaning: 所有必填维度和字段都存在且非空
    action: 进入编译
  blocked:
    meaning: 缺少必填维度或必填字段
    action: 拒绝编译，输出缺失项清单
  partial:
    meaning: 可选维度缺失
    action: 警告，继续编译，标记缺失维度
```

---

## 7. Skill 体系

### 7.1 v1 Skill（保持不变）

v1 的以下 Skill 全部保持不变，直接复用：

| Skill | 职责 | v2 中的角色 |
|---|---|---|
| SSOT 文档生成和拆解 | 标准化转换 + 机械式拆解 | frz-ingest step_2 内部调用 |
| 测试用例生成 | 从 AC 生成可执行测试用例 | frz-ingest step_5 生成验收测试用例 |
| 测试执行 | 执行测试用例 | **线路 1** — 独立执行验收测试 |
| 测试证据收集 | 收集测试结果和证据 | **线路 1** — 收集测试证据 |

```text
LL 验收的两条线路：

线路 1 (v1 test_execution):  跑测试 → 测试报告
线路 2 (impl-verify):        检查完成度 + 工程资料 + 范围合规 + 溯源 → 验收报告

两条线并行执行，各自独立，都通过才算验收通过。
```

### 7.2 v1 Skill 调用接口

frz-ingest 调用 v1 Skill 时，使用以下接口约定：

```yaml
v1_skill_interface:
  # SSOT 文档生成 Skill
  ssot_generation:
    input:
      design_package: Complete Design Package  # §6 定义的结构
      target_format: ssot_chain                 # 输出格式
    output:
      src: SRC 文档
      epic: EPIC 文档（作为 SRC 章节）
      feat: FEAT 文档（作为 EPIC 章节）
      tech: TECH 文档
      ui: UI Spec 文档
      test: TEST 文档
      impl: IMPL 文档
    error_handling:
      missing_input: 返回 blocked 状态 + 缺失项清单
      conflict: 返回 conflict 状态 + 冲突描述
      timeout: 返回 timeout 状态 + 已完成部分的日志，支持重试
      module_import_failure: 返回 error 状态 + 失败模块名 + 堆栈信息
      unexpected_exception: 返回 error 状态 + 异常详情，不静默吞掉

  # 测试用例生成 Skill
  test_generation:
    input:
      ssot_chain: 冻结的 SSOT 链
      target_type: acceptance | unit | integration | e2e
    output:
      test_cases: 可执行测试用例列表
      coverage_map: 测试用例与 AC 的映射关系
    error_handling:
      timeout: 返回 timeout 状态 + 已生成的部分测试用例
      generation_failure: 返回 error 状态 + 失败原因，不输出不完整用例
      invalid_ac: 返回 warning + 跳过无效 AC + 继续生成其余用例

  # 测试执行 Skill
  test_execution:
    input:
      test_cases: 测试用例列表
      target_env: 执行环境
    output:
      results: 测试结果
      evidence: 测试证据（日志、截图、覆盖率报告）
    error_handling:
      timeout: 返回 partial_results + 未执行用例列表
      env_setup_failure: 返回 error 状态 + 环境诊断信息

  # 测试证据收集 Skill
  evidence_collection:
    input:
      test_results: 测试结果
      execution_report: 执行报告
    output:
      evidence_package: 结构化的证据包
      coverage_summary: 覆盖率摘要
    error_handling:
      missing_artifact: 返回 warning + 缺失项 + 可用部分
```

### 7.3 `frz-ingest` — SSOT 编译器 + 冻结器（新增）

#### 职责

接收 Complete Design Package，检查完整性，编译为 SSOT 链，冻结。

#### 处理流程

```yaml
frz_ingest_flow:
  step_1_completeness_check:
    action: 使用 §6.3 的规则检查输入完整性
    output: completeness_verdict (pass/blocked/partial)
    on_blocked: 终止，输出缺失项清单

  step_2_compile:
    action: 将 Complete Design Package 编译为 SSOT 链
    description: |
      编译 = 映射 + 拆解 + 格式标准化，不是推导。
      大部分字段直接映射，EPIC/FEAT/IMPL 按规则拆分。
    sub_steps:
      2_1_src:
        source: business_design
        target: SRC
        method: 直接映射（问题域/目标/边界/约束）
      2_2_epic:
        source: product_design.user_journey_map
        target: EPIC (作为 SRC 章节)
        method: 按用户旅程拆分为能力域
        nesting: |
          EPIC 作为 SRC.epics 数组的元素写入。
          每个用户旅程 → 一个 EPIC 条目，嵌套在 SRC 容器内。
          EPIC 内部包含 feats 数组，FEAT 作为 EPIC 的章节嵌套。
      2_3_feat:
        source: product_design.acceptance_criteria + user_journey_map
        target: FEAT (作为 EPIC 章节)
        method: 按 AC 拆分为可验收切片
        nesting: |
          FEAT 作为对应 EPIC.feats 数组的元素写入。
          一个 EPIC 下的多个 FEAT 按 AC 组拆分，每个 FEAT 独立可验收。
      2_4_tech:
        source: architecture_design (tech_stack, sync_async_strategy, non_functional)
        target: TECH
        method: 直接映射
      2_5_arch:
        source: architecture_design (layering, data_flow, storage_design, integration_points)
        target: ARCH
        method: 直接映射
      2_6_api:
        source: architecture_design (api_contract, sequence_diagrams)
        target: API
        method: 直接映射
      2_7_ui:
        source: ux_design
        target: UI Spec
        method: 直接映射（含 prototype 引用）
        condition: 有 ux_design 时
      2_8_impl:
        source: engineering_design + FEAT 列表
        target: IMPL (task 包)
        method: 拆解（每个 FEAT → 独立 task，每个 task 含上游上下文）
      2_9_cross_refs:
        source: 所有 SSOT 对象
        target: cross_axis_refs
        method: 机械关联（FEAT ↔ TECH/UI/API 的引用关系）
      2_10_traceability:
        source: 所有编译步骤
        target: source_refs (段落级)
        method: 记录每个 SSOT 元素的源位置
        recording_mechanism: |
          每个 SSOT 元素（SRC、EPIC、FEAT、TECH、ARCH、API、UI、IMPL）
          接收一个 source_refs 数组。编译时，每个子步骤（2_1-2_8）
          将其源映射记录为 {source_path}#{section}.{paragraph} 格式
          写入对应 SSOT 元素的 source_refs。
          示例: pre_ssot.product_design.md#S3.P2
          含义: 文档 pre_ssot.product_design.md 的第 3 节第 2 段
        source_ref_format: "{source_path}#{section}.{paragraph}"
        example: "pre_ssot.product_design.md#S3.P2"
        yaml_input_format: |
          当输入为 YAML/JSON 结构化数据时，段落编号规则调整为：
          以顶级 key 为节边界，节内以嵌套 key 路径为段落编号。
          格式: {source_path}#{top_key}.{nested_key_path}
          示例: complete_design_package.yaml#product_design.prd
          含义: complete_design_package.yaml 中 product_design.prd 字段
          复杂嵌套示例: complete_design_package.yaml#ux_design.prototype.source
    field_mapping_tables:
      # 直接映射步骤的字段级映射
      2_1_src_mapping:
        business_design.product_vision → SRC.business_goal
        business_design.scope_declaration → SRC.scope_boundaries + SRC.non_goals
        business_design.user_personas → SRC.target_users
        business_design.success_metrics → SRC.global_constraints (参考)
        business_design.priority → SRC.global_constraints (参考)

      2_4_tech_mapping:
        architecture_design.tech_stack → TECH.tech_stack
        architecture_design.sync_async_strategy → TECH.sync_async
        architecture_design.non_functional → TECH.non_functional

      2_5_arch_mapping:
        architecture_design.layering → ARCH.layering
        architecture_design.data_flow → ARCH.data_flow
        architecture_design.storage_design → ARCH.storage
        architecture_design.integration_points → ARCH.integration

      2_6_api_mapping:
        architecture_design.api_contract → API.endpoints
        architecture_design.sequence_diagrams → API.sequence_diagrams

      2_7_ui_mapping:
        ux_design.design_principles → UI.design_principles
        ux_design.interaction_flow → UI.interaction_flow
        ux_design.state_expression → UI.state_expression
        ux_design.design_tokens → UI.design_tokens
        ux_design.copy_style → UI.copy_style
        ux_design.platform_strategy → UI.platform_strategy
        ux_design.error_state_ux → UI.error_states
        ux_design.prototype → UI.prototype (引用，不复制内容)

      # 拆解步骤的拆分规则
      2_2_epic_splitting:
        rule: 按 user_journey_map 中的用户旅程拆分为能力域
        input: product_design.user_journey_map
        output: 每个旅程 → 一个 EPIC 章节
        nesting: EPIC 作为 SRC.epics 数组元素，嵌套在 SRC 容器内
        epic_fields:
          epic_id: 自动生成，格式 EPIC-{序号}
          capability_name: 从旅程名称映射
          user_value: 从旅程价值描述映射
          included_scenarios: 从旅程步骤提取
          excluded_scenarios: 从旅程边界提取

      2_3_feat_splitting:
        rule: 按 acceptance_criteria 拆分为可验收切片
        input: product_design.acceptance_criteria + user_journey_map
        output: 每个 AC 组 → 一个 FEAT 章节
        nesting: FEAT 作为 EPIC.feats 数组元素，嵌套在对应 EPIC 内
        feat_fields:
          feat_id: 自动生成，格式 FEAT-{EPIC_ID}-{序号}
          title: 从 AC 主题提取
          acceptance_criteria: 直接映射 AC
          main_flow: 从 AC 的 Given-When-Then 提取
          state_changes: 从 state_transitions 映射

      2_8_impl_splitting:
        rule: 每个 FEAT → 独立 task
        input: engineering_design + FEAT 列表
        output: 每个 FEAT → 一个 IMPL task
        task_fields:
          task_id: 自动生成，格式 TASK-{FEAT_ID}
          allowed_scope: 从 FEAT.cross_axis_refs + architecture_design 推导
          forbidden_scope: 从 FEAT.non_goals + SRC.scope_boundaries 推导
          upstream_context: 包含 FEAT.AC + TECH 关键决策 + API 端点列表
    error_handling:
      conflict: 终止，输出冲突描述
      missing_input: 终止，输出缺失项
      v1_skill_failure: |
        当内部调用的 v1 Skill 返回 error/timeout 时：
        - 记录失败的 Skill 名称、步骤、错误详情
        - 终止编译，返回 compile_blocked 状态
        - 输出已完成部分的日志和失败原因
        - 支持修复后重试（从失败步骤继续）

  step_3_alignment_check:
    action: 检查 SSOT 链内部一致性
    # 若 ITERATION-DOCUMENT-CHECKLIST.md 不存在，则 step_3 的检查使用本 ADR 内定义的规则
    checks:
      - requirement_coverage: FEAT 是否覆盖 SRC 中的所有需求
      - cross_axis_consistency: TECH/ARCH/API/UI 是否与 FEAT 对齐
      - traceability: 每个 SSOT 元素是否能追溯到输入
    failure_modes:
      requirement_gap: |
        检查方式: 统计 SRC 中 triggering_scenarios 和 scope_boundaries 中声明的需求项数，
        与 EPIC.feats 中的 FEAT 数量对比。如果 FEAT 数量 < 声明的需求项数，
        则存在 requirement_gap。
        注意: SRC schema 中不包含 requirement_count 字段，
        因此使用 triggering_scenarios + scope_boundaries 的条目数作为需求项数代理值。
        action: 终止，输出未覆盖需求清单
      cross_axis_mismatch: TECH/ARCH/API 描述与 FEAT 的 main_flow 不一致
        action: 终止，输出不一致项
      traceability_break: 编译产物无法追溯到输入源
        action: 终止，输出失联元素
      structural_mismatch: FEAT/TECH 数量与 EPIC 声明不符
        action: 警告，输出差异说明
    output: alignment_verdict (pass/fail)
    on_fail: 终止，输出 issues 列表，不进入漂移检测

  step_4_drift_detection:
    action: 使用 ITERATION-DOCUMENT-CHECKLIST.md 模板 B 进行漂移检测
    # 若 ITERATION-DOCUMENT-CHECKLIST.md 不存在，则 step_4 的检查使用本 ADR 内定义的规则
    checks:
      - source_tracing: 来源追溯检查
      - scope_drift: 范围漂移检测
      - intent_drift: 意图漂移检测（抽样 3 条）
      - tech_drift: 技术漂移检测
      - design_drift: 设计漂移检测
    output: drift_verdict (pass/drift_found)
    on_drift: 终止，输出漂移项清单

  step_4_5_dimension_quality_gate:
    action: 对 SSOT 链各维度进行质量评分，未达 A 级则打回修复
    description: |
      在 drift 检测之后、验收测试生成之前，对编译产出的 6 个维度（SRC/TECH/ARCH/API/UI/IMPL）
      分别执行质量评分。每个维度按 ITERATION-DOCUMENT-CHECKLIST.md 的必输要素逐项打分，
      100 分制，≥90 分为 A 级。
    scoring_dimensions:
      - src
      - tech
      - arch
      - api
      - ui
      - impl
    grade_thresholds:
      A: {min_score: 90, meaning: "信息完整、无语义漂移、标准统一，可直接进入 Freeze"}
      B: {min_score: 75, meaning: "核心信息完整，存在次要缺失，建议修复后进入 Freeze"}
      C: {min_score: 60, meaning: "信息部分缺失，存在阻塞项，必须修复后才能进入 Freeze"}
      D: {min_score: 40, meaning: "严重缺失，无法支持下游工程实施"}
      F: {min_score: 0,  meaning: "维度产出为空或完全不可用"}
    freeze_rule: "所有维度必须 ≥ A 级（score ≥ 90），否则 Freeze 被阻塞"
    auto_repair:
      enabled: true
      max_iterations: 3
      strategies:
        parser_gap: "字段在 __raw__ 中但 Parser 未提取 → 放宽正则、降低 heading 级别、增加同义词映射"
        compiler_gap: "字段已提取但 Compiler 未映射 → 修复映射逻辑、扩展 dataclass 字段"
        cross_dimension_fallback: "本维度为空但其他维度有相关内容 → 跨维度回退查找"
        markdown_noise: "内容包含 Markdown 噪音 → _clean_markdown_noise() 清洗"
      human_escalation: "3 轮自动修复后仍不达 A 级 → 生成 HUMAN-REVIEW 阻塞清单，等待人工补充"
    quality_report_output:
      path: "QUALITY-REPORT-{frz_ref}__{slug}.md"
      content: "各维度得分、空字段清单、改进建议、自动修复日志"
    human_review_output:
      path: "HUMAN-REVIEW-{frz_ref}__{slug}.yaml"
      content: "需要人工补充的维度、缺失的 checklist 条目、建议补充的文档章节"
    output: dimension_quality_verdicts (list[DimensionQualityVerdict])
    on_blocked: 终止，输出质量报告 + 人工审查清单，进入 auto_repair 循环或人类介入

  step_5_generate_acceptance_tests:
    action: 调用 v1 test_generation Skill（§7.2 接口）
    input:
      ssot_chain: step_2 输出的冻结 SSOT 链（§7.2 test_generation.input.ssot_chain）
      target_type: acceptance  # §7.2 test_generation.input.target_type
    output: 可执行验收测试用例
    description: |
      调用 §7.2 定义的 test_generation Skill 接口。
      input.ssot_chain 使用 step_2 编译输出的 SSOT 链（含 FEAT.AC）。
      input.target_type 固定为 acceptance。
      生成的测试用例不冻结为 SSOT 对象，作为 FRZ Package 附件。
    test_types:
      api_test: 从 FEAT.AC + API 定义生成 API 测试用例
      e2e_test: 从 FEAT.AC + prototype 生成 E2E 测试用例（有 prototype 时）
    timing: 在 frz-ingest 内生成，作为 FRZ Package 的附件
    error_handling:
      v1_skill_timeout: |
        当 v1 test_generation Skill 超时时：
        - 记录超时时长和已完成的用例数
        - 终止编译，返回 compile_blocked 状态
        - 输出已生成的部分用例作为参考
        - 支持重试（从头重新生成，不追加）
      generation_partial_failure: |
        当部分 AC 的测试用例生成失败时：
        - 成功的用例保留
        - 失败的 AC 列出并标记
        - 如果失败 AC 数 > 总 AC 数的 20%，整体终止
        - 如果 ≤ 20%，输出警告 + 成功用例 + 失败清单
    # 验收测试用例在编译时生成，随 FRZ Package 一起交付给 GSD
    # GSD 可查看（了解验收标准），但最终由 LL 执行

  step_6_freeze:
    action: 冻结 SSOT 链
    output: FRZ Package
    freeze_rules:
      - 冻结后不允许静默修改
      - 小变更走 Experience Patch
      - 大变更走 FRZ Revise
    freeze_state_machine:
      states: [draft, frozen, revised]
      transitions:
        draft_to_frozen:
          trigger: frz-ingest step_6（所有检查通过后）
          guard: completeness=pass AND alignment=pass AND drift=pass AND all_dimensions_grade=A
        frozen_to_revised:
          trigger: FRZ Revise 流程
          guard: 人类发起，需记录修订原因
        revised_to_frozen:
          trigger: frz-ingest 重新编译（修订后）
          guard: 同 draft_to_frozen
      invalid_transitions:
        - frozen_to_draft: 不允许（必须走 FRZ Revise）
        - draft_to_revised: 不允许（必须先冻结）
```

#### 输出 Schema

```yaml
frz_package:
  frz_ref: string          # FRZ 唯一标识，格式: FRZ-{YYYYMMDD}-{序号}
  version: string          # 版本号，格式: v{major}.{minor}
  created_at: timestamp    # 创建时间
  source_package_ref: string  # 源 Design Package 引用

  frozen_sot_chain:
    src: SRC 文档
    epic: EPIC 文档（作为 SRC 章节）
    feat: FEAT 文档（作为 EPIC 章节）
    tech: TECH 文档
    arch: ARCH 文档        # 架构设计
    api: API 文档          # API 契约
    ui: UI Spec 文档       # 可选（有 UI 时）
    impl: IMPL 文档        # task 实施包

  acceptance_test_cases:   # 附件，不冻结为 SSOT 对象
    api_tests: list        # API 测试用例（从 FEAT.AC + API 生成）
    e2e_tests: list        # E2E 测试用例（从 FEAT.AC + prototype 生成）
    coverage_map: map      # AC → 测试用例映射
    total_ac: int          # 总 AC 数
    covered_ac: int        # 已覆盖 AC 数

  completeness_check:
    verdict: pass | blocked | partial
    missing_items: list    # 缺失项清单
    warnings: list         # 警告项清单

  alignment_check:
    verdict: pass | fail
    issues: list           # 一致性问题清单

  drift_check:
    verdict: pass | drift_found
    drift_items: list      # 漂移项清单

  dimension_quality_check:
    verdict: pass | blocked
    dimensions:
      - dimension: src | tech | arch | api | ui | impl
        score: int           # 0-100
        grade: A | B | C | D | F
        blockers: list        # 阻塞项清单
        warnings: list        # 警告项清单
        auto_repairable: boolean
        human_required: boolean
    quality_report_ref: string    # QUALITY-REPORT 文件路径
    human_review_ref: string      # HUMAN-REVIEW 文件路径

  evidence_refs:
    source_docs: list      # 源文档引用
    compilation_log: string  # 编译日志引用
```

#### 不可协商规则

- 不补全缺失需求（输入不完整时拒绝编译）
- 不静默修复语义冲突
- 不改变业务意图（遵守红色警戒线）
- 所有冻结内容必须能追溯到上游来源
- 缺少阻断信息时输出 `compile_blocked`

#### 异常处理

```yaml
frz_ingest_error_handling:
  compile_blocked:
    meaning: 输入不完整
    action: 输出缺失项清单，等待人类补充后重试
    retry: 支持增量重试（只补充缺失项，不重新编译已有部分）

  conflict:
    meaning: SSOT 链内部存在冲突
    action: 输出冲突描述，等待人类裁决
    retry: 裁决后重新编译

  drift_found:
    meaning: 编译过程引入了漂移
    action: 输出漂移项清单，拒绝冻结
    retry: 修正后重新编译

  quality_gate_blocked:
    meaning: 一个或多个维度未达到 A 级质量评分
    action: 输出 DIMENSION-QUALITY-REPORT + HUMAN-REVIEW 清单
    retry: |
      1. 自动修复：frz-ingest 执行最多 3 轮 auto_repair（放宽提取规则、跨维度回退、清洗噪音）
      2. 人工补充：若 3 轮后仍不达 A 级，人类根据 HUMAN-REVIEW 清单补充设计文档
      3. 重新编译：补充后重新运行 frz-ingest
    escalation: |
      当自动修复 3 轮失败且人类未补充时，FRZ Package 不允许生成。
      产出物仅保留 QUALITY-REPORT 和 HUMAN-REVIEW，供人工决策。

  partial_compile:
    meaning: 可选维度缺失，部分编译
    action: 输出部分结果 + 警告，标记缺失维度
    retry: 补充缺失维度后可增量编译

  v1_skill_failure:
    meaning: 内部调用的 v1 Skill 执行失败（超时/异常/模块错误）
    action: 终止编译，输出失败步骤和错误详情
    retry: 修复后从头重试（编译是幂等操作）
```

### 7.4 `impl-verify` — 完成度验收（新增）

#### 职责

GSD 交付后，验证功能是否做完、工程资料是否齐全、范围是否合规。**不跑测试 — 测试由线路 1（v1 test_execution）独立执行。**

#### 定位

```text
LL 验收分两条独立线路：

线路 1: v1 test_execution — 跑验收测试用例，检查测试是否通过
线路 2: impl-verify — 检查功能完成度、工程资料、范围合规、溯源

两条线并行执行，都通过才算验收通过。
impl-verify 不重复线路 1 的工作。
```

#### 输入 Schema

```yaml
impl_verify_input:
  frz_package: FRZ Package  # §7.3 输出的冻结包（含 SSOT 链）

  gsd_delivery:             # GSD 交付物
    feat_ref: string        # 对应的 FEAT ID
    code:
      files_changed: list   # 修改的文件列表
      files_added: list     # 新增的文件列表
      git_diff_ref: string  # git diff 引用
    engineering_artifacts:  # 工程资料（必填）
      change_description: string     # 代码变更说明（改了什么、为什么）
      key_decisions: list            # 关键决策记录（技术选型、架构决策）
      dependency_changes: list       # 依赖变更说明（新增/升级了什么）
      known_issues: list             # 已知问题和限制
      rollback_plan: string          # 回滚方案（如适用）
    execution_report:       # 执行报告（可选）
      phase: string
      tasks_completed: list
      tasks_failed: list
      blockers: list
```

#### 验收过程

```yaml
impl_verify_flow:
  step_1_task_completion_check:
    action: 检查功能是否做完
    process:
      - 从 IMPL 提取所有 task 及其 allowed_scope
      - 对每个 task，检查代码变更是否覆盖了 allowed_scope 中的文件
      - 检查每个 task 是否标记完成状态
      - 检查每个 FEAT 是否全部交付
    checks:
      task_scope_coverage:
        description: allowed_scope 中的文件是否都被修改
        method: 对比 IMPL.allowed_files vs GSD code.files_changed + files_added
      task_completion_status:
        description: 每个 task 是否标记完成
        method: 检查 GSD execution_report.tasks_completed
      feat_coverage:
        description: 每个 FEAT 是否全部交付
        method: 检查所有 FEAT 的 task 是否都已完成
    output:
      total_tasks: int
      completed_tasks: int
      incomplete_tasks: list      # 未完成的 task 详情
      scope_gaps: list           # allowed_scope 中未被修改的文件

  step_2_engineering_artifacts_check:
    action: 检查工程资料是否齐全
    required_artifacts:
      change_description:
        check: 非空且有意义（不是占位符）
        machine_judgeable: |
          自动检查: 非空 AND 长度 ≥ 50 字符 AND 不匹配已知占位符模式
          （如 "TODO", "placeholder", "TBD", "待补充"）
          人工复查: 内容是否准确描述了变更（半自动，工具标记可疑项）
      key_decisions:
        check: 列表非空（至少记录了关键的技术选型决策）
        machine_judgeable: "自动检查: 列表非空 AND 每项长度 ≥ 20 字符"
      dependency_changes:
        check: 如有新增/升级依赖，必须提供说明
        machine_judgeable: "自动检查: 如果 files_changed 包含 package.json/requirements.txt 等依赖文件，则 dependency_changes 必须非空"
      known_issues:
        check: 列表存在（可以为空，但字段必须存在）
        machine_judgeable: "自动检查: 字段存在（允许空列表）"
      rollback_plan:
        check: 如涉及数据迁移或破坏性变更，必须提供回滚方案
        machine_judgeable: |
          自动检查: 如果 change_description 包含 "migration"、"database"、
          "breaking change"、"schema" 等关键词，则 rollback_plan 必须非空
    output:
      artifacts_complete: boolean
      missing_artifacts: list     # 缺失的资料清单
      artifact_quality: good | insufficient | missing

  step_3_scope_compliance_check:
    action: 检查是否有越界行为
    checks:
      forbidden_scope_violation:
        description: 是否修改了禁止修改的文件
        method: 对比 GSD code vs IMPL.forbidden_scope
      unauthorized_feature:
        description: 是否实现了未在 SSOT 中定义的功能
        method: 对比 GSD 代码变更 vs SSOT 中的 FEAT/TECH/ARCH/API
        algorithm: |
          将 GSD code.files_changed + files_added 中的每个文件，
          与 IMPL.allowed_files 逐一对比。不在 allowed_files 中的文件
          → unauthorized_feature 违规。
        process:
          - 提取 GSD 代码变更中所有新增/修改的文件
          - 对每个文件，检查是否在 IMPL.allowed_files 中
          - 不在 allowed_files 中的文件 → unauthorized_feature 违规
          - 阈值: 0（不允许任何未授权的新增文件）
      semantic_change:
        description: 是否通过实现细节改变了产品语义
        method: 从 FEAT 提取 business_rules 和 state_transitions
        automation_level: semi_manual
        algorithm: |
          从 FEAT 提取所有 state_transitions 和 business_rules。
          对比代码中的条件分支（if/else、switch）和路由定义（route definitions）。
          未匹配的分支 → semantic_change 疑似违规。
          本检查为半自动化：工具标记潜在违规，人工确认。
        process:
          - 从 FEAT 提取所有 state_transitions 和 business_rules
          - 扫描代码中的条件分支和路由定义
          - 对比 FEAT 定义的状态转换与代码中的实际分支
          - 未匹配的分支标记为 semantic_change 疑似违规
          - 人工确认后判定为违规或误报
        note: 此检查无法完全自动化，依赖人工确认疑似违规项
    output:
      violations: list

  step_4_traceability_check:
    action: 检查代码变更能否追溯到 SSOT
    process:
      - 对每个代码变更文件，检查是否能追溯到 FEAT/TECH/ARCH/API
      - 检查 cross_axis_refs 是否与实际代码结构一致
    traceability_tiers:
      full_trace:
        meaning: 代码变更可追溯到具体的 FEAT/TECH/ARCH/API 元素
        weight: 1.0
      partial_trace:
        meaning: 代码变更可追溯到 SSOT 对象但无法精确到具体元素
        weight: 0.5
      no_trace:
        meaning: 代码变更无法追溯到任何 SSOT 对象
        weight: 0.0
    exemptions:
      config_files:
        description: 配置文件变更（如 .env、.gitignore、CI 配置）
        weight: 0.0  # 不计入 traceability 分子分母
      tooling_files:
        description: 工具链文件变更（如 linter 配置、formatter 配置）
        weight: 0.0
      generated_files:
        description: 自动生成的文件（如 lock 文件、编译产物）
        weight: 0.0
    output:
      traceable_changes: int
      untraceable_changes: list   # 无法追溯的变更
      traceability_rate: float  # 计算方式: Σ(weight) / (total - exempted)

  step_5_verdict:
    action: 综合判定
    rules:
      pass: 所有 task 完成 + 工程资料齐全 + 无范围违规 + 溯源率 ≥ 阈值
      fail: 任一 task 未完成 或 工程资料缺失 或 有范围违规 或 溯源率 < 阈值
      conditional_pass: 部分 FEAT 已交付且已交付部分通过验收（仅对已交付部分有效）
      threshold: 100%  # 可配置；使用 tiered traceability_rate（含豁免权重）
    transition_rules:
      conditional_pass_to_pass: 当剩余 FEAT 交付并验证通过后，verdict 升级为 pass
      conditional_pass_to_fail: 当截止时间超过且未完成交付时，verdict 降级为 fail
    注意: |
      本步骤的 verdict 仅反映完成度验收结果。
      最终验收通过需要本 verdict + 线路 1 (v1 test_execution) 的测试报告都通过。
      双线路收敛点见 §4.1 dual_track_convergence。
```

#### 输出 Schema

```yaml
completion_verification_report:
  frz_ref: string
  feat_ref: string
  verdict: pass | fail | conditional_pass

  task_completion:
    total_tasks: int
    completed_tasks: int
    incomplete_tasks: list
    scope_gaps: list

  engineering_artifacts:
    artifacts_complete: boolean
    missing_artifacts: list
    artifact_quality: good | insufficient | missing

  scope_compliance:
    violations: list
    violation_count: int

  traceability:
    traceable_changes: int
    untraceable_changes: list
    traceability_rate: float
    exemptions_applied: list

  required_actions:
    bug_fixes: list
    patch_candidates: list
    frz_revision_required: boolean

  summary: string
```

#### 不可协商规则

- 任务未完成 → 必须 fail
- 工程资料缺失 → 必须 fail
- forbidden_scope 被修改 → 必须 fail
- 未授权功能 → 必须 fail
- 需求本身有误 → 不允许 GSD 直接补，必须走 FRZ Revise
- Minor UI / Interaction 问题 → Experience Patch
- 实现偏差 → Bug Fix

#### 异常处理

```yaml
impl_verify_error_handling:
  partial_delivery:
    meaning: GSD 只交付了部分 FEAT
    action: 只验收已交付部分
    verdict: conditional_pass（仅对已交付部分）

  code_not_compilable:
    meaning: GSD 交付的代码无法编译
    action: 直接 fail，要求修复后重新交付

  missing_engineering_artifacts:
    meaning: GSD 未提供工程资料
    action: 直接 fail，要求补充工程资料后重新验收
```

---

## 8. 需求轴结构调整

### 8.1 SRC / EPIC / FEAT 关系

保留三层，但调整为容器-章节关系：

```text
SRC (容器)
  ├── EPIC (章节) — 能力域 / 业务闭环
  └── FEAT (章节) — 可验收功能切片，下游 GSD 的执行单位
```

关键点：
- SRC 是顶层容器
- EPIC 和 FEAT 是 SRC 中的章节结构
- 下游 GSD 按 FEAT 粒度消费，一个 FEAT = 一个 task 任务包
- 不合并 SRC / EPIC / FEAT（SRC 保留需求根和边界，EPIC 保留业务能力域）

### 8.2 向后兼容策略

v2 的 SRC/EPIC/FEAT 采用容器-章节结构，与 v1 的独立文件结构不同。向后兼容策略：

```yaml
backward_compatibility:
  # v1 到 v2 的迁移
  v1_to_v2_migration:
    strategy: 渐进迁移
    rules:
      - 现有 v1 SSOT 文档保持不变，继续作为 legacy 使用
      - 新需求使用 v2 格式
      - 旧需求的修改可以保持 v1 格式，不强制迁移
    migration_tool: 可选，未来如有需要可开发 v1→v2 转换工具

  # v2 到 v1 的兼容
  v2_to_v1_compat:
    strategy: 读取兼容
    rules:
      - v2 的 SRC 容器可以被 v1 工具读取（EPIC/FEAT 作为独立对象）
      - v1 工具不需要理解 v2 的容器结构
      - impl-verify 可以同时处理 v1 和 v2 格式的 SSOT

  # 格式共存
  coexistence:
    strategy: 按项目/需求区分
    rules:
      - 同一项目中可以同时存在 v1 和 v2 格式的 SSOT
      - 通过 freeze_status 字段区分冻结状态，通过 format_version 字段区分格式版本
      - impl-verify 支持两种格式的验收

  # 混合链交互规则（v1 和 v2 文档同时存在时）
  mixed_chain_rules:
    principle: 同一 FRZ Package 内部的 SSOT 链必须格式一致
    cross_reference:
      v2_feat_refs_v1_tech: 允许，impl-verify 分别按各自格式验收
      v1_feat_refs_v2_tech: 允许，impl-verify 分别按各自格式验收
    impl_verify_behavior:
      - 逐文档判断格式版本（根据 freeze_status 和 format_version 字段）
      - 按对应版本的规则执行验收
      - 在验收报告中标注混合格式情况
    recommendation: 尽量避免混合格式；如不可避免，优先统一为 v2 格式

  # FRZ Package output schema 与现有 FRZPackage dataclass 的关系
  schema_migration:
    status: 待实现阶段对比
    description: |
      本 ADR 定义的 frz-ingest output schema 与现有 frz_schema.py 中的 FRZPackage
      dataclass 存在字段重叠。具体差异和迁移路径需在 FRZ-055 实现阶段通过代码级
      schema 对比确定。当前 ADR 的 output schema 为权威定义，现有 dataclass 应向
      此 schema 对齐。
    action: FRZ-055 实现时，对比 FRZPackage dataclass 与本 ADR output schema，记录差异并制定迁移计划
```

### 8.3 SRC

SRC 是需求轴的根事实对象，回答：为什么做？为谁做？解决什么问题？不解决什么问题？全局边界和约束是什么？

```yaml
src:
  src_id: string
  title: string
  version: string           # SRC 版本号
  format_version: string    # 格式版本号（区分 v1/v2 格式）
  problem_domain: string
  business_goal: string
  target_users: list
  triggering_scenarios: list
  scope_boundaries: list
  non_goals: list
  global_constraints: list
  source_refs: list
  open_questions: list
  freeze_status: frozen | draft | revised
  epics:                    # EPIC 作为 SRC 的章节
    - epic_id: string
      capability_name: string
      user_value: string
      business_closure: string
      included_scenarios: list
      excluded_scenarios: list
      acceptance_theme: string
      cross_axis_refs:
        ui_refs: list
        tech_refs: list
        test_refs: list
      feats:                # FEAT 作为 EPIC 的章节
        - feat_id: string
          title: string
          user_value: string
          trigger: string
          main_flow: list
          alternative_flows: list
          state_changes: list
          acceptance_criteria: list
          uat_scenarios: list
          non_goals: list
          dependencies: list
          cross_axis_refs:
            ui_refs: list
            tech_refs: list
            api_refs: list
            e2e_refs: list
          gsd_phase_hint:
            recommended_phase: string
            can_be_independently_uat: boolean
            blocking_dependencies: list
          source_refs: list
```

---

## 9. Traceability 与漂移防控

### 9.1 来源追溯

LL v2 要求 source refs 从文件级升级为段落级 / journey step 级 / design unit 级。

```yaml
traceability:
  frz_ref: string
  source_spans:
    - ref: string            # 源文档引用，格式: {文档路径}#{章节}.{段落}
      type: explicit | inferred
      mapped_to:             # 映射到的 SSOT 元素
        - string

段落级追溯的实现方式:
  # frz-ingest 编译时，对每个 SSOT 元素记录其源位置
  # 源位置格式取决于输入类型：
  #
  # Markdown 输入: {文档路径}#{章节}.{段落编号}
  #   示例: pre_ssot.product_design.md#S3.P2
  #   含义: 文档 pre_ssot.product_design.md 的第 3 节第 2 段
  #   段落编号规则: 以 H2/H3 标题为节边界，节内以空行分段
  #
  # YAML/JSON 输入: {文件路径}#{顶级key}.{嵌套key路径}
  #   示例: complete_design_package.yaml#product_design.prd
  #   含义: complete_design_package.yaml 中 product_design.prd 字段
  #   嵌套示例: complete_design_package.yaml#ux_design.prototype.source

  实现复杂度: 低
  # 原因: 编译过程中，v1 的标准化转换逻辑已经建立了元素与源的映射
  # frz-ingest 只需要在转换时记录源位置，不需要额外的 NLP 分析

  维护规则:
    - source_ref 在编译时写入后不可修改（冻结状态）
    - 源文档编辑后，source_ref 可能失效（指向已变更的位置）
    - 失效的 source_ref 不影响已冻结的 SSOT，但应在 FRZ Revise 时更新
    - 验收时发现 source_ref 失效，标记为 warning（不阻断验收）
```

### 9.2 漂移防控

复用 `ITERATION-DOCUMENT-CHECKLIST.md` 的漂移防控机制：

```yaml
drift_prevention:
  # 编译时漂移检测（frz-ingest 内部，§7.3 step_4）
  compilation_drift:
    - source_tracing: 来源追溯检查
    - scope_drift: 范围漂移检测
    - intent_drift: 意图漂移检测（抽样 3 条）
    - tech_drift: 技术漂移检测
    - design_drift: 设计漂移检测

  # 验收时漂移检测（impl-verify 内部，§7.4 step_4）
  verification_drift:
    - unauthorized_check: 未授权行为检查
    - forbidden_scope_violation: 禁止范围违规检查

  # 时序关系
  timing:
    - 编译时漂移检测: frz-ingest 内部，在冻结前执行
    - 验收时漂移检测: impl-verify 内部，在验收时执行
    - 两者独立，不重叠
```

---

## 10. Gate 规则

LL v2 的 Gate 核心是确认：
- 输入是否完整（§6.3 检查）
- 编译过程是否只做结构化转换（无语义新增）
- 是否保留完整追溯
- SSOT 链各部分是否一致

### 10.1 Gate 与 Freeze Guard 的关系

```yaml
gate_and_freeze_guard:
  # Freeze Guard 是 v1 的冻结保护机制
  # Gate 是 v2 的决策层

  freeze_guard:
    角色: 保护已冻结的 SSOT 不被修改
    触发: 任何对冻结 SSOT 的修改尝试
    行为: 阻止修改，要求走 FRZ Revise

  gate:
    角色: 决策是否可以进入下游
    触发: 编译完成或验收完成
    行为: 输出 pass/fail/revise

  关系:
    - frz-ingest 的冻结步骤会调用 Freeze Guard 注册冻结
    - Gate 是独立的决策层，不替代 Freeze Guard
    - Freeze Guard 保护冻结状态，Gate 决策是否可以冻结
```

### 10.2 Gate 决策

```yaml
gate_decision:
  pass:
    meaning: 可冻结，可进入下游
    criteria:
      - completeness_check.verdict == pass
      - alignment_check.verdict == pass
      - drift_check.verdict == pass

  fail:
    meaning: 输入不完整、编译漂移或证据不足
    criteria:
      - completeness_check.verdict == blocked
      - drift_check.verdict == drift_found
      - alignment_check.verdict == fail

  revise:
    meaning: 需要人类修改 Pre-SSOT / FRZ 后重跑
    criteria:
      - 发现需求本身的错误或遗漏
      - 发现不可调和的冲突
```

### 10.3 语义缺口规则

语义缺口不得 conditional pass。只要存在以下问题，必须 fail 或 revise：
- open question 未关闭
- 上游来源缺失
- 编译过程中发现轴间冲突
- invented semantics > 0（编译产物中存在无法追溯到输入的语义内容，见 §5 术语定义）
- 测试覆盖关键验收缺失
- IMPL 缺少可执行证据计划

---

## 11. 与 GSD 的关系

### 11.1 发包方-外包方模型

| 角色 | 类比 | 职责 |
|---|---|---|
| **LL（发包方）** | 甲方 | 编译 SSOT、冻结语义、两条线路并行验收 |
| **GSD（外包方）** | 乙方 | 执行 FEAT 任务包、自测、交付代码+测试证据+工程资料 |

**协作原则：frz-ingest 的输出给 GSD，GSD 的输出给 impl-verify，中间没有多余的交互。**

```text
LL frz-ingest → FRZ Package (SSOT + 验收测试用例) → GSD
GSD → 代码 → LL impl-verify
```

### 11.2 合同约束

```yaml
contract_constraints:
  # GSD 必须遵守的约束
  gsd_obligations:
    - 只执行 FEAT 任务包中定义的任务
    - 不得发明新需求
    - 不得修改冻结验收标准
    - 不得绕过 forbidden scope
    - 不得通过实现细节改变产品语义
    # 注：GSD 不需要向 LL 提供测试证据
    # GSD 的测试是 GSD 自己的质量保证
    # LL 的验收是独立的，LL 自己跑测试

  # GSD 交付物格式要求
  delivery_format:
    code:
      files_changed: list    # 必填
      files_added: list      # 必填
      git_diff_ref: string   # 必填
    engineering_artifacts:   # 必填，impl-verify 验收用
      change_description: string     # 代码变更说明
      key_decisions: list            # 关键决策记录
      dependency_changes: list       # 依赖变更说明
      known_issues: list             # 已知问题和限制
      rollback_plan: string          # 回滚方案（如适用）
    test_evidence:           # 可选（参考信息，LL 独立执行验收测试）
      test_results: list
      coverage_report: string
      execution_logs: list
    execution_report:        # 可选，了解执行情况
      phase: string
      tasks_completed: list
      tasks_failed: list
      blockers: list

  # 验收时限
  acceptance_timeline:
    # 以下为策略性目标，非工程约束
    # AI 执行的 skill 不具备时钟/调度能力，实际执行时间取决于会话时长
    # 此处定义的是人类期望的服务水平，实现时需通过外部调度机制（如 CI cron、人工触发）保障
    max_acceptance_time: 24h    # 策略目标
    max_evidence_supplement_time: 48h  # 策略目标
    enforcement: |
      此时限为 SLA 目标，不作为 frz-ingest/impl-verify 的内置约束。
      实现方式: 通过外部调度机制（如 CI cron job、人工触发重跑）
      在超时后自动通知人类介入。
      超时本身不改变 verdict，但人类可基于超时决定手动干预。

  # 违约处理
  breach_handling:
    missing_evidence: 直接 fail，要求补充
    partial_delivery: 只验收已交付部分
    non_compilable_code: 直接 fail，要求修复
    unauthorized_feature: 直接 fail，要求移除未授权代码
    semantic_change: fail，升级到 FRZ Revise

  # 违约检测机制
  violation_detection:
    unauthorized_feature:
      method: 对比 GSD 代码变更 vs SSOT 中的 FEAT 定义
      algorithm: |
        将 GSD code.files_changed + files_added 中的每个文件，
        与 IMPL.allowed_files 逐一对比。不在 allowed_files 中的文件
        → unauthorized_feature 违规。
      process:
        - 提取 GSD 交付物中所有新增/修改的代码文件
        - 对每个文件，检查是否在 IMPL.allowed_files 中
        - 不在 allowed_files 中的文件 → unauthorized_feature 违规
      threshold: 0  # 不允许任何未授权的新增功能
    semantic_change:
      method: 对比实现行为 vs SSOT 中的业务规则
      automation_level: semi_manual
      algorithm: |
        从 FEAT 提取所有 state_transitions 和 business_rules。
        对比代码中的条件分支（if/else、switch）和路由定义（route definitions）。
        未匹配的分支 → semantic_change 疑似违规。
        本检查为半自动化：工具标记潜在违规，人工确认。
      process:
        - 从 FEAT 提取所有 state_transitions 和 business_rules
        - 扫描代码中的条件分支和路由定义
        - 对比 FEAT 定义的状态转换与代码中的实际分支
        - 未匹配的分支标记为 semantic_change 疑似违规
        - 人工确认后判定为违规或误报
      threshold: 0  # 不允许任何语义变更
```

### 11.3 GSD 只消费 FEAT

GSD 按 FEAT 粒度消费 SSOT，每个 FEAT = 一个 task 任务包。

标准流程：

```text
frz-ingest 编译冻结 SSOT + 生成验收测试用例
    ↓
FRZ Package (SSOT 链 + 验收测试用例)
    ↓
GSD 执行（编码 + 自己的测试，LL 不关心）
    ↓
交付代码
    ↓
impl-verify（LL 自己跑验收测试 + checklist 检查）
```

### 11.4 GSD 不允许做的事情

- 不允许发明新需求
- 不允许修改冻结验收标准
- 不允许绕过 forbidden scope
- 不允许通过实现细节改变产品语义
- 不允许把测试阶段发现的需求缺口直接补进代码

如果 GSD 发现冻结对象无法实施，应输出 conflict / blocker，并回流至 LL / FRZ Revise。

---

## 12. 问题回流机制

实施后问题分三类处理。

| 问题类型 | 处理路径 | 触发条件 |
|---|---|---|
| 实现没有满足冻结需求 | Bug Fix / GSD Remediation | impl-verify 判定 fail，且需求本身正确 |
| UI / Interaction 小问题，不改变语义 | Experience Patch | impl-verify 发现 minor UI/interaction 问题 |
| 冻结需求本身错误、遗漏或冲突 | FRZ Revise | impl-verify 或 GSD 发现需求本身有误 |

### 12.1 FRZ Revise 流程

```yaml
frz_revise_flow:
  trigger:
    - impl-verify 发现需求本身的错误
    - GSD 发现冻结对象无法实施
    - 测试发现需求遗漏
    - 人类主动发现需求问题

  process:
    step_1: 人类发起 FRZ Revise 请求
    step_2: 记录修订原因和修订内容
    step_3: 更新 Pre-SSOT 设计包
    step_4: 重新运行 frz-ingest 编译
    step_5: 新 FRZ Package 版本号递增
    step_6: 通知相关 GSD 执行器

  versioning:
    # 语义版本规则 (semver)
    # minor (v1.0 → v1.1): 修正措辞/补漏（不改变需求意图和范围）
    #   示例: 修正 AC 措辞、补充遗漏的边界条件、修正拼写
    # major (v1.x → v2.0): 新增/删除需求、修改范围、改变验收标准意图
    #   示例: 新增 FEAT、删除 AC、修改业务规则、改变用户旅程
    - FRZ Package 版本号递增: v1.0 → v1.1 (minor) 或 v2.0 (major)
    - 保留历史版本，可追溯
    - 旧版本标记为 superseded

  version_classification_decision_tree: |
    问: 修订是否改变了任何 FEAT 的 acceptance_criteria 的意图？
      是 → major
      否 → 继续
    问: 修订是否新增或删除了任何 FEAT？
      是 → major
      否 → 继续
    问: 修订是否改变了 SRC 的 scope_boundaries？
      是 → major
      否 → 继续
    问: 修订是否改变了任何 business_rules 或 state_transitions？
      是 → major
      否 → 继续
    问: 修订是否仅涉及措辞修正、拼写、格式、遗漏的边界条件补充？
      是 → minor
      否 → 默认 major（不确定时按 major 处理）

  traceability:
    - 记录每次 Revise 的原因、内容、影响范围
    - 关联到具体的 SSOT 元素

  rollback:
    # 编译错误回滚（冻结后发现编译过程本身有误）
    trigger: 冻结后发现 frz-ingest 编译逻辑有 bug（如映射错误、格式化错误）
    process:
      step_1: 标记当前 FRZ Package 为 corrupted
      step_2: 保留 corrupted 版本作为审计记录
      step_3: 修正 frz-ingest 编译逻辑
      step_4: 使用相同输入重新运行 frz-ingest
      step_5: 新 FRZ Package 版本号递增（major）
      step_6: 通知相关 GSD 执行器使用新版本
    与 FRZ Revise 的区别:
      FRZ Revise: 需求本身有误（输入问题）
      Rollback: 编译逻辑有误（工具问题）
```

### 12.2 变更控制

- 小变更（不改变语义）：Experience Patch
- 大变更（需要修改 SSOT）：FRZ Revise — 开新需求，重新走 frz-ingest

---

## 13. SSOT 格式版本管理

```yaml
ssot_format_versioning:
  # 格式版本号
  format_version: string  # 格式: {major}.{minor}

  # 版本规则
  versioning_rules:
    major: 结构性变更（新增必填字段、删除字段、改变层级关系）
    minor: 兼容性变更（新增可选字段、新增文档类型）

  # 向后兼容策略
  backward_compatibility:
    - minor 版本变更: 向后兼容，旧工具可以读取新格式
    - major 版本变更: 不向后兼容，需要工具升级

  # 版本变更流程
  change_process:
    step_1: 在 ADR 中记录格式变更
    step_2: 更新本 ADR 中的 schema 定义
    step_3: 通知所有下游工具
    step_4: 提供迁移指南（如需）

  # 当前版本
  current_version: "1.0"
```

---

## 14. 演化策略

### 14.1 LL 的消亡路径

> 注：以下演化策略为说明性内容（非规范性），基于当前判断的估计，可随实际演进调整。

LL 的存在理由是"填补工具空白"。当工具成熟时，LL 应逐步退出。

#### 消亡触发条件

```yaml
exit_trigger_conditions:
  ssot_management:
    trigger: 出现支持标准化 SSOT 格式的工具
    criteria:
      - 工具能读取和写入 §8.3 定义的 SRC 格式
      - 工具支持 EPIC/FEAT 章节结构
      - 工具支持 freeze_status 管理
      - 工具在实际项目中稳定使用 ≥ 3 个月
    exit_action: frz-ingest 的编译逻辑由工具替代，LL 只保留冻结逻辑

  test_execution:
    trigger: 出现成熟的 AI 测试执行工具
    criteria:
      - 工具能自动生成验收测试用例
      - 工具能自动执行测试并收集证据
      - 工具通过独立基准测试（benchmark suite），AC 覆盖率 ≥ 100%，证据收集质量与 v1 测试 Skill 持平
      - 工具在实际项目中稳定使用 ≥ 3 个月
    exit_action: LL 退出测试执行，只保留验收对比逻辑

  acceptance_verification:
    trigger: 出现支持文档级验收的工具
    criteria:
      - 工具能自动对比 SSOT 文档与代码交付物
      - 工具能自动生成 checklist 并执行
      - 工具通过独立基准测试（benchmark suite），验收结果与 impl-verify 一致率 ≥ 95%
    exit_action: LL 退出验收，整个 LL 框架可以退役
```

### 14.2 Skill = AI 推理的预编译

Skill 本质上是 AI 推理的固定化。随着 AI 能力增长，Skill 会自然变薄：

```text
当下: Skill 做固定转换 → 确定性高，性能好
中期: Skill 逐渐变薄 → 只保留核心校验逻辑
远期: Skill 几乎消失 → AI 直接做实时转换
```

LL v2 的 2 个 Skill 不是"永久架构"，而是"当前 AI 能力下的占位符"。

### 14.3 动态能力边界

没有本质上不能交给 AI 的决策。关键是动态识别当前 AI 能力边界：

- **当下方式**：人工判断 + 历史回溯（了解 AI/工具能力 → 使用 → 评估调整）
- **未来方向**：逐步系统化（置信度阈值、能力画像、历史数据驱动）

### 14.4 工具替换策略

- 核心 SSOT 格式保持稳定
- 工具替换时，AI 写转换 Skill（适配成本低，LLM 兼容性强）
- LL 跟着项目走，不绑定特定工具

---

## 15. 迁移策略

### 15.1 v1 保持不变

v1 的所有 Skill 全部保持不变：
- SSOT 文档生成和拆解逻辑 → frz-ingest 内部复用
- 测试用例生成/执行/证据收集 → 验收测试复用

### 15.2 新增 2 个 v2 Skill

```text
新增:
  ll-v2-frz-ingest    — 编译 + 冻结
  ll-v2-impl-verify   — 文档级验收
```

### 15.3 渐进落地顺序

#### Phase 1：frz-ingest 骨架

- 输入完整性检查（§6.3 规则）
- 调用 v1 Skill 接口（§7.2 定义）
- 冻结机制
- 漂移检测
- 段落级 source_refs
- 异常处理（§7.3 异常处理）

#### Phase 2：impl-verify 骨架

- checklist 自动生成（§7.4 生成规则）
- 测试证据覆盖检查
- 问题分类（Bug / Patch / Revise）
- 异常处理（§7.4 异常处理）

#### Phase 3：验收测试集成

- 复用 v1 测试执行能力
- 验收测试用例生成
- 测试证据收集和对比

#### Phase 4：扩展与优化

- impl-verify 支持更多文档类型（verifier 扩展）
- 动态能力边界机制
- 与更多工具的适配
- FRZ Revise 流程实现

---

## 16. Consequences

### 16.1 正向影响

1. **定位清晰**
   LL 从"做所有事"变成"编译 + 验收"，职责边界明确。

2. **大幅简化**
   从 8 个暴露 Skill 精简为 2 个，维护成本显著降低。

3. **符合"抓两头"原则**
   入口卡死（编译+冻结）+ 出口卡死（文档验收），中间层自由演化。

4. **v1 资产完全复用**
   标准化转换、测试生成/执行/证据收集全部复用，不需要重建。

5. **自然消亡路径**
   随 AI 能力增长，Skill 会自然变薄，LL 逐步退出工具已覆盖的领域。

6. **工具可替换**
   LL 不绑定特定工具，新工具出现时低成本适配。

### 16.2 代价

1. **v2 砍掉了智能补全能力**
   如果上游设计不完整，v2 会拒绝编译，而不是补全。这要求上游工具（BMAD 等）的输出质量更高。

2. **impl-verify 是文档级验收**
   不能发现"代码技术上正确但业务上错误"的问题。这是设计选择 — LL 管工程正确性，不管商业正确性。

3. **需要维护 SSOT 格式标准**
   虽然工具可替换，但 SSOT 的内部格式需要保持稳定。

### 16.3 本文档的规范性说明

本文档中，以下部分为**规范性**（实现必须严格遵循）：
- §5 术语定义
- §6 完整性检查规则和判定标准
- §7.2 v1 Skill 调用接口
- §7.3 / §7.4 异常处理定义
- §8.2 向后兼容策略
- §10 Gate 决策规则
- §11.2 合同约束
- §13 版本管理规则

以下部分为**说明性**（实现可参考但可调整）：
- §4 主流程图（展示架构意图）
- §7.3 / §7.4 处理流程步骤（展示处理顺序，具体实现可调整）
- §14 演化策略（基于当前判断的估计，可随实际演进调整）
- §15 迁移策略（落地顺序可调整）

---

## 17. Rejected Alternatives

### 17.1 保留 8 个 v2 Skill

拒绝。违背"不断瘦身"原则。8 个 Skill 增加维护成本，且中间层可以内化到两端。

### 17.2 独立 alignment-gate

拒绝。对齐检查可以内化到 frz-ingest 或 impl-verify 中，不需要独立 Skill。且实践表明即使有独立 Gate 也还会出问题。

### 17.3 三轴独立冻结（UI/TECH/TEST）

拒绝。可以合并到 frz-ingest 的编译过程中，不需要 3 个独立 Skill。

### 17.4 让 GSD 直接消费全部 SSOT 对象

拒绝。执行器上下文过大，容易选择性读取或自行解释需求。

### 17.5 ADR + 独立 SKILL-SPEC 文档

拒绝。对 AI 不友好 — 需要跨文件引用，上下文碎片化。单文档更适配 AI 工作流。

---

## 18. Final Decision Summary

本 ADR 决定：

1. LL v2 从"需求分析师"转型为"SSOT 编译器 + 验收官"
2. 从 8 个暴露 Skill 精简为 2 个：frz-ingest + impl-verify
3. 核心原则是"抓两头" — 入口编译冻结 + 出口版本验收
4. v1 全部保持不变，v2 复用 v1 的标准化转换和测试能力
5. v2 砍掉智能补全，只保留映射+拆解+格式标准化
6. **SSOT 链不含 TEST** — SRC/EPIC/FEAT/TECH/ARCH/API/UI/IMPL
7. **ux_design 必填**（有 UI 时），必须包含 HTML 高保真原型
8. **test_design 可选**，不冻结为 SSOT 对象，仅作为验收测试用例生成参考
9. 编译 = 映射（大部分字段直接映射）+ 拆解（EPIC/FEAT/IMPL 按规则拆分）
10. **LL 验收分两条线路**：线路 1 (v1 test_execution) 跑测试 + 线路 2 (impl-verify) 检查完成度
11. **GSD 交付物包含工程资料**（变更说明、决策记录、依赖变更、已知问题、回滚方案）
12. 协作模型：frz-ingest 输出 → GSD → 代码+测试证据+工程资料 → 两条验收线并行
13. 验收测试用例在 frz-ingest 内生成，作为 FRZ Package 附件
14. 两条验收线通过 AND gate 收敛后才算验收通过
15. LL 有自然消亡路径 — 工具成熟后逐步退出
16. 旧 Skill 保留为 legacy / v1 compatibility mode
17. 定义了 Complete Design Package 的完整 schema（§6）
18. 定义了编译的 10 个子步骤和详细映射规则（§7.3 step_2）
19. 定义了向后兼容策略（§8.2）
20. 定义了 SSOT 格式版本管理（§13）
21. 定义了消亡触发条件（§14.1）
22. 统一了术语（§5），包括 invented semantics、alignment、drift 的精确定义
23. 明确了 Gate 与 Freeze Guard 的关系（§10.1）
24. 定义了 GSD 合同约束（§11.2）— GSD 交付代码+测试证据+工程资料
25. 定义了 FRZ Revise 流程（§12.1），含 minor/major 分类决策树
26. 定义了完整性验证的执行方式（§1.2）
27. 定义了对齐检查的失败模式和处理（§7.3 step_3），含 requirement_gap 改进比较逻辑
28. 定义了 FRZ Revise 的 minor/major 版本判定标准（§12.1）
29. 定义了 GSD 违约检测机制（§11.2 violation_detection），含 semi_manual 标记
30. 定义了 v1/v2 混合链交互规则（§8.2 mixed_chain_rules）
31. 修复了消亡触发条件的循环定义（§14.1 benchmark suite）
32. 定义了编译错误回滚机制（§12.1 rollback）
33. 区分了完整性检查 vs 需求质量门控（§3.3 注释）
34. 区分了规范性 vs 说明性内容（§16.3）
35. 定义了双线路收敛逻辑（§4.1 dual_track_convergence），含 AND gate 和失败路由
36. 定义了 traceability 分层权重和豁免机制（§7.4 step_4）
37. 定义了 v1 Skill 调用的完整错误处理（§7.2），含超时和模块失败
38. 标准化了 freeze_status 命名，添加了 format_version 字段（§8.3）
39. 定义了容器-章节嵌套规则（§7.3 step_2_2/step_2_3）
40. 定义了 YAML 输入的 source_ref 格式（§7.3 step_2_10, §9.1）
41. 定义了 acceptance_timeline 的执行方式（§11.2）

核心原则：

```text
LL v2 不再是需求分析师，而是 SSOT 编译器、语义冻结器和版本验收官。
抓两头，放中间。两条验收线并行，AND gate 收敛，都通过才算通过。
```
