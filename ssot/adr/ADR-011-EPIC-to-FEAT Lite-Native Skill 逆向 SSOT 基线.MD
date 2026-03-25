# ADR-011：EPIC-to-FEAT Lite-Native Skill 逆向 SSOT 基线

* 状态：Accepted
* 日期：2026-03-25
* 决策者：Le Zeng
* 适用范围：`ll-product-epic-to-feat` skill、`product.epic-to-feat` lite-native runtime、`feat_freeze_package`
* 相关 ADR：ADR-001、ADR-003、ADR-004、ADR-005、ADR-006、ADR-008、ADR-009

---

# 1. 背景

`ll-product-epic-to-feat` 已经在仓库中形成了可运行实现：

* 有独立 skill 契约：`skills/ll-product-epic-to-feat/ll.contract.yaml`
* 有输入/输出 contract 与 schema
* 有本地 runtime：`scripts/epic_to_feat.py`
* 有 executor / supervisor 双角色约束
* 有产物写入、evidence、freeze guard 与下游 handoff
* 有单元测试冻结关键行为

但当前缺少一份正式 ADR，把这些“已经写死在实现里”的语义收敛成可引用的 SSOT 基线。

如果不补这层文档，后续最容易发生三类漂移：

* 把 canonical workflow template 当成唯一真相，却忽略本仓库已经落地的 lite-native runtime 压缩解释；
* 把 `epic-to-feat` 误解成“写几份 FEAT 文档”的文案型 skill，而不是受治理的 package transformer；
* 下游在 `TECH / TASK / TESTSET / delivery-prep / plan pipeline` 消费时，各自重新解释输入、边界、freeze 条件与 traceability。

因此需要一份逆向 ADR：

## **以当前 checked-in implementation 为事实来源，冻结 `ll-product-epic-to-feat` 在 LL 仓库中的真实 SSOT 语义。**

---

# 2. 问题陈述

当前仓库里，`epic-to-feat` 的真实行为并不只存在于某一个地方，而是被分散在多层实现中：

* skill 描述声明 canonical authority、输入输出边界与执行顺序；
* `input/contract.yaml`、`output/contract.yaml` 定义 package 结构；
* `epic_to_feat_common.py` 定义输入包准入与强校验；
* `epic_to_feat_derivation.py` 定义 FEAT 切分逻辑、约束、依赖与 acceptance checks；
* `epic_to_feat_runtime.py` 定义 bundle 结构、review/acceptance/gate 语义；
* `epic_to_feat_cli_integration.py` 定义 CLI commit、evidence、package manifest 与 freeze gate 落盘；
* `tests/unit/test_lee_product_epic_to_feat.py` 把关键推导规则冻结成可回归验证的断言。

这意味着：

* 如果只读 `spec-global` 的 workflow 模板，会漏掉本仓库的 lite-native 压缩实现；
* 如果只读 `SKILL.md`，会漏掉结构化字段、缺陷策略、CLI commit 与 freeze-ready 条件；
* 如果只看测试，会看到结果，但看不到完整边界定义。

所以，本 ADR 要回答的不是“理论上的 epic-to-feat 应该怎样”，而是：

## **当前仓库里已经存在的 `ll-product-epic-to-feat`，到底被实现成了什么。**

---

# 3. 决策

## 3.1 决策摘要

LL 正式冻结以下事实为当前仓库内 `epic-to-feat` 的逆向 SSOT 基线：

1. `ll-product-epic-to-feat` 是一个 **lite-native governed workflow skill**，不是普通文档生成器。
2. 它的唯一正式输入是 **freeze-ready 的 `epic_freeze_package`**，且必须来自 `product.src-to-epic`。
3. 它的唯一正式输出是 **一个 `feat_freeze_package` 目录包**，而不是若干松散 FEAT 文档。
4. 它在实现上采用 **executor + supervisor + freeze guard** 的双角色闭环，而不是 executor 自判完成。
5. 它在语义上是 **EPIC 边界向 FEAT 边界的受治理降阶与冻结**，不是继续做 TECH、TASK、TESTSET 的直接编写。
6. 它的下游目标被正式固定为：
   * `workflow.product.task.feat_to_delivery_prep`
   * `workflow.product.feat_to_plan_pipeline`
