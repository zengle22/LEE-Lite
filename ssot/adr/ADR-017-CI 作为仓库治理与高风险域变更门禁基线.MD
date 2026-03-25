# ADR-017：CI 作为仓库治理与高风险域变更门禁基线

* 状态：Draft
* 日期：2026-03-25
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x 仓库级持续集成、PR 门禁、变更分层校验
* 相关 ADR：ADR-004、ADR-005、ADR-008、ADR-009、ADR-015、ADR-016

---

# 1. 背景

当前仓库已经逐步形成五层稳定结构：

* `spec/` 承载规则、契约与 schema；
* `skills/` 承载 governed skill 定义与脚本；
* `cli/` 承载 CLI-first file runtime；
* `artifacts/` 承载评审输出、evidence 与 lineage；
* `docs/` 承载面向人的长期说明。

## 1.1 Canonical Repo Topology

为避免 CI 自己演化成第二套目录真相，先冻结仓库路径语义。

### 正式路径名

* `ssot/`：正式真相层，承载 `ADR`、`SRC`、`EPIC`、`FEAT`、`TECH`、`IMPL`、`TESTSET` 等对象实例与正式治理输入。
* `spec/`：正式标准层，承载可复用 contract、schema、governance rule、skill standard、artifact standard 等“规则本身”。
* `skills/`：正式 skill bundle 层，承载 governed workflow 的 contract、lifecycle、schema、prompt、脚本与 adapter 配置。
* `cli/`：正式 runtime interface 层，承载 CLI parser、command surface、runtime helper 与 protocol 实现。
* `tests/`：正式验证层，承载 CI 可调用的测试、fixture、golden 与回归样例。

### 历史兼容路径名

* `docs/adr/` 可作为历史说明入口被引用，但不再作为正式 ADR 真相层；当前正式 ADR 以 `ssot/adr/` 为准。
* `.local/raw-to-src-inputs/`、`.workflow/`、其他本地试验目录可保留历史材料或过程态输入，但不属于 merge 时的正式真相层。

### `spec/` 与 `ssot/` 的关系

* `ssot/` 不是 `spec/` 的子集，也不是 `spec/` 的别名。
* `ssot/` 表达“被治理的正式对象实例与正式决策”。
* `spec/` 表达“约束这些对象与运行时的复用标准、schema、contract 与规则”。
* CI 在“真相层路径”上以 `ssot/` 为准；CI 在“标准依赖路径”上同时消费 `spec/`。
* 因此，`ssot-governance` 的 canonical target 是 `ssot/`，而 `spec/**` 的变更应通过依赖映射触发 `skill-governance`、`cli-governance` 或 `cross-domain-compat`，而不是把 `spec/` 混写成另一个 SSOT 目录。

### 哪些路径参与治理，哪些只是说明或投影

* 直接参与治理：`ssot/`、`spec/`、`skills/`、`cli/`、`tests/`
* 运行期输出与证据：`artifacts/`
* 说明、导读、投影视图：`docs/`、`examples/`
* 本地过程态或临时态：`.local/`、`.workflow/`、缓存目录、运行期 scratch

后续 validator 必须遵守这组路径语义，不能自行发明“另一套正式目录解释”。

其中，真正会持续影响主链稳定性的高风险域，当前集中在三块：

* `ssot/`：定义对象模型、ADR、对象命名、继承边界与正式真相；
* `skills/`：定义 workflow contract、lifecycle、schema、prompt、脚本与 evidence 约束；
* `cli/`：定义主链 runtime command surface、请求响应边界、校验器与治理 helper。

如果这三块缺少 CI 约束，仓库会持续出现三类典型漂移：

* `SSOT` 文件命名、对象类型、引用关系、历史兼容边界逐步失真；
* `SKILL.md`、`ll.contract.yaml`、`ll.lifecycle.yaml`、`schema.json`、脚本入口之间发生静默不一致；
* `cli/ll.py` 暴露的命令面、`cli/lib/` 实际运行时行为、`tests/` 中假设的调用方式彼此脱节。

