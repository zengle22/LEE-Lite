# Phase 3: 结算 Skill + 回写工具 - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

创建 `ll-experience-patch-settle` 技能，实现批量 Patch 结算 + 回写草稿生成。

- 批量读取 `pending_backwrite` 状态的 Patch
- 按 `change_class` 分类处理：visual → retain_in_code, interaction → UI/Flow/TESTSET 草案, semantic → 新建 SRC 链候选
- 生成 `resolved_patches.yaml` 结算报告
- 更新 Patch 状态 + `patch_registry.json`
- Agent 全自动处理，仅在判定需要时升级人工确认
- 本阶段只生成新文件（delta 草案 + SRC 候选），不修改任何 frozen SSOT

不涉及：测试联动（Phase 4）、Hook 集成（Phase 6）、24h Blocking（Phase 7）。

</domain>

<decisions>
## Implementation Decisions

### 技能归属
- **D-01:** 新建独立技能 `ll-experience-patch-settle`，不扩展 `ll-qa-settlement`（两者输入输出域完全不同）

### 回写映射（以 ADR §4.4 为准）
- **D-02:** visual → `retain_in_code`，不回写主 SSOT（仅保留代码）
- **D-03:** interaction → `pending_backwrite`，生成 `ui-spec-delta.yaml` + `flow-spec-delta.yaml` + `test-impact-draft.yaml`
- **D-04:** semantic → `upgraded_to_src`，生成 `SRC-XXXX__{slug}.yaml` 候选文档

### 回写边界
- **D-05:** 本阶段只生成新文件（delta 草案 + SRC 候选），不修改任何 frozen SSOT
- **D-06:** 回写 delta 文件必须带原文引用（类似 diff 格式，便于后续合并定位）
- **D-07:** "执行" = 更新 Patch 状态 + 写 delta 文件 + 出结算报告，无其他动作

### 自动化策略
- **D-08:** 默认 Agent 全自动处理（无需人工审核），仅在判定需要时升级人工确认
- **D-09:** Agent 按 `change_class` 自动分组批量处理，不确定/有冲突时才升级人工
- **D-10:** 升级人工确认条件：`change_class` 歧义、`test_impact` 不确定、同文件多 Patch 冲突

### Claude's Discretion
- Executor prompt 的具体措辞和引导方式
- delta 文件的具体格式（JSON vs YAML）
- 批量操作的分组策略粒度
- `ll.lifecycle.yaml` 是否本阶段创建

### Folded Todos
None

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ADR / Design
- `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` — ADR-049 全文，核心真理源
  - §4.4: 分类与回写目标自动映射
  - §7: 回写规则（7.1 可不回写, 7.2 必须回写 UI/流转/交互规范）
  - §8: 结算机制（8.1 触发条件, 8.2 结算动作四选一, 8.3 批量操作, 8.4 结算节奏, 8.5 告警规则）
  - §11: 与代码实现的关系
  - §12.3: Patch 辅助回写（AI 自动生成回写清单 + 草案）
  - §12.4: 结算操作的 Agent 归属
- `.planning/ROADMAP.md` — Phase 3 goal + success criteria
- `.planning/REQUIREMENTS.md` — REQ-PATCH-03

### Existing Patterns
- `skills/ll-qa-settlement/SKILL.md` — 现有 settlement 技能结构模板（参考文件组织）
- `skills/ll-patch-capture/SKILL.md` — Phase 2 创建的 Patch 登记技能（同域参考）
- `skills/ll-patch-capture/scripts/run.sh` — 技能 wrapper 入口模式
- `cli/lib/patch_schema.py` — Phase 1 创建的 schema 验证器（结算时需读取 Patch 并验证）
- `ssot/schemas/qa/patch.yaml` — Patch schema 定义
- `ssot/experience-patches/example-feat/patch_registry.json` — registry 格式

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli/lib/patch_schema.py` — 读取 pending_backwrite Patch 时可复用验证逻辑
- `ssot/experience-patches/` — Patch 存储目录，结算时扫描此处
- `ssot/experience-patches/example-feat/patch_registry.json` — 需要更新的 registry 索引
- `skills/ll-qa-settlement/` — 提供完整的技能文件结构模板（SKILL.md + executor.md + supervisor.md + scripts + contracts）

### Established Patterns
- 所有 `ll-*` 技能使用 SKILL.md + executor.md + supervisor.md + contracts + scripts 结构
- run.sh 作为 Claude Code wrapper 入口，支持 CLI 子进程调用
- Executor 负责生成/执行，Supervisor 负责验证（Phase 2 已建立）

### Integration Points
- 读取 `ssot/experience-patches/` 下所有 `pending_backwrite` 状态 Patch
- 更新每条 Patch 的 `status` 字段
- 更新 `patch_registry.json` 索引
- 输出 `resolved_patches.yaml` 结算报告到 FEAT 子目录
- 输出 delta 文件到 FEAT 子目录（`ui-spec-delta.yaml` 等）
- CLI 注册 `patch-settle` 动作

</code_context>

<specifics>
## Specific Ideas

- Agent 全自动处理：读取 Patch → 分类 → 生成 delta/SRC 候选 → 更新状态 → 出报告
- 升级人工确认仅在有歧义时触发（change_class 模糊、test_impact 不确定、多 Patch 冲突）
- delta 文件类似 diff 格式：带原文引用 + 修改建议，便于后续 Milestone 合并定位
- 结算报告 `resolved_patches.yaml` 记录每条 Patch 的处理方式、时间戳、操作摘要

</specifics>

<deferred>
## Deferred Ideas

- 审核后实际合并 delta 到 frozen SSOT → 后续 Milestone
- Patch 冲突检测 + 索引/查询 → Phase 6 或独立
- Test-aware 联动（TESTSET 标记 needs_review）→ Phase 4
- PreToolUse hook 自动触发 → Phase 6
- 24h blocking 机制 → Phase 7

</deferred>

---

*Phase: 03-skill*
*Context gathered: 2026-04-16*
