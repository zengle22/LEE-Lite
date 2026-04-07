# ADR-043：当前 Governed Skill 输出采用语义覆盖合同、双轨评审视图与可执行 Completeness Gate 基线

* 状态：Draft
* 日期：2026-04-07
* 决策者：Le Zeng
* 适用范围：`ll-product-epic-to-feat`、`ll-dev-feat-to-tech`、`ll-dev-feat-to-proto`、`ll-dev-proto-to-ui`、对应 `feat_freeze_package` / `tech_design_package` / `prototype_package` / `ui_spec_package`、各 skill 的 `output/schema.json` / `output/semantic-checklist.md` / `*-review-report.json` / `*-completeness-report.json` / `ui-semantic-source-ledger.json` / runtime validators / freeze gates
* 相关 ADR：ADR-011、ADR-015、ADR-021、ADR-033、ADR-036、ADR-039、ADR-040、ADR-041、ADR-042

---

# 1. 背景

当前仓库已经不是“没有结构”的阶段。

围绕主链与下游 design / implementation 派生，系统已经具备一组明确的治理基础：

* ADR-015 已经明确 `Machine SSOT + Human Review Projection` 的双层表达模型；
* ADR-039 已经把 review contract、coverage gate、review projection 当成正式治理对象；
* ADR-040 / ADR-041 / ADR-042 已经把 `FEAT -> PROTOTYPE -> UI`、Journey Structural Spec、UI Shell Snapshot、Surface Map owner binding 等边界逐步冻结下来；
* 当前 skill 实现本身也已经引入了很多正确方向的对象：
  * `ll-product-epic-to-feat` 已有 `output/schema.json`、`output/semantic-checklist.md`、`integration-context.json`、`handoff-to-feat-downstreams.json`；
  * `ll-dev-feat-to-tech` 已有 `need_assessment`、`design_consistency_check`、`integration_context`、`surface_map_ref`、`owner_binding_status`；
  * `ll-dev-feat-to-proto` 已有 `journey-ux-ascii.md`、`ui-shell-spec.md`、reachability / smoke / placeholder lint / review / freeze gate；
  * `ll-dev-proto-to-ui` 已有 `ui-semantic-source-ledger.json`、`document-test-report.json`、review / completeness / freeze gate。

也就是说，当前问题已经不再是“有没有结构化输出”，而是：

## **结构已经存在，但语义密度、评审抓手与可执行 completeness 仍然没有被统一冻结。**

最近这批 skill 产物已经暴露出几个典型现象：

* `epic-to-feat` 虽然已经输出 `identity_and_scenario`、`business_flow`、`acceptance_and_testability` 等块，但 derivation 里仍然保留了 `Primary product actor`、`secondary product actor` 这类 generic fallback；
* `feat-to-tech` 虽然已经有 `state_machine`、`integration_points`、`technical_glossary_and_canonical_ownership` 等结构，但 schema 和 validator 仍主要验证“字段/section 是否存在”，没有把“是否足够具体、是否还是占位、是否已和当前 FEAT 对齐”变成硬门禁；
* 实际生成样本里已经出现：
  * actor / role 被占位词通过；
  * glossary 行内容为 `None` 或 generic owner；
  * `Exception and Compensation` / `Integration Points` 被复用为跨 FEAT 的通用叙述，而不是当前 FEAT 的专属失败路径和集成边界；
* `prototype` / `ui` 已经强制了 `journey`、`shell`、`ledger`、`reachability`，但对交互状态、异常路径、反馈语义、信息层级这些真正决定 UI / UX 是否“冻结到位”的内容，仍缺少统一的 semantic completeness contract。

因此，当前系统的真实阶段已经变成：

## **SSOT 不是缺骨架，而是缺“这一层必须说完整什么”的正式定义。**

---

# 2. 问题陈述

本 ADR 要解决的不是“让 AI 写得更长”，而是以下四类结构性问题。

## 2.1 结构通过不等于语义冻结

