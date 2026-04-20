# ADR-050：SSOT 语义治理总纲 — FRZ / 抽取 / 稳定 / 变更 / 三轴 / 执行闭环

> **SSOT ID**: ADR-050
> **Title**: SSOT 语义治理总纲 — 从生成链到语义治理的体系级架构决策
> **Status**: Accepted
> **Version**: v1.0
> **Effective Date**: 2026-04-17
> **Scope**: SSOT 语义治理 / 架构总览 / 多 ADR 协同
> **Owner**: 架构 / 质量治理
> **Governance Kind**: NEW
> **Audience**: 产品、架构、AI 实施代理、测试
> **Depends On**: ADR-045 (FRZ), ADR-047 (双链测试), ADR-049 (Experience Patch)

---

## 1. 背景

### 1.1 One-Sentence Summary

> **SSOT 从"逐层生成链"升级为"前置 FRZ 统一语义 → SSOT 结构化表达 → Task Pack 驱动执行 → 双链验证收敛 → 变更分级回流治理"的闭环体系。**

### 1.2 历史问题

原有 SSOT 流程为：

```text
SRC → EPIC → FEAT → TECH/UI/TEST
```

逐层生成导致：
- 上游信息不足 → 下游脑补
- 语义逐层漂移
- 与第三方高质量文档重复

### 1.3 已解决的部分

已有 ADR 已解决大部分结构性问题：

| 问题域 | 解决 ADR | 状态 |
|--------|---------|------|
| FRZ 冻结层 | ADR-045 | Trial Approved |
| 双链测试 | ADR-047 | Trial Approved |
| Experience Patch | ADR-049 | Frozen |

### 1.4 本 ADR 的目的

本 ADR 不替代已有 ADR，而是：
1. **提炼 6 条核心架构原则**，形成可一句话表达的治理总纲
2. **补充已有 ADR 之间的协同关系**，消除灰色地带
3. **引入 3 条新决策**（执行语义稳定、三轴管理强度、Task Pack 循环），补齐已有 ADR 未覆盖的治理盲区

---

## 2. 核心原则（一句话架构）

```
前置 FRZ 统一语义
  → SSOT 结构化表达（抽取非生成）
    → Task Pack 驱动顺序执行
      → 双链验证收敛（API + E2E）
        → 变更分级回流治理（minor patch / major FRZ）
```

### 2.1 原则映射表

| 原则 | 对应 ADR | 状态 |
|------|---------|------|
| FRZ 唯一语义真相源 | ADR-045 | 已有 |
| SSOT 分层语义抽取 | 本节 §3（新） | 新增 |
| 执行层语义稳定 | 本节 §4（新） | 新增 |
| 变更分级机制 | ADR-049 + 本节 §5（补充） | 协同 |
| 三轴管理强度 | 本节 §6（新） | 新增 |
| Task Pack 顺序执行 | 本节 §7（新，ADR-018 具体化） | 新增 |
| 双链测试收敛 | ADR-047 | 已有 |

---

## 3. FRZ 定义 — 来源、内容、进入路径

### 3.1 FRZ 从哪里来

FRZ（Freeze Package）不是从 raw input 直接生成的，而是通过**外部框架充分讨论后产出的文档集合，经冻结后进入 SSOT 体系**。

**完整流程**：

```
需求讨论阶段（外部框架）
  BMAD / Superpowers / OMC 等
    ├─ 产品讨论 → PRD
    ├─ 架构讨论 → Architecture Doc
    ├─ 体验讨论 → UX Doc (Journey / Wireframe)
    ├─ 测试讨论 → Test Strategy
    └─ 其他 → 讨论记录、会议纪要
         ↓
文档收敛 + 冲突消解 + 共识确认
         ↓
      FRZ 冻结
         ↓
进入 SSOT 体系，成为唯一语义真相源
```

**关键原则**：

> **FRZ 是讨论结果的冻结，不是 AI 的生成产物。** 所有 FRZ 内容必须来自真实的人类讨论或第三方框架输出，不得由 AI 自行编造。

### 3.2 FRZ 包含什么内容

#### 3.2.1 输入文档集合（冻结前的源文档）

FRZ 的输入来自以下文档类型（按讨论需要组合）：

| 文档类型 | 来源框架 | 冻结内容 |
|---------|---------|---------|
| **PRD** | BMAD-PRD / Superpowers / 手写 | 产品边界、用户能力、业务规则 |
| **Architecture** | BMAD-Architecture / 架构讨论 | 系统边界、技术约束、集成点 |
| **UX Doc** | BMAD-UX / 体验讨论 | 用户旅程、页面流程、交互规则 |
| **Test Strategy** | BMAD-Test / 测试讨论 | 验收口径、测试范围 |
| **Journey / Story** | BMAD-Story / Superpowers | 用户故事、场景描述 |

