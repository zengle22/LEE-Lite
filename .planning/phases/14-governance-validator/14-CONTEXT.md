# Phase 14: 治理对象验证器 - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

实现 governance_validator.py，覆盖 SRC-009 定义的 11 个治理对象字段校验（required/optional/forbidden）。

Requirements: GOV-01 ~ GOV-03

Success Criteria:
1. 11 个治理对象均通过字段校验
2. required_fields / optional_fields / forbidden_fields 与 SRC-009 完全一致
3. 错误消息清晰指出缺失/多余/禁止字段

</domain>

<decisions>
## Implementation Decisions

### Architecture
- **D-01:** Single file `governance_validator.py` — one file with 11 object definitions + validate() for each

### Validation Mode
- **D-02:** Collect-all violations (return list of all violations) — consistent with enum_guard.py pattern

### Dataclass Design
- **D-03:** Frozen dataclass per object (SkillValidator, ModuleValidator, etc.) — type-safe, immutable, follows task_pack_schema.py pattern

### CLI Structure
- **D-04:** Unified entry point with `--object` flag — `python -m cli.lib.governance_validator --object Skill file.yaml`

### Integration
- **D-05:** Tight coupling with enum_guard — call `enum_guard.validate_enums()` internally for objects with enum fields

### 11 Governance Objects (from SRC-009)
| Object | Required Fields | Forbidden Fields |
|--------|-----------------|------------------|
| Skill | skill_id, purpose, orchestrates | internal_module_registration, direct_implementation |
| Module | module_id, axis, input, output | skill_registration |
| AssertionLayer | layer_id, name, description, verification_method | optional_for_golden_paths |
| FailureClass | class_id, name, description, common_manifestations | ad_hoc_classification |
| GoldenPath | path_id, priority, description, dependencies | undefined_environment, undefined_data |
| Gate | verdict, case_pass_rate, assertion_coverage, bypass_violations, verifier_verdict, product_bugs, env_consistency | hidden_verifier_failure |
| StateMachine | states, transitions, on_fail_behavior | free_form_execution |
| RunManifest | run_id, app_commit, base_url, browser, generated_at | mutable_after_creation |
| Environment | base_url, browser, timeout, headless | embedded_in_testset |
| Accident | case_id, manifest, screenshots, traces, network_log, console_log, failure_classification | ad_hoc_format |
| Verifier | verdict, confidence, c_layer_verdict, detail | shared_context_with_runner |

### Error Message Format
- **D-06:** Consistent with enum_guard style: `{label}: field '{field}' is required/missing`
- **D-07:** Collect all violations before raising, report complete list

### Claude's Discretion
- Specific dataclass field names and types
- Helper function naming conventions
- Test file organization

</decisions>

<canonical_refs>
## Canonical References

### Governance Definitions
- `ssot/src/SRC-009__adr-052-ssot-semantic-governance-upgrade.md` — 11 governance objects with required/optional/forbidden fields

### Pattern References
- `cli/lib/enum_guard.py` — collect-all validation pattern, validate_enums() function
- `cli/lib/task_pack_schema.py` — frozen dataclass pattern, validate() pattern
- `cli/lib/qa_schemas.py` — _require(), _enum_check() helper functions

### Prior Context
- `.planning/phases/12-schema-layer/12-CONTEXT.md` — schema file patterns
- `.planning/phases/12-schema-layer/12-CONTEXT.md §D-04` — dataclass(frozen=True) + validation function pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_require()`, `_enum_check()` helpers from qa_schemas.py
- EnumGuardViolation dataclass from enum_guard.py
- Frozen dataclass pattern from task_pack_schema.py

### Established Patterns
- dataclass(frozen=True) for immutable definitions
- validate(data: dict) -> Dataclass pattern
- validate_file(path) -> Dataclass pattern
- CLI main() with --type/--object flags
- Collect-all validation (enum_guard.validate_enums)

### Integration Points
- enum_guard.py — for validating enum fields within governance objects
- cli/lib/protocol.py — Phase 15 will integrate governance_validator into SSOT write path

</code_context>

<specifics>
## Specific Ideas

- 11 objects with enum fields should call enum_guard.validate_enums() internally
- Gate object has verdict field that uses gate_verdict enum
- Module object has module_id field that uses module_id enum
- Skill object has skill_id field that uses skill_id enum
- StateMachine object has states field that may reference phase enum

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-governance-validator*
*Context gathered: 2026-04-22*
