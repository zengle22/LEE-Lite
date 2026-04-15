# Problem Solving Session: Experience Patch Layer for SSOT Governance

**Date:** 2026-04-15
**Problem Solver:** shadowyang-42
**Problem Category:** Process / SSOT Governance / UX Change Management

---

## 🎯 PROBLEM DEFINITION

### Initial Problem Statement

体验期高频碎改（按钮位置、文案、页面跳转、交互微调等）在当前 SSOT 体系中无处安放：
- 直接改代码 → SSOT 漂移 → AI 基于旧规范生成时覆盖已有优化
- 每次先改 SSOT → 流程过重 → 体验迭代速度大幅下降
- 缺少变更分层 → visual / interaction / semantic 改动混在一起处理
- 测试链不同步 → Harness 按旧路径验证，产生假通过/假失败

### Refined Problem Statement

**在"SSOT 作为长期真相源"与"体验期需要快速试错"之间存在治理空白，需要一个轻量中间层来：**
1. 承接高频细粒度改动，允许代码先行但不留痕
2. 按变更影响程度分类（visual / interaction / semantic），差异化决定回写目标和时机
3. 当变更影响用户路径时，驱动 TESTSET 同步更新
4. 建立结算机制，防止 Patch 层堆积成为第二套真相系统

### Problem Context

- 现有 SSOT 体系：RAW → SRC → EPIC → FEAT → (UI/TECH/API) → IMPL → TESTSET → RELEASE_NOTE
- 46+ ADR 已覆盖架构决策
- 治理模式：每个 artifact 有明确生命周期和关联关系
- 当前缺失：体验期高频碎改的中间治理层
- 用户交互模式：在 Claude Code 中执行 skill，无手动 CLI 环节

### Success Criteria

1. SSOT 漂移率降低：AI 生成不再因过时而覆盖已有优化
2. 测试链同步：影响用户路径的 Patch 自动触发 TESTSET 更新
3. 迭代速度不降：体验期改动不被重流程阻塞
4. 变更分层清晰：visual / interaction / semantic 各有明确处理路径
5. 高层 SSOT 保持干净：视觉噪声不污染产品真相层

---

## 🔍 DIAGNOSIS AND ROOT CAUSE ANALYSIS

### Problem Boundaries (Is/Is Not)

| 维度 | IS (问题所在) | IS NOT (不是问题) |
|------|-------------|-----------------|
| 阶段 | 体验验证期、UI review 阶段 | 初期需求定义阶段、正式发版后 |
| 变更类型 | 高频、细粒度、低门槛 | 新 FEAT 开发、重大架构变更 |
| 影响范围 | 单页面、单模块、局部交互 | 跨模块、影响状态机/数据模型 |
| 谁受影响 | 体验设计师、前端开发、AI 生成器 | 后端架构、API 契约层 |
| 表现形式 | 代码新、SSOT 旧、测试旧 | 完全没代码改动、或完全按 SSOT 走 |

**模式识别：** 问题集中在"SSOT 已定型 → 代码已实现 → 体验验证中"这个阶段的尾部微调。

### Root Cause Analysis

使用 **Five Whys** + **Systems Thinking** 诊断：

1. **Why:** AI 基于旧 SSOT 生成代码会覆盖体验优化？
   → 因为体验改动只留在代码层，没回写 SSOT

2. **Why:** 体验改动没回写 SSOT？
   → 因为回写流程太重，每条碎改都要更新 FEAT/UI/TECH/TESTSET

3. **Why:** 回写流程重？
   → 因为当前没有"轻量留痕"的中间产物，要么全写要么不写

4. **Why:** 没有中间产物？
   → 因为 SSOT 体系设计时关注的是"正式规范"，没预留"体验验证期临时记录"的位置

5. **Why (root):** 治理模型缺少"变更影响度分层"机制，所有变更被当作同等重要程度处理

### Contributing Factors

1. **流程粒度不匹配：** SSOT artifact 的设计粒度 > 体验碎改粒度
2. **回写成本过高：** 更新一个按钮位置需要修改多个 artifact
3. **缺少分类标准：** 没有 formal 的方式区分"改个颜色"和"改业务规则"
4. **测试链脱节：** 体验改动不影响 TESTSET 的定义，但实际影响验证路径
5. **AI 工程特殊性：** 人类可以记住改了什么，AI 只看 SSOT，SSOT 失真 = AI 失明

### System Dynamics

```
体验改动 → 改代码(快) → 不回写(省时间) → SSOT变旧 → AI基于旧SSOT生成 → 覆盖优化 → 返工
    ↑                                                              |
    |____________________________________ 人记得住，AI记不住 _______|

引入 Patch 层后：
体验改动 → 改代码 + 记 Patch → SSOT仍准 → AI读取Patch → 生成兼容 → 定期结算回写
```

---

## 📊 ANALYSIS

### Force Field Analysis

**Driving Forces (Supporting Solution):**
- 已经有成熟的 SSOT 体系作为基础，Patch 层只需"挂在上面"而非重建
- AI 工程实践天然适合结构化数据（YAML Patch），可以自动化处理
- 痛点明确且高频，投资回报率高
- 你已经有 artifact taxonomy 和生命周期管理的经验可复用