#### 3.2.2 FRZ 冻结产物（进入 SSOT 的工件）

FRZ 冻结后输出为结构化包：

| 文件 | 用途 | 格式 |
|------|------|------|
| `frz-package.json` | 结构化元数据 + MSC 校验 + 内容索引 | JSON |
| `freeze.yaml` | 冻结语义内容，SSOT 抽取的唯一依据 | YAML |
| `evidence.yaml` | 证据追溯：源文档引用、矛盾登记、归一化决策 | YAML |
| `index.md` | 人类可读摘要，快速审阅用 | Markdown |

#### 3.2.3 核心内容结构（freeze.yaml / frz-package.json.freeze）

FRZ 必须包含以下 MSC（Minimum Semantic Completeness）维度，缺一不可：

| MSC 维度 | 含义 | 示例 | 锚点 ID 格式 |
|----------|------|------|-------------|
| `product_boundary` | 什么在范围内、什么不在 | in_scope / out_of_scope | 无 |
| `core_journeys` | 核心用户流程 | 步骤列表 | `JRN-xxx` |
| `domain_model` | 核心实体及其关系 | 实体定义、必填字段 | `ENT-xxx` |
| `state_machine` | 状态机定义 | 状态、转换、守卫 | `SM-xxx` |
| `acceptance_contract` | 验收口径 | expected_outcomes / acceptance_impact | `FC-xxx` |

此外还包含：

| 字段 | 含义 | 锚点 ID 格式 |
|------|------|-------------|
| `constraints` | 不可漂移的硬约束 | 无 |
| `derived_allowed` | 允许下游派生的范围 | 无 |
| `known_unknowns` | 未决项（必须有 owner + expires_in） | `UNK-xxx` |
| `enum` | 冻结枚举 | `ENUM-xxx` |

#### 3.2.4 具体示例（来自实际 FRZ）

```json
{
  "artifact_type": "frz_candidate_package",
  "frz_id": "FRZ-raw-to-src",
  "msc": {
    "required": ["product_boundary", "core_journeys", "domain_model", "state_machine", "acceptance_contract"],
    "missing": [],
    "valid": true
  },
  "freeze": {
    "product_boundary": { "in_scope": [...], "out_of_scope": [...] },
    "core_journeys": [{ "id": "JRN-001", "name": "...", "steps": [...] }],
    "domain_model": [{ "id": "ENT-001", "name": "...", "contract": {...} }],
    "state_machine": [],
    "acceptance_contract": { "expected_outcomes": [...], "acceptance_impact": [...] },
    "constraints": [...],
    "derived_allowed": [...],
    "known_unknowns": [{ "id": "UNK-001", "topic": "...", "status": "open", "expires_in": "2 cycles" }]
  },
  "evidence": {
    "source_refs": ["prd-v2.md", "architecture-v1.md", "ux-journey.md"],
    "raw_path": "artifacts/frz-input/xxx/"
  }
}
```

### 3.3 FRZ 的 MSC 校验门控

FRZ 必须通过 MSC（Minimum Semantic Completeness）校验才能进入 frozen 状态：

```
5 维度检查：product_boundary + core_journeys + domain_model + state_machine + acceptance_contract
           ↓
      全部存在且非空 → frozen（可被下游引用）
      任一缺失 → blocked（不得进入下游，需补全）
```

缺失任一维度时的处理：
- 该维度标记为 `missing`
- FRZ 状态为 `freeze-ready`（不可被下游引用）
- 必须回到讨论阶段补全后才能进入 `frozen`

### 3.4 FRZ 的存放位置

```
artifacts/
  frz-input/              ← 冻结前的源文档集合（PRD/ARCH/UX 等）
  raw-to-src/
    frz-package/          ← 最新 FRZ（默认引用）
    frz-smoke-<date>/     ← 历史 FRZ（按 run 归档）
      frz-package/
      input/              ← 源输入快照
      document-test-report.json ← 文档测试结果
      contradiction-register.json ← 矛盾登记
```

> **关键**：FRZ 存放在 `artifacts/`，不进入 `ssot/` 主链（ADR-045 §2.1）。SSOT 通过 `frz_package_ref` 引用 FRZ，而非直接包含。

### 3.5 与 ADR-045 的关系

本节是 ADR-045 的总纲级摘要：
- ADR-045 定义 FRZ 的完整规范（MSC、投影不变性、锚点、来源标注）
- 本节定义 FRZ 在整体架构中的位置、来源、内容和校验门控
- 细节以 ADR-045 为准

---

