# Phase 1: QA Schema 定义 - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning
**Source:** Discussion + ADR-047 analysis

<domain>
## Phase Boundary

建立统一的 QA 测试治理 schema（plan/manifest/spec/settlement 四层资产结构），作为 `ssot/schemas/qa/` 真理源。所有 11 个技能的输入/输出必须符合这些 schema。

本阶段产出：
1. 4 个 YAML schema 文件（plan.yaml, manifest.yaml, spec.yaml, settlement.yaml）
2. Python dataclass 验证器（`cli/lib/qa_schemas.py`）
3. 用手工样例文件通过验证器测试

</domain>

<decisions>
## Implementation Decisions

### Schema 结构
- plan: 只定义范围和优先级，不包含具体测试断言
- manifest: 只追踪状态（lifecycle_status / mapping_status / evidence_status / waiver_status），不包含设计细节
- spec: 只定义测试合同（请求/断言/证据要求），不包含执行结果
- settlement: 只结算结果和放行建议，不回溯设计

### Schema 位置
- `ssot/schemas/qa/` 作为真理源
- Python 验证器读取这些 schema 进行校验

### 数据格式
- YAML（与现有 ADR-047 资产定义一致）
- Python dataclass + PyYAML 验证（不引入新依赖，项目已有 pyyaml）

### 验证器设计
- `cli/lib/qa_schemas.py` — 核心 dataclass 定义 + 校验函数
- 每个 asset type 有对应的 `validate()` 函数
- 验证失败返回非零退出码

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ADR-047 Schema Definitions
- `ssot/adr/ADR-047-测试体系重建 - 双链治理.md` — 定义了所有 schema 的字段和结构（§4.1.5, §4.2.5, §10）
- `.planning/ROADMAP.md` — Phase 1 的目标和成功标准
- `.planning/REQUIREMENTS.md` — REQ-01: QA 统一 schema 定义

### Existing Codebase Patterns
- `cli/lib/errors.py` — 现有 CommandError dataclass 模式
- `cli/lib/` — 现有库模块的组织方式
- `ssot/adr/` — 现有 ADR 文档的格式和引用方式

</canonical_refs>

<specifics>
## Specific Ideas

ADR-047 §4.1.5 定义了 api-test-plan / api-coverage-manifest / api-test-spec 的示例结构。
ADR-047 §4.2.5 定义了 e2e-journey-plan / e2e-coverage-manifest / e2e-journey-spec 的示例结构。
ADR-047 §10 定义了 settlement report 的结构。
ADR-047 §15 定义了 manifest 状态机和分层状态字段。

每个 schema 文件应包含：
1. 完整的字段定义（名称、类型、是否必填、枚举值）
2. 嵌套对象的结构定义
3. 状态枚举的合法值
4. 引用关系（如 coverage_id → case_id 映射）

</specifics>

<deferred>
## Deferred Ideas

- API 侧和 E2E 侧的 schema 可以先只定义 API 侧，E2E 侧在 Phase 2-3 补充（ADR-047 说先 API 链）
- gate_rules schema 可以合并到 settlement 中或单独定义

</deferred>

---

*Phase: 01-qa-schema*
*Context gathered: 2026-04-14 via discussion*
