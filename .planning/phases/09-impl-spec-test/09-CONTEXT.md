# Phase 09: 执行语义稳定 + impl-spec-test 增强 - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

在 `ll-qa-impl-spec-test` 中集成语义稳定性检查（第9维度），交付静默覆盖防护机制。
所有 `ll-dev-*` 技能的 `validate_output.sh` 加 `silent_override.py` 校验。

4 requirements: STAB-01, STAB-02, STAB-03, STAB-04
3 plans: silent_override.py, impl-spec-test 加第9维度, 所有 dev skills 的 validate_output.sh 更新
</domain>

<decisions>
## Implementation Decisions

### Baseline Selection
- **D-01:** silent_override.py 比对输出产物与 **FRZ 锚点语义**（非 FEAT baseline）
- **D-02:** 直接使用 Phase 8 的 `drift_detector.py`，不重新实现
- **D-03:** 需要 FRZ 加载能力（通过 `frz_registry` 或文件路径引用）

### Block vs Pass Threshold（分级裁决）
- **D-04:** 以下情况 **block**：anchor missing、语义篡改（tampered）、constraint violation、新字段超出 derived_allowed
- **D-05:** 以下情况 **pass_with_revisions**：允许范围内的额外字段、expired known_unknown 仍开放
- **D-06:** semantic_stability 维度 verdict 中必须包含 `semantic_drift` 字段

### Dev Skill Scope
- **D-07:** 所有 6 个 `ll-dev-*` 技能都加 silent_override 检查，但使用**分层 baseline**：
  - `feat-to-tech`, `tech-to-impl` → 完整 FRZ 锚点比对
  - `feat-to-ui`, `proto-to-ui` → 仅 JRN/SM 锚点
  - `feat-to-proto`, `feat-to-surface-map` → 轻量 product_boundary 检查

### Classifier Behavior
- **D-08:** 基于规则的自动化分类（clarification vs semantic_change），不使用 LLM 或人工审查门
- **D-09:** 判断标准：输出新增/修改/删除的字段若映射到 FRZ 锚点 → 检查锚点名称匹配且内容为补充 → clarification；锚点名称不同或内容矛盾 → semantic_change
- **D-10:** semantic_change 判定标准与 ADR-050 §5.2 一致：导致下游测试用例预期行为变化的变更 = 语义变更

### Claude's Discretion
- silent_override.py 的具体实现路径选择（直接库 vs 独立脚本）
- validate_output.sh 中的错误输出格式
- 第9维度在 dimension_reviews JSON 中的具体结构

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core governance
- `ssot/adr/ADR-050-SSOT语义治理总纲.md` — 总纲，§5 执行语义稳定、§6 变更分级
- `.planning/REQUIREMENTS.md` — STAB-01~04 需求定义
- `.planning/ROADMAP.md` — Phase 9 goal + success criteria

### Phase 8 artifacts (dependencies)
- `.planning/phases/08-frz-src/08-01-SUMMARY.md` — drift_detector implementation
- `cli/lib/drift_detector.py` — 漂移检测库（直接复用）
- `cli/lib/projection_guard.py` — 投影不变性守卫

### Existing impl-spec-test
- `skills/ll-qa-impl-spec-test/scripts/impl_spec_test_skill_guard.py` — 现有 8 维度校验

### Dev skills (all need validate_output.sh update)
- `skills/ll-dev-feat-to-tech/scripts/validate_output.sh`
- `skills/ll-dev-tech-to-impl/scripts/validate_output.sh`
- `skills/ll-dev-feat-to-ui/scripts/validate_output.sh`
- `skills/ll-dev-proto-to-ui/scripts/validate_output.sh`
- `skills/ll-dev-feat-to-proto/scripts/validate_output.sh`
- `skills/ll-dev-feat-to-surface-map/scripts/validate_output.sh`
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cli/lib/drift_detector.py` — 漂移检测库，27 tests passing，含 check_drift/check_derived_allowed/check_constraints/check_known_unknowns
- `cli/lib/projection_guard.py` — 投影守卫，9 tests passing
- `cli/lib/anchor_registry.py` — 锚点注册表（Phase 8 extended for multi-projection）
- `cli/lib/frz_extractor.py` — FRZ 加载与抽取

### Established Patterns
- impl-spec-test 使用 JSON envelope with `_ref` field resolution pattern
- validate_output.sh 作为 dev skill 的输出校验入口
- 8 个 ADR-036 维度审查结构（functional_logic, data_modeling, user_journey, etc.）

### Integration Points
- `impl_spec_test_skill_guard.py:validate_output()` 需加第9维度检查
- 每个 dev skill 的 `validate_output.sh` 需调用 `python cli/lib/silent_override.py check`
- dimension_reviews JSON 需加 `semantic_stability` key
</code_context>

<specifics>
## Specific Ideas

- Phase 8 的验证中发现了一个 bug（check_constraints 不检查 output_data["constraints"] 列表），已在执行中修复。silent_override 不应重复此 bug。
- ADR-050 §5.2 的判据："如果一个变更会导致下游测试用例的预期行为发生变化，它就是语义变更" — 这是分类器的核心判断标准。
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-impl-spec-test*
*Context gathered: 2026-04-18*
