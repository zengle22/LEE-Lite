# ADR-049：引入体验修正层（Experience Patch Layer）以承接产品体验阶段的高频细粒度变更

> **SSOT ID**: ADR-049
> **Title**: 引入体验修正层（Experience Patch Layer）以承接产品体验阶段的高频细粒度变更
> **Status**: Frozen
> **Version**: v2.1 (终审修订版)
> **Effective Date**: 2026-04-15
> **Last Revised**: 2026-04-15
> **Scope**: SSOT 变更治理 / UX 变更管理 / 双路径分流
> **Owner**: 产品 / 质量治理
> **Governance Kind**: NEW
> **Audience**: 产品、前端、AI 实施代理、测试
> **Depends On**: ADR-047 (双链治理), ADR-048 (SSOT 与 Droid 接入)

---

## 1. 背景

### 1.1 One-Sentence Summary

> **体验变更分两条路径：小变更走 Patch 层（代码先行、留痕缓冲），大变更走新 SRC 链（完整治理），各走各的路径，互不干扰。**

### 1.2 双路径分流模型

用户在体验产品或审查功能时，会产生两类变更行为：

**路径一：小变更（Prompt-to-Patch）**
- 粒度细：按钮位置、文案优化、间距调整、默认展开逻辑等
- 频率高：一轮体验可能产生 10-20 条
- 描述简单：一个 prompt 就能说清楚
- 不影响业务语义、状态机、数据含义
- 处理方式：prompt 给 agent + 自动调 skill 记录 Patch

**路径二：大变更（Document-to-SRC）**
- 需要前置讨论：调用 BMAD / Superpowers / OMC 等工具
- 产出结构化文档：多份 PRD、架构、设计文档
- 影响用户能力、页面流转、业务规则
- 处理方式：直接新建 SRC，走完整 EPIC → FEAT → ... 链

### 1.3 为什么需要这个 ADR

当前 SSOT 体系已经建立完整治理流程，但在"体验期碎改"场景下存在明显张力：

| 痛点 | 根因 | 本 ADR 解决方式 |
|------|------|----------------|
| SSOT 漂移 → AI 基于旧规范覆盖优化 | 小变更直接改代码不留痕 | Patch 层留痕 + AI 读取 |
| 测试链不同步 → Harness 按旧路径验证 | 体验改动未触发 TESTSET 更新 | test_impact 强制声明 |
| 流程摩擦影响迭代速度 | 所有变更被同等处理 | 双路径分流 |
| 变更分层不清 | 没有分类标准 | 三层分类模型 |

### 1.4 根因分析

经 Five Whys 诊断，根因是**治理粒度不匹配**：SSOT artifact 的设计粒度 > 体验碎改粒度。不是流程本身有问题，而是缺少中间层来承接小粒度变更。

---

## 2. 决策

### 2.1 引入 Experience Patch Layer（EPL）作为小变更缓冲层

EPL 位于**代码实现层**与**正式 SSOT 主规范层**之间，仅承接**小变更**。

职责：
1. 承接体验阶段产生的高频细粒度改动
2. 允许**代码先行、留痕缓冲**（窗口期最长 24h）
3. 对变更进行结构化分类
4. 按规则决定是否、何时、回写到哪一层 SSOT
5. 当变更影响测试路径时，驱动 TESTSET 同步更新

### 2.2 大变更直接走新 SRC 链

对于需要前置讨论/设计文档的大变更，**不在 Patch 层处理**，直接新建 SRC 候选，走完整治理流程。这是现有 SRC 体系惯例的延续（当前 8 个 SRC 均为 frozen，更新时新建而非修改）。

### 2.3 两条路径的对比

| 维度 | 路径一：小变更（Patch） | 路径二：大变更（SRC） |
|------|------------------------|----------------------|
| 入口 | prompt to agent | BMAD/Superpowers/OMC 文档 |
| 记录方式 | skill 自动记 Patch | 新建 SRC（候选） |
| 审批 | 人工确认即可 | 走 Gate 审批 |
| 去向 | Patch 层缓冲 → 定期结算 | 完整 SSOT 链（EPIC → FEAT → ...） |
| 测试联动 | Patch 标记 test_impact | TESTSET 随新链生成 |
| AI 上下文 | 读取 SSOT + active Patch | 读取完整 SSOT 链 |
| 产物格式 | 轻量 YAML（结构化记录） | 完整 SRC YAML（治理文档） |

### 2.4 路径选择决策树

> **设计说明（H4 修订）**：决策树改为基于变更属性的判断，不依赖工具链知识。
> **终审修订**：两个顶级检查为**独立门控**，任一指向 SRC 即走 SRC。

```
体验变更
    │
    ┌─ 门控 1：是否影响业务规则/状态机/数据含义？
    │   ├─ 是 → 路径二：SRC
    │   └─ 否 → 继续
    │
    ┌─ 门控 2：是否需要多方利益相关者对齐？
    │   ├─ 是 → 路径二：SRC
    │   └─ 否 → 继续
    │
    ┌─ 门控 3（最终判断）：是否仅影响视觉/文案/布局？
        ├─ 是 → 路径一：Patch（visual）
        └─ 否 → 是否影响页面跳转/入口位置/操作顺序？
                   ├─ 是 → 路径一：Patch（interaction）
                   └─ 否 → 路径一：Patch（visual）
```