## 4. 决策：SSOT 从生成链升级为语义抽取与归属链

### 4.1 决策

SSOT 不再承担逐级内容生成职责，改为：

> 基于前置冻结文档包（FRZ），进行分层语义抽取与归属管理。

具体规则：
- SRC / EPIC / FEAT 保留，用于组织与追溯
- 各层内容从 **统一语义源（FRZ）抽取**，而非仅依赖直接父节点
- SSOT 只表达 FRZ，**不得改写 FRZ 语义**

### 4.2 与 ADR-045 的关系

本条是 ADR-045 §2.4（投影不变性）的上层表达：
- ADR-045 定义 FRZ → SRC 的投影规则
- 本条定义整个 SSOT 主链（SRC → EPIC → FEAT → ...）的抽取原则

### 4.3 后果

| 正面 | 负面 |
|------|------|
| 消除逐层语义漂移 | 需要建立抽取规则 |
| 复用高质量前置内容 | 对 FRZ 质量依赖更高 |
| 提升全链一致性 | 下游不得自行补义 |

---

## 5. 决策：执行阶段禁止修改语义真相（只允许补全）

### 5.1 决策

定义两类变更：

| 类型 | 定义 | 示例 | 处理方式 |
|------|------|------|---------|
| **执行澄清**（允许） | 不改变语义的参数补充 | UI 细节、技术实现、参数补充 | 直接补全到 SSOT |
| **语义变更**（禁止直接修改） | 改变用户路径、功能逻辑、验收标准 | 新增用户动作、修改状态机、改变 AC | 必须回到 FRZ 重新冻结 |

### 5.2 语义稳定的判断标准

> **如果一个变更会导致下游测试用例的预期行为发生变化，它就是语义变更。**

具体判断：
- 用户路径变化 → 语义变更
- 功能逻辑变化 → 语义变更
- 验收标准变化 → 语义变更
- UI 样式微调 → 执行澄清
- 技术实现细节 → 执行澄清
- 参数默认值补充 → 执行澄清

### 5.3 与 ADR-045 的关系

本条是 ADR-045 §2.2（Pre-SSOT 与 SSOT 内补全边界）在执行层的具体化：
- ADR-045 定义"方向性真相" vs "派生性设计"
- 本条定义执行层的"澄清" vs "语义变更"判断标准

### 5.4 后果

| 正面 | 负面 |
|------|------|
| 防止执行层污染 SSOT | 需要变更分级判断 |
| 保持语义稳定 | 执行层发现语义问题需回流 |
| 测试目标稳定 | 增加回流成本 |

---

## 6. 决策：变更分级机制（Minor / Major）— 与 ADR-049 协同

### 6.1 决策

ADR-049 已有三级分类（visual / interaction / semantic），本条将其映射到两级的变更处理路径：

| ADR-049 分类 | 变更级别 | 处理路径 | 回写目标 |
|-------------|---------|---------|---------|
| visual | **Minor** | Patch → retain_in_code | 不回写 SSOT |
| interaction | **Minor** | Patch → backwrite UI/TESTSET | UI Spec / Flow Spec |
| semantic | **Major** | 回 FRZ → 重新冻结 → 更新 SSOT | 新建 SRC |

### 6.2 Minor Change 规则

- 不改变语义
- 直接 patch SSOT（通过 ADR-049 Patch 层）
- 记录版本
- 每 N 次 patch 后必须进行一次 clean rebase（防止 patch 堆积）

### 6.3 Major Change 规则

- 改变语义
- 必须回到 FRZ 层
- 重新冻结后更新 SSOT
- 不得绕过 FRZ 直接修改 SSOT 语义

### 6.4 后果

| 正面 | 负面 |
|------|------|
| 小变更快速处理 | 需要控制 patch 累积 |
| 大变更受控 | 回流 FRZ 增加成本 |
| 流速与可控兼顾 | clean rebase 需要人工介入 |

---

## 7. 决策：三轴管理强度 — 需求强、实施弱、证据轻

### 7.1 决策

系统存在三轴，采用不同管理强度：

#### 需求轴（强 SSOT）

- SRC / EPIC / FEAT
- semantics（user_story / AC 等）
- 冻结 + 版本 + 变更流程
- 由 ADR-045 / ADR-049 治理

#### 实施轴（弱管理）

仅记录执行状态：

```yaml
task_id: TASK-xxx
status: pending | running | done | failed
```

- 不纳入 SSOT 链
- 不做复杂建模
- 仅作为执行进度的轻量追踪

#### 证据轴（轻挂载）

仅要求绑定关系：

```yaml
verifies: AC-xxx
evidence_ref: artifacts/tests/evidence/xxx
```

