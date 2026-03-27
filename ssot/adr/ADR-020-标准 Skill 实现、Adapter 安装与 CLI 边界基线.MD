# ADR-020：标准 Skill 实现、Adapter 安装与 CLI 边界基线

* 状态：Accepted
* 日期：2026-03-27
* 决策者：Le Zeng
* 适用范围：LEE Lite（LL）v0.x 全部 governed skill、Codex/Claude Code skill 入口、repo CLI/runtime 边界
* 相关 ADR：ADR-001、ADR-004、ADR-005、ADR-007、ADR-012、ADR-013、ADR-014、ADR-016、ADR-017、ADR-018、ADR-019

---

# 1. 背景

随着 `raw-to-src`、`src-to-epic`、`epic-to-feat`、`feat-to-tech`、`tech-to-impl`、`feat-to-testset`、gate orchestration 与 execution runner 等链路逐步落地，LL 已经形成比较稳定的 `skill-first` 主体架构。

但近期实现与设计过程中，围绕“什么叫 skill”再次出现明显漂移：

* 有时把 skill 理解为 `skills/l{n}/<skill-name>/` 下的 canonical governed skill bundle；
* 有时把 skill 理解为安装到 Codex / Claude Code 后可以直接触发的 adapter；
* 有时又把 skill 理解为 repo 内部 `ll` CLI 里新增的一个 action；
* 还有时把 `cli/lib/*.py` 里的 runtime helper 误当成“用户可调用的 skill 入口”本身。

这类漂移已经带来实际问题：

* FEAT/TECH/IMPL 中写“Claude/Codex CLI 可调用的 skill 入口”，实现却被落成 `ll skill ...` 子命令；
* canonical governed skill bundle 没有生成，adapter 也没有安装，但实现方误以为需求已经满足；
* `skills/`、`cli/`、`agents/<provider>.yaml`、`ll.contract.yaml`、`SKILL.md`、runtime command surface 的职责再次混层；
* 容易把“repo 内控制面”误写成“用户可触发的 agent skill”。

而 ADR-001、ADR-004、ADR-016、ADR-017 实际已经给出足够强的方向性约束：

* LL 是 `skill-first` 架构；
* `skills/` 承载 governed skill bundle；
* skill 与 CLI 执行器、gate CLI、runtime carrier 必须分层；
* Codex/Claude Code 使用的 skill 应通过标准 skill shell 与 adapter 安装进入运行时，而不是临时拼一个 repo CLI action。

因此，需要一份新的统一 ADR，明确冻结：

## **LL 中“标准 skill”的正式实现形态、安装方式、交付边界，以及它与 repo CLI/runtime 的关系。**

---

# 2. 问题陈述

LL 当前需要解决的不是“再补一份 skill 命名建议”，而是以下几个硬问题：

* 什么对象才算“标准 skill”；
* `skills/l{n}/<name>/`、Codex adapter、repo CLI action、runtime helper 分别是什么；
* 当 FEAT/TECH/IMPL 写“Claude/Codex CLI 可调用的 skill 入口”时，交付物最小集合是什么；
* `cli/` 能承载什么，不能替代什么；
* `ll skill ...` 这类 repo CLI action 在体系中的定位是什么；
* 后续所有 skill 的 authority 应该落在哪一层，而不是再次凭实现习惯漂移。

如果这一层不冻结，会持续出现以下问题。

## 2.1 把 repo CLI action 误当成 skill

例如新增：

```text
ll skill some-entry
```

并不自动等于：

* 已经创建 canonical governed skill bundle；
* 已经具备 Codex / Claude Code 可调用 skill；
* 已经具备 adapter 安装与 provider metadata；
* 已经满足 `skills/` 层治理要求。

## 2.2 把 runtime carrier 误当成用户入口

像：

* `cli/lib/*.py`
* `cli/commands/*.py`
* `loop.run-execution`
* `job.claim`

这些都可能是内部 runtime carrier 或 control surface，但它们本身不是标准 skill。

## 2.3 技术包冻结了错误 carrier

如果 TECH/IMPL 只冻结：

* `cli/lib/...`
* `cli/commands/...`

而没有冻结：

* `skills/l{n}/<skill>/SKILL.md`
* `ll.contract.yaml`
* `ll.lifecycle.yaml`
* `input/output contract`
* `agents/<provider>.yaml`
* adapter 安装路径

那么实现者很容易把“需要一个 skill”误落成“需要一个 CLI action”。

## 2.4 用户可调用边界与仓库控制面混层