> **说明**：门控 1 和门控 2 为独立检查。若任意一个触发 SRC，无需继续后续判断。

---

## 3. 核心决策原则

### 3.1 SSOT 仍然是长期真相源

本 ADR **不改变** SSOT 作为正式系统真相源的地位。所有 SRC 仍然 frozen，更新时新建而非修改。

### 3.2 小变更：代码先行、Patch 留痕、24h 窗口期结算

对小变更采用：
- 先在代码中快速验证
- 同时通过 PreToolUse hook skill 自动记录到 Patch 层
- **Patch 窗口期最长 24h**，超期自动 blocking

> **代码可热修，但不得无痕；可以延迟回写，但不得超过 24h。**

### 3.3 大变更：新建 SRC，走完整治理

对大变更：
- BMAD/Superpowers/OMC 产出文档作为 SRC 的 source_artifact
- 创建新 SRC 候选
- Gate 审批通过后 frozen
- 走完整 EPIC → FEAT → ... 链

### 3.4 AI 必须能读取 Patch — 通过 PreToolUse Hook 强制注入

> **设计说明（C4 修订）**：不依赖 AI 记忆或 prompt 注入，通过 PreToolUse hook 在代码写入前强制触发 Patch context 注入。

Patch 层的核心价值之一是防止 AI 基于旧 SSOT 覆盖已有优化。因此：
- 实现为 **PreToolUse hook skill**，在 `Edit` / `Write` 工具调用前自动触发
- Hook 扫描目标文件所属 FEAT 下的 active Patch，注入到 AI 上下文
- AI 生成代码时自动兼容"SSOT + active Patch"的组合规则
- 仅加载与当前编辑文件相关的 Patch（按 `changed_files` 匹配），避免 context 膨胀（H7 修订）

### 3.5 不是所有改动都应进入高层 SSOT

纯表现层小修正不要求全部进入 FEAT / TECH / 上游主规范。它们可以停留在 Patch 层或 UI 细则层，无需污染高层产品定义。

---

## 4. 变更分类模型

体验期变更统一分为三类：

### 4.1 Visual Patch（表现层修正）

**定义**：仅影响视觉呈现或局部布局，不改变业务语义和核心交互规则。

**示例**：
- 按钮颜色/尺寸/位置微调（仅调整 CSS 属性，不改变 DOM 层级或交互路径）
- 文案优化（不改变字段含义或验收标准）
- 间距调整、图标替换
- 默认视觉排序优化
- 样式对齐修复

**边界说明（H3 修订）**：以下情况**不是** Visual：
- 按钮位置移动导致用户操作路径改变 → **Interaction**
- 文案改变影响验收标准或字段含义 → **Semantic**
- 元素从隐藏变为常驻，改变可达性 → **Interaction**

**处理原则**：
- 可直接改代码
- 必须记录 Patch（skill 自动）
- 不要求回写高层 SSOT
- 必要时仅更新 UI 细则或组件规范

### 4.2 Interaction Patch（交互层修正）

**定义**：影响用户操作路径、页面关系、入口位置、动作顺序，但尚未改变底层业务模型。

**示例**：
- 页面 A 不再跳 B 而是跳 C
- 按钮从二级菜单前置到一级操作区
- 表单提交前增加确认步骤
- 某入口由隐藏改为常驻
- 页面流程顺序变化

**边界说明（H3 修订）**：以下情况**不是** Interaction：
- 仅改变按钮颜色/大小，不改变操作路径 → **Visual**
- 新增正式用户动作或修改业务规则 → **Semantic**

**处理原则**：
- 可先改代码验证
- 必须记录 Patch
- 必须回写：UI Spec、页面流转图/交互规则文档
- 必要时更新 TESTSET / TC / 验收描述

### 4.3 Semantic Patch（语义层修正）

**定义**：影响产品能力、业务规则、状态、数据语义、输入输出定义或验收口径。

**示例**：
- 新增正式用户动作
- 修改状态机
- 修改字段含义或数据流
- 某操作从可选变为必经
- 训练计划调整逻辑变化
- 用户反馈闭环规则变化

**处理原则**：
- **不应长期停留在 Patch 层**
- 应升级为新建 SRC，走完整治理流程
- 至少需要更新：FEAT、UI、TECH、API（如有）、TESTSET / TC / REPORT 验收口径

### 4.4 分类与回写目标的自动映射

```
change_class      →  must_backwrite_ssot  →  backwrite_targets
────────────────────────────────────────────────────────────────
visual            →  false                 →  [UI 细则（可选）]
interaction       →  true                  →  [UI Spec, Flow Spec, TESTSET（如 test_impact）]
semantic          →  true                  →  [新建 SRC]（升级为完整治理）
```

> **重要（H6 修订）**：`change_class`、`test_impact`、`backwrite_targets` 由 AI 预填，但标记为 **human-reviewed** 字段，必须由人工确认或修改后才可入库。AI 不得自动提交。

### 4.5 AI 分类分歧解决规则（H3 修订）