- 不做复杂证据建模
- 证据格式由 ADR-047 定义
- 仅要求可追溯、可验证

### 7.2 为什么不一律强管理

- 需求轴是真相源，必须严格控制
- 实施轴变化频繁，强管理会拖慢执行
- 证据轴的核心价值是绑定关系，不是结构复杂度
- 三轴一律强管理会导致系统过重，执行效率下降

### 7.3 后果

| 正面 | 负面 |
|------|------|
| 避免系统过重 | 实施信息结构较弱 |
| 保持执行效率 | 实施变更追溯较弱 |
| 聚焦核心治理对象 | 需防止实施轴演变为第二 SSOT |

---

## 8. 决策：Task Pack + 顺序执行循环（替代复杂编排）

### 8.1 决策

不构建复杂调度系统，采用：

> **任务队列 + 顺序执行循环（loop）**

```text
tasks.yaml
   ↓
loop:
  取一个可执行 task
  → 执行
  → 双链测试
  → 更新状态
  → 下一轮
```

### 8.2 与 ADR-018 的关系

ADR-018 定义了 Execution Loop Job Runner 的抽象，本条定义具体的使用模式：
- ADR-018 提供运行时基础设施
- 本条定义 Task Pack 结构、执行顺序、失败处理

### 8.3 Task Pack 结构

```yaml
task_pack:
  pack_id: PACK-xxx
  feat_ref: FEAT-xxx
  tasks:
    - task_id: TASK-xxx
      type: impl | test | review
      depends_on: [TASK-yyy]
      status: pending
```

### 8.4 执行规则

- 不做复杂 DAG
- 不做并发调度
- 控制同时未完成任务数量（默认 ≤ 1）
- 失败 task 暂停 loop，等待人工介入
- 每个 task 完成后触发双链验证（如适用）

### 8.5 后果

| 正面 | 负面 |
|------|------|
| 极高稳定性 | 并发能力弱 |
| 实现成本极低 | 不是最优调度 |
| 易于调试和追溯 | 大任务执行时间较长 |

---

## 9. 协同规则

### 9.1 本 ADR 与已有 ADR 的关系

```
                    ┌─ ADR-045 (FRZ 冻结层)
                    │
本 ADR-050 ────────┼─ ADR-047 (双链测试)
    (总纲)          │
                    ├─ ADR-049 (Experience Patch)
                    │
                    └─ ADR-018 (Execution Loop)
```

### 9.2 冲突解决

- 本 ADR 与已有 ADR 冲突时，已有 ADR 优先（已有 ADR 经过更详细的评审）
- 本 ADR 仅在已有 ADR 未覆盖的灰色地带作出决策
- 若未来已有 ADR 修订后与本 ADR 冲突，以已有 ADR 为准

### 9.3 执行优先级

当多个 ADR 同时适用时，执行顺序：
1. FRZ 冻结检查（ADR-045）
2. 语义稳定性判断（本 ADR §5）
3. 变更分级（本 ADR §6 + ADR-049）
4. Task Pack 执行（本 ADR §8）
5. 双链验证（ADR-047）

---

## 10. 不采纳的方案

### 10.1 SSOT 继续逐层生成

不采纳原因：语义漂移不可控，与高质量前置文档重复。

### 10.2 执行层可自由修改语义

不采纳原因：SSOT 漂移、测试目标不稳定、AI 重新澄清需求导致语义污染。

### 10.3 三轴一律强 SSOT 管理

不采纳原因：系统过重，执行效率下降，实施轴信息变化过快不适合强结构。

### 10.4 复杂 DAG 调度 + 并发执行

不采纳原因：实现复杂、不稳定、当前阶段不需要。顺序 loop 足够稳定且易调试。

---

## 11. 最终决策摘要

本 ADR 作出以下决策：

1. **FRZ 定义**：raw-to-src 生成，MSC 五维度校验，存放 artifacts/（§3）
2. **SSOT 改为语义抽取**：从 FRZ 分层抽取，不逐层生成（§4）
3. **执行层语义稳定**：只能补全，不能改变语义（§5）
4. **变更分级协同**：visual/interaction → Minor，semantic → Major（§6）
5. **三轴管理强度**：需求强、实施弱、证据轻（§7）
6. **Task Pack 顺序执行**：不做复杂编排，loop 驱动（§8）
7. **与已有 ADR 协同**：ADR-045/047/049/018 各司其职，本 ADR 填补灰色地带（§9）

---

## 12. 一句话原则

> **前置 FRZ 统一语义 → SSOT 结构化表达 → Task Pack 驱动执行 → 双链验证收敛 → 变更分级回流治理：快在 execution，稳在 semantics，轻在 implementation，重在 evidence。**