“Claude/Codex CLI 可调用”在本项目里，首先意味着：

* 该能力存在为标准 skill；
* 可通过 skill shell / adapter 被调用；
* 有明确 prompt/contract/boundary。

它不等于：

* 任何仓库内部 CLI 都可以拿来冒充 skill；
* 任何 repo command surface 都天然是 agent-facing skill。

---

# 3. 决策

## 3.1 决策摘要

LL v0.x 正式采用以下分层定义：

1. `skills/l{n}/<skill-name>/` 是 **canonical governed skill bundle** 的正式承载；`standard skill` 只是其对外简写。
2. Codex / Claude Code 实际使用的 skill，是 canonical governed skill bundle 经过 adapter 安装后的 **installed skill adapter**。
3. `cli/` 是 **repo 内 runtime / control / tooling carrier**，不是 skill 本体。
4. 当需求写“需要一个 Claude/Codex CLI 可调用的 skill 入口”时，**必须交付 canonical governed skill bundle**；仅新增 repo CLI action 不视为满足。
5. 后续所有 skill 的 authority，默认以本 ADR 为准；若某个实现想偏离，必须在新的 ADR 或明确 FEAT/TECH/IMPL 中显式豁免，而不能靠实现习惯隐式偏离。

---

## 3.2 正式定义

### A. Canonical Governed Skill Bundle

LL 中标准 skill 的正式 authority 名称统一为：

> **canonical governed skill bundle**

对外可简写为：

> **standard skill**

其正式定义为：

> **一个位于 `skills/l{n}/<skill-name>/` 下、具备标准 skill shell 与 governed workflow contract 的 canonical skill bundle。**

其中：

* `l3`：完整闭环 workflow skill；
* `l2`：串联多个 L3 的阶段 pipeline skill；
* `l1`：串联多个 L2 的长程 orchestration skill。

因此，canonical skill path 的正式模式为：

```text
skills/l{n}/<skill-name>/
```

兼容说明：

* 历史平铺目录 `skills/<skill-name>/` 只视为过渡兼容布局；
* 新增或重构后的 canonical governed skill bundle，默认必须声明所属层级并落在 `skills/l{n}/<skill-name>/`；
* 若某个 skill 暂时仍保留平铺路径，必须在其 FEAT/TECH/IMPL 或 bundle metadata 中显式声明该兼容例外，不能把平铺路径再次当成新标准。

它至少应包含：

* `SKILL.md`
* `ll.contract.yaml`
* `ll.lifecycle.yaml`
* `input/contract.yaml`
* `input/schema.json`
* `output/contract.yaml`
* `output/schema.json`

以及按需要包含：

* `agents/executor.md`
* `agents/supervisor.md`
* `agents/<provider>.yaml`
* `scripts/`
* `resources/`
* `evidence/`

### B. Installed Skill Adapter

Codex / Claude Code 实际使用的 skill，不直接等于仓库内 canonical source，而是：

> **canonical governed skill bundle 通过 adapter 安装后，进入用户本地 skill runtime 的 installed adapter copy。**

标准安装路径由 `ll-skill-install` 负责，参考：

* canonical source：`skills/l{n}/<skill-name>/`
* installer：`skills/ll-skill-install/scripts/install_adapter.py`
* installed destination：`$CODEX_HOME/skills/<skill-name>` 或等价 Codex skills 目录

因此：

* 仓库 skill 是 authority；
* installed adapter 是运行副本；
* 不应手改 installed copy 代替修改 canonical source。
* 安装器只允许做复制、路径映射、必要的 provider/runtime metadata 适配，不得改变 skill 的语义边界、contract 语义、lifecycle 语义或必需产物语义。

### C. Tooling CLI

repo CLI 中直接面向 workflow scripts 或工具脚本的命令，属于 tooling/runtime carrier，例如：

* skill 内部调用的 `python scripts/*.py ...`
* validation helper
* freeze guard
* package builder

这类命令可以被 skill 调用，但本身不是 skill。

### D. Control CLI

repo `cli/` 中承载 control surface 的命令，属于：

> **runtime control plane / governance execution plane**

例如：

* `ll gate ...`
* `ll registry ...`
* `ll artifact ...`
* `ll loop ...`
* `ll job ...`

它们是仓库治理运行时的一部分。

它们可以：

* 被 skill 内部调用；
* 被 operator 直接调用；
* 作为 runtime carrier 暴露内部控制面。

但它们不自动等于：

* canonical governed skill bundle；
* Codex/Claude Code 的标准 skill 入口。

### E. Runtime Helper / Library

