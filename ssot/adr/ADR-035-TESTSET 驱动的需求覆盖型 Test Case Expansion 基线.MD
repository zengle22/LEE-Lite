# ADR-035：TESTSET 驱动的需求覆盖型 Test Case Expansion 基线

* 状态：Draft
* 日期：2026-03-31
* 决策者：Le Zeng
* 适用范围：`ll-qa-feat-to-testset`、`ll-test-exec-cli`、`ll-test-exec-web-e2e`、`TESTSET` / `TestCasePack` / test report contract
* 相关 ADR：ADR-007、ADR-012、ADR-018

---

# 1. 背景

前一轮关于 QA test execution 的实现，已经证明下面几件事是可行的：

* `TESTSET -> test-exec-cli -> evidence / report / TSE` 这条 governed 链可以跑通；
* `coverage_goal`、`branch_families`、`expansion_hints` 等 qualification 字段可以由 `feat-to-testset` 自动派生；
* `test-exec-cli` 可以在 qualification 模式下做 line / branch coverage 采集、expanded case 生成与多轮执行；
* ADR-018 的若干真实链路已经可以跑到 line / branch 目标。

但同一轮验证也暴露出一个更基础的问题：

> 当前最需要解决的主矛盾，不是“如何把 coverage 百分比自动推到更高”，而是“如何让一个 TESTSET 进来后，系统稳定地展开出覆盖功能点、边界条件、正负向逻辑的 runnable test cases，并统一执行与报告”。

换句话说，系统之前正在向一个过重的“自动 qualification 平台”演化，而没有先把更基本、也更有价值的一层冻结下来：

* 上游如何稳定表达“该测什么”
* 下游如何稳定展开“该怎么测”
* `acceptance / risk -> case -> report` 的 traceability 如何成为硬契约

如果这一层不先冻结，后续会出现三类典型漂移：

* `TESTSET` 被一步步推成半个执行 DSL；
* `test-exec-cli` 被一步步推成万能编排器；
* 测试报告重新退化成“coverage 百分比汇报”，而不是“需求与风险验证汇报”。

因此，本 ADR 要修订之前偏重 qualification automation 的方向，明确冻结：

## **当前阶段的主目标是：构建一套 TESTSET 驱动的、需求覆盖导向的 test case expansion 与执行系统。**

在这套系统中：

* coverage 是参考指标；
* 功能点、边界条件、正负向逻辑、异常/冲突路径的系统性覆盖才是主目标；
* `test-exec-cli` 首先要成为“需求驱动测试用例展开与执行引擎”，而不是“自动 coverage 收敛工具”。

---

# 2. 问题陈述

当前需要回答的，不是“怎么继续增加 coverage feedback loop 的复杂度”，而是下面几个更基本的问题：

## 2.1 `TESTSET` 到底该表达什么

如果 `TESTSET` 只表达抽象策略，而不表达足够稳定的功能面、逻辑维度与 traceability contract，下游展开就会继续依赖：

* 人工理解 FEAT / ADR / 需求文档；
* 人工决定哪些正向 / 负向 / 边界 case 该出现；
* 人工为特定场景编写 harness。

## 2.2 `test-exec-cli` 到底该自动化什么

如果执行层的主要目标被定义为“把 coverage 自动补到 80%”，那实现会自然向：

* coverage gap feedback loop
* expansion seed
* harness 补丁
* branch / line 收敛

倾斜，而不是先解决：

* 一个 TESTSET 进来以后，怎么稳定展开出完整功能型 case pack；
* 每个 acceptance / risk 到底被哪些 cases 覆盖；
* 报告到底该怎么呈现测试价值。

## 2.3 Traceability 到底是不是 P0

如果 `acceptance / risk -> case -> report` 不是硬 contract，而只是报告里的附属描述，那么系统仍会退回：

* case 是临时生成的；
* coverage 是主要判断依据；
* 功能与风险覆盖只能靠人工解释。

## 2.4 功能型测试设计与 qualification automation 的边界是什么

如果不先把二者分层，就会继续混淆：

* 需求覆盖型 case expansion
* coverage-driven qualification expansion

前者应该是主路径；
后者应该是增强路径。

本 ADR 要解决的，是先把主路径冻结。

---

# 3. 决策

## 3.1 决策摘要

LL 正式采用：

## **一套 TESTSET 驱动的、需求覆盖型的 Test Case Expansion 基线**

作为 `feat-to-testset` 与 `test-exec-*` 之间的新标准接缝。

本 ADR 冻结以下原则：

