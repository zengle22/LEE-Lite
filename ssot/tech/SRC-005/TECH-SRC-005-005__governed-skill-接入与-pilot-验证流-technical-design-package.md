---
id: TECH-SRC-005-005
ssot_type: TECH
tech_ref: TECH-SRC-005-005
feat_ref: FEAT-SRC-005-005
title: governed skill 接入与 pilot 验证流 Technical Design Package
status: accepted
schema_version: 1.0.0
workflow_key: dev.feat-to-tech
workflow_run_id: adr011-raw2src-fix-20260327-r1--feat-src-005-005
candidate_package_ref: artifacts/feat-to-tech/adr011-raw2src-fix-20260327-r1--feat-src-005-005
gate_decision_ref: artifacts/active/gates/decisions/feat-to-tech-adr011-raw2src-fix-20260327-r1--feat-src-005-005-tech-design-bundle-decision.json
frozen_at: '2026-03-29T14:26:55Z'
---

# governed skill 接入与 pilot 验证流 Technical Design Package


## Selected FEAT

- feat_ref: `FEAT-SRC-005-005`
- title: governed skill 接入与 pilot 验证流
- axis_id: skill-adoption-e2e
- resolved_axis: adoption_e2e
- epic_freeze_ref: `EPIC-SRC-005-001`
- src_root_id: `SRC-005`
- goal: 冻结 governed skill 的 onboarding、pilot、cutover 与 fallback 规则，让主链能力通过真实链路验证成立。
- authoritative_artifact: pilot evidence package
- upstream_feat: FEAT-SRC-005-001, FEAT-SRC-005-002, FEAT-SRC-005-003, FEAT-SRC-005-004
- downstream_feat: None
- gate_decision_dependency_feat_refs: FEAT-SRC-005-002
- admission_dependency_feat_refs: FEAT-SRC-005-003

## Need Assessment

- arch_required: True
  - ARCH required by boundary/runtime placement.
  - Keyword hits: 边界.
- api_required: True
  - API required by command-level contract surface.
  - Keyword hits: consumer, handoff, proposal.

## TECH Design

- Design focus:
  - Freeze a concrete TECH design for governed skill 接入与 pilot 验证流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.
- Implementation rules:
  - Epic-level constraints：当 rollout_required 为 true 时，foundation 与 adoption_e2e 必须同时落成，并至少保留一条真实 producer -> consumer -> audit -> gate pilot 主链。
  - Epic-level constraints：本 EPIC 直接负责形成可被多 skill 共享继承的主链受治理交接闭环，而不是回退为单一上游业务对象清单。
  - Epic-level constraints：主能力轴固定为：主链 loop / handoff / gate 协作、candidate -> formal 物化链、对象分层与准入、主链交接对象的 IO / 路径边界；这些能力轴作为 cross-cutting constraints 约束多个 FEAT。
  - Onboarding / migration_cutover 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。
  - Onboarding scope and migration waves are explicit: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.
  - At least one real pilot chain is required: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.
  - Adoption scope does not expand into repository-wide governance: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.
- Non-functional requirements:
  - Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
  - Keep the package freeze-ready by recording execution evidence and supervision evidence.
  - Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
  - Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.

### Implementation Carrier View
- Foundation 能力先稳定，再把 governed skill 按 onboarding matrix 与 migration wave 接入主链。
- Pilot chain 必须覆盖 producer -> gate -> formal object -> consumer -> audit 的真实闭环，而不是组件内局部验证。
- Cutover controller 只负责切换与回退边界，不重写 foundation FEAT 或 ADR-005 的实现模块。

```text
[cli/commands/rollout/command.py]
              |
              v
[cli/lib/rollout_state.py] --> [cli/lib/pilot_chain.py] --> [Pilot / Cutover Evidence]
              |
              +--> [cli/commands/audit/command.py]
```

### State Model
- `skill_registered` -> `pilot_enabled` -> `cutover_guarded` -> `e2e_verified` -> `wave_accepted`
- `cutover_guarded(fail)` -> `fallback_triggered` -> `pilot_enabled`

### Module Plan
- Handoff runtime adapter：负责把受治理对象写入/读取主链 runtime，并维持 traceability。
- Decision boundary adapter：负责把上游 FEAT 约束映射成 runtime 可执行边界，不把实现责任散落到业务 skill。
- Onboarding registry：记录 governed skill 接入矩阵、scope 与 migration wave。
- Pilot orchestration verifier：收集 producer -> consumer -> audit -> gate 的真实闭环证据并支撑 cutover/fallback。

### Implementation Strategy
- 先冻结 onboarding matrix、pilot chain 和 cutover guard，再按 wave 接入 governed skill。
- 先跑最小真实 producer -> consumer -> audit -> gate pilot，稳定后再扩大接入波次。
- 每个 wave 都必须保留 fallback 条件与 rollback evidence，不能一次性全量切换。

### Implementation Unit Mapping
- `cli/lib/protocol.py` (`extend`): 定义 `OnboardingMatrix`、`CutoverDirective`、`PilotEvidenceRef` 结构。
- `cli/lib/rollout_state.py` (`new`): 保存 onboarding wave、cutover state 和 fallback marker。
- `cli/lib/pilot_chain.py` (`new`): 校验 producer -> consumer -> audit -> gate 的真实闭环证据。
- `cli/commands/rollout/command.py` (`extend`): 提供 onboarding wave、cutover、fallback 操作，依赖 `cli/lib/rollout_state.py`。
- `cli/commands/audit/command.py` (`extend`): 消费 pilot evidence 并把 findings 回交给 cutover decision。