7. 它的输出必须强到足以让下游继续派生 `TECH`、`TASK`、`TESTSET`，而不需要重新回读或重拆父 EPIC。

---

## 3.2 Canonical Authority 的正式解释

`skills/ll-product-epic-to-feat/SKILL.md` 中的 canonical workflow template：

```text
E:\ai\LEE\spec-global\departments\product\workflows\templates\epic-to-feat\v1\workflow.yaml
```

在本 ADR 中被解释为：

* **上游语义来源**
* **阶段命名来源**
* **边界约束来源**

但不是本仓库内唯一的运行时真相。

本仓库内真正可执行、可校验、可回归的 authority 由以下 checked-in implementation 共同构成：

* `skills/ll-product-epic-to-feat/ll.contract.yaml`
* `skills/ll-product-epic-to-feat/input/contract.yaml`
* `skills/ll-product-epic-to-feat/output/contract.yaml`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat.py`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat_common.py`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat_derivation.py`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat_cli_integration.py`
* `tests/unit/test_lee_product_epic_to_feat.py`

因此，本 skill 的 SSOT 应按以下优先级理解：

```text
checked-in runtime + contracts + tests
  > skill prose
  > upstream template naming
```

换句话说：

## **只要仓库内 runtime、contract 与测试已经形成稳定闭环，它们就是本地实现语义的第一真相。**

---

## 3.3 正式输入边界

`ll-product-epic-to-feat` 只接受一个目录级输入包，且该目录必须满足 `epic_freeze_package` 约束。

正式输入最小集为：

* `package-manifest.json`
* `epic-freeze.md`
* `epic-freeze.json`
* `epic-review-report.json`
* `epic-acceptance-report.json`
* `epic-defect-list.json`
* `epic-freeze-gate.json`
* `handoff-to-epic-to-feat.json`
* `execution-evidence.json`
* `supervision-evidence.json`

同时必须满足以下条件：

* `artifact_type = epic_freeze_package`
* `workflow_key = product.src-to-epic`
* `status ∈ {accepted, frozen}`
* `epic-freeze-gate.json.freeze_ready = true`
* `epic_freeze_ref` 非空
* `src_root_id` 非空
* `source_refs` 非空，且至少能恢复一个 `SRC-*` ref
* `scope`、`non_goals`、`decomposition_rules`、`constraints_and_dependencies` 不可缺失
* 必须来自已治理、可冻结的 EPIC 层，而不是 raw / SRC candidate / informal markdown

以下输入被正式视为非法：

* raw requirement
* ADR 原文
* `src_candidate_package`
* 直接手写的 FEAT bundle
* 未 freeze-ready 的 EPIC candidate

这意味着：

## **`epic-to-feat` 不是“从任何上游说明文档继续拆 FEAT”，而是“只消费已通过上游治理的 EPIC freeze package”。**

---

## 3.4 正式阶段压缩模型

canonical workflow template 在本仓库中被压缩解释为 lite-native runtime，但关键 checkpoint 被保留。

保留的 canonical stage 为：

1. `input_validation`
2. `feat_boundary_design`
3. `feat_spec_generation`
4. `feat_identity_prepare`
5. `feat_review`
6. `feat_acceptance_review`
7. `feat_identity_formalize`
8. `feat_freeze_gate`

本仓库中的运行时压缩为：

### executor 负责

* 解析 authoritative EPIC context
* 从 `capability_axes` / `scope` 生成 FEAT 边界
* 生成 `feat-freeze-bundle.md/.json`
* 生成初始 review / acceptance / defect / handoff 内容
* 记录 execution evidence
* 通过 CLI commit 将主产物提交到受治理 artifacts 路径

### supervisor 负责

* 复核 FEAT 是否仍是 FEAT，而不是 task/UI/implementation slice
* 复核 traceability、acceptance checks、downstream readiness
* 生成 supervision evidence
* 生成 `feat-freeze-gate.json`
* 在当前实现中给出 `pass / revise` 结论，并据此决定 freeze-ready 与否

因此，当前实现的正式理解是：