1. 当前阶段 `test-exec-cli` / `test-exec-web-e2e` 的主目标，不是自动把 coverage 收敛到阈值，而是把 `TESTSET` 稳定展开为覆盖功能点、边界条件、正负向逻辑的 `TestCasePack`。
2. coverage 保留为参考指标，但不是主驱动，也不是主成功标准。
3. `TESTSET` 继续是测试设计对象，而不是执行 DSL。
4. `functional_areas` 必须升级为 typed object，而不是自由文本标签。
5. `logic_dimensions` 必须升级为分层维度模型，而不是一个平铺列表。
6. `acceptance / risk -> case -> report` traceability 必须提升为 P0 contract，进入 schema 与 case pack，而不能只停留在测试报告叙述层。
7. `coverage_matrix` 在本 ADR 中指“需求覆盖矩阵”，不是代码 coverage 报表；它必须成为 `case_expander` 的直接输入之一。
8. `test-exec-cli` 的实现重心正式转移到：
   * `case_expander`
   * `fixture_planner`
   * `script_mapper`
9. coverage-driven qualification expansion 继续保留，但降级为增强路径，不得再主导主流程的对象建模与报告结构。
10. Phase 1 必须先把“traceable case pack”做扎实，再谈更高级的自动执行泛化。

---

## 3.2 系统定位

本 ADR 正式将该系统定位为：

## **需求驱动的测试用例展开与执行系统**

而不是：

* 代码覆盖工具
* coverage 自动收敛工具
* test generation 炫技器
* 通用万能编排器

其主问题始终是：

> 如何把需求、acceptance、风险点与状态约束，系统性翻译成可执行测试资产并执行。

---

# 4. 对象边界修订

## 4.1 `TESTSET` 的职责

`TESTSET` 继续负责定义：

* 测试范围
* 功能点
* 风险重点
* acceptance traceability
* 最小测试策略单元
* 测试层
* 环境前提
* 禁止覆盖或延后覆盖的区域

`TESTSET` 不负责：

* 最终 runnable case 数；
* 最终执行脚本；
* 为代码 coverage 人工穷举所有分支实例；
* 把自己膨胀成执行 DSL。

本 ADR 在 ADR-012 基础上进一步冻结：

## **`TESTSET` 是测试设计对象，不是执行语言，也不是 coverage qualification case inventory。**

## 4.2 `TestCasePack` 的职责

`TestCasePack` 负责承接：

* 由 `TESTSET` 展开的、结构化的、可执行的测试用例资产；
* 每个 case 对功能点、acceptance、risk 的 traceability；
* 执行所需的最小 fixtures / script mapping 信息。

它是 `test-exec-*` 的主输入资产之一，也是测试报告的直接来源对象。

## 4.3 `coverage_matrix` 的职责

本 ADR 新增一层正式对象语义：

## **`coverage_matrix` 指需求覆盖矩阵，不是代码 coverage 结果。**

它至少用于表达：

* 哪些 acceptance 必须被哪些 case family 覆盖；
* 哪些 risk 必须被哪些 case family 覆盖；
* 哪些 functional area 至少需要哪些 case family。

`coverage_matrix` 是 case expansion 的 contract，不是执行后统计产物。

---

# 5. `TESTSET` schema 修订

## 5.1 `functional_areas` 必须是 typed object

本 ADR 明确拒绝把 `functional_areas` 仅定义为自由文本列表。

不推荐：

```yaml
functional_areas:
  - runner entry
  - monitor surface
  - recovery flow
```

推荐最小基线：

```yaml
functional_areas:
  - key: runner_entry
    kind: control_surface
    related_entities: [execution_job]
    related_commands: [loop.run-execution]
  - key: recovery_flow
    kind: stateful_flow
    related_entities: [execution_job]
    related_commands: [loop.recover-jobs]
```

正式原则：

* `key` 必须稳定；
* `kind` 必须可枚举；
* `related_entities` 与 `related_commands` 必须可机器消费；
* label 或 title 可以作为展示字段存在，但不能替代 typed object。

## 5.2 `logic_dimensions` 必须是分层维度模型

本 ADR 明确拒绝把所有 logic dimension 平铺在一个列表中。

不推荐：

```yaml
logic_dimensions:
  - happy_path
  - boundary_conditions
  - invalid_input
  - state_conflict
  - retry_reentry
  - read_only_guard
```

推荐最小基线：

```yaml
logic_dimensions:
  universal:
    - happy_path
    - invalid_input
    - boundary_conditions
  stateful:
    - valid_transition
    - invalid_transition
    - retry_reentry
  control_surface:
    - authorized_action
    - rejected_action
    - read_only_guard
```