当 AI 建议的分类与人工判断不一致时：
1. 人工判断优先
2. AI 记录分歧原因到 Patch 的 `source.notes` 字段
3. 若分歧频繁出现（同一用户 3 次以上），AI 调整分类决策树的权重

---

## 5. Patch 产物设计

### 5.1 目录结构

> **设计说明（C1 修订）**：当前 FEAT artifact 是 flat `.md` 文件（如 `ssot/feat/FEAT-SRC-001-001__mainline-collaboration-loop.md`），不是目录。为避免破坏性迁移，Patch 存放在**独立目录**，通过 `feat_ref` 字段关联。

```
ssot/
  experience-patches/
    FEAT-SRC-001-001/
      UXPATCH-0001__move-regenerate-button-to-primary-action.yaml
      UXPATCH-0002__change-plan-detail-submit-confirm-flow.yaml
    FEAT-SRC-003-001/
      UXPATCH-0001__xxx.yaml
```

**选择独立目录的原因**：
- 无需迁移现有 23 个 FEAT 文件从 flat 到目录结构
- 通过 `feat_ref` 字段建立关联，保持查询简单
- 按 FEAT 范围结算不受影响
- 对现有 artifact taxonomy 零侵入

### 5.2 Patch 冲突检测（H1 修订）

同一 FEAT 下可能出现多个 Patch 修改同一文件/模块。处理规则：

1. **登记时检测**：新 Patch 登记时，AI 扫描同 FEAT 下 active/validated Patch 的 `changed_files`，若存在重叠则标记 `conflict: true`
2. **冲突解决**：以最新 Patch 为准，旧 Patch 自动标记为 `superseded` → 结算时 discard
3. **同源冲突**：若两个 Patch 由同一轮体验产生且互斥，人工决定保留哪个
4. **跨文件无冲突**：修改不同文件的 Patch 可并行存在

### 5.3 Patch YAML Schema

```yaml
id: UXPATCH-0001                              # 序列号，目录内自增
type: experience_patch
status: draft                                 # 新建时从 draft 开始
created_at: 2026-04-15T10:30:00+08:00
updated_at: 2026-04-15T10:30:00+08:00

title: Move regenerate button to primary action area
summary: 将"重新生成计划"按钮前置到训练计划详情页主操作区

source:
  from: product_experience
  actor: human                                # human | ai_suggested
  session: ux-review-2026-04-15
  prompt_ref: "把重新生成按钮放到主操作区"       # 原始 prompt 快照
  ai_suggested_class: interaction             # AI 建议的分类
  human_confirmed_class: interaction          # 人工确认的分类（必填）

scope:
  feat_ref: FEAT-SRC-001-001                  # 关联的 FEAT ID
  ui_ref: UI-FEAT-SRC-001-001                 # 如有
  tech_ref: TECH-SRC-001-001                  # 如有
  page: training_plan_detail
  module: plan_adjustment

change_class: interaction                     # visual | interaction | semantic（human-reviewed）
severity: medium                              # low | medium | high

conflict: false                               # 是否与同 FEAT 其他 Patch 冲突（H1）
conflict_details: null                        # 如冲突，记录冲突的 Patch ID 和解决方式

problem:
  user_issue: 用户在详情页不容易发现"重新生成"动作
  evidence: 体验过程中多次漏点该按钮

decision:
  code_hotfix_allowed: true
  must_backwrite_ssot: true                   # 自动根据 change_class 推导（human-reviewed）
  backwrite_targets:                          # 自动根据 change_class 推导（human-reviewed）
    - UI-FEAT-SRC-001-001
    - TESTSET-SRC-001-001
  backwrite_deadline: 2026-04-16T10:30:00+08:00  # interaction: 24h; semantic: 立即升级SRC

implementation:
  code_changed: true
  changed_files:
    - apps/web/src/pages/training-plan/detail.tsx
    - apps/web/src/components/plan/PlanActionBar.tsx

test_impact:                                  # human-reviewed
  impacts_user_path: true                     # interaction/semantic 默认 true
  impacts_acceptance: true
  impacts_existing_testcases: true
  affected_routes:                            # （H8 修订）AI 必须列出变更的 route
    - /training-plan/:id/detail
  test_targets:
    - TC-FEAT-SRC-001-001-PLAN-DETAIL-ACTION
    - TC-FEAT-SRC-001-001-PLAN-REGENERATE-FLOW

related_ids:                                  # 由文件系统确定性查找填充，非 AI 推断
  - FEAT-SRC-001-001
  - UI-FEAT-SRC-001-001
  - TESTSET-SRC-001-001

resolution:
  backwrite_status: pending                   # pending | backwritten | discarded | upgraded_to_src | superseded
  merged_into_ssot_at: null
  src_created: null                           # 如升级为 SRC，记录 SRC ID
  closed_at: null
```

### 5.4 Patch ID 命名规范

> **简化（架构评审反馈）**：ID 不再嵌入完整 FEAT ID（文件名已通过目录关联），仅保留序列号。

```
UXPATCH-{SEQUENCE}__{slug-description}

示例：
ssot/experience-patches/FEAT-SRC-001-001/UXPATCH-0001__move-regenerate-button.yaml
ssot/experience-patches/FEAT-SRC-003-001/UXPATCH-0002__change-default-collapse.yaml
```