**Restraining Forces (Blocking Solution):**
- 新增一层治理对象 → 维护成本增加
- 若结算纪律不足 → Patch 层变成第二真相系统
- 工具链需要适配（patch registry, patch-aware harness, backwrite tooling）
- 需要改变团队（人+AI）的工作习惯

**最强力量：** AI 工程特殊性（SSOT 失真直接影响生成质量）是最强驱动力；工具链适配是最大阻力。

### Constraint Identification

1. **必须兼容现有 SSOT 体系：** Patch 不能破坏 artifact taxonomy
2. **不能增加过多流程负担：** 否则回归到"每次先改 SSOT"的问题
3. **必须有强制结算机制：** 否则 Patch 堆积
4. **必须与测试联动：** 否则 Harness 失真
5. **必须对 AI 可读：** AI 需要知道当前正式规则 + 已接纳 Patch

### Key Insights

1. **核心矛盾不是"快 vs 规范"，而是"粒度不匹配"** — SSOT 的粒度太大，装不下体验碎改
2. **"代码先行"不是问题，"无痕"才是问题** — 关键是留痕，不在于先后顺序
3. **三层分类（visual/interaction/semantic）是核心设计** — 它决定了哪些可以停留在轻量层，哪些必须升级
4. **测试链联动是最大价值点之一** — 当前最大的损失是测试验证失真
5. **Patch 层的最大风险不是"多了一层"，而是"变成第二真相系统"** — 必须有明确的结算纪律

---

## 💡 SOLUTION GENERATION

### Methods Used

- **Morphological Analysis** — 系统探索 Patch 层各维度的组合方案
- **Assumption Busting** — 挑战"必须先改 SSOT"和"所有改动都要进高层"的假设

### Generated Solutions

| # | 方案 | 描述 | 适用场景 |
|---|------|------|---------|
| A | **Experience Patch Layer (ADR 方案)** | 轻量 YAML Patch + 分类 + 结算 + 测试联动 | 全面解决 |
| B | **SSOT 增量更新** | 给现有 artifact 增加 `patch` 状态，不改目录结构 | 最小改动 |
| C | **Commit Message 治理** | 用约定式提交标记体验改动，git 即 Patch | 最轻量 |
| D | **AI Context Overlay** | 不改任何产物，在 AI 生成前注入上下文文件 | 纯 AI 向 |
| E | **UI Diff Registry** | 只记录 UI 层变更，不回写 SSOT 主规范 | 仅视觉层 |

### Creative Alternatives

1. **Patch-as-Code-Comment:** 用特殊格式的 code comment 标记体验改动，工具自动扫描
2. **Session-Based Patch:** 每次 Claude Code session 自动输出 session_diff.yaml，人工审核
3. **Dual-Mode SSOT:** SSOT 本身支持 `stable` + `experimental` 两个通道，不需要额外产物

---

## ⚖️ SOLUTION EVALUATION

### Evaluation Criteria

| 标准 | 权重 | 说明 |
|------|------|------|
| 解决 SSOT 漂移 | 25% | 核心痛点 |
| 测试链同步 | 20% | 第二大痛点 |
| 流程负担 | 20% | 不能比现在更重 |
| 与现有体系兼容 | 15% | 不破坏 artifact taxonomy |
| AI 可读性 | 10% | AI 能解析并利用 |
| 实施成本 | 10% | 工具链工作量 |

### Solution Analysis

| 方案 | SSOT漂移(25) | 测试同步(20) | 流程负担(20) | 兼容性(15) | AI可读(10) | 成本(10) | 总分 |
|------|-------------|-------------|-------------|-----------|-----------|---------|------|
| A: EPL (ADR) | 5/5 | 5/5 | 3/5 | 4/5 | 5/5 | 3/5 | **75.5** |
| B: SSOT增量 | 4/5 | 3/5 | 4/5 | 5/5 | 4/5 | 4/5 | **68.0** |
| C: Commit治理 | 3/5 | 1/5 | 5/5 | 5/5 | 2/5 | 5/5 | **54.0** |
| D: AI Overlay | 2/5 | 1/5 | 5/5 | 5/5 | 5/5 | 5/5 | **54.5** |
| E: UI Diff | 3/5 | 2/5 | 4/5 | 4/5 | 4/5 | 4/5 | **56.5** |

### Recommended Solution

**方案 A: Experience Patch Layer (ADR 方案)** — 得分最高

### Rationale

1. **唯一同时解决四个痛点的方案：** SSOT 漂移 + 测试同步 + 流程负担 + 变更分层
2. **三层分类是核心价值：** 区分 visual/interaction/semantic 让差异化治理成为可能
3. **YAML 结构化数据天然适合 AI 处理：** 比 commit message 或 code comment 更可靠
4. **风险可控：** 最大风险（第二真相系统）可通过结算机制化解
5. **可渐进实施：** 先跑通最小闭环，再扩展工具链

**需关注的改进点：**
- 流程负担评分 3/5 — 需确保 Patch 登记足够轻量（理想情况：AI 自动生成，人工审核）
- 实施成本 3/5 — 需要开发 patch registry / backwrite tooling，但可分阶段