另一方面，如果一上来把 CI 设计成“所有内容全量重跑”的重型流水线，也会迅速失去实用性：

* PR 反馈过慢；
* 路径不相关改动也被高成本 job 阻塞；
* 本应做 nightly 的全链回归侵入日常开发；
* 历史噪音与临时工件让门禁失去可信度。

因此，需要冻结一份正式 ADR，定义：

## **LL 仓库的 CI 应采用治理优先、路径感知、分层门禁的方案，并重点管控 `ssot`、`skills`、`cli` 三个高风险域。**

---

# 2. 问题陈述

LL 当前需要解决的，不是“要不要上 GitHub Actions”这样的平台问题，而是下面几个更本质的问题。

## 2.1 什么应该成为 merge blocker

并不是所有检查都适合做 PR 必过门禁。

如果把全量 integration、E2E、pilot chain、历史工件对比全部放进 PR 阶段：

* 反馈速度会过慢；
* 临时不稳定项会污染主线；
* 开发者会倾向于规避 CI，而不是信任 CI。

因此必须先冻结：哪些检查是 `required`，哪些只适合 `nightly`、`manual` 或 `post-merge`。

## 2.2 为什么必须按域治理，而不是只跑通用单测

只跑 `pytest` 并不能覆盖这三个核心风险：

* `ssot/` 的风险主要是对象治理与引用边界漂移，不只是 Python 行为错误；
* `skills/` 的风险主要是结构完备性、契约一致性、路径引用有效性，不只是脚本 import 是否成功；
* `cli/` 的风险主要是 command surface、请求响应协议、skill/contract 兼容性，不只是函数级单元测试。

因此必须把 CI 明确设计成：

## **通用测试 + 域专属治理校验**

而不是二选一。

## 2.3 为什么 `ssot`、`skills`、`cli` 需要更高等级的人机双重门禁

这三块的改动不是普通实现细节，它们分别对应：

* 正式真相；
* 受治理 skill 契约；
* 主链运行时接口。

一旦这些边界被错误修改，损害是跨目录扩散的。

因此，这三块不仅需要自动化校验，还需要 `CODEOWNERS + required review + required status checks` 的联合门禁。

## 2.4 为什么 CI 不能被做成新的“第二真相源”

CI 应验证正式对象与正式代码，而不是再发明一套平行规则文件。

因此：

* `ssot/` 的规则必须继承 ADR 与正式 schema；
* `skills/` 的规则必须继承 skill bundle 的正式 contract/lifecycle/schema；
* `cli/` 的规则必须继承 CLI parser、runtime protocol 与测试契约；
* CI 自身只能表达“如何验证”，不能重写“什么是真相”。

---

# 3. 决策

LL v0.x 正式采用以下 CI 基线：

## **一套治理优先、路径感知、分层门禁的 CI 方案。**

其核心原则如下：

1. PR 阶段只阻塞快速、确定性强、与改动直接相关的检查。
2. `ssot`、`skills`、`cli` 三个高风险域采用专项校验 job，而不是并入一个模糊的“lint/test”。
3. `spec/` 作为正式标准依赖层，不单独宣称真相层，但其变更必须通过依赖映射触发下游治理校验。
4. 跨域改动或单域高影响改动都必须触发兼容性检查，防止 `SSOT -> skill -> CLI` 链路断裂。
5. 更重的全量回归、端到端链路、golden drift 与 pilot 验证优先放在 nightly 或 manual dispatch。
6. CI 结果必须输出清晰、可定位、可审计的失败原因，不能只给出笼统红灯。
7. `CODEOWNERS` 必须覆盖三大高风险域的关键文件。
8. 当前默认运行时以仓库现实为准，先固定 Python `3.13`，不在 v0 首轮引入多版本矩阵。

一句话总结：

> **LL 的 CI 不是普通代码测试流水线，而是仓库治理边界的自动化门禁。**

---

# 4. 总体结构

CI 分为三层。

## 4.1 第一层：PR Required Checks

这是所有进入主分支前必须通过的最小可信门禁。

目标：