---

## 6. Patch 生命周期

### 6.1 状态枚举

| 状态 | 含义 | 自动迁移条件 |
|------|------|-------------|
| `draft` | 已登记，尚未验证 | AI 改代码完成 → `active` |
| `active` | 已进入实现/试改阶段 | 人工确认保留 → `validated` |
| `validated` | 体验验证通过，确认保留 | 自动触发结算评估 → `pending_backwrite` / `retain_in_code` / `discarded` |
| `pending_backwrite` | 确认需回写，尚未完成 | 回写完成 → `backwritten` |
| `backwritten` | 已完成正式规范更新 | 归档 → `archived` |
| `retain_in_code` | 保留代码，不升级 SSOT（Visual 终端状态） | 归档 → `archived` |
| `upgraded_to_src` | 已升级为 SRC（semantic Patch） | 归档 → `archived` |
| `superseded` | 被更新的 Patch 替代（冲突解决） | 归档 → `archived` |
| `discarded` | 试验后放弃 | — |
| `archived` | 已归档，不再活跃 | — |

### 6.2 生命周期流程图

```
prompt → skill 登记 → draft
                │
         agent 改代码验证
                │
              active
                │
        ┌───────┴───────┐
        │               │
   体验不通过       体验通过
        │               │
    discarded       validated
                        │
                 ┌──────┴──────────────┐
                 │                     │
          visual Patch           interaction/semantic
                 │                     │
          retain_in_code         pending_backwrite
                 │                     │
            archived          ┌────────┴────────┐
                              │                 │
                       interaction         semantic
                       回写 UI/TESTSET     新建 SRC
                              │                 │
                        backwritten      upgraded_to_src
                              │                 │
                           archived          archived

冲突分支：
  active → 冲突检测 → superseded → archived
```

### 6.3 生命周期强制规则

> **P0-1 修订**：24h 计时统一从 `validated` 开始（人工确认保留后），非 `active`。

- **窗口期上限 24h**：从 `validated` 到任何终端状态（`backwritten` / `retain_in_code` / `upgraded_to_src` / `discarded`）不得超过 24h
- **超期 blocking**：超过 24h 未结算的 Patch，其 `changed_files` 被列入 blocking list，阻止基于这些文件的进一步代码生成（C2 修订）
- **自动归档**：`archived` Patch 保留 30 天后自动清理（防止目录膨胀）
- **终端状态定义**：`backwritten`、`retain_in_code`、`upgraded_to_src`、`discarded` 均为终端状态（`resolved`）

### 6.4 异常场景处理（终审修订）

**FEAT 删除时的 Patch 清理**：
- 当一个 FEAT 被删除或合并到其他 FEAT 时，其 `ssot/experience-patches/FEAT-XXX/` 下所有非终态 Patch 自动 `discarded` → `archived`
- 已关联代码变更的 Patch 需人工确认是否需要回写到新的 FEAT

**人工直接编辑代码（无 AI 会话）**：
- 若人类直接在编辑器中修改代码（非 AI 改代码），下次 AI 会话启动时自动扫描 git diff 并生成 Patch 草案
- Patch 状态从 `draft` 开始，等待人工确认
- 此场景下 24h 计时从 `validated`（人工确认）开始，非代码编辑时间

**Interaction Patch 回写是否需要 Gate（P1 明确）**：
- Interaction Patch 回写 UI Spec / Flow Spec / TESTSET 为直接 artifact 更新，**不需要 Gate 审批**
- Semantic Patch 升级为 SRC 必须走 Gate 审批

---

## 7. 回写规则

### 7.1 可不立即回写主 SSOT 的情况

满足**全部**以下条件时，可仅保留在 Patch 层：
- 不改变用户能力
- 不改变页面流转关系
- 不改变交互规则
- 不改变业务语义
- 不影响验收路径
- 仅为视觉/文案/布局级优化（`change_class: visual`）

### 7.2 必须回写 UI / 流转 / 交互规范的情况

满足**任一**条件时（`change_class: interaction`）：
- 页面跳转关系发生变化
- 入口层级发生变化
- 主操作区动作发生变化
- 用户路径顺序发生变化
- 默认交互动作发生变化
- UI 上的关键可见性 / 可达性发生变化

### 7.3 必须升级为新 SRC 的情况

满足**任一**条件时（`change_class: semantic`）：
- 用户能力发生变化
- 业务规则发生变化
- 数据语义发生变化
- 状态机发生变化
- 输入输出定义发生变化
- 验收标准发生变化
- 测试路径或测试对象发生变化

升级路径：Patch → 创建新 SRC 候选 → Gate 审批 → frozen SRC → 完整下游链

### 7.4 Semantic Patch 升级被 Gate 拒绝时的回滚路径（H2 修订）

若 semantic Patch 升级生成的 SRC 被 Gate 拒绝：
1. Patch 状态置为 `discarded`
2. AI 生成回滚方案：将 `changed_files` 恢复到 Patch 前的状态（通过 git revert 或代码分析）
3. 人工审核回滚方案后执行
4. 回滚完成后 → `archived`

---

## 8. 结算机制

### 8.1 结算触发条件

