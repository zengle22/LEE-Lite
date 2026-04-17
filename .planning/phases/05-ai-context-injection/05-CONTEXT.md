# Phase 5: AI Context 注入 - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning
**Source:** ADR-049 v2.1 + ADR-047 v1.4

<domain>
## Phase Boundary

实现 AI 生成代码前自动注入 Patch context 的变更管理机制。本质上是变更管理 awareness recording — 当用户触发新的 SSOT 链生成时，AI 需要感知已有的 Patch context，避免重复或覆盖生产期已验证的 UX 修正。

不涉及：
- 原始 SSOT skill 本身（feat-to-tech / feat-to-ui / feat-to-proto 等完全不受影响）
- 强制 AI 遵守 Patch（那是 Phase 6 PreToolUse hook 的事）
- SSOT 链内修订（由 gate + revise 机制控制）
- 简单 visual Patch 的记录（由 patch-capture skill 处理）

**前提变更**：ADR-047 把 TESTSET 降级为兼容视图，真理源为 manifest + spec 层。Phase 5 作为变更管理，需感知 Patch 但不改变现有 SSOT skill 的产出格式。

</domain>

<decisions>
## Implementation Decisions

### Phase Scope (来自用户讨论)
- **D-01:** Phase 5 本质是变更管理 awareness recording，在用户触发新 SSOT 链生成时让 AI 感知 Patch context
- **D-02:** 原始 SSOT skill（feat-to-tech / feat-to-ui / feat-to-proto 等）不受影响 — Patch context 只在新 SSOT 链生成时注入 awareness
- **D-03:** 不强制 AI 遵守 Patch — 这是 awareness 而非 enforcement；enforcement 留给 Phase 6 PreToolUse hook

### 触发方式（来自用户讨论）
- **D-04:** 新 SSOT 链生成由用户直接触发和管理（不是 settle skill 自动触发）
- **D-05:** simple visual Patch 由 patch-capture skill 单独记录，不进入新 SSOT 链生成流程
- **D-06:** interaction/semantic Patch 通过 settle skill 处理后，用户可手动触发新 SSOT 链进行回写

### Patch Context 注入机制
- **D-07:** Patch context 通过 Phase 4 已实现的 `resolve_patch_context(feat_ref)` 读取
- **D-08:** 只注入 `validated` + `pending_backwrite` patches（per ADR-049 §10.3）
- **D-09:** Patch context 以 awareness 形式记录到产出物中，表明 AI 已考虑 Patch context
- **D-10:** 不改变现有 skill 的 executor.md 结构 — 采用最轻量注入方式

### Phase 3 校准（来自讨论确认）
- **D-11:** Phase 3 settle skill 的行为：visual → retain_in_code; interaction → 生成 delta 草案; semantic → 生成 SRC 候选; pending_backwrite → 直接写回到现有 SSOT artifact

### Claude's Discretion
- Patch context 的具体记录格式（新文件 vs 产出物中的 section）
- 注入时机：Python runtime 自动执行 vs executor.md 中显式指令
- 产出物中 awareness 的具体表现形式

### Folded Todos
None

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ADR / Design
- `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` — ADR-049 全文
  - §12.1: Patch-Aware Context 注入
  - §14.2: AI Context 注入（REQ-PATCH-05 来源）
  - §4.4: 分类与回写目标自动映射（含 test_impact 默认规则）
  - §10.3: 冲突解决规则
  - §12.2: AI 自动填充规范
- `ssot/adr/ADR-047-测试体系重建 - 双链治理.md` — 双链测试治理架构
- `.planning/ROADMAP.md` — Phase 5 goal: "AI 生成代码前自动注入 Patch 上下文，防止覆盖已有优化"
- `.planning/REQUIREMENTS.md` — REQ-PATCH-05（AI Context 注入）

### Existing Patterns
- `cli/lib/test_exec_artifacts.py` — PatchContext dataclass, resolve_patch_context()（Phase 4 产出）
- `cli/lib/patch_schema.py` — Patch schema 验证器 + resolve_patch_conflicts()
- `skills/ll-experience-patch-settle/scripts/settle_runtime.py` — settlement 运行时
- `skills/ll-patch-capture/scripts/patch_capture_runtime.py` — patch 登记运行时

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `resolve_patch_context()` in `cli/lib/test_exec_artifacts.py` — 已实现的 Patch 上下文解析函数，扫描 ssot/experience-patches/ 下 validated + pending_backwrite patches
- `PatchContext` frozen dataclass — 7 字段 typed struct（has_active_patches, validated_patches, pending_patches, conflict_resolution, directory_hash, reviewed_at_latest, feat_ref）
- `_compute_patch_dir_hash()` — TOCTOU 防护的 SHA1 hash 计算
- `_build_conflict_resolution_map()` — per-coverage_id 冲突解决映射（skip/warn/use_patch）

### Established Patterns
- 每个 skill 的 `scripts/` 目录下有独立的 Python runtime
- `executor.md` 定义 AI 的行为指令
- `feat_to_*.py` 是 CLI 入口，导入 `scripts/` 下的 runtime 模块
- dataclass + YAML read/write 是项目的标准数据模式

### Integration Points
- 新 SSOT 链生成时需要调用 `resolve_patch_context(feat_ref)` 获取 Patch context
- Patch context 需要以 awareness 形式记录到 skill 产出物中
- 与 Phase 4 的输出直接消费关系

</code_context>

<specifics>
## Specific Ideas

- Phase 5 需要最轻量实现：读取 PatchContext → 产出 awareness recording
- 不改变现有 skill 的 executor.md 结构
- awareness recording 的具体格式和位置由 planner 决定
- Phase 3 settle 后的 pending_backwrite 直接写回 SSOT artifact

</specifics>

<deferred>
## Deferred Ideas

- Phase 6: PreToolUse hook 自动触发 Patch 登记（强制 AI 遵守）
- Phase 7: 24h Blocking 机制
- Patch 冲突自动检测 → 统一后由 settle skill 消费
- SSOT 链内修订（由 gate + revise 机制处理，不在 Patch 业务范围）

</deferred>

---

*Phase: 05-ai-context-injection*
*Context gathered: 2026-04-17, assumptions mode with user correction*