* 快；
* 稳；
* 对改动敏感；
* 能直接阻断高风险漂移。

## 4.2 第二层：Main Branch Full Validation

这是合并到主分支后的全量校验层。

目标：

* 验证整体仓库仍可作为一个整体工作；
* 补跑 PR 阶段未必适合阻塞的较重测试；
* 为夜间回归提供稳定基线。

## 4.3 第三层：Nightly / Manual Governance Regression

这是较重、较全、允许逐步建设的回归层。

目标：

* 跑全链 workflow；
* 检查 golden drift；
* 检查历史样例与主链兼容性；
* 为发布或大范围重构提供前置可信度。

---

# 5. PR 必过门禁

## 5.0 Required Check Contract 模板

所有 required check 都必须按统一契约定义，至少冻结以下字段：

* `Input`：读取哪些正式对象、路径或版本化 manifest。
* `Assertion`：什么条件成立才算通过，必须避免“明显冲突”这类自由裁量表达。
* `Fail Mode`：失败如何分类，至少区分结构错误、引用错误、兼容错误、缺失错误、快照漂移错误。
* `Output`：产出什么机器可读报告，供 CI 汇总、PR 注释或后续回归消费。
* `Owner`：哪一类维护者负责此 validator 的规则收敛与误报治理。

如需额外字段，允许补充 `Trigger`、`Scope`、`Dependencies`，但不得省略上述五项。

## 5.1 `repo-hygiene`

所有 PR 默认触发。

* `Input`：PR changed files、仓库忽略规则、YAML/JSON 文件、Markdown 文件、受管控的临时目录清单。
* `Assertion`：
  * YAML / JSON 必须可解析。
  * Markdown 只做基础文件有效性检查，包括非空、编码正常、无明显损坏；是否增加 frontmatter / heading lint 另行冻结。
  * 新增文件不得命中禁止提交模式，如 `__pycache__/`、`*.pyc`、运行期 cache、编辑器垃圾文件。
  * `.local/`、`.workflow/`、运行期临时输出不得作为正式变更提交，除非后续 ADR 明确放行。
  * 文本文件不得为空文件或明显损坏。
* `Fail Mode`：`parse_error`、`invalid_markdown_file`、`forbidden_generated_file`、`forbidden_runtime_state_commit`、`corrupt_or_empty_file`
* `Output`：`repo-hygiene-report.json`
* `Owner`：仓库维护者 + CI 维护者

说明：对仓库中已存在的历史噪音，第一阶段采用“禁止新增”而不是“立刻清零”。

## 5.2 `unit-fast`

所有 PR 默认触发。

* `Input`：`tests/unit/`、测试选择 manifest、Python `3.13` 运行环境。
* `Assertion`：
  * 版本化定义的 fast unit 集必须全部通过。
  * 未被纳入 fast 集的测试不得被误计为通过依据。
* `Fail Mode`：`test_failure`、`test_collection_error`、`environment_bootstrap_error`
* `Output`：`unit-fast-report.json` + 原生测试报告
* `Owner`：CLI/skill/runtime 代码维护者

说明：v0 第一轮可直接运行 `python -m pytest tests/unit`；后续若拆 shard，必须通过版本化测试清单定义。

约束：`unit-fast` 的目标是保持 PR 阶段快速反馈；当 `tests/unit/` 总执行时长超出可接受阈值时，必须引入版本化 fast manifest，而不是继续无界增长。

## 5.3 `ssot-governance`

当 PR 修改 `ssot/**` 时必触发并作为 required check。

* `Input`：`ssot/**`、ADR-008 定义的 canonical object model、位于 `spec/` 下的 machine-readable object-kind registry 或等价 schema、ADR 文件最小元信息规则、对象引用解析规则。
* `Assertion`：
  * `ssot/` 下对象路径必须落在已接受的 canonical object kind 中。
  * 文件命名、对象 ID、文内主标识必须一致。
  * ADR 引用、对象上游引用、关联对象引用必须可解析。
  * 未引入正式 ADR 的前提下，不得新增 canonical object kind。
  * `ADR-*` 文件必须具备标题、状态、日期、相关 ADR 与正文主体。
