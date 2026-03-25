# ADR-010：src-to-epic Governed Workflow 具体实现冻结方案

* 状态：Accepted
* 日期：2026-03-25
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x `ll-product-src-to-epic` lite-native 治理实现
* 相关 ADR：ADR-002、ADR-004、ADR-005、ADR-008、ADR-009

---

# 1. 背景

仓库中 `skills/ll-product-src-to-epic/` 已经不是概念草案，而是一个可直接运行的 lite-native governed workflow：

* 有独立 `ll.contract.yaml`、输入/输出 contract、schema 与 semantic checklist；
* 有 `scripts/src_to_epic.py` 作为 CLI 入口；
* 有 `src_to_epic_runtime.py`、`src_to_epic_derivation.py`、`src_to_epic_cli_integration.py` 承担运行时、派生与物化逻辑；
* 有 executor / supervisor 双角色提示词；
* 有真实产物目录 `artifacts/src-to-epic/<run_id>/` 证明该链路已可落盘执行。

但到目前为止，这套实现仍主要存在于 skill 文件和脚本中，缺少一份 SSOT 级 ADR 去明确回答：

> `src-to-epic` 这条链路在 LL 中，到底冻结了哪些对象边界、运行阶段、派生规则、freeze gate 条件，以及哪些退化实现属于违规？

如果这层不冻结，会出现三类漂移：

* 有人把它理解成“把 SRC 改写成一篇 EPIC 文档”的轻量转换；
* 有人把 rollout / adoption / E2E 当成第二个并列 EPIC，而不是同一 EPIC 内必须保留的拆分要求；
* 有人绕过 execution / supervision / artifact commit / gate，只手写最终文件，导致治理证据链断裂。

因此，需要基于当前真实实现，逆向沉淀一份正式 ADR。

---

# 2. 决策

LL v0.x 正式冻结以下 `src-to-epic` 实现基线：

## **`ll-product-src-to-epic` 是一个以 `src_candidate_package` 为唯一正式输入、以 `epic_freeze_package` 为唯一正式输出的双阶段 governed workflow。**

该决策包含以下五个不可分割的子决策：

1. 输入准入必须是 `ll-product-raw-to-src` 产出的 `freeze_ready` 包，而不是原始需求或未冻结 SRC 草稿。
2. 运行时必须经过 `executor -> supervisor -> freeze gate` 三段，而不是单角色直接产出并自我批准。
3. 输出必须同时包含 EPIC 主文档、结构化 JSON、review / acceptance / defect / handoff / evidence / gate 产物。
4. EPIC 必须保持为 multi-FEAT capability boundary，不得塌缩为 FEAT、TASK、UI 细节或实现计划。
5. 当上游 SRC 涉及共享治理底座、skill 接入迁移或跨 skill E2E 时，仍只产出一个主 EPIC，但必须在该 EPIC 内显式保留 rollout / adoption / E2E 拆分要求。

---

# 3. 输入与输出边界

## 3.1 正式输入

`src-to-epic` 的正式输入固定为一个 `src_candidate_package`，并满足以下条件：

* `artifact_type = src_candidate_package`
* `status = freeze_ready`
* `workflow_key = product.raw-to-src`
* 必须包含 `package-manifest.json`、`src-candidate.md`、`src-candidate.json`、`structural-report.json`、`source-semantic-findings.json`、`acceptance-report.json`、`result-summary.json`、`proposed-next-actions.json`、`execution-evidence.json`、`supervision-evidence.json`
* `src-candidate.json` 必须带有 `workflow_run_id`、`title`、`source_kind`、`source_refs`、`problem_statement`、`target_users`、`trigger_scenarios`、`business_drivers`、`key_constraints`、`in_scope`、`out_of_scope`

因此，本 workflow 明确拒绝以下输入：

* 原始需求、ADR 文本、business opportunity
* `blocked`、`human_handoff_proposed`、`rejected` 等未冻结状态包
* 直接给一个 `epic_freeze_package`
* 缺失 provenance、evidence 或 acceptance report 的半成品 SRC 包

## 3.2 正式输出

`src-to-epic` 的正式输出固定为一个 `epic_freeze_package`，并至少包含：

* `epic-freeze.md`
* `epic-freeze.json`
* `epic-review-report.json`
* `epic-acceptance-report.json`
* `epic-defect-list.json`
* `epic-freeze-gate.json`
* `handoff-to-epic-to-feat.json`
* `execution-evidence.json`
* `supervision-evidence.json`

输出对象最小语义固定为：