位于 `cli/lib/`、`skills/**/scripts/` 中的 helper / runtime module，只是实现载体。

它们可以承接：

* context bootstrap
* protocol parse
* dispatch
* validation
* evidence writeback

但它们不是用户入口对象。

---

## 3.3 分层模型

LL 正式采用如下 skill 分层：

```text
Canonical Governed Skill Bundle
  -> skills/l{n}/<skill-name>/
  -> SKILL.md + contract + lifecycle + schema + agents + scripts

Installed Skill Adapter
  -> installed into Codex / Claude Code runtime
  -> generated from canonical governed skill bundle

Repo CLI / Runtime
  -> cli/commands/*
  -> cli/lib/*
  -> loop/job/gate/registry/artifact control surfaces

Workflow Scripts / Helpers
  -> skills/**/scripts/*
  -> validation, package build, execution helpers
```

这四层必须区分，不能互相冒充。

---

## 3.4 对“Claude/Codex CLI 可调用的 skill 入口”的正式解释

当 FEAT、TECH、IMPL、TESTSET、ADR 中写：

* `Claude/Codex CLI 可调用`
* `operator-facing skill entry`
* `named skill entry`
* `独立 skill 入口`

其默认正式含义是：

## **必须存在一个 canonical governed skill bundle，可被安装成 Codex / Claude Code skill adapter 并由 agent runtime 触发。**

它不默认等于：

* `cli/ll.py` 里新增一个 action；
* `cli/commands/*.py` 里新增一个 handler；
* `cli/lib/*.py` 里新增一个 helper。

若设计确实只需要 repo CLI control surface，而不需要 skill bundle，则必须明确写成：

* `operator-facing repo CLI control surface`
* `runtime control entry`
* `CLI command surface`

而不是再用“skill entry”这个词。

---

# 4. 标准 Skill 的最小交付要求

## 4.1 新增 skill 的最小文件集

凡新增一个 canonical governed skill bundle，最小交付物必须包括：

* `skills/l{n}/<skill-name>/SKILL.md`
* `skills/l{n}/<skill-name>/ll.contract.yaml`
* `skills/l{n}/<skill-name>/ll.lifecycle.yaml`
* `skills/l{n}/<skill-name>/input/contract.yaml`
* `skills/l{n}/<skill-name>/input/schema.json`
* `skills/l{n}/<skill-name>/output/contract.yaml`
* `skills/l{n}/<skill-name>/output/schema.json`

若 skill 需要 executor/provider metadata，则再包含：

* `skills/l{n}/<skill-name>/agents/<provider>.yaml`

说明：

* provider metadata 不是所有 skill 的默认必备文件；
* 只有当 bundle 声明了 provider adapter 或 executor adapter 时，才需要对应的 `agents/<provider>.yaml`；
* `agents/openai.yaml` 只是 provider metadata 的一个实例，不得再被视为所有标准 skill 的默认固定文件名。

若 skill 需要双角色治理，则再包含：

* `agents/executor.md`
* `agents/supervisor.md`

若 skill 需要本地执行脚本，则再包含：

* `scripts/*.py` 或其它 runtime helper

## 4.2 新增 skill 的最小验证要求

至少应满足：

* `skill-governance` 能通过 bundle 完备性校验；
* `SKILL.md` 与 `ll.contract.yaml` 的 boundary 不冲突；
* runtime entry 可被最小 smoke test 调用；
* 若声明 provider adapter，则 `agents/*.yaml` 可解析；
* 若需要安装到 Codex，则必须能通过 `ll-skill-install` 生成 adapter。

## 4.3 新增 skill 的最小测试要求

至少应覆盖：

* bundle 结构存在性
* contract/schema 最小一致性
* runtime happy path
* 关键 boundary/negative case
* 若有 repo CLI 承载层，则 skill 与 CLI 之间的承载关系 smoke test
* installed adapter 可发现性 smoke test
* installed adapter 可触发性 smoke test

---

# 5. Skill 与 Repo CLI 的正式边界

## 5.1 skill 可以依赖 CLI

标准 skill 可以调用：

* repo CLI control surface
* tool CLI
* gateway/registry/gate runtime

例如：

* skill 调 `ll gate ...`
* skill 调 `ll artifact ...`
* skill 调 `python scripts/...`

这完全允许。

## 5.2 CLI 不能替代 skill

但仅有以下内容，不足以宣称“已经实现了一个标准 skill”：

* `cli/ll.py` 新增 command
* `cli/commands/*.py` 新增 action
* `cli/lib/*.py` 新增 runtime helper
* 文档里描述了 operator command

