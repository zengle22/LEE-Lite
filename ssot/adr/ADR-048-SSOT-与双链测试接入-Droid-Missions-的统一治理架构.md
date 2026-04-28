# ADR-048：SSOT 与双链测试接入 Droid Missions 的统一治理架构

> **SSOT ID**: ADR-048
> **Status**: 重新定义 (2026-04-13)
> **Supersedes**: 原 v1.0 (2026-04-10)
> **Version**: v2.0
> **Scope**: LL / LEE 项目执行引擎接入与运行时统一
> **Governance Kind**: TRANSFER
> **Depends On**: ADR-047 (v1.4, Trial Approved)
> **Implementation Status**: 未实现（见 REINTERPRETATION）

---

## 核心重新定义

> **更新日期**: 2026-04-13
> **原因**: 之前的实现方向跑偏，自建了伪 Droid 运行时

### Droid Missions 是什么

Droid Missions 是 Factory.ai CLI 的**内置功能**（`/enter-mission`），不是我们开发的工具。

工作方式：
1. `/enter-mission` → 描述目标 → 对话确定范围 → 批准计划
2. Orchestrator 自动分解为 milestones → features
3. 每个 feature 启动独立 worker session（干净上下文）
4. 每个 milestone 结束时有 validation 阶段
5. Git 是真相源，全程自动协调
6. 支持 24+ 小时长程任务，最长达 16 天

**关键能力：Droid 自己会分解任务、并行执行、验证结果、从失败恢复。我们不需要造这些。**

---

### ADR-048 的真正目标

**把我们的 SSOT 文档能力和双链测试能力，作为结构化输入喂给 Droid Missions，让它跑通从需求到代码到验证的完整闭环。**

```
我们的价值                    Droid Missions 的价值
────────                      ─────────────────────
SSOT 链冻结需求               Droid 分解为 milestones/features
双链定义验证标准              Droid spawn workers 执行验证
Governance gate 决策          Droid 的 validation 阶段
                              Droid 自动回流和修复

输入: 我们给 Droid 结构化的 SSOT 文档 + 双链资产
输出: Droid 给我们运行完成的代码 + 验证通过的证据
```

---

### 我们不需要造的（Droid 已有）

| 之前造的 | 实际上 |
|---------|--------|
| Mission Compiler | Droid Orchestrator 自己读取文档、自己分解任务 |
| Droid Runtime workers | Droid 自己 spawn worker sessions |
| Gate Evaluation | Droid 的 validation 阶段自动做这件事 |
| skill_invoker.py 分发 | Droid 自己协调 |
| Job 队列和状态机 | Droid 用 git 作为真相源 |
| execution_runner.py | Droid 的 Mission 执行引擎 |

---

### 我们实际需要做的是什么

#### 1. 让 SSOT 文档对 Droid 友好

Droid 需要能理解我们的文档结构：
- FEAT 文档的格式是否 Droid 能直接消费？
- 验收标准（AC）是否足够明确让 Droid 验证？
- 双链 manifest/spec 是否 Droid 的 validation worker 能执行？

#### 2. 让双链测试可被 Droid 执行

Droid 的 validation worker 需要能运行我们的测试：
- API spec → Droid 能执行 API 验证
- E2E spec → Droid 有 computer use 可以做 UI 验证
- 证据采集 → Droid 自己记录执行结果

#### 3. 可能的 Skill 集成

给 Droid 提供 custom skills：
- 运行我们特定的测试工具
- 读取特定的 SSOT 文档格式
- 产出特定格式的证据报告

#### 4. 治理层集成

我们的 gate 决策如何与 Droid 的 validation 结果对接：
- Droid validation 通过 → 我们的 gate approve
- Droid validation 失败 → 我们的 gate block → Droid 创建 fix feature
- 这个回流路径可能只需要配置，不需要写代码

---

### 结论

**ADR-048 不是开发需求，是集成需求。** 我们需要的是：

1. 调整 SSOT 文档格式让 Droid 能理解
2. 调整双链测试让 Droid 能执行
3. 可能写少量 glue skills
4. 定义治理层和 Droid validation 的对接协议

**不需要：Mission Compiler、Droid Runtime、Gate Evaluation、Job 队列、分发器——这些 Droid 全都有。**

---

## 附录 A：原 v1.0 规范要点（已废弃）

> 以下为 2026-04-10 v1.0 规范的核心要点，已被 v2.0 重新定义取代。

### 原方案架构（废弃）

原 v1.0 定义了三层架构：

| 真相源 | 职责 | 产出 |
|--------|------|------|
| **SSOT** | 需求真理源 | 冻结的功能契约、用户旅程 |
| **双链测试** | 测试真理源 | 覆盖账本、测试合同、证据结算 |
| **Droid Missions** | 执行与验证运行时 | mission 执行、证据采集、状态回写 |

### 原方案被废弃的原因

1. **Mission Compiler** — Droid Orchestrator 自己读取文档，不需要我们造
2. **Droid Runtime workers** — Droid 自己 spawn workers，不需要我们造
3. **Gate Evaluation** — Droid 的 validation 阶段自动做，不需要我们造
4. **Job 队列和状态机** — Droid 用 git 作为真相源，不需要我们造

### 关键决策记录（原 v1.0）

| # | 决策 | 状态 |
|---|------|------|
| D1 | 旧 testset 退出体系 | 保留 |
| D2 | Fix Feature 必须新建 | 保留 |
| D3 | 三层真相源分离 | 保留方向，废弃自建运行时 |
| D4 | Scrutiny-Validator 与 User-Testing-Validator 分离 | 待定（Droid 已有类似能力） |
| D5 | Gate decision 映射为 milestone decision | 保留 |
| D6 | Fix Feature 迭代上限 3 次 | 保留 |
| D7 | 字段级 mapping spec 先行 | **废弃** — Droid 自己理解文档 |

---

## 附录 B：历史实现尝试记录

以下文件/目录曾被创建，现已删除：

- ~~FEAT-SRC-RAW-TO-SRC-ADR048-001 (Mission Compiler)~~
- ~~FEAT-SRC-RAW-TO-SRC-ADR048-002 (Droid Runtime)~~
- ~~FEAT-SRC-RAW-TO-SRC-ADR048-003 (Gate Evaluation)~~
- ~~IMPL-SRC-RAW-TO-SRC-ADR048-001/002/003~~
- ~~EPIC-SRC-RAW-TO-SRC-ADR048~~
- ~~所有旧的 ADR048 tech/arch/api 文档~~

---

## 下一步

1. **评估 SSOT 文档格式** — 检查当前 feat/prototype 格式是否 Droid 可直接消费
2. **评估双链测试可执行性** — 检查 manifest/spec 是否 Droid validation worker 可执行
3. **定义 Droid 集成方案** — 如需，写少量 glue skills
4. **参考 ADR-054** — 实施轴接入需求轴的双链桥接可能与此相关