* `Fail Mode`：`invalid_object_path`、`identifier_drift`、`broken_reference`、`unauthorized_object_kind`、`adr_metadata_missing`
* `Output`：`ssot-governance-report.json` + `ssot-change-summary.json`
* `Owner`：SSOT/ADR 维护者

特别约束：

* ADR-008 负责 canonical object model 的治理定义；`spec/` 下的 registry / schema 负责执行承载；CI 不得自行发明 object kind、path pattern 或最小字段规则。
* `ssot/adr/**` 变更除 CI 通过外，必须要求人工 review。
* `docs/` 中的说明性文档不作为正式 SSOT 校验入口，避免形成第二真相源。

## 5.4 `skill-governance`

当 PR 修改 `skills/**` 时必触发并作为 required check。

* `Input`：变更 skill bundle、`SKILL.md`、`ll.contract.yaml`、`ll.lifecycle.yaml`、`input/contract.yaml`、`input/schema.json`、`output/contract.yaml`、`output/schema.json`、可选 `agents/*.yaml` adapter 配置。
* `Assertion`：
  * 每个变更 skill bundle 必须具备最小 governed bundle 文件集：`SKILL.md`、`ll.contract.yaml`、`ll.lifecycle.yaml`、`input/contract.yaml`、`input/schema.json`、`output/contract.yaml`、`output/schema.json`。
  * `ll.contract.yaml`、`ll.lifecycle.yaml`、`input/output schema` 必须可解析。
  * contract 中声明的 prompt、schema、template、evidence schema、脚本入口路径必须存在。
  * 若 bundle 声明了 executor adapter，则对应 `agents/*.yaml` 必须存在且可解析；未声明时不得强制要求某个 provider 文件名。
  * runtime command 中引用的脚本必须存在，并通过 import / parser 构建级别 smoke。
  * `SKILL.md` 中声明的 workflow boundary、input/output artifact type 必须与 contract 定义一致。
* `Fail Mode`：`bundle_file_missing`、`contract_parse_error`、`broken_declared_path`、`adapter_config_missing_or_invalid`、`runtime_entry_smoke_failed`、`bundle_contract_mismatch`
* `Output`：`skill-governance-report.json`
* `Owner`：各 skill 域维护者 + skill governance 维护者

特别约束：

* executor adapter config 必须保持 provider-neutral，不得把 `agents/openai.yaml` 固化为所有 skill 的唯一必备文件。
* skill 契约层错误必须按结构不完整、引用失效、契约不一致等固定分类报错。

## 5.5 `cli-governance`

当 PR 修改 `cli/**` 时必触发并作为 required check。

* `Input`：`cli/ll.py`、`cli/commands/**`、`cli/lib/**`、CLI surface snapshot、request/response protocol tests。
* `Assertion`：
  * `cli/ll.py` parser 必须成功构建。
  * 顶层 command group、action、参数形状必须与上一版 snapshot 比较，并显式标记新增、删除、破坏性变化。
  * 受影响 CLI 模块必须通过对应单测，至少覆盖 `tests/unit/test_cli_runtime.py`、`tests/unit/test_cli_runtime_governed_flows.py`、`tests/unit/test_cli_skill_test_exec.py` 中相关集合。
  * request/response 协议字段、命令路由与 skill runtime 承载约定不得破坏既有测试契约。
* `Fail Mode`：`parser_build_failed`、`cli_surface_drift`、`protocol_contract_break`、`targeted_test_failure`
* `Output`：`cli-governance-report.json` + `cli-surface-snapshot.json` + `cli-surface-diff.json`
* `Owner`：CLI/runtime 维护者

特别约束：

* `cli/ll.py`、`cli/commands/**`、`cli/lib/**` 的接口级变更必须要求人工 review。
* `machine-readable snapshot diff` 在此明确指 `command group / action / args shape` 的版本化 JSON 快照差异。

## 5.6 `cross-domain-compat`