当前很多 validator 主要在检查：

* 文件是否存在；
* section / heading 是否存在；
* 数组是否非空；
* ref 是否齐全；
* owner / surface_map / journey / shell 是否被带上。

这些检查是必要的，但不够。

它们只能证明：

* 输出没有缺块；
* 主链没有断；
* 人类 review 至少有材料可看。

它们不能证明：

* actor 是否真实；
* business rule 是否明确；
* exception path 是否与当前 FEAT 相关；
* TECH 的 state machine 是否真的是实现语义，而不是 generic lifecycle；
* UI 的状态、反馈和异常行为是否被显式冻结；
* 下游是否还能被迫二次推断。

## 2.2 `semantic-checklist.md` 现在更多还是“人类提示”，还不是“机器合同”

当前每个 skill 已经开始带 `output/semantic-checklist.md`。

这是正确的方向，但现在它的角色仍偏向：

* 提醒作者；
* 提醒 reviewer；
* 解释应该关注什么。

它还没有变成：

* machine-readable 的维度清单；
* validator 可执行的 completeness contract；
* freeze gate 的正式输入。

结果就是：

## **系统知道“应该更完整”，但还不知道“什么情况下必须判定不完整”。**

## 2.3 当前输出主要仍是单通道 SSOT，不是稳定的双轨表达

虽然 ADR-015 已经确立双层表达模型，但当前很多 bundle markdown 仍更像：

* 结构化 JSON 的 prose 包装；
* 给 AI 和 reviewer 共用的一份混合稿；
* 能读，但不是专门为 review 设计的 narrative / checklist / anchor view。

这会带来两个直接问题：

* 人类 reviewer 仍然需要自己从 bundle 中提炼关键判断点；
* 机器也没有得到一份明确的“已覆盖维度 -> 证据 -> review question”的投影。

## 2.4 下游 skill 仍然经常在补推断，而不是消费冻结语义

当前主链已经开始通过 `integration_context`、`surface_map`、`journey`、`ui-shell`、`semantic_source_ledger` 等对象减少推断。

但只要上游 package 仍允许“generic placeholder + section existence”通过，就会出现以下退化：

* `TECH` 需要补推 actor、规则、边界；
* `PROTOTYPE` 需要补推异常路径和状态语义；
* `UI` 需要补推 field semantics、feedback intent、信息层级；
* `IMPL` 和 `TESTSET` 最后会承担本该在 FEAT / TECH / UI 层冻结的语义债务。

这违反了现有主链已经建立的一个基本原则：

## **下游只能深化语义，不能补发明上游语义。**

---

# 3. 决策

## 3.1 决策摘要

从本 ADR 生效起，当前仓库内已实现的 governed skill 输出正式采用以下统一模型：

## **Skill Output = Structural Contract × Semantic Dimension Profile × Human Review Projection × Executable Completeness Gate**

也就是说：

1. `schema.json` 继续负责结构与类型；
2. 新增或补齐 machine-readable 的 `semantic dimension profile`，定义“这一层必须覆盖哪些语义面”；
3. 现有 markdown bundle / review report / completeness report 必须从这些维度中投影出明确 review anchors；
4. freeze gate 必须同时要求：
   * `structural_pass = true`
   * `semantic_pass = true`

任何只满足第一项、不满足第二项的产物，都不得再被视为“freeze-ready”。

## 3.2 Phase 1 先覆盖已落地链路

本 ADR Phase 1 只强制覆盖当前仓库已经实现、并且已有 validator / gate 的四类 skill：

* `ll-product-epic-to-feat`
* `ll-dev-feat-to-tech`
* `ll-dev-feat-to-proto`
* `ll-dev-proto-to-ui`

也即：

* `feat_freeze_package`
* `tech_design_package`
* `prototype_package`
* `ui_spec_package`

Phase 2 再向上游与下游扩展到：

* `raw-to-src`
* `src-to-epic`
* future `arch` / `api`
* `impl_candidate_package`
* `testset_candidate_package`