正式原则：

* `universal` 维度适用于大多数功能点；
* `stateful` 维度只适用于状态机或生命周期相关 area；
* `control_surface` 维度只适用于控制面 / 只读面 / 权限边界面。

这不是表现层整理，而是为了让 `case_expander` 能稳定推导“某类功能面适用哪些 case families”。

## 5.3 `state_matrix` 升级为 `state_model`

本 ADR 认为，简单罗列状态集合不足以支撑高质量的 case expansion。

不推荐：

```yaml
state_matrix:
  - entity: execution_job
    states: [ready, claimed, running, waiting_human, failed, deadletter]
```

推荐最小基线：

```yaml
state_model:
  - entity: execution_job
    states: [ready, claimed, running, waiting_human, failed, deadletter]
    valid_transitions:
      - [ready, claimed]
      - [claimed, running]
      - [running, waiting_human]
      - [running, failed]
    guarded_actions:
      - command: loop.run-execution
        allowed_in: [ready, claimed]
        rejected_in: [waiting_human, deadletter]
```

正式原则：

* 至少要支持合法迁移、非法迁移、守卫动作、拒绝动作这四类 case 生成；
* 不要求一开始做成超重状态机 DSL；
* 但不能停留在“只有状态名，没有状态关系”。

## 5.4 `case_expansion_rules` 必须可执行化

本 ADR 明确拒绝只有设计口号式的展开规则。

不推荐：

```yaml
case_expansion_rules:
  per_acceptance:
    require:
      - happy_path
      - negative_path
```

推荐最小基线：

```yaml
case_expansion_rules:
  per_acceptance:
    default_dimensions: [happy_path]
    add_negative_when:
      - has_rejection_clause
      - has_invalid_input_constraint
  per_stateful_area:
    default_dimensions: [valid_transition, invalid_transition]
  per_control_surface:
    default_dimensions: [authorized_action, rejected_action, read_only_guard]
```

正式原则：

* 规则必须告诉执行器“什么时候需要哪些 case families”；
* 不能只告诉执行器“应该测得全面一点”。

## 5.5 新增 `coverage_matrix`

本 ADR 将 `coverage_matrix` 提升为 P0 contract。

最小表达示例：

```yaml
coverage_matrix:
  acceptances:
    - acc_id: ACC-001
      covered_by_case_families: [happy_path, invalid_input]
  risks:
    - risk_id: RISK-003
      covered_by_case_families: [invalid_transition, retry_reentry]
  functional_areas:
    - area_key: recovery_flow
      required_case_families: [happy_path, invalid_transition, error_propagation]
```

正式原则：

* `case_expander` 必须先读 `coverage_matrix`，再做展开；
* 测试充分性首先由需求覆盖矩阵判断，而不是由代码 coverage 判断。

---

# 6. `test-exec-*` 职责修订

## 6.1 主职责

`ll-test-exec-cli` / `ll-test-exec-web-e2e` 的主职责修订为：

1. 读取 `TESTSET`
2. 读取 `coverage_matrix`
3. 读取 `functional_areas`
4. 读取 `logic_dimensions`
5. 读取 `state_model`
6. 展开 `TestCasePack`
7. 规划 fixtures
8. 绑定脚本模板
9. 执行
10. 汇总结果与 traceability report

coverage 采集仍可继续保留，但只属于附加结果。

## 6.2 实现重心

当前阶段实现重心正式冻结为：

* `case_expander`
* `fixture_planner`
* `script_mapper`

而不是：

* coverage feedback loop
* branch seed 强化
* 自动 qualification 收敛

## 6.3 报告重心

测试报告的主结构正式冻结为：

1. 功能覆盖摘要
2. acceptance traceability
3. risk traceability
4. case matrix
5. 执行结果
6. coverage summary（附录）

coverage 不得再作为报告主标题级指标压过“测了什么、如何验证”的表达。

---

# 7. Phase 规划修订

## 7.1 Phase 1A：Traceable Case Pack

Phase 1A 的目标是：

## **先把 traceable case pack 跑通。**

范围：

* `functional_areas`
* 分层 `logic_dimensions`
* `coverage_matrix`
* acceptance / risk traceability
* `case_expander`

此阶段要求：

* 自动产出结构化 `TestCasePack`
* 每个 case 都能追溯到：
  * `functional_area`
  * `acceptance`
  * `risk`
  * `case_family`

此阶段不要求：

* 覆盖率自动收敛
* 复杂 fixture 全自动化
* 任意新 testset 零模板执行

