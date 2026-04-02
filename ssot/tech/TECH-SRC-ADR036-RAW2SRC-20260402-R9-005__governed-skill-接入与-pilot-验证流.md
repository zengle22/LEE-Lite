---
id: "TECH-SRC-ADR036-RAW2SRC-20260402-R9-005"
ssot_type: TECH
title: governed skill 接入与 pilot 验证流
status: accepted
schema_version: 1.0.0
workflow_key: "dev.feat-to-tech"
workflow_run_id: "adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-005"
source_refs:
- "product.epic-to-feat::adr036-src2epic-20260402-r4"
- "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005"
- "TECH-SRC-ADR036-RAW2SRC-20260402-R9-005"
- "EPIC-IMPL-IMPLEMENTATION-READINESS"
- "SRC-ADR036-RAW2SRC-20260402-R9"
- "product.raw-to-src::adr036-raw2src-20260402-r9"
- "ADR-036"
- "ADR-014"
- "ADR-033"
- "ADR-034"
- "ADR-035"
- "product.src-to-epic::adr036-raw2src-20260402-r10"
candidate_artifact_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-005/tech-spec.md"
gate_decision_ref: "artifacts/active/gates/decisions/adr036-chain-manual-approval-20260402.json"
parent_id: "FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005"
arch_ref: "ARCH-SRC-ADR036-RAW2SRC-20260402-R9-005"
api_ref: "API-SRC-ADR036-RAW2SRC-20260402-R9-005"
candidate_package_ref: "artifacts/feat-to-tech/adr036-src2epic-20260402-r4--feat-src-adr036-raw2src-20260402-r9-005"
---

# TECH-SRC-ADR036-RAW2SRC-20260402-R9-005

## Overview

把 governed skill 的接入、pilot、cutover 与 fallback 冻结成可验证的业务接入流，而不是把上线建立在口头假设上。

## Design Focus

- Freeze a concrete TECH design for governed skill 接入与 pilot 验证流, preserving FEAT semantics while making runtime carriers and contracts implementation-ready.

## Implementation Rules

- 来源与依赖约束：`IMPL` 是主测试对象，`FEAT / TECH / ARCH / API / UI / TESTSET` 是联动 authority。
- 来源与依赖约束：authoritative upstream objects 冲突时，workflow 只能检测、升级并建议修复目标，不得自行建立新的 business truth 或 design truth。
- 来源与依赖约束：workflow 至少覆盖功能逻辑、数据与状态、用户旅程、UI 可用性、API 契约、实施可执行性、可测试性、兼容迁移风险 8 个维度。
- Onboarding / migration_cutover 只面向本主链治理能力涉及的 governed skill 接入，不扩大为仓库级全局文件治理改造。
- Onboarding scope and migration waves are explicit: The FEAT must define onboarding scope, migration waves, and cutover / fallback rules without pretending all governed skills migrate at once.
- At least one real pilot chain is required: The FEAT must require at least one real producer -> consumer -> audit -> gate pilot chain instead of relying only on component-local tests.
- Adoption scope does not expand into repository-wide governance: The FEAT must keep onboarding limited to governed skills in the mainline capability scope and reject warehouse-wide governance expansion.
- Revision constraint: Gate revise: round 1 | semantic_lock_preservation | Preserve implementation_readiness_rule semantic lock: keep qa.impl-spec-test as a pre-implementation gate only, keep IMPL as the main tested object, keep upstream...

## Non-Functional Requirements

- Preserve FEAT, EPIC, and SRC traceability across every emitted design object.
- Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.
- Keep the package freeze-ready by recording execution evidence and supervision evidence.
- Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.

## Implementation Carrier View

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

## State Model

- `skill_registered` -> `pilot_enabled` -> `cutover_guarded` -> `e2e_verified` -> `wave_accepted`
- `cutover_guarded(fail)` -> `fallback_triggered` -> `pilot_enabled`

## Module Plan

- Handoff runtime adapter：负责把受治理对象写入/读取主链 runtime，并维持 traceability。
- Decision boundary adapter：负责把上游 FEAT 约束映射成 runtime 可执行边界，不把实现责任散落到业务 skill。
- Onboarding registry：记录 governed skill 接入矩阵、scope 与 migration wave。
- Pilot orchestration verifier：收集 producer -> consumer -> audit -> gate 的真实闭环证据并支撑 cutover/fallback。

## Implementation Strategy

- 先冻结 onboarding matrix、pilot chain 和 cutover guard，再按 wave 接入 governed skill。
- 先跑最小真实 producer -> consumer -> audit -> gate pilot，稳定后再扩大接入波次。
- 每个 wave 都必须保留 fallback 条件与 rollback evidence，不能一次性全量切换。

## Implementation Unit Mapping

- `cli/lib/protocol.py` (`extend`): 定义 `OnboardingMatrix`、`CutoverDirective`、`PilotEvidenceRef` 结构。
- `cli/lib/rollout_state.py` (`new`): 保存 onboarding wave、cutover state 和 fallback marker。
- `cli/lib/pilot_chain.py` (`new`): 校验 producer -> consumer -> audit -> gate 的真实闭环证据。
- `cli/commands/rollout/command.py` (`extend`): 提供 onboarding wave、cutover、fallback 操作，依赖 `cli/lib/rollout_state.py`。
- `cli/commands/audit/command.py` (`extend`): 消费 pilot evidence 并把 findings 回交给 cutover decision。

## Interface Contracts

- `OnboardingDirective`: input=`skill_ref`, `wave_id`, `scope`, `compat_mode`; output=`status`, `runtime_binding_ref`, `cutover_guard_ref`; errors=`unknown_skill`, `scope_invalid`, `foundation_missing`; idempotent=`yes by skill_ref + wave_id`; precondition=`foundation features freeze-ready`。
- `PilotEvidenceSubmission`: input=`pilot_chain_ref`, `producer_ref`, `consumer_ref`, `audit_ref`, `gate_ref`; output=`evidence_status`, `cutover_recommendation`; errors=`missing_chain_step`, `audit_not_traceable`; idempotent=`yes by pilot_chain_ref`; precondition=`pilot chain 已完整执行一次`。

## Main Sequence

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

## Exception and Compensation

- pilot chain 中任一步 evidence 缺失：cutover 直接 fail closed，维持 compat mode。
- cutover success 但 audit handoff fail：允许 partial success，但 wave 状态标记 `audit_pending`，禁止扩大 rollout。
- fallback trigger fail：保留 current wave 冻结，要求人工介入，不允许自动继续下一波次。

## Integration Points

- 调用方：现有 governed skill 的 onboarding/cutover 由 `cli/commands/rollout/command.py` 发起，audit findings 由 `cli/commands/audit/command.py` 消费。
- 挂接点：compat mode 在 skill 接入 wave 前打开；file-handoff 和 gate/repair 路径必须进入 pilot evidence 链。
- 旧系统兼容：先接入选定 pilot skill，再按 wave 扩大；未在 onboarding matrix 内的旧 skill 保持现状不切换。

## Minimal Code Skeleton

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

## Traceability

- Need Assessment: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
- TECH Design: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
- Cross-Artifact Consistency: product.epic-to-feat::adr036-src2epic-20260402-r4, FEAT-SRC-ADR036-RAW2SRC-20260402-R9-005, EPIC-IMPL-IMPLEMENTATION-READINESS, SRC-ADR036-RAW2SRC-20260402-R9