## 3.3 结构合同与语义合同正式分离

每个 governed skill 的输出层，从本 ADR 起必须同时存在两类正式合同：

### A. Structural Contract

继续由现有：

* `output/contract.yaml`
* `output/schema.json`

负责，关注：

* artifact type
* required refs
* required sections
* required files
* owner binding
* lineage
* handoff shape

### B. Semantic Dimension Profile

新增或补齐 machine-readable 的语义维度定义文件，推荐统一放在：

* `output/semantic-dimensions.json`

从本 ADR 起，这里采用严格单一来源：

## **`semantic-dimensions.json` 是唯一 SSOT。**

`output/semantic-checklist.md` 与各类 report 不再允许手写维护，而必须由 `semantic-dimensions.json` 投影生成。

也就是说：

* `semantic-dimensions.json`：唯一语义合同；
* `semantic-checklist.md`：自动生成的人类速查视图；
* `semantic-coverage` / `review-report`：自动生成的执行结果视图；
* runtime validator、completeness report、review gate 都必须消费同一份 `semantic-dimensions.json`。

### `semantic-dimensions.json` 最小格式

```json
{
  "artifact_type": "feat_freeze_package",
  "schema_version": "1.0.0",
  "core_dimensions": [
    {
      "id": "actor_model",
      "required": true,
      "min_evidence_count": 1,
      "disallow_placeholders": true,
      "review_question": "是否能明确知道谁触发、谁消费、谁承担完成态？"
    }
  ],
  "auxiliary_dimensions": [
    {
      "id": "timeline_detail",
      "required": false
    }
  ]
}
```

## 3.4 当前四类 package 的强制语义维度

### 3.4.1 `feat_freeze_package`

`FEAT` 不再只要求“有 Identity / Flow / Acceptance 块”，但也不采用无限扩张的细粒度清单。

本 ADR 明确：

## **每层 freeze gate 只允许 5-7 个 core dimensions 进入硬门禁。**

其余内容如需保留，只能作为 `auxiliary_dimensions`，用于 authoring 提示或 reviewer 参考，不得进入 Phase 1 freeze gate。

`FEAT` 的核心维度固定为：

```yaml
feat_core_dimensions:
  - actor_and_intent
  - flow_and_journey
  - rules_and_constraints
  - inputs_outputs_and_authority
  - edge_cases_and_boundary
  - acceptance_and_testability
```

其中：

* `actor_and_intent` 不允许再用 `Primary product actor`、`secondary product actor` 之类占位语；
* `flow_and_journey` 负责主流程与关键分支，不要求把时间线、协作细节拆成单独 gate 维度；
* `rules_and_constraints` 负责业务规则、不可替代路径和禁止下游改写的约束；
* `inputs_outputs_and_authority` 负责输入对象、输出对象、authoritative artifact 与 design impact signal；
* `edge_cases_and_boundary` 负责异常路径、非责任边界、adjacent capability boundary；
* `acceptance_and_testability` 负责 acceptance checks 与 test dimensions。

以下内容允许保留为 `auxiliary_dimensions`，但 Phase 1 不进 gate：

* timeline detail
* collaboration detail
* rollout hints
* candidate design surfaces explanation prose

### 3.4.2 `tech_design_package`

`TECH` 也采用少量核心维度，而不是把所有 section 都提升成同等强度的 gate：

```yaml
tech_core_dimensions:
  - carrier_and_module_responsibility
  - contracts_and_field_semantics
  - state_and_runtime_flow
  - failure_and_compensation
  - integration_and_compatibility
  - ownership_and_constraints
```

本 ADR 进一步明确：