满足**任一**条件时，必须进行 Patch 结算：
- 一轮集中体验结束
- 一个 FEAT 进入下一阶段开发前
- 准备进行重新生成 / 大规模重构前
- 准备交付测试前
- 准备冻结版本前
- Patch 数量超过阈值（单 FEAT 超过 10 条）
- `validated` Patch 超过 24h 未结算

### 8.2 结算动作

对每条 Patch 做四选一处理：

| 动作 | 适用场景 | 结果 |
|------|---------|------|
| `discard` | 试验无效 | → `discarded` → `archived` |
| `retain_in_code` | 仅表现层细节（visual 终端状态） | 保留代码，不升级 SSOT → `retain_in_code` → `archived` |
| `backwrite_ui` | 交互层修正 | 回写 UI spec / flow spec / TESTSET → `backwritten` → `archived` |
| `upgrade_to_src` | 语义层修正 | 新建 SRC，走完整治理 → `upgraded_to_src` → `archived` |

> **P1 补充**：增加批量操作 `bulk-upgrade-to-src`（多条语义 Patch 合并生成一个 SRC）和 `merge-patches`（同 FEAT 同模块的多条 Patch 合并为一条）。

### 8.3 批量结算操作（C3 修订）

为避免结算疲劳，支持以下批量操作：

| 批量操作 | 适用场景 | 说明 |
|----------|---------|------|
| `approve-by-class` | 按 change_class 批量处理 | 如"所有 visual → retain_in_code" |
| `approve-all-validated` | 所有已验证 Patch | 批量标记为 validated |
| `discard-all-superseded` | 冲突已被替代的 Patch | 一键清理 |
| `snooze` | 不确定的 Patch | 延迟 24h 后再结算 |
| `auto-settle-visual` | 纯视觉 Patch 集中处理 | visual 类自动 retain_in_code |
| `bulk-upgrade-to-src` | 多条语义 Patch | 合并生成一个 SRC，而非每条一个 |
| `merge-patches` | 同 FEAT 同模块多条 Patch | 合并为一条后再 backwrite |
| `approve-by-feat` | 阶段结束清理 | 一键结算某 FEAT 下所有 Patch |

> **AI 辅助**：结算时 AI 自动按 change_class 分组展示，建议批量操作，人工只需确认。

### 8.4 结算节奏

| 节奏 | 触发 | 动作 |
|------|------|------|
| 日结 | 当天体验结束 | 快速标记 discard / retain（可用批量操作） |
| 阶段结 | 一个 FEAT 体验完成 | 完整清算所有 active/validated Patch |
| 发版结 | 发版/冻结前 | 强制清空所有 `pending_backwrite` |

### 8.5 告警规则

> **收紧（C2 修订）**：窗口期从 3 天收紧到 24h。

| 条件 | 级别 | 动作 |
|------|------|------|
| validated Patch 超过 12h 未结算 | WARN | 提醒结算 |
| validated Patch 超过 24h 未结算 | ERROR | **强制 blocking**：相关 changed_files 阻止进一步代码生成 |
| pending_backwrite 超过 24h 未回写 | ERROR | 强制触发结算，必要时 blocking |
| Patch 对应代码已变更但 `related_ids` 为空 | WARN | 补全关联 |
| `test_impact=true` 但未关联 TESTSET/TC | ERROR | 阻断结算，要求补全 |

---

## 9. 用户操作流程

### 9.1 小变更（Prompt-to-Patch）

> **修订（H5）**：skill 不再需要手动调用，改为自动触发。

```
用户: "把重新生成按钮放到主操作区"
  → AI 改代码
  → PreToolUse hook 自动触发：检测到代码变更
  → AI 自动填充 Patch YAML（预填 change_class、test_impact、backwrite_targets）
  → AI 展示 Patch 草案，用户确认或修改分类
  → 用户确认后 → Patch 入库
  → 继续体验...
```

**关键约束：零手动登记步骤。** 用户不需要手动写 YAML 或调 skill。Patch 登记是 AI 改代码的副作用，通过 PreToolUse hook 自动触发（或 CLAUDE.md 规则引导 AI 自动读取），人工仅需确认分类。

> **机制澄清（终审修订）**：PreToolUse hook 在 Claude Code 中不能直接修改 AI 的上下文窗口。实际实现为双机制：
> 1. **MVP**：CLAUDE.md 规则指示 AI 在 Edit/Write 前自动读取相关 Patch 文件
> 2. **Phase 2**：PreToolUse hook 写入临时 context 文件，配合 CLAUDE.md 规则实现强制读取

### 9.2 大变更（Document-to-SRC）

```
用户: 调 BMAD/Superpowers/OMC 跑需求讨论
  → 产出结构化文档
  → AI 基于文档创建新 SRC 候选
  → Gate 审批
  → frozen → 走完整 EPIC → FEAT → ... 链
```

### 9.3 结算操作

```
用户: 调结算 skill（或自动触发）
  → AI 扫描 FEAT 下所有 active/validated Patch
  → 按 change_class 分组展示
  → AI 建议批量操作（如"3 条 visual → 建议 auto-settle-visual"）
  → 用户确认或调整
  → AI 自动执行对应动作
  → 生成结算报告
```

---

