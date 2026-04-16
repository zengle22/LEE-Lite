# Phase 2: Patch 登记 Skill - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

创建 `ll-patch-capture` 技能，实现双路径登记：
- Prompt-to-Patch：用户描述变更 → AI 生成 Patch YAML → Supervisor Agent 审核 → 自动入库（必要时升级人工确认）
- Document-to-SRC：委托给现有 `ll-product-raw-to-src` 处理，本技能仅负责路由 + 关联 Patch 记录

自动更新 `patch_registry.json`，CLI 注册 `patch-capture` 动作。

不涉及：结算/回写（Phase 3）、测试联动（Phase 4）、Hook 自动触发（Phase 6）。

</domain>

<decisions>
## Implementation Decisions

### 技能结构
- **D-01:** 遵循现有 `ll-*` 受管技能模式，与项目 29 个已有技能保持一致
- **D-02:** 技能命名为 `ll-patch-capture`（非 `ll-experience-patch-register`，更准确描述行为）
- **D-03:** 文件结构：`SKILL.md` + `ll.contract.yaml` + `input/` + `output/` + `agents/executor.md` + `agents/supervisor.md` + `scripts/run.sh`

### 交互流程（三步式）
- **D-04:** AI 分析变更 → 生成 Patch YAML 草案 → Supervisor Agent 审核 → 自动入库
- **D-05:** 默认全自动，用户仅收到"已登记 UXPATCH-XXXX"通知
- **D-06:** 仅在 Supervisor Agent 判定需要时才升级人工确认，展示审查清单

### Supervisor Agent 审核规则
- **D-07:** Supervisor 使用 Phase 1 创建的 `cli/lib/patch_schema.py` 进行 schema 验证
- **D-08:** 自动通过条件：schema 验证通过 + 无冲突 + change_class 置信度高 + 非 semantic
- **D-09:** 升级人工确认条件：
  - Schema 验证失败（必填字段缺失或枚举值非法）
  - change_class 分类置信度低（visual vs interaction 模糊）
  - 检测到冲突（同 FEAT 下已有 Patch 修改同一文件）
  - Semantic Patch（需要升级 SRC 决策）
  - 该 FEAT 的首条 Patch（建立基线需确认）
  - test_impact 有争议（影响测试路径但 AI 判断不确定）

### AI 分类自动化
- **D-10:** AI 预填全部字段：change_class、test_impact、backwrite_targets、scope.page、scope.module、changed_files、affected_routes
- **D-11:** AI 预填规则：change_class 基于 ADR-049 §2.4 决策树；test_impact 对 interaction/semantic 默认 true、visual 默认 false；backwrite_targets 按 ADR-049 §4.4 映射表推导
- **D-12:** 所有 AI 预填字段标记为 human-reviewed（ADR-049 §12.2）

### Document-to-SRC 路径
- **D-13:** Document-to-SRC 委托给现有 `ll-product-raw-to-src` 技能，本技能不做 SRC 生成
- **D-14:** 本技能负责路由判断：检测输入类型（prompt vs 文档）→ 分发到对应路径
- **D-15:** 如果 Document-to-SRC 涉及体验层变更，本技能同时生成一条 semantic Patch 作为关联记录（resolution.src_created = SRC ID）

### CLI 入口
- **D-16:** CLI 注册 `patch-capture` 动作，支持脚本和 hook 调用

### Claude's Discretion
- Executor prompt 的具体措辞和引导方式
- Supervisor 审核清单的细粒度（具体检查项数量）
- 置信度阈值的具体数值（如 change_class 置信度低于多少触发升级）
- `ll.lifecycle.yaml` 是否本阶段就创建（ADR 提到但 MVP 可延后）

</decisions>

<specifics>
## Specific Ideas

- 参考 `ll-qa-settlement` 的技能结构作为模板（agents/executor.md + supervisor.md 模式）
- AI 登记完成后仅展示一行摘要："已登记 UXPATCH-0001 (interaction) → ssot/experience-patches/FEAT-XXX/"
- Supervisor 升级人工确认时展示结构化审查清单，类似表格形式让用户快速决策
</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ADR / Design
- `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` — ADR-049 全文，核心真理源
  - §2.4: 路径选择决策树
  - §4.4: 分类与回写目标映射
  - §5.3: Patch YAML Schema
  - §9.1: Prompt-to-Patch 用户操作流程
  - §12.2: Patch 自动生成规范
  - §12.5: Patch YAML 验证
- `.planning/ROADMAP.md` — Phase 2 goal + success criteria
- `.planning/REQUIREMENTS.md` — REQ-PATCH-02

### Existing Patterns
- `skills/ll-qa-settlement/SKILL.md` — 现有受管技能结构模板
- `skills/ll-qa-settlement/agents/executor.md` — Executor Agent prompt 模式
- `skills/ll-qa-settlement/agents/supervisor.md` — Supervisor Agent 验证模式
- `cli/lib/patch_schema.py` — Phase 1 创建的 schema 验证器
- `ssot/schemas/qa/patch.yaml` — Phase 1 创建的 Patch schema 定义
- `ssot/experience-patches/example-feat/patch_registry.json` — Phase 1 创建的 registry 示例

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli/lib/patch_schema.py` — Phase 1 的 schema 验证器，Supervisor Agent 可直接调用
- `ssot/schemas/qa/patch.yaml` — Patch schema 定义，AI 生成时需参考字段结构
- 29 个 `ll-*` 技能 — 提供统一的技能文件结构模板和命名约定

### Established Patterns
- 所有 `ll-*` 技能使用 SKILL.md + executor.md + supervisor.md + contracts 结构
- Executor 负责生成/执行，Supervisor 负责验证
- scripts/run.sh 作为 Claude Code wrapper 入口

### Integration Points
- 输出写入 `ssot/experience-patches/{FEAT-ID}/` 目录（Phase 1 已创建）
- 需要更新 `ssot/experience-patches/{FEAT-ID}/patch_registry.json` 索引
- CLI 注册到项目的命令行入口（遵循现有 qa_schemas.py 的 CLI 模式）

</code_context>

<deferred>
## Deferred Ideas

- PreToolUse Hook 自动触发登记 → Phase 6
- 结算 Skill → Phase 3
- 测试联动 → Phase 4
- AI Context 注入 → Phase 5
- 24h Blocking 机制 → Phase 7

</deferred>

---

*Phase: 02-patch-skill*
*Context gathered: 2026-04-16*