* `state_and_runtime_flow` 负责 `state_machine`、`main_sequence`、`io_matrix` 这组实现闭环；
* `ownership_and_constraints` 负责 glossary / canonical ownership / algorithm constraints；
* `State Machine` 不能用 generic `prepared -> executing -> recorded` 之类跨 FEAT 复用的生命周期敷衍；
* `Technical Glossary and Canonical Ownership` 不允许输出 `None`、空 owner 或纯 bundle-generic owner；
* `Exception and Compensation` 必须对应当前 FEAT 的真实失败路径，不得复用与当前 FEAT 无关的历史 handoff/runtime 异常段落；
* `Integration Points` 必须明确当前 FEAT 接到哪个现有模块、命令、文件、契约或运行时对象。

以下内容允许先保留为 `auxiliary_dimensions`：

* observability / NFR detail
* migration detail
* optional ARCH/API summary quality
* extended pseudocode richness

### 3.4.3 `prototype_package`

`PROTOTYPE` 当前已经在结构上补强了 `journey-ux-ascii.md`、`ui-shell-spec.md`、route / smoke / lint。

从本 ADR 起，还必须把这些结构对象升级成明确的体验语义覆盖：

```yaml
prototype_core_dimensions:
  - journey_and_surface_slice
  - entry_exit_and_initial_view
  - cta_and_container_semantics
  - primary_states_and_feedback
  - exception_retry_skip_paths
  - shell_alignment_and_owner_binding
```

也就是说，`prototype` gate 不能只证明：

* 页面可点击；
* route 可达；
* placeholder 不存在；
* journey 文件存在。

还必须证明：

* 初始视图与入口条件明确；
* 至少一条 happy path、至少一条异常/降级 path 已被表达；
* CTA 层级、容器类型、关键反馈已冻结；
* 当前 prototype 更新的是哪个 shared prototype owner、它不打算解决什么。

以下内容允许作为 `auxiliary_dimensions`：

* visual polish
* non-goals prose
* expanded review guide copy

### 3.4.4 `ui_spec_package`

`UI` 当前已经有 `ui-semantic-source-ledger.json`，这是非常正确的基础。

从本 ADR 起，`UI` 还必须强制覆盖以下实现前交互语义：

```yaml
ui_core_dimensions:
  - page_goal_and_task_flow
  - information_hierarchy_and_regions
  - field_action_validation_and_feedback
  - state_behaviors
  - component_container_contracts
  - source_ledger_and_inference_disclosure
```

本 ADR 要求：

* `ui-semantic-source-ledger.json` 不只是“来源分类账”，还要成为 semantic coverage 的证据来源；
* `page goal`、`main path`、`branch path`、`state behavior` 不能只留在 markdown prose 里，必须能在 coverage report 中被机器定位；
* 所有 AI 推断都必须继续显式标记，不能因为“有 UI spec”就被默认为事实；
* `UI` 是 implementation-facing 契约，而不是 prototype narrative 的复述。

以下内容允许作为 `auxiliary_dimensions`：

* accessibility detail
* content guideline detail
* extended component catalog prose

## 3.5 validator 采用分层策略，不试图用 rule engine 解决全部语义问题

本 ADR 明确反对把 semantic validator 做成“全能 NLP 判断器”。

Phase 1 必须采用三层策略：

### Level 1：硬规则

用于 machine gate，必须稳定、可解释、可维护。

典型包括：

* 缺字段
* 空数组
* 缺文件
* `None`
* `TBD`
* placeholder keyword
* ref 缺失
* surface_map / owner / journey / shell / ledger 缺失

### Level 2：弱规则

用于 machine heuristic，不直接替代人审。

典型包括：

* 内容长度过短
* 没有动作词 / 对象词
* 当前 section 与 selected FEAT title/topic 的词族重合度过低
* 证据定位不到 source ref
* 需要至少一个异常路径但当前为 0

### Level 3：AI review

用于语义质量判断，不应被伪装成 deterministic rule。

典型包括：

* 是否具体
* 是否合理
* 是否真的是这一层独占语义
* 是否虽然“看起来完整”，但其实仍然空壳

因此，本 ADR 的原则是：