## 10. 与测试体系的衔接

### 10.1 test_impact 强制声明

Patch 元数据中必须显式声明：
- 是否影响用户路径
- 是否影响验收
- 是否影响既有 testcase
- 需要更新哪些 TESTSET / TC
- **变更影响的 routes 列表**（H8 修订）

`change_class: interaction` 和 `semantic` 默认 `test_impact: true`。

### 10.2 Interaction / Semantic Patch 不得只改 UI 不改测试

若 Patch 影响用户路径、页面跳转、默认流程、动作顺序或用户可见状态，必须：
- 更新 TESTSET
- 必要时重写/新增 TC
- 在 REPORT / EVI 中按新路径采证

### 10.3 Harness 验证"SSOT + validated/Pending Patch"的冲突解决规则（C5 修订）

在 Patch 尚未回写期间，若其已被确认为保留方案，测试执行应遵循以下优先级规则：

1. **SSOT 是基线**：正式 SSOT 规则始终生效
2. **validated/pending Patch 覆盖 SSOT**：在 Patch 的 scope 范围内（page + module），Patch 规则优先于 SSOT 规则
3. **多个 Patch 冲突**：以最新 `validated` 状态的 Patch 为准，`active` 状态的 Patch 仅提示告警
4. **Patch 与 SSOT 不可调和的冲突**：标记为 `TEST_BLOCKED`，不执行测试，告警人工裁决
5. **Patch 未覆盖的 SSOT 规则**：按 SSOT 原样执行

> **实现说明**：Harness 在启动时扫描 `ssot/experience-patches/` 下所有 `validated` / `pending_backwrite` 状态的 Patch，按 `feat_ref` 分组，合并到对应 FEAT 的测试上下文中。合并逻辑为增量覆盖（不是替换），未被 Patch 覆盖的 SSOT 规则保持不变。

---

## 11. 与代码实现的关系

本 ADR 明确采用：

> **"先试改代码 + Patch 留痕 + 24h 窗口期结算回写"**
> 作为体验期默认机制。

这意味着：
- 代码并不总是最后一步
- 体验期允许"实现先行"
- 但这种先行必须受 Patch 层治理，**窗口期最长 24h**
- 不允许长期无痕漂移
- 超期 blocking 机制确保代码不会在 spec 真空期运行超过 24h

---

## 12. AI 集成规范

### 12.1 Patch-Aware Context 注入

> **修订（C4）**：实现为 PreToolUse hook，不依赖 AI 记忆。

**机制**：PreToolUse hook skill，在 `Edit` / `Write` 工具调用前自动触发。

**触发流程**：
1. Hook 拦截代码写入操作
2. 扫描 `ssot/experience-patches/` 下所有非终态 Patch
3. **按文件匹配过滤**：仅加载 `changed_files` 与目标编辑文件相关的 Patch（H7）
4. 将相关 Patch YAML 注入 AI 上下文
5. AI 基于"SSOT + active Patch"生成/修改代码
6. Hook 放行

**Context 预算控制（H7 + 终审修订）**：
- 仅加载与当前编辑文件相关的 Patch 完整 YAML
- 同 FEAT 下其他 Patch 仅加载一行摘要（ID + title + change_class）
- 总 Patch 注入不超过 3000 tokens，最多 10 条完整 YAML
- 超过 10 条时显示 WARN 并要求人工 review
- 超过预算时按 `updated_at` 降序截断

### 12.2 Patch 自动生成

AI 检测代码变更后，应自动：
1. 分析变更影响范围（页面、模块、交互路径）
2. 列出变更影响的 **routes 列表**（H8 修订）
3. 建议 `change_class` 分类（标记为 human-reviewed）
4. 生成 Patch 草案
5. 标记 `test_impact`（标记为 human-reviewed）
6. 建议 `backwrite_targets`（标记为 human-reviewed）
7. **填充 `related_ids` 通过文件系统确定性查找**（从 FEAT 目录查找关联的 UI/TECH/TESTSET ID），而非 AI 推断
   - 若某 artifact 类型查找返回零结果，保留部分结果并发出 WARN
   - 命名约定漂移时查找失败也应 WARN，不阻断但标记
8. 提交人工审核确认

> **可靠性声明（H6 修订）**：AI 不得自动提交 Patch。`change_class`、`test_impact`、`backwrite_targets` 必须由人工确认后入库。

### 12.3 Patch 辅助回写

结算时 AI 应自动：
1. 根据 `change_class` 生成回写目标清单
2. 为 `interaction` Patch 生成 UI spec / flow spec 更新草案
3. 为 `semantic` Patch 生成新 SRC 候选草案
4. 人工审核后执行

### 12.4 结算操作的 Agent 归属

> **明确化（AI 工程评审反馈）**：

| 操作 | 负责方 | 说明 |
|------|--------|------|
| Patch 登记 | 当前编辑 agent（executor） | 改代码时自动触发 |
| 结算 | `ll-qa-settlement` skill | 已有 settlement 能力可复用 |
| 回写执行 | planner + executor 链 | 回写 UI spec 需要读取现有规范、计算 delta、写入更新 |

### 12.5 Patch YAML 验证（终审 P0 修订）