以下两类情况任一命中都必须触发并作为 required check：

* 目录联动触发：同一 PR 同时修改 `ssot/**`、`skills/**`、`cli/**` 中任意两域或三域。
* 影响面触发：即使只修改一域，但该变更命中了正式依赖链上的驱动文件，也必须触发最小兼容 smoke。

影响面判定必须来自正式依赖映射，而不是只看目录 co-change。依赖映射的正式输入至少包括：

* `ssot/**` 中的对象类型、对象引用、ADR 边界；
* `spec/contracts/**`、`spec/governance/**`、`spec/skill-standard/**` 中的 contract / schema / rule；
* `skills/**/ll.contract.yaml`、`skills/**/ll.lifecycle.yaml`、`input/output schema`、runtime command 声明；
* `cli/ll.py` 与 `cli/commands/**` 暴露的 command/action surface；
* `cli/lib/**` 中承载 protocol、runtime mapping、skill execution assumption 的模块。

* `Input`：正式依赖映射、受影响 workflow 清单、最小兼容 smoke manifest、相关 unit/integration 测试。
* `Assertion`：
  * `SSOT -> skill contract -> CLI/runtime` 的关键链路必须仍自洽。
  * 被依赖映射命中的 workflow 必须通过最小兼容 smoke。
  * 单域变更若破坏下游承载假设，必须被识别为跨域兼容失败，而不能因为未 co-change 而漏检。
* `Fail Mode`：`dependency_mapping_resolution_error`、`cross_domain_smoke_failed`、`runtime_mapping_break`、`contract_chain_break`
* `Output`：`cross-domain-compat-report.json` + `impacted-dependency-chain.json`
* `Owner`：跨域治理维护者

说明：

* v0 阶段允许使用推导式依赖映射，但每次执行都必须产出版本化的 `impacted-dependency-chain.json`，并将其视为本次兼容性判定的最小真相载体。
* 当依赖解析失败、影响面无法确定或映射来源冲突未决时，`cross-domain-compat` 必须默认 fail closed，而不是跳过。
* `impacted workflow` 清单可以由自动推导为主、版本化辅助清单为辅，但最终都必须收敛进 `impacted-dependency-chain.json`。
* 这是三大高风险域的联锁门禁，不能省略。
* 其目标是尽早识别跨层断裂，而不是替代全量 E2E。

---

# 6. Main Branch 全量校验

主分支在每次 merge 后应执行比 PR 更完整的一组检查。

至少包括：

* 全量 `tests/unit/`；
* `tests/integration/` 中已经稳定的集成测试；
* 全量 `ssot-governance` 扫描，而不是仅限变更文件；
* 全量 `skill-governance` 扫描，而不是仅限变更 skill；
* 全量 `cli-governance` 扫描，而不是仅限变更模块；
* 一组由版本化 smoke manifest 定义的 workflow compatibility smoke。

这层的目标是回答：

> 合并后的仓库，作为一个整体，是否仍然满足最基本的治理一致性。

---

# 7. Nightly / Manual 回归层

nightly 或手动触发层优先承载较重回归。

建议逐步纳入：

* `tests/e2e/`
* `tests/qa/`
* 由版本化回归清单定义的典型 workflow 全链样例回归
* 历史 `ADR` 样例与固定 fixture 的 golden diff
* 关键 artifacts 的 schema 与 report 完整性抽查
* 发布前或大重构前的 full governance regression

说明：

* 这一层可以失败告警，但不应该反向拖慢所有日常 PR；
* 只有当某项 nightly 检查已经足够稳定，才上提为 required check。
* “足够稳定”至少意味着：规则定义已版本化、误报已收敛、失败可定位、执行时长可接受。

---

# 8. 三个重点域的专门管控策略

## 8.1 `ssot`：把控“真相层”

`ssot` 的 CI 目标不是文风统一，而是：

* 对象层不漂移；
* 正式路径不漂移；
* 引用链不损坏；
* 新旧对象兼容解释不被静默破坏。

因此，`ssot` 的重点门禁应是：