如果需求是 “新增 skill”，则这些只能算 skill 的实现依赖或 runtime carrier，不能算 skill 本体。

## 5.3 Control CLI 的正确定位

repo CLI 的正确定位是：

* governance runtime
* file-based control plane
* artifact/job/handoff/gate/registry execution carrier
* operator control surface

因此：

* `ll gate` 是 gate CLI
* `ll loop` / `ll job` 是 execution runner control CLI
* 它们都不是 canonical governed skill bundle 本身

## 5.4 `ll skill ...` 的边界

若 repo 内存在 `ll skill ...` 这一组命令，其定位最多只能是：

* 为 repo 内已有 canonical governed skill bundle 提供一个便捷承载层；或
* 为已有 skill runtime 提供 protocol-compatible wrapper；或
* 为测试/回归/兼容桥接保留的 CLI façade

它不应被当成：

* skill 的唯一正式实现形态
* 替代 `skills/l{n}/<skill>/...` 的 canonical source

换句话说：

## **`ll skill ...` 可以是 skill façade，但不能是 skill authority。**

默认禁令：

* 除非仓库内已经存在同名 canonical governed skill bundle，否则不允许新增 `ll skill <name>` façade；
* 不允许以“先做 façade，后补 canonical bundle”为默认实施顺序。

---

# 6. 对后续 FEAT / TECH / IMPL 的强制解释规则

自本 ADR 生效后，后续任何 FEAT / TECH / IMPL 若写：

* `新增 skill`
* `独立 skill 入口`
* `Claude/Codex CLI 用户入口`
* `operator-facing skill`

默认必须同时冻结以下信息：

1. canonical skill name
2. canonical skill level：`l1 | l2 | l3`
3. canonical skill path：`skills/l{n}/<skill-name>/`
4. input artifact boundary
5. output artifact boundary
6. 是否声明 provider adapter；若声明，对应 `agents/<provider>.yaml` 是什么
7. 是否需要 adapter install
8. skill 依赖哪些 repo CLI/runtime carrier

若未冻结这些信息，就不应声称“skill 入口已设计完成”。

相反，如果需求只打算交付 repo CLI，则必须显式写：

* `repo CLI control surface`
* `runtime command surface`
* `operator command`

不得继续沿用“skill”一词偷换概念。

---

# 7. 对当前仓库的直接约束

## 7.1 `skills/` 是 canonical authority

`skills/` 目录只放 governed workflow skill 定义与其治理包。

后续新 skill，默认都应新增在：

```text
skills/l{n}/<skill-name>/
```

而不是先从：

* `cli/commands/`
* `cli/lib/`
* `docs/`

开始伪装 skill。

## 7.2 `cli/` 是 runtime/control authority

`cli/` 目录承载：

* gate/runtime/control protocol
* operator control plane
* artifact/job/handoff/registry orchestration

它可以被 skill 使用，但不能替代 skill bundle。

## 7.3 adapter 安装必须走标准安装器

需要进入 Codex / Claude Code 运行时的 skill，默认应通过：

```powershell
python skills/ll-skill-install/scripts/install_adapter.py --source <canonical-skill-dir> --replace
```

或其标准包装面完成。

不得手工复制目录、手工拼 prompt、手工改 installed adapter 元数据来代替正式安装。

安装器边界进一步冻结为：

* installer 只同步 canonical governed skill bundle 到 installed adapter；
* installer 不得注入新的 authority 信息；
* installer 不得在安装阶段改写 skill contract、lifecycle、semantic boundary、required evidence 或 output semantics；
* 若安装阶段需要 provider/runtime 适配，该适配必须保持语义等价。

---

# 8. 反模式清单

本 ADR 生效后，以下都属于明确反模式。

## 8.1 只加 `ll` 子命令，不建 canonical skill

如果需求是“新增一个 skill”，但只提交：

* `cli/ll.py`
* `cli/commands/*.py`

没有 `skills/l{n}/<skill>/...`

则不满足本 ADR。

## 8.2 只写 `cli/lib/*.py` 就声称 skill 入口已完成

runtime helper、context bootstrapper、protocol parser 都只是内部承载。

没有 canonical governed skill bundle，不算 skill 交付完成。

## 8.3 用 `docs/*.md` 或临时计划代替 skill authority

实现计划、review note、落地方案都不是 canonical skill source。

skill authority 必须落在：

* `skills/l{n}/<skill>/...`
* 以及与之对应的正式 SSOT 冻结对象