```text
freeze-ready EPIC package
  -> executor 生成 FEAT bundle
  -> supervisor 复核 FEAT bundle
  -> freeze guard 校验 package readiness
  -> 下游 handoff
```

---

## 3.5 正式输出边界

`ll-product-epic-to-feat` 的唯一正式输出是：

## **一个 `artifacts/epic-to-feat/<run_id>` 目录下的 `feat_freeze_package`**

正式输出最小集为：

* `feat-freeze-bundle.md`
* `feat-freeze-bundle.json`
* `feat-review-report.json`
* `feat-acceptance-report.json`
* `feat-defect-list.json`
* `feat-freeze-gate.json`
* `handoff-to-feat-downstreams.json`
* `execution-evidence.json`
* `supervision-evidence.json`

此外还会落盘：

* `package-manifest.json`
* `_cli/*.request.json`
* `_cli/*.response.json`

正式 markdown sections 为：

* `FEAT Bundle Intent`
* `EPIC Context`
* `Boundary Matrix`
* `FEAT Inventory`
* `Acceptance and Review`
* `Downstream Handoff`
* `Traceability`

其中 `FEAT Inventory` 在当前基线下不再允许只列 `goal / scope / constraints / acceptance checks`。每个 FEAT 还必须冻结以下产品级子块：

* `Identity and Scenario`
* `Business Flow`
* `Product Objects and Deliverables`
* `Collaboration and Timeline`
* `Acceptance and Testability`
* `Frozen Downstream Boundary`

正式 JSON 最小头字段为：

* `artifact_type = feat_freeze_package`
* `workflow_key = product.epic-to-feat`
* `workflow_run_id`
* `status`
* `schema_version`
* `epic_freeze_ref`
* `src_root_id`
* `feat_refs`
* `downstream_workflows`
* `source_refs`

因此：

## **本 skill 输出的是“可供下游继续消费的受治理 bundle”，不是“写完几份 FEAT markdown 就算结束”。**

---

## 3.6 FEAT 的正式语义约束

本 skill 输出中的每一个 FEAT 都必须满足以下约束：

* 保持 FEAT 层，不得塌缩成 TASK
* 保持独立可验收
* 保持对父 EPIC 的 traceability
* 保持对下游 delivery-prep / plan 的可消费性
* 不得沦为 UI wireframe 说明
* 不得沦为 implementation-only slice
* 不得新增未在父 EPIC 中声明的新需求主题

在当前实现里，这些约束进一步被固化为结构性下限：

* 每个 FEAT 必须有 `feat_ref`
* 每个 FEAT 必须有 `title`
* 每个 FEAT 必须有 `business_value`
* 每个 FEAT 必须有 `identity_and_scenario`
* 每个 FEAT 必须有 `business_flow`
* 每个 FEAT 必须有 `product_objects_and_deliverables`
* 每个 FEAT 必须有 `collaboration_and_timeline`
* 每个 FEAT 必须有 `acceptance_and_testability`
* 每个 FEAT 必须有 `frozen_downstream_boundary`
* 每个 FEAT 至少有 3 条 `acceptance_checks`
* 每个 FEAT 至少有 4 条 `constraints`
* 每个 FEAT 至少有 3 条 `scope` bullets

这意味着当前实现正式拒绝“抽象治理切片 FEAT”。如果一个 FEAT 不能让下游在不回读 TECH 的情况下说清：

* 谁在什么场景下使用它
* 业务如何流转
* 交付物是什么
* 哪些业务语义已经冻结

那么该 FEAT 就还不合格。

bundle 级还必须满足：

* `boundary_matrix` 与 `feat_refs` 对齐
* `bundle_shared_non_goals` 非空
* `bundle_acceptance_conventions` 非空
* `source_refs` 中同时保留：
  * `product.src-to-epic::<run_id>`
  * `EPIC-*`
  * `SRC-*`

这一定义正式意味着：

## **FEAT 的成立标准，不是“标题像 FEAT”，而是“边界、约束、验收、追溯、下游可消费性同时成立”。**

---

## 3.7 FEAT 切分的正式规则

当前实现中，FEAT 的 primary decomposition axis 来自：

* `epic_json.capability_axes`
* 若缺失，则退化使用 `scope`

标准基础轴包括：