**问题**：AI 可能生成格式错误或缺少必填字段的 YAML（如 `change_class: typo`）。

**验证时机**：
1. **创建时验证**：Patch 文件写入 `ssot/experience-patches/` 后立即运行
2. **提交时验证**：git commit pre-commit hook 拦截无效 Patch
3. **读取时验证**：Hook 注入 context 前先校验，无效 Patch 标记 WARN 并跳过

**验证内容**：
- YAML 格式合法
- 必填字段存在：`id`、`status`、`change_class`、`feat_ref`、`source.actor`、`source.human_confirmed_class`
- 枚举值合法：`change_class` ∈ {visual, interaction, semantic}；`status` 为合法枚举
- `human_confirmed_class` 不为 null（确保经过人工审核）

**实现**：MVP 阶段由 AI 在生成 Patch 后自行校验（Python/PyYAML + 内置校验逻辑）。Phase 2 提取为独立 `validate-patch` 脚本，供 hook 和 CLI 复用。

---

## 13. 不采纳的方案

### 13.1 方案 A：所有改动必须先改 SSOT 再改代码

**不采纳原因**：体验期高频碎改节奏太快，流程过重，会显著降低 UX 探索效率。

### 13.2 方案 B：所有细节都直接改代码，不回 SSOT

**不采纳原因**：SSOT 很快失真，AI 基于旧规范生成会冲掉已有修正，验收/测试/代码和产品定义脱节。

### 13.3 方案 C：把所有 Patch 全部写入高层 SSOT

**不采纳原因**：高层规范会被视觉噪声污染，产品真相层失去抽象性。

### 13.4 方案 D：大变更也走 Patch 层

**不采纳原因**：大变更需要完整治理（Gate 审批、EPIC/FEAT 分解），Patch 层无法承载。且现有 SRC 体系已支持新建 SRC 的方式处理变更，重复建设无意义。

### 13.5 方案 E：Patch 挂在 FEAT 目录下（作为子目录）

**不采纳原因**：当前 FEAT artifact 是 flat `.md` 文件，不是目录。迁移 23 个 FEAT 从 flat 到目录结构是破坏性变更，成本过高。改用独立目录 `ssot/experience-patches/` 通过 `feat_ref` 关联。

---

## 14. 影响与收益

### 14.1 正向收益

| 收益 | 说明 |
|------|------|
| 体验迭代速度不降 | 小变更快速试错，不被重流程卡死 |
| 消除 SSOT 漂移 | 所有改动至少进入 Patch 层，AI 通过 hook 强制读取 |
| 高层 SSOT 保持干净 | 视觉噪声不污染产品真相层 |
| 测试链同步更新 | 交互变更与测试回归形成联动 |
| 大变更治理完整 | 新建 SRC 走完整流程，可追溯 |
| 适合 AI 工程实践 | AI 可区分正式规则、已验证 Patch、已废弃试验 |
| 零额外步骤 | PreToolUse hook 自动触发，用户不需手动操作 |

### 14.2 代价与风险

| 代价/风险 | 缓解措施 |
|-----------|---------|
| 新增一层治理对象 | Patch 自动登记 + 强制 24h 结算 + blocking 机制 |
| Patch 堆积成第二真相系统 | 24h 强制 blocking + 批量结算 + 30 天自动归档清理 |
| 工具链需要适配 | MVP 先手动，Phase 2 实现 PreToolUse hook 自动化 |
| 分类标准模糊 | 决策树 + 边界示例 + AI 辅助建议 + 人工最终决定 |
| AI 误分类导致测试遗漏 | change_class/test_impact 必须 human-reviewed，AI 不得自动提交 |

---

## 15. 执行规范

### 15.1 默认规则

- 体验期小变更允许直接改代码
- 但必须通过 PreToolUse hook 自动登记 Patch
- 无 Patch 的体验小变更视为违规
- 大变更直接新建 SRC，不走 Patch 层

### 15.2 分类规则

每条 Patch 必须标明：
- `change_class`: `visual | interaction | semantic`（AI 预填 + human-reviewed）
- `must_backwrite_ssot`: 自动根据 change_class 推导（human-reviewed）
- `test_impact`: 自动根据 change_class 推导（human-reviewed）

### 15.3 审计规则

以下情况需告警：
- `validated` Patch 超过 12h 未结算 → WARN
- `validated` Patch 超过 24h 未结算 → ERROR + blocking
- `pending_backwrite` 超过 24h 未回写 → ERROR + blocking
- Patch 对应代码已变更但 `related_ids` 为空 → WARN
- `test_impact=true` 但未关联 TESTSET / TC → ERROR + 阻断结算

---

## 16. 后续演进建议

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| MVP | 手动登记 Patch（AI 预填 YAML，人工确认）+ 手动结算 | P0 |
| Phase 2 | PreToolUse hook 自动触发 Patch 登记 | P0 |
| Phase 2 | AI 辅助结算（生成回写草稿 + 建议批量操作） | P1 |
| Phase 2 | Patch 索引 / 查询 / 冲突检测 | P1 |
| Phase 3 | Patch-aware Harness 集成（Section 10.3 冲突解决规则实现） | P1 |
| Phase 3 | 自动回写 SSOT 草稿 | P2 |
| Phase 3 | 审计告警自动化 + 24h blocking 强制执行 | P2 |

