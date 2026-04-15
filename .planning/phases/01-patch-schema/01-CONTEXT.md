# Phase 1: Patch Schema + 目录结构 - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning
**Source:** ADR-049 v2.1 (frozen)

<domain>
## Phase Boundary

定义 Patch YAML schema 文件和目录结构规范，为 ADR-049 体验修正层的所有后续工作奠定基础。

本阶段只产出：
1. Patch YAML schema 定义文件（`ssot/schemas/qa/patch.yaml`）
2. 目录结构示例 + README
3. Python schema 验证器（`cli/lib/patch_schema.py`）
4. patch_registry.json schema 定义

不涉及：
- Patch 登记 skill（Phase 2）
- 结算 skill（Phase 3）
- Hook 集成（Phase 6）
</domain>

<decisions>
## Implementation Decisions

### Patch Schema 结构（来自 ADR-049 §5.3）
- Patch 文件位置：`ssot/experience-patches/{FEAT-ID}/UXPATCH-{SEQ}__{slug}.yaml`
- ID 命名：`UXPATCH-{SEQUENCE}__{slug-description}`
- 必填字段：id, type, status, created_at, updated_at, title, summary, source, scope, change_class
- source 必填子字段：from, actor, session, prompt_ref, ai_suggested_class, human_confirmed_class
- scope 必填子字段：feat_ref, page, module
- change_class 枚举：visual | interaction | semantic
- status 枚举：draft → active → validated → pending_backwrite/backwritten/retain_in_code/upgraded_to_src/superseded/discarded → archived
- resolution 必填子字段：backwrite_status（pending | backwritten | discarded | upgraded_to_src | superseded）

### 目录结构（来自 ADR-049 §5.1）
- 独立目录：`ssot/experience-patches/`（不挂在 FEAT 下，避免破坏现有 flat 文件结构）
- 每个 FEAT 一个子目录
- patch_registry.json 放在 FEAT 子目录下

### Schema 验证规则（来自 ADR-049 §12.5）
- 创建时验证：Patch 写入后立即运行
- 提交时验证：pre-commit hook 拦截
- 读取时验证：Hook 注入前先校验
- 验证内容：YAML 格式合法、必填字段存在、枚举值合法、human_confirmed_class 不为 null

### Python 验证器实现
- 放在 `cli/lib/patch_schema.py`（遵循现有 qa_schemas.py 模式）
- 使用 Python dataclass + PyYAML（项目已有依赖）
- 需要支持从 ADR-049 schema 定义生成验证逻辑

### patch_registry.json 格式
- 每个 FEAT 子目录一个
- 记录所有 Patch 的 id, status, change_type, created_at, title

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ADR / Design
- `ssot/adr/ADR-049-引入体验修正层-Experience-Patch-Layer.md` — ADR-049 全文（真理源）
- `.planning/ROADMAP.md` — Phase 1 goal + success criteria
- `.planning/REQUIREMENTS.md` — REQ-PATCH-01

### Existing Patterns
- `ssot/schemas/qa/plan.yaml` — 现有 QA schema 模式（参考格式）
- `ssot/schemas/qa/manifest.yaml` — 现有 QA schema 模式
- `ssot/schemas/qa/settlement.yaml` — 现有 QA schema 模式
- `cli/lib/qa_schemas.py` — 现有 Python 验证器模式（参考实现）
- `tests/qa_schema/` — 现有测试模式（参考测试结构）

</canonical_refs>

<specifics>
## Specific Ideas

### Patch YAML 核心字段清单（直接可用）

**顶层字段：**
- `id` (string, required): UXPATCH-0001 格式
- `type` (string, required): 固定值 "experience_patch"
- `status` (enum, required): draft/active/validated/pending_backwrite/backwritten/retain_in_code/upgraded_to_src/superseded/discarded/archived
- `created_at` (datetime, required)
- `updated_at` (datetime, required)
- `title` (string, required)
- `summary` (string, required)
- `source` (object, required)
- `scope` (object, required)
- `change_class` (enum, required): visual/interaction/semantic
- `severity` (enum, optional): low/medium/high
- `conflict` (boolean, optional): 默认 false
- `conflict_details` (object, optional)
- `problem` (object, optional): user_issue, evidence
- `decision` (object, optional): code_hotfix_allowed, must_backwrite_ssot, backwrite_targets, backwrite_deadline
- `implementation` (object, optional): code_changed, changed_files
- `test_impact` (object, optional): impacts_user_path, impacts_acceptance, impacts_existing_testcases, affected_routes, test_targets
- `related_ids` (array of string, optional)
- `resolution` (object, optional): backwrite_status, merged_into_ssot_at, src_created, closed_at

**source 子字段：**
- `from` (string, required): 固定 "product_experience"
- `actor` (enum, required): human | ai_suggested
- `session` (string, required)
- `prompt_ref` (string, required)
- `ai_suggested_class` (enum, optional): visual/interaction/semantic
- `human_confirmed_class` (enum, required): visual/interaction/semantic

**scope 子字段：**
- `feat_ref` (string, required)
- `ui_ref` (string, optional)
- `tech_ref` (string, optional)
- `page` (string, required)
- `module` (string, required)

**test_impact 子字段：**
- `impacts_user_path` (boolean)
- `impacts_acceptance` (boolean)
- `impacts_existing_testcases` (boolean)
- `affected_routes` (array of string)
- `test_targets` (array of string)

**resolution 子字段：**
- `backwrite_status` (enum): pending | backwritten | discarded | upgraded_to_src | superseded
- `merged_into_ssot_at` (datetime, nullable)
- `src_created` (string, nullable): SRC ID
- `closed_at` (datetime, nullable)

</specifics>

<deferred>
## Deferred Ideas

None — ADR-049 covers Phase 1 scope fully.
</deferred>

---

*Phase: 01-patch-schema*
*Context gathered: 2026-04-16 from ADR-049 v2.1*