* `collaboration-loop`
* `handoff-formalization`
* `object-layering`
* `artifact-io-governance`

当上游 EPIC 满足：

* `rollout_requirement.required = true`

则必须额外生成：

* `skill-adoption-e2e`

这不是可选注释，而是实现里显式强制的 FEAT coverage。

若 `rollout_required = true` 却没有生成 `skill-adoption-e2e` FEAT，当前实现会记为 `P1` 缺陷，并阻断 freeze-ready。

同时，当前实现把 FEAT track 正式分成：

* `foundation`
* `adoption_e2e`

其中：

* 除 `skill-adoption-e2e` 外，默认都属于 `foundation`
* adoption/E2E 是 cross-cutting overlay，但在输出中被提升为独立 FEAT，而不是 release note 附注

---

## 3.8 ADR-005 前置基础注入规则

当前实现中存在一个重要的逆向事实：

如果 EPIC 体现出主链 IO/path 治理语义，且 source refs 满足以下任一条件：

* 已显式包含 `ADR-005`
* 或同时包含 `ADR-001`、`ADR-003`、`ADR-006` 且存在 `artifact-io-governance` 轴

则 runtime 会把 `ADR-005` 视为前置基础，并注入：

* `source_refs`
* `prerequisite_foundations`
* IO 相关 FEAT 的 goal / scope / constraints / dependency 描述

该规则的正式解释是：

## **对于 mainline handoff / formalization / IO-path 治理类 EPIC，ADR-005 被视为 prerequisite foundation，而不是与本 EPIC 并列重写的能力面。**

因此下游不得在 `epic-to-feat` 或其派生 FEAT 中重新实现：

* Gateway
* Path Policy
* Registry

它们只能被消费、接线、继承、约束化，不应在本 skill 中被再次定义为新的 primary foundation module。

---

## 3.9 Review、Acceptance 与 Gate 的正式语义

当前实现中的 review / acceptance / gate 不是装饰性附件，而是正式 runtime 对象。

### `feat-review-report.json`

负责表达：

* FEAT 分解是否保持 EPIC decomposition boundary
* 是否形成 boundary matrix
* 是否保留下游 workflow target
* 是否形成 foundation vs adoption/E2E track map

### `feat-acceptance-report.json`

至少覆盖以下维度：

* `independent_acceptance_boundary`
* `parent_child_traceability`
* `downstream_readiness`
* `structured_acceptance_checks`
* `evidence_completeness`

### `feat-defect-list.json`

当前实现至少会对以下问题产生缺陷：

* FEAT 数量不足以形成有效边界拆分
* 某 FEAT 的 acceptance checks 不足
* rollout-required EPIC 缺少 adoption/E2E FEAT coverage

### `feat-freeze-gate.json`

freeze-ready 需同时满足：

* execution evidence present
* supervision evidence present
* feat refs present
* downstream handoff present
* structured acceptance checks complete
* feat count valid

因此，当前 skill 的正式语义是：

## **FEAT freeze 不是 executor 产出文件即成立，而是 supervisor 通过后、gate checks 全绿后才成立。**

---

## 3.10 CLI-First Materialization 的正式地位

根据实现，主 bundle markdown 不直接以自由文件写入作为最终成立方式，而是通过：

```text
cli.ll artifact commit
```

完成受治理提交。

这一步会生成：

* request payload
* response payload
* registry record
* receipt ref

这意味着 `epic-to-feat` 明确继承 ADR-009 的 CLI-first runtime 承载路线，而不是自由文件写入路线。

正式约束为：

* `feat-freeze-bundle.md` 必须通过 CLI commit 进入正式 artifact 路径
* `package-manifest.json` 必须记录 CLI commit 结果引用
* executor 与 supervisor commit 是可追踪对象，不是隐式 side effect

---

## 3.11 下游 handoff 的正式定义

`handoff-to-feat-downstreams.json` 不是普通说明文件，而是下游正式路由对象。

其中必须保留：

* `epic_freeze_ref`
* `src_root_id`
* `feat_refs`
* `feat_track_map`
* `target_workflows`
* `derivable_children`
* `primary_artifact_ref`
* `supporting_artifact_refs`
* `prerequisite_foundations`