---

## 17. 最终决策摘要

本 ADR 决定：

1. 引入 **Experience Patch Layer** 作为小变更缓冲层
2. 大变更**直接新建 SRC**，走完整治理流程（现有惯例延续）
3. 建立**双路径分流模型**：Prompt-to-Patch / Document-to-SRC
4. 建立三类变更分层：`visual` / `interaction` / `semantic`（含边界示例和分歧解决）
5. 明确差异化回写规则：不回写 / 回写 UI / 升级 SRC
6. 建立 Patch 生命周期、结算制度与测试联动机制
7. 保持 SSOT 作为长期正式真相源，所有 SRC 仍 frozen
8. **AI 必须能读取 Patch**，通过 PreToolUse hook 强制注入，不依赖记忆
9. **Patch 窗口期最长 24h**，超期 blocking，防止 spec 真空期过长
10. **关键分类字段 human-reviewed**，AI 只预填，不自动提交
11. **批量结算操作**，避免用户疲劳
13. **Patch 存放在独立目录** `ssot/experience-patches/`，避免破坏 FEAT 现有结构
14. **24h 计时从 `validated` 开始**，终端状态包含 `retain_in_code`
15. **YAML 三重验证**：创建时 / 提交时 / 读取时
16. **决策树改为三个独立门控**，任一指向 SRC 即走 SRC

---

## 18. 评审修订记录

### v2.0 → v2.1（终审修订）

| 修订编号 | 来源 | 问题 | 修订内容 |
|----------|------|------|---------|
| P0-1 | 架构 | 24h 计时起点矛盾 | 统一为 `validated` 作为计时起点 |
| P0-2 | 架构 | Visual Patch 无终端状态 | 新增 `retain_in_code` 状态，纳入终端状态定义 |
| P0-3 | 架构 | Schema 示例状态为 `active` | 修正为 `draft` |
| P1-1 | 产品 | 决策树门控歧义 | 改为三个独立门控，任一指向 SRC 即走 SRC |
| P1-2 | 产品 | 缺少批量操作 | 新增 `bulk-upgrade-to-src` / `merge-patches` / `approve-by-feat` |
| P1-3 | 产品 | "零额外步骤"用词不精确 | 改为"零手动登记步骤" |
| P1-4 | AI 工程 | PreToolUse hook 机制未拆分 | 明确 MVP 用 CLAUDE.md 规则，Phase 2 加 hook |
| P1-5 | AI 工程 | 无 YAML 验证机制 | 新增 Section 12.5，定义三重验证时机和内容 |
| P1-6 | 架构 | FEAT 删除时 Patch 孤儿 | 新增 Section 6.4：自动 discard + 人工确认 |
| P1-7 | 架构 | 人工编辑代码路径未覆盖 | 新增 Section 6.4：下次 AI 会话自动扫描 diff |
| P1-8 | 架构 | Interaction 回写是否需 Gate 不明确 | 明确：UI/TESTSET 直接更新，Semantic 才走 Gate |

### v1.0 → v2.0（Party Mode 评审修订版）

| 修订编号 | 来源 | 问题 | 修订内容 |
|----------|------|------|---------|
| C1 | 架构 | FEAT 是 flat 文件不是目录 | Patch 移至独立目录 `ssot/experience-patches/`，通过 `feat_ref` 关联 |
| C2 | 架构 | 代码先行违反 frozen 原则 | 窗口期收紧到 24h，超期 blocking |
| C3 | 产品 | 结算四选一操作疲劳 | 增加批量操作：approve-by-class / approve-all-validated / snooze / auto-settle-visual |
| C4 | AI 工程 | Context 注入机制未指定 | 实现为 PreToolUse hook，Edit/Write 前强制触发 |
| C5 | 测试 | Harness 冲突解决未定义 | Section 10.3 定义 5 条冲突解决规则 |
| H1 | 架构 | 多 Patch 同模块无合并策略 | Section 5.2 增加冲突检测与解决规则 |
| H2 | 架构 | Semantic 升级被拒无回滚 | Section 7.4 增加 Gate 拒绝时的回滚路径 |
| H3 | 产品 | 分类边界模糊 | Section 4.1/4.2 增加"不是 X"的边界示例 + 4.5 分歧解决 |
| H4 | 产品 | 决策树依赖工具链知识 | Section 2.4 改为基于变更属性的决策树 |
| H5 | 产品 | "零额外步骤"不成立 | Section 9.1 改为 PreToolUse hook 自动触发 |
| H6 | AI 工程 | AI 预填字段易出错 | 标记 change_class/test_impact/backwrite_targets 为 human-reviewed |
| H7 | AI 工程 | 10+ Patch 全量读取消耗 context | Section 12.1 增加文件匹配过滤 + 3000 token 预算上限 |
| H8 | 测试 | test_impact 自动检测不可靠 | Patch schema 增加 `affected_routes` 必填字段 |

---

## 19. 一句话原则

> **体验期可以快，但不能乱；可以先改代码，但不能不留痕；可以延迟回写 SSOT，但不得超过 24h。大变更走 SRC，小变更走 Patch，各走各路，互不干扰。**
