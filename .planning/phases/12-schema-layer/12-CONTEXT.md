# Phase 12: Schema 定义层 - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

定义 TESTSET、Environment、Gate 三个 YAML schema，含 forbidden/required field guards。不实现执行逻辑，仅定义结构校验。

Requirements: SCHEMA-01 ~ SCHEMA-06

Success Criteria:
1. TESTSET schema 拒绝 test_case_pack / script_pack 字段（FC-006）
2. Environment schema 要求 base_url / browser / timeout / headless 字段
3. Gate schema 仅接受 pass / conditional_pass / fail / provisional_pass 四个 verdict
4. 所有 schema 对合法输入返回成功，对非法输入返回清晰错误信息

</domain>

<decisions>
## Implementation Decisions

### 文件组织
- **D-01:** 三个 schema 各自独立文件：`testset_schema.py`, `environment_schema.py`, `gate_schema.py`
- **D-02:** 对应 YAML schema 文件放在 `ssot/schemas/qa/` 目录：`testset.yaml`, `environment.yaml`, `gate.yaml`
- **D-03:** 测试文件对应命名：`test_testset_schema.py`, `test_environment_schema.py`, `test_gate_schema.py`

### 验证模式
- **D-04:** 使用 `dataclass(frozen=True)` + 验证函数模式，与 `task_pack_schema.py`、`qa_schemas.py` 一致
- **D-05:** 同时维护 `ssot/schemas/qa/*.yaml` 外部 YAML schema 定义文件（项目已有约定）
- **D-06:** SchemaError 统一继承 `ValueError`，命名为 `TestsetSchemaError`、`EnvironmentSchemaError`、`GateSchemaError`

### 错误消息风格
- **D-07:** 简洁单行错误，沿用 `_require()` + `_enum_check()` 模式
- **D-08:** 错误消息包含字段名、非法值、允许值列表（如 `QaSchemaError` 现有格式）

### CLI 入口
- **D-09:** 每个 schema 独立 `__main__` 入口，格式 `python -m cli.lib.testset_schema file.yaml`
- **D-10:** 支持 `--type` 参数和文件列表，与现有模式一致

### Claude's Discretion
- 具体 dataclass 字段默认值设计
- YAML schema 文件的具体格式风格

### Folded Todos
- 无

</decisions>

<canonical_refs>
## Canonical References

### Schema 定义
- `ssot/src/SRC-009__adr-052-ssot-semantic-governance-upgrade.md` — 11 个治理对象契约、6 个枚举字段冻结值、7 条 Frozen Contracts
- `ssot/adr/ADR-052-测试体系轴化-需求轴与实施轴.md` — 环境定义、Gate verdict、分层规则、模块接口契约
- `ssot/feat/FEAT-009-D__test-governance-declarative-asset-layering.md` — FEAT 级验收标准
- `.planning/REQUIREMENTS.md` — SCHEMA-01 ~ SCHEMA-06 详细需求

### 已有模式参考
- `cli/lib/task_pack_schema.py` — 独立 schema 文件模式、dataclass + enum + 验证函数
- `cli/lib/qa_schemas.py` — 多 schema 统一文件模式、`_require()` / `_enum_check()` 辅助函数
- `cli/lib/frz_schema.py` — Frozen dataclass + MSC 验证模式
- `ssot/schemas/qa/task_pack.yaml` — 外部 YAML schema 文件格式

### Frozen Contracts
- FC-006: TESTSET 中不得嵌入 test_case_pack / script_pack
- FC-007: verifier 必须使用独立认证上下文 (shared_context_with_runner 为 forbidden field)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_require()`, `_enum_check()` helpers from `qa_schemas.py` — 可复制用于新 schema
- `QaSchemaError` base class — 可考虑复用或各自独立
- `task_pack_schema.py` 完整模式 — 最接近 Phase 12 需要的设计

### Established Patterns
- `dataclass(frozen=True)` for immutable schema definitions
- Enum classes for field validation (TaskType, TaskStatus, etc.)
- `validate(data: dict) -> Dataclass` dict-level validation
- `validate_file(path) -> Dataclass` file-level validation
- `_VALIDATORS` dict for schema type auto-detection
- CLI `main()` with `--type` flag and multi-file support

### Integration Points
- `cli/lib/protocol.py` — SSOT 写入路径，Phase 15 将集成 enum_guard
- `cli/lib/skill_invoker.py:168-169` — 已校验 test_environment_ref 但无对应生成技能
- `ssot/tests/gate/gate-evaluator.py` — 已有 Gate 评价逻辑，需对齐新 schema

</code_context>

<specifics>
## Specific Ideas

- 保持与现有代码风格 100% 一致，不引入新范式
- 三个 schema 的 enum_guard 验证值必须与 SRC-009 枚举冻结表完全一致
- TESTSET forbidden fields: test_case_pack, script_pack (FC-006)
- Environment forbidden fields: embedded_in_testset
- Gate forbidden fields: hidden_verifier_failure (FC-004 related)

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-schema-layer*
*Context gathered: 2026-04-22*