### Interface Contracts
- `OnboardingDirective`: input=`skill_ref`, `wave_id`, `scope`, `compat_mode`; output=`status`, `runtime_binding_ref`, `cutover_guard_ref`; errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent=`yes by skill_ref + wave_id`; precondition=`foundation features freeze-ready`。
- `PilotEvidenceSubmission`: input=`pilot_chain_ref`, `producer_ref`, `consumer_ref`, `audit_ref`, `gate_ref`; output=`evidence_status`, `cutover_recommendation`; errors=`missing_chain_step`, `audit_not_traceable`; idempotent=`yes by pilot_chain_ref`; precondition=`pilot chain 已完整执行一次`。

### Main Sequence
- 1. resolve onboarding directive and targeted wave
- 2. verify foundation readiness and compat mode
- 3. bind selected skill to mainline runtime / gate hooks
- 4. run pilot chain and capture producer -> consumer -> audit -> gate evidence
- 5. evaluate cutover guard and emit fallback recommendation when needed
- 6. persist wave status and rollout evidence

```text
Producer -> Runtime : emit governed object
Runtime  -> Gate    : route through mainline gate
Gate     -> Consumer: publish formal refs
Consumer -> Audit   : produce audit evidence
Audit    -> Gate    : confirm pilot readiness or fallback
```

### Exception and Compensation
- pilot chain 中任一步 evidence 缺失：cutover 直接 fail closed，维持 compat mode。
- cutover success 但 audit handoff fail：允许 partial success，但 wave 状态标记 `audit_pending`，禁止扩大 rollout。
- fallback trigger fail：保留 current wave 冻结，要求人工介入，不允许自动继续下一波次。

### Integration Points
- 调用方：现有 governed skill 的 onboarding/cutover 由 `cli/commands/rollout/command.py` 发起，audit findings 由 `cli/commands/audit/command.py` 消费。
- 挂接点：compat mode 在 skill 接入 wave 前打开；file-handoff 和 gate/repair 路径必须进入 pilot evidence 链。
- 旧系统兼容：先接入选定 pilot skill，再按 wave 扩大；未在 onboarding matrix 内的旧 skill 保持现状不切换。

### Minimal Code Skeleton
- Happy path:
```python
def run_pilot_wave(directive: OnboardingDirective) -> PilotWaveResult:
    binding = bind_skill_to_mainline(directive.skill_ref, directive.compat_mode)
    evidence = execute_pilot_chain(binding, directive.scope)
    verdict = evaluate_cutover_guard(evidence)
    persist_wave_state(directive.wave_id, verdict, evidence)
    return PilotWaveResult(binding_ref=binding.binding_ref, cutover_verdict=verdict)
```

- Failure path:
```python
def run_pilot_wave_with_fallback(directive: OnboardingDirective) -> PilotWaveResult:
    binding = bind_skill_to_mainline(directive.skill_ref, directive.compat_mode)
    evidence = execute_pilot_chain(binding, directive.scope)
    if not evidence.is_complete:
        keep_compat_mode(binding.binding_ref)
        return PilotWaveResult.fail(reason='pilot_evidence_incomplete')
    return run_pilot_wave(directive)
```

## Optional ARCH

- arch_ref: `ARCH-SRC-005-005`
- summary_topics:
  - Boundary to foundation FEATs: 本 FEAT 只定义 onboarding/pilot/cutover 挂接边界，不重写 collaboration、gate decision/publication、IO foundation internals。
  - Boundary to audit/gate consumption: 本 FEAT 组织 pilot evidence 与 cutover routing，不新建平行 decision 体系。
  - Dedicated rollout placement is required so wave state、compat mode 与 fallback remain authoritative across skill adoption.
- see: `arch-design.md`

## Optional API

- api_ref: `API-SRC-005-005`
- contract_surfaces:
  - skill onboarding contract
  - pilot evidence submission contract
- command_refs:
  - `ll rollout onboard-skill`
  - `ll audit submit-pilot-evidence`
- response_envelope:
  - success: `{ ok: true, command_ref, trace_ref, result }`
  - error: `{ ok: false, command_ref, trace_ref, error }`
- see: `api-contract.md`

## Cross-Artifact Consistency

- passed: True
- structural_passed: True
- semantic_passed: True
- checks:
  - [structural] TECH mandatory: True (TECH is always emitted for the selected FEAT.)
  - [structural] Traceability present: True (Selected FEAT carries authoritative source refs for downstream design derivation.)
  - [structural] ARCH coverage: True (ARCH coverage matches the selected FEAT boundary needs.)
  - [structural] API coverage: True (API coverage includes concrete command-level contracts.)
  - [semantic] ARCH / TECH separation: True (ARCH keeps boundary placement while TECH keeps implementation carriers.)
  - [semantic] API contract completeness: True (API contracts carry schema, semantics, invariants, and canonical refs.)
- issues:
  - None
- minor_open_items:
  - Freeze a command-level error mapping table for `code -> retryable -> idempotent_replay` in a later API revision if validator-grade contract testing needs a closed semantics table.
  - Optional ARCH/API summaries are still embedded in the bundle for one-shot review; a later revision may collapse them to pure references to reduce duplication risk.

## Downstream Handoff

- target_workflow: workflow.dev.tech_to_impl
- tech_ref: `TECH-SRC-005-005`
- arch_ref: `ARCH-SRC-005-005`
- api_ref: `API-SRC-005-005`

## Traceability

- Need Assessment: scope, dependencies, acceptance_checks <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-005, EPIC-SRC-005-001, SRC-005
- TECH Design: goal, scope, constraints <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-005, EPIC-SRC-005-001, SRC-005
- Cross-Artifact Consistency: dependencies, outputs, acceptance_checks <- product.epic-to-feat::adr011-raw2src-fix-20260327-r1, FEAT-SRC-005-005, EPIC-SRC-005-001, SRC-005