## **不要试图用 rule engine 解决全部 semantic quality；machine validator 负责挡低级错误和明显空壳，剩余质量判断交给 review 层。**

## 3.6 语义 completeness 采用显式状态制

从本 ADR 起，每个 required semantic dimension 必须输出显式 coverage 状态。

推荐状态集合如下：

```yaml
semantic_dimension_status:
  - explicit
  - partial
  - missing
  - placeholder
  - conflict
```

判断规则：

* `explicit`: 有明确语义、可定位 evidence、与当前 artifact 对齐；
* `partial`: 有内容，但缺边界、缺异常、缺输入输出、缺 owner、缺 source trace 中至少一项；
* `missing`: 对应维度不存在；
* `placeholder`: 有字段，但内容是 generic fallback、模板句、`None`、`TBD`、占位 actor、无关复制文本；
* `conflict`: 当前维度与 upstream truth、surface_map owner、journey/source ledger 或当前 selected FEAT 冲突。

### semantic gate 判定

默认规则固定为：

## **只要存在 required dimension 的 `missing` / `placeholder` / `conflict`，语义 gate 必须失败。**

`partial` 在 Phase 1 可以进入 `revised`，不得进入 `accepted` / `frozen`。

## 3.7 现有 report/gate 文件统一升级为语义证据承载层

为了减少当前实现改造成本，Phase 1 不强制引入新的 artifact 命名。

可以直接复用现有：

* `feat-review-report.json`
* `tech-review-report.json`
* `prototype-completeness-report.json`
* `ui-spec-completeness-report.json`
* `document-test-report.json`
* `ui-semantic-source-ledger.json`

但这些 artifact 必须新增统一字段：

```json
{
  "semantic_coverage": {
    "dimensions": [
      {
        "id": "actor_model",
        "status": "explicit",
        "evidence_refs": ["feat-freeze-bundle.json#/features/0/identity_and_scenario/primary_actor"],
        "review_anchor": "能否明确判断谁触发、谁交付、谁消费完成态？"
      }
    ],
    "semantic_passed": true
  }
}
```

Phase 2 如需统一命名，可再收敛为：

* `semantic-coverage-report.json`

但本 ADR 的关键不是文件名，而是：

## **semantic completeness 必须进入现有 freeze gate 的正式判定。**

同时，生成关系固定为：

```text
semantic-dimensions.json
  -> semantic-checklist.md
  -> semantic coverage in review/completeness reports
  -> freeze gate semantic_pass
```

不允许手写 checklist 再反向“同步”到 dimensions 或 report。

## 3.8 review 体验采用三种固定视图

从本 ADR 起：

* `feat-freeze-bundle.md`
* `tech-design-bundle.md`
* `prototype-bundle.md`
* `ui-spec-bundle.md`

它们不再只被统称为“Human Review Projection”，而是要明确拆成三种 review view：

### A. Narrative View

讲人话，帮助 reviewer 快速理解当前层冻结了什么。

### B. Checklist View

按 core dimensions 逐条回答：

* 是否覆盖；
* 证据在哪；
* 当前状态是 `explicit / partial / missing / placeholder / conflict`。

### C. Diff View

用于回答“这次比上游或上版新增了什么、改写了什么、保持了什么”。

至少要支持：

* 与上游 authoritative input 的语义增量差异；
* 与同 owner 上一版 artifact 的变更差异。

只有这样，review 才不是“读一大篇 prose”，而是能快速判断：

* 当前层说了什么；
* 说得够不够；
* 这次究竟新增了什么。

## 3.9 每一层必须新增信息，不允许只做语义改写

从本 ADR 起，当前已落地链路正式采用以下新增信息责任：

* `FEAT`：新增产品意图、actor、journey、规则、authoritative output、边界；
* `TECH`：新增实现机制、状态机、接口语义、失败路径、集成点、可观测性；
* `PROTOTYPE`：新增可体验的主流程/状态/反馈/容器语义；
* `UI`：新增 implementation-facing 页面目标、信息层级、字段/动作/状态/组件/可访问性契约。