成功标准：

* case pack 完整
* 结构稳定
* traceability 清晰

## 7.2 Phase 1B：统一执行

Phase 1B 的目标是：

## **让 Traceable Case Pack 变成统一可执行资产。**

范围：

* `fixture_planner`
* `script_mapper`
* 统一 runner template
* test report

此阶段要求：

* 不再为每个 testset 单独手写大量 ad hoc harness
* 至少对常见模式建立模板化执行路径

## 7.3 Phase 2：Qualification 作为增强路径

Phase 2 才允许继续推进：

* line / branch coverage qualification
* coverage-driven expansion
* 自动收敛

但本 ADR 明确规定：

## **Phase 2 不得反向塑造 Phase 1 的主对象和主流程。**

---

# 8. 成功标准

本 ADR 的成功标准不是：

* “平均 coverage 提高到多少”

而是：

1. 一个 `TESTSET` 进入后，可以自动展开出完整、结构稳定的 `TestCasePack`
2. 每个 acceptance 与 risk 至少能回链到一个 case family
3. `functional_areas`、`logic_dimensions`、`state_model` 能稳定驱动 case expansion
4. 测试报告首先体现需求覆盖，而不是 coverage 百分比
5. 新增 testset 时，优先新增策略与模板，而不是继续增加 ad hoc harness

---

# 9. 对 ADR-007 / ADR-012 的修订性影响

本 ADR 不推翻 ADR-007 与 ADR-012，而是修订其当前阶段的实施优先级。

## 9.1 对 ADR-007 的影响

ADR-007 中关于：

* `TestSet`
* `TestCasePack`
* `ScriptPack`
* qualification mode
* evidence / report / TSE

的主对象边界继续有效。

本 ADR 的修订点是：

* 当前阶段应优先把 `TestCasePack` 做成需求覆盖导向的测试资产；
* qualification automation 继续保留，但不再作为对象建模主驱动。

## 9.2 对 ADR-012 的影响

ADR-012 中关于：

* `TESTSET` 是测试设计对象
* `TESTSET` 不直接生成 `TestCasePack`
* `TESTSET` 不膨胀为执行 inventory

继续有效。

本 ADR 的修订点是：

* `feat-to-testset` 必须更明确地产出 typed `functional_areas`、分层 `logic_dimensions`、`state_model`、`coverage_matrix` 这类“可展开测试设计 contract”；
* 而不只是给出 coverage qualification hints。

---

# 10. 明确拒绝的方向

本 ADR 明确拒绝以下方向作为当前阶段主路径：

## 10.1 继续把主问题定义为“coverage 自动补到阈值”

不采纳。

原因：

* 会把主流程重新拉回 qualification 平台；
* 会继续弱化需求覆盖与风险覆盖；
* 会推高执行器复杂度。

## 10.2 继续把 `functional_areas` 作为自由文本标签

不采纳。

原因：

* 不稳定；
* 无法挂规则；
* 无法稳定生成 case。

## 10.3 继续把 `logic_dimensions` 作为平铺列表

不采纳。

原因：

* 不能清晰表达哪些维度适用于哪些 area；
* 不利于 `case_expander` 泛化。

## 10.4 把 traceability 只放在报告层

不采纳。

原因：

* 这样系统仍然不是需求驱动；
* traceability 必须进入 schema 与 case pack。

---

# 11. 后续行动

本 ADR 通过后，后续实施必须按以下顺序推进：

1. 修订 `TESTSET` schema
   * 引入 typed `functional_areas`
   * 引入分层 `logic_dimensions`
   * 引入 `state_model`
   * 引入 `coverage_matrix`
2. 修订 `feat_to_testset_derivation`
   * 生成上述字段
3. 修订 `TestCasePack` schema
   * 强制每个 case 携带 acceptance / risk / area / family traceability
4. 实现 `case_expander`
   * 先做 Phase 1A
5. 实现 `fixture_planner` 与 `script_mapper`
   * 再做 Phase 1B
6. 最后才继续增强 qualification mode

正式实施纪律是：

## **下一步不要再扩复杂度，而是先冻结 area / dimension / traceability 三个核心 contract。**

---

# 12. 一句话结论

## **LL 当前阶段正式从“自动补 coverage”降维收敛到“需求驱动的 test case 展开与执行”。下一步的关键不是再加更多自动 qualification 模块，而是先冻结 `functional_areas`、`logic_dimensions`、`coverage_matrix` 与 traceability contract，让 `TESTSET -> TestCasePack -> report` 真正成为稳定的需求覆盖主链。**