* `artifact_type = epic_freeze_package`
* `workflow_key = product.src-to-epic`
* `downstream_workflow = product.epic-to-feat`
* 必须保留 `epic_freeze_ref`
* 必须保留 `src_root_id`
* 必须保留 `source_refs`

这意味着 `src-to-epic` 不是单一 Markdown 产出器，而是一个正式 package materializer。

---

# 4. 运行时模型

## 4.1 CLI-first 入口

当前实现已经冻结为 CLI-first runtime，统一入口为：

```bash
python scripts/src_to_epic.py run --input <src-package-dir> --repo-root <repo-root>
```

同时提供以下受管子命令：

* `executor-run`
* `supervisor-review`
* `validate-input`
* `validate-output`
* `validate-package-readiness`
* `freeze-guard`
* `collect-evidence`

这说明 `src-to-epic` 的正式接口是命令行与文件对象，而不是内嵌在 agent prompt 里的隐式步骤。

## 4.2 三段式推进

运行时按如下顺序推进：

### 第一段：Input validation

先对输入包做结构校验与准入判断，包括：

* freeze-ready 状态检查
* 上游 workflow 是否为 `product.raw-to-src`
* 推荐下游是否与 `product.src-to-epic` 一致
* 必填字段、必需 artifacts、traceability 是否完整

### 第二段：Executor draft

`executor_run()` 的职责是：

* 读取上游 SRC package
* 派生 EPIC payload
* 写出 EPIC 主文档和结构化 artifacts
* 记录 execution evidence
* 通过 `cli.ll artifact commit` 完成 `epic-freeze.md` 的正式 commit

因此，executor 并不是“写一份草稿就结束”，而是必须完成一次正式 artifact materialization。

### 第三段：Supervisor review + freeze gate

`supervisor_review()` 的职责是：

* 基于输出包中的 `product.raw-to-src::<run_id>` 反查 authoritative source package
* 重新生成派生结果并构造 supervision evidence
* 写出 `epic-freeze-gate.json`
* 更新 EPIC 状态并再次执行一次 artifact commit

最终是否 `freeze_ready`，不是由 executor 决定，而是由 supervision decision 与 gate checks 共同决定。

---

# 5. EPIC 派生规则

## 5.1 基本派生原则

`src-to-epic` 的核心实现不是“改写文案”，而是把上游问题空间提升到 EPIC 能力边界：

* 保留 `src_root_id`
* 保留 authoritative `source_refs`
* 形成一个供 `product.epic-to-feat` 继续拆分的单一 EPIC 真相
* 把 FEAT 分解规则写进 EPIC，但不直接越级产生 FEAT 实现内容

当前实现明确要求：

* EPIC 必须是 multi-FEAT boundary
* FEAT 只是 downstream handoff 的目标，不是本阶段直接产物
* TASK、实现顺序、UI 线框、实现细节都属于越界内容

## 5.2 多 FEAT 判定

当前实现通过 `multi_feat_score()` 对输入做 EPIC 合法性判断。判定信号来自：

* `in_scope` 数量
* `trigger_scenarios` 数量
* `bridge_context.governance_objects` 数量
* `expected_downstream_objects` 数量

当输入显示不出足够独立的能力切片时，系统会把“EPIC boundary may collapse to a single FEAT”写入 defect list，并阻止 freeze。

## 5.3 治理型 SRC 的固定能力轴

当输入被识别为 governance bridge package 时，当前实现不会自由发挥，而是优先收敛到一组固定 capability axes：

* 主链协作闭环能力
* 正式交接与物化能力
* 对象分层与准入能力
* 主链文件 IO 与路径治理能力
* 在需要 rollout 时，再追加技能接入与跨 skill 闭环验证能力

这意味着对治理型 SRC，EPIC 不是从上游条目机械平移，而是强制上浮到受治理主链能力层。

## 5.4 Rollout / Adoption 决策

当前实现通过 `assess_rollout_requirement()` 判断是否需要 rollout / adoption / cross-skill E2E：

* 共享治理底座或共用运行时变化
* 现有 skill / workflow 接入迁移
* 效果成立依赖真实 producer / consumer 集成
* 需要跨 skill E2E 或 handoff / gate 闭环验证

一旦命中，不允许另起第二个 EPIC；正式策略是：

## **保持单一主 EPIC，同时在同一 EPIC 中显式冻结 `foundation` 与 `adoption_e2e` 两类下游 FEAT track。**

---

# 6. 约束分层与下游交接