## 8.4 把 installed adapter 当成 canonical source

adapter 是运行副本，不是 authority。

不得修改：

* `$CODEX_HOME/skills/<skill-name>/`

来代替修改仓库中的 canonical skill。

## 8.5 用“skill”指代任何 operator command

不是所有 command 都是 skill。

后续文档中若是 repo CLI，应明确写：

* command
* control surface
* runtime entry
* CLI action

而不是继续模糊写成 skill。

---

# 9. 与既有 ADR 的关系

## 9.1 与 ADR-001 的关系

ADR-001 冻结了 LL 是 `skill-first` 架构，并且明确：

* `skills/` 只放 workflow skill 定义；
* skill 不等于执行器；
* 执行循环与 human gate loop 是外部会话；
* skill 具有 `L1/L2/L3` 分层语义。

ADR-020 进一步把“canonical governed skill bundle 到底长什么样、如何安装到 Codex/Claude Code、与 CLI 的边界是什么”正式冻结下来，并把 `L1/L2/L3` 的层级路径与 bundle authority 正式接上。

## 9.2 与 ADR-004 的关系

ADR-004 冻结了统一 skill execution contract 与公共 skill kernel。

ADR-020 补的是载体层：

* canonical governed skill bundle 放哪；
* adapter 怎么安装；
* 哪些对象不是 skill 本体。

同时继承 ADR-004 对 adapter 的约束：

* adapter 只适配交互方式与运行时元数据；
* adapter 不得改写 contract 语义；
* adapter 不得回灌 authority 到 skill 本体。

## 9.3 与 ADR-016 的关系

ADR-016 已明确：

> gate CLI 是执行器，gate skill 是人类决策编排器。

ADR-020 将这条原则推广为所有 skill 的统一基线：

> CLI 可以是 carrier，但 skill 与 CLI 不是同一层对象。

## 9.4 与 ADR-017 的关系

ADR-017 已把 `skills/`、`cli/`、`ssot/` 识别为三个高风险域，并明确：

* `skills/` 管 bundle 契约层；
* `cli/` 管 protocol/runtime/control 层；
* `agents/*.yaml` 应保持 provider-neutral，而不是把某个 provider 文件名固化成唯一标准。

ADR-020 把这种 CI 层分域门禁，上升为架构层对象边界。

## 9.5 与 ADR-018 / ADR-019 的关系

ADR-018 定义 execution runner 是自动推进运行时，不是业务 skill。

ADR-019 以及后续 operator-facing skill 设计，若写“独立 skill 入口”，必须按 ADR-020 解释为：

* canonical governed skill bundle
* installed adapter
* 可选 CLI/runtime carrier

而不是仅交付 repo CLI façade。

---

# 10. 实施规则

本 ADR 生效后，后续新增或修改 skill 时，默认按以下顺序实施：

1. 先冻结 FEAT / TECH / IMPL 中的 canonical skill identity、level 与 boundary；
2. 在 `skills/l{n}/<skill-name>/` 下生成 canonical governed skill bundle；
3. 让 skill 通过最小 governance / smoke 校验；
4. 若需要进入 Codex / Claude Code，则通过 `ll-skill-install` 安装 adapter；
5. 验证 installed adapter 的 discoverability 与 invokability；
6. 如需 repo CLI/control plane，作为 skill 的 carrier 或依赖层单独实现；
7. 不得再以 repo CLI action 单独冒充 skill 交付。

---

# 11. 结论

LL 后续所有“skill”相关设计与实现，正式以本 ADR 为准：

## **标准 skill 的 authority 在 `skills/l{n}/<skill-name>/` canonical governed skill bundle；Codex / Claude Code 使用的是其 installed adapter；repo `cli/` 只是 runtime/control/tooling carrier，不能再单独冒充 skill 本体。**

如果某个后续设计只想新增 operator command，而不打算交付 canonical skill bundle，就必须把对象命名成：

* repo CLI control surface
* runtime command
* operator entry

而不能再写成“新增一个 skill”。

---

# 12. 后续边界

本 ADR 当前优先冻结的是：

* skill 的对象边界
* canonical bundle 与 adapter / CLI / helper 的边界
* 路径 authority 与安装 authority

它暂不细化 skill 生命周期状态机，例如：

* canonical bundle 何时视为 install-ready
* canonical bundle 未安装时的治理状态
* installed adapter deprecated / drift / mismatch 的修复责任

这类 lifecycle 规则可在后续 ADR 中单独冻结，但不得影响本 ADR 已确定的对象边界与 authority 关系。