本 ADR 补充一个硬约束：

## **每一层必须新增上游尚未冻结的语义；任何仅为改写、重述或同义转写的内容，应判为 semantic failure。**

## 3.10 下游 handoff 必须显式携带语义 readiness

现有 handoff 继续保留，但从本 ADR 起必须明确区分：

* `structural_ready`
* `semantic_ready`
* `open_semantic_gaps`

没有 `semantic_ready = true` 的 package，不得被下游当成 authoritative input 使用。

---

# 4. 硬规则

## Rule 1：结构完整不等于语义完整

有 section、有数组、有 ref，不代表该层已经 freeze-ready。

## Rule 2：占位词、generic fallback、`None`、无关复用文本一律不得记为已覆盖

以下内容必须直接判定为 `placeholder` 或 `conflict`：

* `Primary product actor`
* `secondary product actor`
* `None`
* `TBD`
* 与当前 FEAT topic 不一致的复用异常段落
* 与当前 layer 无关的通用 lifecycle prose

## Rule 3：每层必须覆盖本层独占语义面

`FEAT`、`TECH`、`PROTOTYPE`、`UI` 不得只做同义改写。

## Rule 4：`semantic-checklist.md` 不再是唯一语义标准

它必须由 `semantic-dimensions.json` 自动生成，不允许手写维护。

## Rule 5：validator 必须采用 L1/L2/L3 分层策略

不要试图用 rule engine 一次性解决全部 semantic quality。

## Rule 6：review 必须同时提供 Narrative / Checklist / Diff 三种视图

否则即使语义更完整，人类评审体验仍然低效。

## Rule 7：downstream 不得补推断 upstream required semantics

如果某 required semantic dimension 缺失，必须回到上游修复，而不是由下游补写。

## Rule 8：freeze gate 只有在 structural 和 semantic 同时通过时才允许 `accepted` / `frozen`

任何 `partial` / `placeholder` / `conflict` 都必须阻止进入最终冻结状态。

---

# 5. 对现有 skill 的直接影响

## 5.1 对 `ll-product-epic-to-feat`

需要做的不是再加 section，而是：

* 把 `identity_and_scenario`、`business_flow`、`acceptance_and_testability` 等现有块，升级成 machine-checkable semantic dimensions；
* 把 generic actor / timeline / handoff fallback 纳入 placeholder detector；
* 把 `design_impact_required`、`candidate_design_surfaces`、`surface_map_required_reason` 纳入 semantic coverage，而不是只做 downstream routing hint；
* 让 `handoff-to-feat-downstreams.json` 显式携带 semantic readiness 和 gap 摘要。

## 5.2 对 `ll-dev-feat-to-tech`

重点不是增加更多字段，而是把当前已有字段“验深”：

* `state_machine` 必须是当前 FEAT 的状态语义，而不是 generic lifecycle；
* `technical_glossary_and_canonical_ownership` 必须是真正可执行的 canonical ownership；
* `exception_and_compensation` 与 `integration_points` 必须被 topic-aligned 检查；
* `need_assessment`、`integration_context_sufficiency`、`design_consistency_check` 必须成为 semantic gate 的输入，而不是 bundle 内部说明。

## 5.3 对 `ll-dev-feat-to-proto`

当前已经有很好的结构治理基础，Phase 1 重点是把：

* journey
* shell
* route reachability
* placeholder lint
* review decision

统一提升为“体验语义 coverage”。

也就是说，prototype 不能只证明“能点通”，还要证明：

* 状态是否完整；
* 异常/降级/retry 是否表达；
* CTA 与容器是否有明确语义；
* 当前 prototype 更新 shared owner 的 scope 是什么。

## 5.4 对 `ll-dev-proto-to-ui`

当前最大的优势是已经有 `ui-semantic-source-ledger.json`。

Phase 1 重点是：