## 6.1 三层约束

对于治理型 EPIC，当前实现已经冻结三层 constraint groups：

* `Epic-level constraints`
* `Authoritative inherited constraints`
* `Downstream preservation rules`

这三层的意义分别是：

* EPIC 层约束：定义本 EPIC 自己的能力边界与分解主轴
* 来源继承约束：保留上游 SRC 的 authoritative constraints，但不让它们重新定义 EPIC 主边界
* 下游保留规则：明确 epic-to-feat 必须继承哪些 ID、trace 与 acceptance semantics

因此，下游不能把 source-level object rules 错误提升为 EPIC 主语义，也不能在 FEAT 层改写 `src_root_id`、`epic_freeze_ref` 或 authoritative `source_refs`。

## 6.2 正式 handoff

`handoff-to-epic-to-feat.json` 不是附属说明，而是正式下游交接对象。它至少冻结：

* `from_skill = ll-product-src-to-epic`
* `to_skill = product.epic-to-feat`
* `epic_freeze_ref`
* `src_root_id`
* `required_context`
* `required_feat_tracks`
* `prerequisite_foundations`

因此，下游 `epic-to-feat` 应消费的是 formal handoff object，而不是仅凭阅读 EPIC 正文自行理解下一步。

---

# 7. Freeze Gate 与证据规则

当前实现的 freeze gate 由 `epic-freeze-gate.json` 表达，并要求至少满足：

* `execution_evidence_present = true`
* `supervision_evidence_present = true`
* `epic_freeze_ref_presence = true`
* `downstream_handoff_presence = true`
* `adr025_acceptance_complete = true`
* `multi_feat_boundary_preserved = true`
* 当 rollout 必需时，`rollout_plan_present_when_required = true`

同时，package readiness 还要求输出结构校验通过，包括：

* Markdown 必备章节齐全
* `epic-freeze.json`、`handoff-to-epic-to-feat.json`、`epic-freeze-gate.json` 字段一致
* 来源引用必须至少含 `product.raw-to-src::<run_id>` 与 `SRC-*`
* 对治理型 EPIC，constraint groups、decomposition rules、success metrics 必须满足额外约束

这说明在 LL 中，“可以 freeze”不是一句自然语言判断，而是正式 gate object 的结果。

---

# 8. 不允许的退化

以下实现视为违反本 ADR：

1. 直接接收 raw requirement、ADR 文稿或未冻结 SRC，而不是正式 `src_candidate_package`。
2. 只手写 `epic-freeze.md/json`，跳过 execution evidence、supervision evidence、gate artifact 或 CLI commit。
3. 让 executor 自行完成最终 semantic pass 或 self-approve。
4. 发现输入更像单一 FEAT，却仍强行冻结为 EPIC。
5. 将 rollout / adoption / E2E 另起并列第二 EPIC，而不是作为同一主 EPIC 的强制下游拆分要求。
6. 在 EPIC 中直接加入 FEAT/TASK/UI/实现级内容，破坏 `product.epic-to-feat` 的下游边界。
7. 改写或丢失 `src_root_id`、`source_refs`、`epic_freeze_ref`、acceptance artifacts。
8. 对 ADR-005 已提供的 Gateway / Path Policy / Registry 前置能力重新实现一套等价模块，而不是作为前置基础消费。

---

# 9. 对仓库实现的直接影响

本 ADR 对当前仓库的直接含义是：

* `skills/ll-product-src-to-epic/` 下的 contract、runtime、derivation、CLI integration 已构成正式实现基线；
* 后续修改 `src-to-epic` 时，必须同时维护输入准入、双角色监督、formal handoff、evidence 与 gate 的一致性；
* 测试应优先围绕 package 结构、派生规则、gate readiness 和真实 artifacts 断言，而不是只测文本生成结果；
* 若未来要把 `src-to-epic` 改为不同的状态机、不同的对象边界或不同的 rollout 语义，应新增 ADR，而不能在脚本中静默漂移。

---

# 10. 结论

`ll-product-src-to-epic` 在 LL v0.x 中已经不是一个“从 SRC 写到 EPIC”的普通写作 skill，而是一条正式冻结为：

## **`freeze_ready src_candidate_package -> executor materialization -> supervisor review -> epic_freeze_package -> freeze gate -> handoff to product.epic-to-feat`**

的 governed workflow。

这份 ADR 的作用，不是发明一套新方案，而是把仓库里已经存在且可执行的 `src-to-epic` 实现，正式提升为 SSOT 级决策。