正式下游固定为：

* `workflow.product.task.feat_to_delivery_prep`
* `workflow.product.feat_to_plan_pipeline`

正式可派生子对象固定为：

* `TECH`
* `TASK`
* `TESTSET`

`TESTSET` 在当前实现中被正式解释为：

## **下游派生 child，而不是在 `epic-to-feat` 内直接 authored object。**

---

## 3.12 不允许的退化

以下做法被视为违反本 ADR：

1. 直接接受 raw requirement、ADR 原文、SRC candidate 或任意 markdown 作为输入。
2. 跳过 `scripts/epic_to_feat.py`，手工只写最终 FEAT bundle。
3. 让 executor 自己判定 semantic pass 并直接 freeze。
4. 生成只有标题和摘要、没有 acceptance checks / constraints / boundary matrix 的 FEAT。
5. 把 FEAT 写成 TECH、TASK、UI、代码实现说明或 screen TODO。
6. 让下游 workflow 重新回拆父 EPIC，而不是消费当前 FEAT package。
7. 在 `artifact-io-governance` 或 `skill-adoption-e2e` FEAT 里重写 ADR-005 foundation modules。
8. 将 rollout/adoption 要求降级为 release 注释，而不是显式 FEAT coverage。

---

# 4. 设计后果

本 ADR 冻结后，对仓库内后续工作的直接影响是：

## 4.1 对 skill 演进的影响

凡是修改以下任一项的语义：

* 输入包准入条件
* FEAT 切分规则
* required output artifacts
* gate readiness 条件
* 下游 workflow 路由
* rollout/adoption FEAT 强制规则

都不应只改脚本，还应同步更新：

* `ll.contract.yaml`
* `input/output contract`
* `tests/unit/test_lee_product_epic_to_feat.py`
* 本 ADR

## 4.2 对下游消费的影响

下游 `delivery-prep` 与 `plan pipeline` 应把当前 `feat_freeze_package` 当作正式父对象，而不是：

* 重新回读上游 EPIC 自己再拆
* 直接从 `scope` 猜 FEAT
* 通过相邻文件路径做旁路发现

## 4.3 对 SSOT 物化层的影响

当前仓库中 `ssot/feat/*.md`、`ssot/tech/*`、`ssot/tasks/*` 等物化对象，若声称来源于 `epic-to-feat`，则必须服从本 ADR 所冻结的 bundle 结构、traceability 与下游继承边界。

---

# 5. 事实来源

本 ADR 依据以下已检查的实现与断言逆向形成：

* `skills/ll-product-epic-to-feat/SKILL.md`
* `skills/ll-product-epic-to-feat/ll.contract.yaml`
* `skills/ll-product-epic-to-feat/input/contract.yaml`
* `skills/ll-product-epic-to-feat/input/schema.json`
* `skills/ll-product-epic-to-feat/output/contract.yaml`
* `skills/ll-product-epic-to-feat/output/schema.json`
* `skills/ll-product-epic-to-feat/output/template.md`
* `skills/ll-product-epic-to-feat/resources/upstream-workflow-analysis.md`
* `skills/ll-product-epic-to-feat/agents/executor.md`
* `skills/ll-product-epic-to-feat/agents/supervisor.md`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat.py`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat_common.py`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat_derivation.py`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat_runtime.py`
* `skills/ll-product-epic-to-feat/scripts/epic_to_feat_cli_integration.py`
* `tests/unit/test_lee_product_epic_to_feat.py`

因此，这份 ADR 是：

## **implementation-derived SSOT**

而不是独立于实现之外重新发明的一份理想化规范。

---

# 6. 结论

LL 当前仓库中的 `ll-product-epic-to-feat` 已经不是概念草图，而是一条明确落地的受治理主链：

```text
freeze-ready epic_freeze_package
  -> lite-native executor derivation
  -> supervisor semantic review
  -> freeze guard
  -> feat_freeze_package
  -> downstream delivery-prep / plan pipeline
```

本 ADR 正式冻结其逆向 SSOT 基线：

## **`epic-to-feat` 的真相是一个 package transformer、boundary freezer、downstream handoff producer，而不是自由 FEAT 文档生成器。**