* 把 ledger 变成 semantic completeness 的正式证据；
* 把 `page goal / state / validation / feedback / accessibility` 纳入 required dimensions；
* 禁止 UI spec 只保留 proto narrative，而不冻结 implementation-facing 契约。

---

# 6. 实施建议

## Phase 1：最小可落地治理

1. 为四个已落地 skill 新增 `output/semantic-dimensions.json`。
2. 更新 runtime validator，让其在 structural validation 之后执行 semantic coverage validation。
3. 复用现有 `*-review-report.json`、`*-completeness-report.json` 承载 `semantic_coverage`。
4. 增加 placeholder/generic drift detector，先抓最明显的 sentinel：
   * `Primary product actor`
   * `secondary product actor`
   * `None`
   * `TBD`
   * 与当前 selected FEAT topic 不一致的复用段落
5. handoff 增加 `semantic_ready` 与 `open_semantic_gaps`。

## Phase 2：统一双轨评审视图

1. 让 bundle markdown 的 section 顺序与 semantic dimensions 一一对应。
2. 让 review report 自动输出 reviewer question，而不是只输出 pass/fail。
3. 让 completeness report 能直接回答“缺的是哪一类语义”。

## Phase 3：向主链上下游推广

1. 把同样模型扩展到 `raw-to-src`、`src-to-epic`。
2. 对 future `arch` / `api` 派生采用同一套 semantic dimension registry。
3. 在 `impl-spec-test`、`document-test`、future `validate skill` 中统一消费 semantic coverage，而不是各自重新发明完整性标准。

---

# 7. 收益、代价与风险

## 7.1 预期收益

* AI 输出不再靠“把结构填满”就过关；
* human review 不再主要依赖主观感觉，而是基于维度与锚点检查；
* downstream skill 不再承担上游语义补完；
* `surface_map`、`journey`、`ui-shell`、`semantic_source_ledger` 这些已有机制会被真正纳入 completeness contract，而不是只作为附属文件存在；
* FEAT / TECH / PROTOTYPE / UI 之间的信息递增关系会更稳定。

## 7.2 代价

* 每个 skill 需要维护一份 machine-readable 的 semantic dimension profile；
* validator 与 report 需要补语义覆盖逻辑；
* 部分存量输出样本会因为 placeholder / generic reuse 被判为不合格。

## 7.3 风险

* 如果 semantic dimensions 设计得过粗，仍然挡不住“空壳但看似完整”的输出；
* 如果 semantic dimensions 设计得过细，作者负担会陡增，反而诱发形式主义填表；
* 如果 human projection 不跟着 dimensions 走，review 仍然会退回“读一堆 prose”的老路。

因此本 ADR 的关键不是“多几份文件”，而是：

## **把结构、语义、评审与 gate 真正收敛成同一套合同。**

---

# 8. 最终决议

从本 ADR 生效起：

1. **当前 governed skill 输出正式采用 `Structural Contract × Semantic Dimension Profile × Human Review Projection × Executable Completeness Gate` 模型。**
2. **`semantic-checklist.md` 保留为人类视图，但不再作为唯一 semantic contract；machine-readable `semantic-dimensions` 必须成为 validator 与 freeze gate 的正式输入。**
3. **`feat_freeze_package`、`tech_design_package`、`prototype_package`、`ui_spec_package` 都必须输出显式 semantic coverage 状态。**
4. **任何 required semantic dimension 的 `missing` / `placeholder` / `conflict` 都必须阻止 package 进入 `accepted` / `frozen`。**
5. **bundle markdown 从“结构化 prose”升级为 Human Review Projection；handoff 从“结构 ready”升级为“结构 ready + 语义 ready”。**

一句话总结：

> **当前系统缺的不是更多 section，而是每一层“必须说完整什么”的正式合同。**
> **ADR-043 的目标，就是把现有 skill 已经拥有的 schema、semantic checklist、report、ledger、gate 这些散点机制，统一收敛成可执行的语义覆盖体系。**