* 路径与命名规则；
* 对象类型合法性；
* 关联引用可解析性；
* ADR 变更的人审强制；
* 禁止说明性投影覆盖正式真相。

## 8.2 `skills`：把控“契约层”

`skills` 的核心风险不在“脚本能不能跑”，而在“声明与实现是否还是同一个东西”。

因此，`skills` 的重点门禁应是：

* bundle 完整性；
* contract / lifecycle / schema 一致性；
* prompt / schema / template / script 引用有效性；
* runtime command 与真实脚本入口的匹配；
* 受影响 workflow 的最小测试覆盖。

## 8.3 `cli`：把控“运行时接口层”

`cli` 的核心风险不在内部实现细节，而在：

* command surface 是否静默变化；
* request/response 协议是否被破坏；
* skill runtime 是否还能被 CLI 正确承载；
* 新增功能是否补了测试与兼容性校验。

因此，`cli` 的重点门禁应是：

* parser / action surface snapshot；
* runtime contract smoke；
* 关键 command 的单测与集成 smoke；
* 跨 skill 的最小兼容性验证。

---

# 9. CODEOWNERS 与人工门禁

以下路径必须进入高等级人工 review 范围：

* `ssot/adr/**`
* `ssot/src/**`
* `ssot/epic/**`
* `ssot/feat/**`
* `ssot/tech/**`
* `ssot/impl/**`
* `ssot/testset/**`
* `spec/contracts/**`
* `spec/governance/**`
* `spec/skill-standard/**`
* `skills/**/ll.contract.yaml`
* `skills/**/ll.lifecycle.yaml`
* `skills/**/input/**`
* `skills/**/output/**`
* `cli/ll.py`
* `cli/commands/**`
* `cli/lib/**`

原则是：

* 自动化门禁负责挡住结构性错误；
* 人工 review 负责挡住语义性误判与治理边界误设。
* `CODEOWNERS` 应按域设置主 reviewer 与备 reviewer。
* required review 人数应按域分级，而不是所有路径一刀切。
* owner 缺席时必须有 fallback 策略，例如备 reviewer 自动接管或由指定治理 owner 兜底。

两者缺一不可。

---

# 10. 非目标

本 ADR 当前不冻结以下内容：

* 必须使用哪一家 CI 平台；
* 必须立即建设完整的多 Python 版本矩阵；
* 必须在第一版就把所有 `tests/e2e/`、`tests/qa/` 全量纳入 PR 阶段；
* 必须先设计完整发布流水线、制品发布与部署流程；
* 必须在本 ADR 中同时冻结所有 validator 的最终脚本文件名与 CLI 参数。

本 ADR 先冻结的是：

## **CI 应该验证什么，以及哪些域必须更严。**

---

# 11. 落地顺序

建议按三期推进。

## 第一期：先把 required checks 建起来

优先落地：

* `repo-hygiene`
* `unit-fast`
* `ssot-governance`
* `skill-governance`
* `cli-governance`
* `cross-domain-compat`

目标：

* 让 PR 门禁先具备基础可信度；
* 先把三大高风险域收住。

## 第二期：补全主分支全量扫描

优先落地：

* 全量域扫描
* 稳定 integration
* CLI surface snapshot diff
* skill bundle report artifact

目标：

* 让主分支具备整体一致性回归。

## 第三期：建设 nightly / manual 重回归

优先落地：

* workflow E2E
* golden drift
* QA 全链回归
* 发布前 full governance regression

目标：

* 让大改动、发布前检查与历史兼容性验证有稳定承载层。

---

# 12. 结论

LL v0.x 的 CI 路线正式冻结为：

## **治理优先、路径感知、分层门禁**

并明确：

* `ssot` 管真相层；
* `skills` 管契约层；
* `cli` 管运行时接口层；
* 这三层必须成为 CI 的重点管控对象；
* PR 只拦快速且确定的检查；
* 更重的全链回归放在主分支与 nightly 层逐步建设。

这保证 CI 不会退化为“跑一遍测试”，而是能真正守住 LL 仓库最关键的治理边界。
