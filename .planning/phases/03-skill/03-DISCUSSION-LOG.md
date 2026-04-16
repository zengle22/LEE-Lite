# Phase 3: 结算 Skill + 回写工具 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 03-skill
**Areas discussed:** 技能归属, 回写映射, 回写边界, 自动化策略, 回写产出格式

---

## 技能归属

| Option | Description | Selected |
|--------|-------------|----------|
| 新建独立 `ll-experience-patch-settle` | 输入输出域与 `ll-qa-settlement` 完全不同，保持语义清晰 | ✓ |
| 扩展 `ll-qa-settlement` 加 sub-command | 复用框架但污染已有技能语义 | |

**User's choice:** 新建独立 `ll-experience-patch-settle`

## 回写映射

| Option | Description | Selected |
|--------|-------------|----------|
| 以 ADR §4.4 为准 | visual→不回写, interaction→UI/Flow/TESTSET, semantic→新建SRC链 | ✓ |
| 以 ROADMAP 为准 | 简化为 visual→TECH, interaction→UI, semantic→FEAT | |
| 混合 | visual 也回写 TECH 作为变更记录 | |

**User's choice:** 以 ADR §4.4 为准
**Notes:** 用户问清了"升级 SRC"的具体含义，确认是新建 SRC 链候选，不是直接改 SSOT

## 回写边界

| Option | Description | Selected |
|--------|-------------|----------|
| 只生成新文件（草案），不修改 frozen SSOT | 本阶段边界清晰 | ✓ |
| 直接修改目标文件 | 破坏性变更 | |

**User's choice:** 生成新文件即可，不需要审核环节
**Notes:** 用户指出"审核没有意义"，因为全是新文件不涉及修改冻结文档。Agent 全自动处理，有必要才升级人工

## 自动化策略

| Option | Description | Selected |
|--------|-------------|----------|
| Agent 全自动 + 条件升级人工 | 默认自动，有歧义时升级 | ✓ |
| 纯逐条人工确认 | 每步都需要人工 | |

**User's choice:** Agent 来审核，有必要才升级到人工确认，否则直接批量处理

## 回写产出格式

| Option | Description | Selected |
|--------|-------------|----------|
| delta 带原文引用 | 类似 diff 格式，便于后续合并定位 | ✓ |
| 纯新增不带原文 | 简单但后续合并困难 | |

**User's choice:** 需要带原文引用

---

## Claude's Discretion

- Executor prompt 的具体措辞和引导方式
- delta 文件的具体格式（JSON vs YAML）
- 批量操作的分组策略粒度
- `ll.lifecycle.yaml` 是否本阶段创建

## Deferred Ideas

- 审核后实际合并 delta 到 frozen SSOT → 后续 Milestone
- Patch 冲突检测 + 索引/查询 → Phase 6 或独立
- Test-aware 联动（TESTSET 标记 needs_review）→ Phase 4
- PreToolUse hook 自动触发 → Phase 6
- 24h blocking 机制 → Phase 7