---

## 🚀 IMPLEMENTATION PLAN

### Implementation Approach

**分阶段实施，MVP → 完整 → 自动化：**

**Phase 1: MVP（最小可行）**
- 定义 Patch YAML schema
- 确定目录结构（推荐挂在 FEAT 下）
- 人工登记 Patch
- 手动结算

**Phase 2: 工具链**
- Patch 自动生成（AI 检测代码变更 → 建议 Patch）
- Patch 索引/查询
- 结算辅助工具

**Phase 3: 集成**
- Patch-aware Harness
- 自动回写 SSOT 草稿
- 审计告警

### Action Steps

| # | 步骤 | 依赖 | 产出 |
|---|------|------|------|
| 1 | 审批 ADR 草案，确认分类模型和回写规则 | — | 批准的 ADR |
| 2 | 定义 Patch YAML schema（完整版） | Step 1 | schema 文件 |
| 3 | 创建目录结构和命名规范 | Step 2 | `.artifacts/FEAT-XXX/experience-patches/` |
| 4 | 定义 Patch 生命周期管理规则 | Step 2 | 生命周期规范 |
| 5 | 将 Patch 纳入 SSOT artifact 关联关系 | Step 3, 4 | 更新 artifact taxonomy |
| 6 | 创建 Patch 登记 skill / 命令 | Step 3 | CLI 或 skill |
| 7 | 定义测试联动规则（Patch → TESTSET） | Step 2 | 测试联动规范 |
| 8 | 实现 Patch 自动生成（AI 检测 diff） | Step 6 | 自动登记 |
| 9 | 实现结算工具（批量回写） | Step 6, 7 | 结算命令 |
| 10 | Patch-aware Harness 集成 | Step 7, 9 | 测试适配 |

### Resource Requirements

- 1 份 ADR 审批
- YAML schema 设计
- 目录结构创建
- Skill/CLI 开发（Patch 登记 + 结算）
- TESTSET 联动逻辑
- Harness 适配

### Responsible Parties

- **产品决策:** shadowyang-42（审批 ADR、确认分类模型）
- **Schema 设计:** AI + 人工审核
- **工具开发:** AI 主导（skill 开发）
- **测试联动:** 需要理解现有 TESTSET 结构

---

## 📈 MONITORING AND VALIDATION

### Success Metrics

| 指标 | 目标 | 测量方式 |
|------|------|---------|
| SSOT 漂移率 | < 5% | 对比代码与 SSOT 的一致性 |
| Patch 平均存活时间 | < 3 天 | 从 active 到 resolved |
| pending_backwrite 堆积数 | < 5 per FEAT | Patch 索引统计 |
| 测试失真率 | 0% | 假通过/假失败数 |
| Patch 登记轻量度 | < 30 秒/条 | 人工操作时间 |

### Validation Plan

1. **选择一个 FEAT 试点：** 用真实体验改动跑通 Patch 全流程
2. **验证分类准确性：** visual / interaction / semantic 分类是否直觉且无歧义
3. **验证回写可行性：** 实际执行一次结算，确认回写路径畅通
4. **验证 AI 兼容性：** AI 基于"SSOT + Patch"生成代码，不覆盖已有优化

### Risk Mitigation

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Patch 堆积不清算 | 中 | 高 | 强制结算触发条件 + 告警 |
| 分类标准模糊 | 中 | 中 | 提供决策树 + 示例 |
| 增加流程负担 | 低 | 高 | AI 自动登记，人工只审核 |
| 与现有 artifact 冲突 | 低 | 高 | Patch 挂 FEAT 下，不新建顶层类型 |
| 测试链更新遗漏 | 中 | 高 | test_impact 必填 + 审计检查 |

### Adjustment Triggers

- Patch 平均存活时间 > 7 天 → 加强结算纪律
- 同一 FEAT 的 Patch 数 > 10 → 触发强制结算
- AI 仍基于旧 SSOT 生成 → 检查 Patch 是否被 AI 读取
- 出现假通过/假失败 → 检查 test_impact 声明完整性

---

## 📝 LESSONS LEARNED

### Key Learnings

1. **治理的核心不是控制，而是分级** — 不是所有改动都需要同等对待
2. **AI 工程体系中，"留痕"比"先后顺序"更重要** — 人类可以记住改动，AI 依赖结构化数据
3. **中间层的价值在于"缓冲"而非"替代"** — Patch 层必须明确自己是临时状态，不是最终真相

### What Worked

- 用 Three-Whys 快速定位到根因：粒度不匹配，而非流程本身有问题
- Force Field 分析清晰识别了最强驱动力（AI 工程特殊性）和最大阻力（工具链适配）

### What to Avoid

- 避免把 Patch 层设计得太重 — 它是缓冲层，不是新规范体系
- 避免把所有 Patch 都升级为正式 SSOT 变更 — 高层规范需要保持抽象性
- 避免只解决"登记"不解决"结算" — 没有结算的 Patch 层必然腐化

---

_Generated using BMAD Creative Intelligence Suite - Problem Solving Workflow_
